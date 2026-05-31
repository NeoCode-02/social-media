import secrets

import jwt
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
    await db.commit()
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
    return user


async def issue_tokens(user: User) -> tuple[str, str]:
    """Return (access_token, refresh_token); refresh jti is allow-listed in Redis."""
    access = create_access_token(str(user.id))
    refresh, jti = create_refresh_token(str(user.id))
    await get_redis().set(
        REFRESH_KEY.format(jti=jti), str(user.id), ex=settings.refresh_token_ttl_seconds
    )
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
    stored = await redis.get(key)
    if stored is None or stored != sub:
        raise _invalid_refresh
    await redis.delete(key)  # rotate: old token can't be reused
    access = create_access_token(sub)
    new_refresh, new_jti = create_refresh_token(sub)
    await redis.set(REFRESH_KEY.format(jti=new_jti), sub, ex=settings.refresh_token_ttl_seconds)
    return access, new_refresh


async def revoke_refresh(refresh_token: str) -> None:
    try:
        payload = decode_token(refresh_token, "refresh")
    except jwt.PyJWTError:
        return
    await get_redis().delete(REFRESH_KEY.format(jti=payload["jti"]))


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
        return user

    # Link to an existing email account, or create a new verified user.
    user = await db.scalar(select(User).where(User.email == email))
    if user is None:
        user = User(
            email=email,
            username=await _unique_username(db, email),
            display_name=display_name or email.split("@")[0],
            email_verified=True,
        )
        db.add(user)
        await db.flush()
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
