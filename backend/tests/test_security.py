import jwt
import pytest

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)


async def test_password_hash_roundtrip():
    hashed = await hash_password("s3cret-password")
    assert await verify_password(hashed, "s3cret-password")
    assert not await verify_password(hashed, "wrong-password")


def test_access_token_roundtrip():
    token = create_access_token("user-1")
    payload = decode_token(token, "access")
    assert payload["sub"] == "user-1"
    assert payload["type"] == "access"


def test_token_type_mismatch_rejected():
    token = create_access_token("user-1")
    with pytest.raises(jwt.InvalidTokenError):
        decode_token(token, "refresh")


def test_refresh_token_returns_jti():
    token, jti = create_refresh_token("user-2")
    payload = decode_token(token, "refresh")
    assert payload["jti"] == jti
    assert payload["sub"] == "user-2"
