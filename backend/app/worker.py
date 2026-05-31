"""ARQ worker. Run with: ``uv run arq app.worker.WorkerSettings``."""

from typing import Any

from app.core.config import settings
from app.core.email import send_email
from app.core.queue import redis_settings


async def send_verification_email(ctx: dict[str, Any], email: str, code: str) -> None:
    await send_email(
        to=email,
        subject="Your verification code",
        body=(
            f"Welcome to {settings.app_name}!\n\n"
            f"Your verification code is: {code}\n\n"
            f"It expires in {settings.email_code_ttl_seconds // 60} minutes."
        ),
    )


class WorkerSettings:
    functions = [send_verification_email]
    redis_settings = redis_settings()
