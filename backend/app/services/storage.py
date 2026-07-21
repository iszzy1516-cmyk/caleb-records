"""Object storage backends for document uploads.

Supports local filesystem (default) and S3-compatible storage such as
AWS S3 or Cloudflare R2. When S3_UPLOAD_BUCKET is set, uploaded files are
stored in S3; otherwise they remain on the local filesystem.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

from app.core.config import settings


@dataclass
class StorageInfo:
    provider: str  # "local" or "s3"
    file_path: Optional[str]  # local path if provider == local
    storage_key: Optional[str]  # S3 object key if provider == s3
    public_url: Optional[str]  # download URL


def is_s3_configured() -> bool:
    """Return True if S3 upload settings are present."""
    return bool(settings.S3_UPLOAD_BUCKET)


def _get_s3_client():
    """Build an S3 client using explicit credentials or the default credential chain."""
    region = settings.AWS_REGION or "us-east-1"
    kwargs = {
        "region_name": region,
        "config": Config(s3={"addressing_style": "path" if settings.S3_FORCE_PATH_STYLE else "auto"}),
    }
    if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
        kwargs["aws_access_key_id"] = settings.AWS_ACCESS_KEY_ID
        kwargs["aws_secret_access_key"] = settings.AWS_SECRET_ACCESS_KEY
    return boto3.client("s3", **kwargs)


def _build_public_url(key: str) -> str:
    """Return the public URL for an S3 object."""
    if settings.S3_PUBLIC_URL:
        return f"{settings.S3_PUBLIC_URL.rstrip('/')}/{key}"
    bucket = settings.S3_UPLOAD_BUCKET
    region = settings.AWS_REGION or "us-east-1"
    if region == "us-east-1":
        return f"https://{bucket}.s3.amazonaws.com/{key}"
    return f"https://{bucket}.s3.{region}.amazonaws.com/{key}"


def upload_file_to_s3(
    file_path: Path, key: str, content_type: Optional[str] = None, original_filename: Optional[str] = None
) -> str:
    """Upload a local file to S3 and return its public URL.

    Sets Content-Disposition to attachment so public links trigger a download
    rather than opening in the browser.
    """
    client = _get_s3_client()
    extra_args = {"ContentDisposition": f'attachment; filename="{original_filename or Path(key).name}"'}
    if content_type:
        extra_args["ContentType"] = content_type
    client.upload_file(str(file_path), settings.S3_UPLOAD_BUCKET, key, ExtraArgs=extra_args)
    return _build_public_url(key)


def generate_presigned_download_url(
    key: str, filename: Optional[str] = None, expiration: int = 3600
) -> str:
    """Generate a temporary presigned URL that forces the browser to download the file."""
    client = _get_s3_client()
    params = {"Bucket": settings.S3_UPLOAD_BUCKET, "Key": key}
    disposition = f'attachment; filename="{filename or Path(key).name}"'
    params["ResponseContentDisposition"] = disposition
    try:
        return client.generate_presigned_url(
            "get_object",
            Params=params,
            ExpiresIn=expiration,
        )
    except ClientError as exc:
        raise RuntimeError(f"Failed to generate presigned URL: {exc}") from exc


def delete_s3_object(key: str) -> None:
    """Delete an object from S3."""
    client = _get_s3_client()
    client.delete_object(Bucket=settings.S3_UPLOAD_BUCKET, Key=key)
