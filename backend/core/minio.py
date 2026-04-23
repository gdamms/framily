from minio import Minio

from core.config import settings


_minio_client = None


def get_minio_client() -> Minio:
    """Initialize and return MinIO client."""
    global _minio_client
    
    if _minio_client is None:
        _minio_client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE
        )
        
        # Ensure bucket exists
        try:
            if not _minio_client.bucket_exists(settings.MINIO_BUCKET):
                _minio_client.make_bucket(settings.MINIO_BUCKET)
        except Exception:
            pass  # Will fail if MinIO not ready yet
    
    return _minio_client


# Lazy initialization
minio_client = property(lambda self: get_minio_client())


class MinioClientProxy:
    """Proxy to lazily initialize MinIO client."""
    def __getattr__(self, name):
        return getattr(get_minio_client(), name)


minio_client = MinioClientProxy()
