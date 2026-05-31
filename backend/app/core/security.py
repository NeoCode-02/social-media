import uuid
from datetime import UTC, datetime, timedelta
from typing import Any, Literal

import anyio
import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from app.core.config import settings

_hasher = PasswordHasher()

TokenType = Literal["access", "refresh"]


async def hash_password(password: str) -> str:
    """Argon2 hash, run off the event loop (CPU-bound)."""
    return await anyio.to_thread.run_sync(_hasher.hash, password)


async def verify_password(hashed: str, password: str) -> bool:
    def _verify() -> bool:
        try:
            _hasher.verify(hashed, password)
            return True
        except VerifyMismatchError:
            return False

    return await anyio.to_thread.run_sync(_verify)


def _now() -> datetime:
    return datetime.now(UTC)


def create_token(
    subject: str,
    token_type: TokenType,
    ttl_seconds: int,
    jti: str | None = None,
) -> tuple[str, str]:
    """Return (encoded_jwt, jti)."""
    token_id = jti or str(uuid.uuid4())
    now = _now()
    payload: dict[str, Any] = {
        "sub": subject,
        "type": token_type,
        "jti": token_id,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=ttl_seconds)).timestamp()),
    }
    encoded = jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)
    return encoded, token_id


def create_access_token(subject: str) -> str:
    token, _ = create_token(subject, "access", settings.access_token_ttl_seconds)
    return token


def create_refresh_token(subject: str) -> tuple[str, str]:
    return create_token(subject, "refresh", settings.refresh_token_ttl_seconds)


def decode_token(token: str, expected_type: TokenType) -> dict[str, Any]:
    """Decode + validate signature/exp/type. Raises jwt exceptions on failure."""
    payload: dict[str, Any] = jwt.decode(
        token, settings.secret_key, algorithms=[settings.jwt_algorithm]
    )
    if payload.get("type") != expected_type:
        raise jwt.InvalidTokenError(f"expected {expected_type} token")
    return payload
