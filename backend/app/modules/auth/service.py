import json
import secrets

import jwt
import sqlalchemy as sa
from fastapi import HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.queue import enqueue
from app.core.redis import get_redis
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.modules.auth.schemas import RegisterRequest
from app.modules.users.models import OAuthAccount, User

CODE_KEY = "emailcode:{email}"
RESEND_KEY = "emailcode_sent:{email}"
REFRESH_KEY = "refresh:{jti}"
USER_SESSIONS_KEY = "user_sessions:{user_id}"
WS_TICKET_KEY = "wsticket:{ticket}"


def _generate_code() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


async def _store_and_send_code(email: str) -> None:
    redis = get_redis()
    code = _generate_code()
    await redis.set(CODE_KEY.format(email=email), code, ex=settings.email_code_ttl_seconds)
    await redis.set(RESEND_KEY.format(email=email), "1", ex=settings.email_code_resend_seconds)
    await enqueue("send_verification_email", email, code)


async def register_user(db: AsyncSession, data: RegisterRequest) -> User:
    existing = await db.scalar(
        select(User).where(or_(User.email == data.email, User.username == data.username))
    )
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email or username already in use",
        )
    user = User(
        email=data.email,
        username=data.username,
        display_name=data.display_name,
        password_hash=await hash_password(data.password),
    )
    db.add(user)
    try:
        await db.commit()
    except sa.exc.IntegrityError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email or username already in use",
        ) from exc
    await db.refresh(user)
    await _store_and_send_code(data.email)
    return user


async def request_email_code(db: AsyncSession, email: str) -> None:
    user = await db.scalar(select(User).where(User.email == email))
    # Don't reveal whether the address exists / is already verified.
    if user is None or user.email_verified:
        return
    if await get_redis().exists(RESEND_KEY.format(email=email)):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="A code was sent recently; please wait before requesting another",
        )
    await _store_and_send_code(email)


def _is_admin_email(email: str) -> bool:
    return email.lower() in settings.admin_email_set


async def verify_email(db: AsyncSession, email: str, code: str) -> User:
    redis = get_redis()
    stored = await redis.get(CODE_KEY.format(email=email))
    if stored is None or stored != code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired code",
        )
    user = await db.scalar(select(User).where(User.email == email))
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    user.email_verified = True
    if _is_admin_email(user.email):
        user.is_admin = True
    await db.commit()
    await redis.delete(CODE_KEY.format(email=email))
    return user


_invalid_credentials = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
)


async def authenticate(db: AsyncSession, email: str, password: str) -> User:
    user = await db.scalar(select(User).where(User.email == email))
    if user is None or user.password_hash is None:
        raise _invalid_credentials
    if not await verify_password(user.password_hash, password):
        raise _invalid_credentials
    if user.is_banned:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "This account has been banned")
    if _is_admin_email(user.email) and not user.is_admin:
        user.is_admin = True
        await db.commit()
    return user


async def issue_tokens(user: User, parent_jti: str | None = None) -> tuple[str, str]:
    """Return (access_token, refresh_token); refresh jti is allow-listed in Redis."""
    access = create_access_token(str(user.id))
    refresh, jti = create_refresh_token(str(user.id))
    redis = get_redis()
    # Store token with its user_id and parent_jti (for family tracking)
    user_id_str = str(user.id)
    data = {"sub": user_id_str}
    if parent_jti:
        data["parent"] = parent_jti
    await redis.set(
        REFRESH_KEY.format(jti=jti), json.dumps(data), ex=settings.refresh_token_ttl_seconds
    )
    # Add JTI to the user's active session set
    res = redis.sadd(USER_SESSIONS_KEY.format(user_id=user_id_str), jti)
    if not isinstance(res, int):
        await res
    return access, refresh


_invalid_refresh = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token"
)


async def rotate_refresh(refresh_token: str) -> tuple[str, str]:
    redis = get_redis()
    try:
        payload = decode_token(refresh_token, "refresh")
    except jwt.PyJWTError as exc:
        raise _invalid_refresh from exc

    jti, sub = payload["jti"], payload["sub"]
    key = REFRESH_KEY.format(jti=jti)
    stored_raw = await redis.get(key)

    if stored_raw is None:
        # POTENTIAL THEFT: Token is not in the allowlist.
        # Check if it's a known REUSED token (we mark them on rotation).
        if await redis.exists(f"reused:{jti}"):
            # Re-use detected! Revoke the whole family.
            # In a real system, we'd follow the 'parent' chain or use a family_id.
            # For this MVP, we'll revoke all refresh tokens for this user as a safety measure.
            await _revoke_all_for_user(sub)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Security breach detected: refresh token reuse. All sessions revoked.",
            )
        raise _invalid_refresh

    stored = json.loads(stored_raw)
    if stored["sub"] != sub:
        raise _invalid_refresh

    # Mark this token as rotated/used for a short grace period to detect reuse.
    await redis.delete(key)
    res_srem = redis.srem(USER_SESSIONS_KEY.format(user_id=sub), jti)
    if not isinstance(res_srem, int):
        await res_srem
    await redis.set(f"reused:{jti}", "1", ex=3600)

    access = create_access_token(sub)
    new_refresh, new_jti = create_token_family_member(sub, jti)
    # Re-issue tokens manually to link to parent_jti
    data = {"sub": sub, "parent": jti}
    await redis.set(
        REFRESH_KEY.format(jti=new_jti), json.dumps(data), ex=settings.refresh_token_ttl_seconds
    )
    res_sadd = redis.sadd(USER_SESSIONS_KEY.format(user_id=sub), new_jti)
    if not isinstance(res_sadd, int):
        await res_sadd
    return access, new_refresh


async def _revoke_all_for_user(user_id: str) -> None:
    redis = get_redis()
    sessions_key = USER_SESSIONS_KEY.format(user_id=user_id)
    res_smembers = redis.smembers(sessions_key)
    jtis = await res_smembers if not isinstance(res_smembers, set) else res_smembers
    for jti in jtis:
        await redis.delete(REFRESH_KEY.format(jti=jti))
    await redis.delete(sessions_key)


async def issue_ws_ticket(user: User) -> str:
    redis = get_redis()
    ticket = secrets.token_urlsafe(32)
    await redis.set(WS_TICKET_KEY.format(ticket=ticket), str(user.id), ex=10)
    return ticket


async def verify_ws_ticket(ticket: str) -> str | None:
    redis = get_redis()
    key = WS_TICKET_KEY.format(ticket=ticket)
    user_id = await redis.get(key)
    if user_id:
        await redis.delete(key)
        return user_id
    return None


def create_token_family_member(subject: str, parent_jti: str) -> tuple[str, str]:
    # We can reuse create_token but we don't strictly need parent_jti in the JWT itself
    # as we track it in Redis. But having it in the JWT can help for stateless checks.
    return create_refresh_token(subject)


async def revoke_refresh(refresh_token: str) -> None:
    try:
        payload = decode_token(refresh_token, "refresh")
    except jwt.PyJWTError:
        return
    jti = payload["jti"]
    sub = payload["sub"]
    redis = get_redis()
    await redis.delete(REFRESH_KEY.format(jti=jti))
    res_srem = redis.srem(USER_SESSIONS_KEY.format(user_id=sub), jti)
    if not isinstance(res_srem, int):
        await res_srem


async def get_or_create_oauth_user(
    db: AsyncSession,
    provider: str,
    provider_user_id: str,
    email: str,
    display_name: str,
) -> User:
    account = await db.scalar(
        select(OAuthAccount).where(
            OAuthAccount.provider == provider,
            OAuthAccount.provider_user_id == provider_user_id,
        )
    )
    if account is not None:
        user = await db.get(User, account.user_id)
        assert user is not None
        if user.is_banned:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "This account has been banned")
        if _is_admin_email(user.email) and not user.is_admin:
            user.is_admin = True
            await db.commit()
        return user

    # Link to an existing email account, or create a new verified user.
    user = await db.scalar(select(User).where(User.email == email))
    if user is not None and user.is_banned:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "This account has been banned")
    if user is None:
        user = User(
            email=email,
            username=await _unique_username(db, email),
            display_name=display_name or email.split("@")[0],
            email_verified=True,
        )
        db.add(user)
        await db.flush()
    if _is_admin_email(email):
        user.is_admin = True
    user.oauth_accounts.append(OAuthAccount(provider=provider, provider_user_id=provider_user_id))
    await db.commit()
    await db.refresh(user)
    return user


async def _unique_username(db: AsyncSession, email: str) -> str:
    base = "".join(c for c in email.split("@")[0] if c.isalnum())[:24] or "user"
    candidate = base
    while await db.scalar(select(User.id).where(User.username == candidate)) is not None:
        candidate = f"{base}{secrets.randbelow(10000)}"
    return candidate
