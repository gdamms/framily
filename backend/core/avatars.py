from __future__ import annotations

from io import BytesIO

from fastapi import HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse
from PIL import Image, ImageOps, UnidentifiedImageError

from core.config import settings
from core.minio import s3_client

ALLOWED_AVATAR_FORMATS = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MAX_AVATAR_SIZE = 5 * 1024 * 1024  # 5MB
AVATAR_DIMENSION = 512

USER_AVATAR_PREFIX = "profile_pictures"
FRAMILY_AVATAR_PREFIX = "framily_avatars"

_EXTENSIONS = ["jpg", "png", "webp", "gif"]
_CONTENT_TYPES = {
    "jpg": "image/jpeg",
    "png": "image/png",
    "webp": "image/webp",
    "gif": "image/gif",
}


def _object_name(prefix: str, key: str, extension: str) -> str:
    return f"{prefix}/{key}.{extension}"


def _to_square_jpeg(content: bytes) -> bytes:
    """Naively center-crop to a square and resize to AVATAR_DIMENSION x AVATAR_DIMENSION.

    The frontend already crops/resizes client-side, but a client could bypass that, so this
    re-crop always runs server-side too - just a plain center crop, not the user's chosen
    framing, to keep every stored avatar a predictable square regardless of what was sent.
    """
    try:
        image = Image.open(BytesIO(content))
        image = ImageOps.exif_transpose(image)
    except UnidentifiedImageError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid image file"
        )

    if image.mode != "RGB":
        image = image.convert("RGB")

    width, height = image.size
    side = min(width, height)
    left = (width - side) // 2
    top = (height - side) // 2
    image = image.crop((left, top, left + side, top + side))
    image = image.resize((AVATAR_DIMENSION, AVATAR_DIMENSION), Image.LANCZOS)

    buffer = BytesIO()
    image.save(buffer, format="JPEG", quality=90)
    return buffer.getvalue()


async def save_avatar(prefix: str, key: str, file: UploadFile) -> None:
    """Validate and store an uploaded avatar, replacing any existing one for `key`."""
    if file.content_type not in ALLOWED_AVATAR_FORMATS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Allowed: {', '.join(ALLOWED_AVATAR_FORMATS)}"
        )

    content = await file.read()
    if len(content) > MAX_AVATAR_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Max size: {MAX_AVATAR_SIZE / 1024 / 1024}MB"
        )

    content = _to_square_jpeg(content)
    extension = "jpg"

    # Remove any previous avatar, since it may have had a different extension.
    for ext in _EXTENSIONS:
        s3_client.remove_object(settings.S3_BUCKET, _object_name(prefix, key, ext))

    try:
        s3_client.put_object(
            settings.S3_BUCKET,
            _object_name(prefix, key, extension),
            BytesIO(content),
            len(content),
            content_type=_CONTENT_TYPES[extension]
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file: {str(e)}"
        )


def stream_avatar(prefix: str, key: str) -> StreamingResponse:
    """Serve an avatar, trying each supported extension until one is found."""
    for extension in _EXTENSIONS:
        object_name = _object_name(prefix, key, extension)
        try:
            response = s3_client.get_object(settings.S3_BUCKET, object_name)
            return StreamingResponse(
                response.stream(32 * 1024),
                media_type=_CONTENT_TYPES[extension],
                headers={
                    "Cache-Control": "public, max-age=86400",  # Cache for 1 day
                    "Content-Disposition": f"inline; filename={key}.{extension}"
                }
            )
        except Exception:
            continue

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Avatar not found"
    )


def delete_avatar(prefix: str, key: str) -> None:
    for extension in _EXTENSIONS:
        s3_client.remove_object(settings.S3_BUCKET, _object_name(prefix, key, extension))
