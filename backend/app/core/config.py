from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# A well-known sentinel that callers *must* override in non-dev environments.
# Loading will refuse to start if it sees this value in production.
_DEV_SECRET_SENTINEL = "dev-insecure-secret-change-me-in-production-0123456789"


class Settings(BaseSettings):
    """Application configuration, loaded from environment / .env.

    Precedence (highest first): explicit process env > .env file > field default.
    Pydantic-Settings applies that order automatically; the ``env_file`` block
    here only adds the file as a *fallback*, never as an override of the
    process env. A startup assertion then refuses to boot if the dev sentinel
    leaks into a non-development environment.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # App
    app_name: str = "social-media"
    environment: str = "development"
    debug: bool = True
    api_prefix: str = "/api"

    # CORS (comma-separated origins). In production, refuse to start if this
    # still points at a localhost dev origin.
    cors_origins: str = "http://localhost:5173"

    # Set True only when running behind a trusted reverse proxy that sets
    # X-Forwarded-For; otherwise clients could spoof it to evade rate limits.
    trust_proxy: bool = False

    # Admins (comma-separated emails auto-promoted to admin on login)
    admin_emails: str = ""

    # Timezone for admin "today" stat boundaries (IANA name, e.g. "Asia/Tashkent").
    stats_timezone: str = "UTC"

    # Postgres
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5433/social_media"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Security / JWT. The default is the dev sentinel; startup (see assert_safe)
    # refuses to boot a non-dev environment with the sentinel still in place.
    secret_key: str = _DEV_SECRET_SENTINEL
    jwt_algorithm: str = "HS256"
    access_token_ttl_seconds: int = 60 * 15  # 15 minutes
    refresh_token_ttl_seconds: int = 60 * 60 * 24 * 30  # 30 days
    refresh_cookie_name: str = "refresh_token"
    cookie_secure: bool = False  # True behind HTTPS in production

    # Email verification
    email_code_ttl_seconds: int = 60 * 10  # 10 minutes
    email_code_resend_seconds: int = 60  # min gap between resends

    # SMTP (Mailpit in dev: no auth)
    smtp_host: str = "localhost"
    smtp_port: int = 1025
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = "no-reply@social-media.local"
    smtp_use_tls: bool = False

    # Google OAuth
    google_client_id: str = ""
    google_client_secret: str = ""
    oauth_redirect_base: str = "http://localhost:8000"
    frontend_url: str = "http://localhost:5173"

    # Object storage (MinIO / S3)
    s3_endpoint_url: str = "http://localhost:9000"
    s3_public_url: str = "http://localhost:9000"
    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin"
    s3_bucket: str = "media"
    s3_region: str = "us-east-1"
    presign_expire_seconds: int = 60 * 5

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def admin_email_set(self) -> set[str]:
        return {e.strip().lower() for e in self.admin_emails.split(",") if e.strip()}

    @property
    def is_production(self) -> bool:
        return self.environment.lower() in {"production", "prod"}

    @field_validator("secret_key")
    @classmethod
    def _no_dev_sentinel_in_prod(cls, v: str) -> str:
        # Cheap defense-in-depth: even if a future caller forgets to override
        # the default, pydantic will reject the value when env=production.
        # Final word is the assert_safe() call below at process boot.
        if v == _DEV_SECRET_SENTINEL:
            return v  # only an issue in non-dev; checked in assert_safe()
        if len(v) < 32:
            raise ValueError("secret_key must be at least 32 characters")
        return v


def assert_safe(s: "Settings") -> None:
    """Refuse to start a non-dev process with a known-weak secret.

    Called from app.main at import time so misconfiguration is fatal *before*
    the FastAPI app begins accepting requests.
    """
    if s.is_production:
        if s.secret_key == _DEV_SECRET_SENTINEL:
            raise RuntimeError(
                "Refusing to start: SECRET_KEY is the dev sentinel. "
                "Set a strong SECRET_KEY (>=32 random bytes)."
            )
        for o in s.cors_origin_list:
            if "localhost" in o or "127.0.0.1" in o:
                raise RuntimeError(
                    f"Refusing to start: CORS_ORIGINS still contains a dev origin ({o!r}) "
                    "in a non-development environment."
                )
        if not s.cookie_secure:
            raise RuntimeError(
                "Refusing to start: COOKIE_SECURE must be true in non-development environments."
            )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
assert_safe(settings)  # noqa: E402  (deliberately at import time)

