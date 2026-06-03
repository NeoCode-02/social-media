"""Tests for the security primitives + the boot-time guard rails."""
import jwt
import pytest

from app.core.config import assert_safe
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


# --- Boot-time guard rails (Phase 1) ---


def test_secret_key_too_short_rejected():
    from app.core import config

    with pytest.raises(ValueError, match="at least 32"):
        config.Settings(secret_key="x" * 16, environment="dev")


def test_is_production_flag():
    from app.core import config

    prod = config.Settings(secret_key="x" * 32, environment="production")
    assert prod.is_production is True
    dev = config.Settings(secret_key="x" * 32, environment="dev")
    assert dev.is_production is False


def test_localhost_cors_in_prod_blocked():
    from app.core import config

    prod = config.Settings(
        secret_key="x" * 32,
        environment="production",
        cors_origins="https://app.example.com,http://localhost:3000",
        cookie_secure=True,
    )
    with pytest.raises(RuntimeError, match="localhost"):
        assert_safe(prod)


def test_insecure_cookie_in_prod_blocked():
    from app.core import config

    prod = config.Settings(
        secret_key="x" * 32,
        environment="production",
        cors_origins="https://app.example.com",
        cookie_secure=False,
    )
    with pytest.raises(RuntimeError, match="COOKIE_SECURE"):
        assert_safe(prod)


def test_prod_with_sane_settings_passes():
    from app.core import config

    prod = config.Settings(
        secret_key="x" * 64,
        environment="production",
        cors_origins="https://app.example.com",
        cookie_secure=True,
    )
    # Should not raise.
    assert_safe(prod)
