import io
import uuid
from pathlib import Path
from typing import Optional

from fastapi import UploadFile
from minio import Minio

from core.config import settings

_client: Optional[Minio] = None


def get_minio_client() -> Minio:
    global _client
    if _client is None:
        _client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE,
        )
        if not _client.bucket_exists(settings.MINIO_BUCKET):
            _client.make_bucket(settings.MINIO_BUCKET)
    return _client


def _generate_latin_filename(original_name: Optional[str]) -> str:
    suffix = Path(original_name or "").suffix.lower()
    if not suffix.isascii() or len(suffix) > 10:
        suffix = ""
    return f"{uuid.uuid4().hex}{suffix}"


async def upload_media(file: UploadFile, subdir: str) -> str:
    object_name = f"{_generate_latin_filename(file.filename)}"

    data = await file.read()
    client = get_minio_client()
    client.put_object(
        settings.MINIO_BUCKET,
        object_name,
        data=io.BytesIO(data),
        length=len(data),
        content_type=file.content_type or "application/octet-stream",
    )
    return object_name


def build_media_url(object_name: Optional[str]) -> Optional[str]:
    if not object_name:
        return None
    scheme = "https" if settings.MINIO_SECURE else "http"
    return f"{scheme}://{settings.MINIO_ENDPOINT}/{settings.MINIO_BUCKET}/{object_name}"
