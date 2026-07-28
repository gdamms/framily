from __future__ import annotations

from typing import Optional

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

from core.config import settings


_s3_client = None
_s3_wrapper = None


def _build_endpoint_url(endpoint: str, secure: bool) -> str:
    if endpoint.startswith("http://") or endpoint.startswith("https://"):
        return endpoint
    scheme = "https" if secure else "http"
    return f"{scheme}://{endpoint}"


class S3ObjectResponse:
    def __init__(self, body):
        self._body = body

    def stream(self, chunk_size: int):
        while True:
            chunk = self._body.read(chunk_size)
            if not chunk:
                break
            yield chunk


class S3ClientWrapper:
    def __init__(self, client):
        self._client = client

    def put_object(
        self,
        bucket: str,
        object_name: str,
        data,
        length: Optional[int],
        content_type: Optional[str] = None,
    ) -> None:
        kwargs = {
            "Bucket": bucket,
            "Key": object_name,
            "Body": data,
        }
        if content_type:
            kwargs["ContentType"] = content_type
        if length is not None:
            kwargs["ContentLength"] = length
        self._client.put_object(**kwargs)

    def get_object(self, bucket: str, object_name: str) -> S3ObjectResponse:
        response = self._client.get_object(Bucket=bucket, Key=object_name)
        return S3ObjectResponse(response["Body"])

    def remove_object(self, bucket: str, object_name: str) -> None:
        self._client.delete_object(Bucket=bucket, Key=object_name)


def _ensure_bucket(client) -> None:
    try:
        client.head_bucket(Bucket=settings.S3_BUCKET)
        return
    except ClientError:
        pass

    try:
        create_kwargs = {"Bucket": settings.S3_BUCKET}
        if settings.S3_REGION and settings.S3_REGION != "us-east-1":
            create_kwargs["CreateBucketConfiguration"] = {
                "LocationConstraint": settings.S3_REGION
            }
        client.create_bucket(**create_kwargs)
    except Exception:
        pass


def get_s3_client() -> S3ClientWrapper:
    """Initialize and return S3 client wrapper."""
    global _s3_client, _s3_wrapper

    if _s3_client is None:
        endpoint_url = _build_endpoint_url(settings.S3_ENDPOINT, settings.S3_SECURE)
        _s3_client = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=settings.S3_ACCESS_KEY,
            aws_secret_access_key=settings.S3_SECRET_KEY,
            region_name=settings.S3_REGION,
            config=Config(s3={"addressing_style": "path"}),
        )
        _ensure_bucket(_s3_client)
        _s3_wrapper = S3ClientWrapper(_s3_client)

    return _s3_wrapper


class S3ClientProxy:
    """Proxy to lazily initialize S3 client."""

    def __getattr__(self, name):
        return getattr(get_s3_client(), name)


s3_client = S3ClientProxy()
