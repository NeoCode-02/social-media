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

    # Postgres
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5433/social_media"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
