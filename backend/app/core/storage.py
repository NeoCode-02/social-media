from functools import lru_cache
from typing import Any
from urllib.parse import quote

import boto3
from botocore.config import Config

from app.core.config import settings


@lru_cache
def get_s3_client() -> Any:
    return boto3.client(
        "s3",
        endpoint_url=settings.s3_endpoint_url,
        aws_access_key_id=settings.s3_access_key,
        aws_secret_access_key=settings.s3_secret_key,
        region_name=settings.s3_region,
        config=Config(signature_version="s3v4"),
    )


def presigned_put_url(key: str, content_type: str) -> str:
    """Presigned URL the client can PUT a file to directly (local crypto, no IO)."""
    return get_s3_client().generate_presigned_url(
        "put_object",
        Params={
            "Bucket": settings.s3_bucket,
            "Key": key,
            "ContentType": content_type,
        },
        ExpiresIn=settings.presign_expire_seconds,
    )


def _sanitize_download_name(raw: str) -> tuple[str, str]:
    """Make a user-supplied filename safe for Content-Disposition.

    Rules (RFC 6266 / 6266 §5):
      1. Drop all C0 controls (\\x00..\\x1F and \\x7F) — defends against header
         injection via ``\\r\\n`` smuggling and against broken clients.
      2. Cap length at 128 bytes (UTF-8).
      3. Replace path separators (\\ and /) so the user can't forge paths.
      4. Use ``filename*=<enc>`` so non-ASCII names render correctly; fall back
         to an ASCII-only ``filename=`` for ancient clients.
    """
    cleaned = "".join(c for c in raw if c.isprintable() and c not in "\\/")
    encoded = quote(cleaned, safe="")[:128]
    ascii_fallback = "".join(c if 32 <= ord(c) < 127 else "_" for c in cleaned)[:128]
    return encoded, ascii_fallback


def presigned_get_url(key: str, download_name: str | None = None) -> str:
    """Presigned GET URL. If download_name is set, the browser saves the file
    (Content-Disposition: attachment) with that name instead of opening it."""
    params: dict[str, Any] = {"Bucket": settings.s3_bucket, "Key": key}
    if download_name:
        encoded, ascii_fallback = _sanitize_download_name(download_name)
        if not encoded:
            return get_s3_client().generate_presigned_url(
                "get_object", Params=params, ExpiresIn=settings.presign_expire_seconds
            )
        # filename*=UTF-8''… is the modern form; filename=… is the fallback.
        params["ResponseContentDisposition"] = (
            f"attachment; filename=\"{ascii_fallback}\"; "
            f"filename*=UTF-8''{encoded}"
        )
    return get_s3_client().generate_presigned_url(
        "get_object",
        Params=params,
        ExpiresIn=settings.presign_expire_seconds,
    )


def put_object(key: str, data: bytes, content_type: str) -> None:
    """Upload bytes to object storage (sync — call via a thread in async code)."""
    get_s3_client().put_object(
        Bucket=settings.s3_bucket,
        Key=key,
        Body=data,
        ContentType=content_type,
    )


def delete_object(key: str) -> None:
    """Delete an object from storage (sync — call via a thread in async code)."""
    get_s3_client().delete_object(Bucket=settings.s3_bucket, Key=key)


def public_url(key: str) -> str:
    return f"{settings.s3_public_url}/{settings.s3_bucket}/{key}"
