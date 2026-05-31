from functools import lru_cache
from typing import Any

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


def put_object(key: str, data: bytes, content_type: str) -> None:
    """Upload bytes to object storage (sync — call via a thread in async code)."""
    get_s3_client().put_object(
        Bucket=settings.s3_bucket,
        Key=key,
        Body=data,
        ContentType=content_type,
    )


def public_url(key: str) -> str:
    return f"{settings.s3_public_url}/{settings.s3_bucket}/{key}"
