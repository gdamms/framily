from minio import Minio

from core.config import settings


def get_minio_client() -> Minio:
    """Initialize and return MinIO client."""
    client = Minio(
        settings.MINIO_ENDPOINT,
        access_key=settings.MINIO_ACCESS_KEY,
        secret_key=settings.MINIO_SECRET_KEY,
        secure=False
    )

    # Ensure bucket exists
    if not client.bucket_exists(settings.MINIO_BUCKET):
        client.make_bucket(settings.MINIO_BUCKET)

    return client


minio_client = get_minio_client()
