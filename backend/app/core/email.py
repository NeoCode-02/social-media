from email.message import EmailMessage

import aiosmtplib

from app.core.config import settings


async def send_email(to: str, subject: str, body: str) -> None:
    """Send a plain-text email via SMTP (Mailpit in dev)."""
    message = EmailMessage()
    message["From"] = settings.smtp_from
    message["To"] = to
    message["Subject"] = subject
    message.set_content(body)

    await aiosmtplib.send(
        message,
        hostname=settings.smtp_host,
        port=settings.smtp_port,
        username=settings.smtp_user or None,
        password=settings.smtp_password or None,
        use_tls=settings.smtp_use_tls,
    )
