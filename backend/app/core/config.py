from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration, loaded from environment / .env."""

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

    # CORS (comma-separated origins)
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

    # Security / JWT (override SECRET_KEY in production!)
    secret_key: str = "dev-insecure-secret-change-me-in-production-0123456789"
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


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
