from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

import requests

from frame_core.settings import (
    FRAMILY_CHECK_PATH,
    FRAMILY_CREATE_PATH,
    FRAME_DEFAULT_NAME,
    PICTURE_FETCH_PATH,
    REQUEST_TIMEOUT_SECONDS,
)


class FetchStatus(str, Enum):
    IMAGE = "image"
    NO_CONTENT = "no_content"


@dataclass(frozen=True)
class FetchResult:
    status: FetchStatus
    content: bytes | None


class FrameApiError(RuntimeError):
    def __init__(self, message: str, *, transient: bool = True, status_code: int | None = None):
        super().__init__(message)
        self.transient = transient
        self.status_code = status_code


class FrameApiClient:
    def __init__(self, base_url: str, timeout_s: int = REQUEST_TIMEOUT_SECONDS):
        self.base_url = base_url.rstrip("/")
        self.timeout_s = timeout_s

    def _url(self, path: str) -> str:
        return f"{self.base_url}{path}"

    def _request_error(self, error: requests.exceptions.RequestException, context: str) -> FrameApiError:
        return FrameApiError(f"{context}: {error}", transient=True)

    def _safe_json(self, response: requests.Response, context: str) -> dict[str, Any]:
        try:
            payload = response.json()
        except ValueError as error:
            raise FrameApiError(f"{context}: invalid JSON response ({error})", transient=False) from error

        if not isinstance(payload, dict):
            raise FrameApiError(f"{context}: invalid response payload", transient=False)

        return payload

    def create_framily(self, name: str = FRAME_DEFAULT_NAME) -> tuple[str, str]:
        url = self._url(FRAMILY_CREATE_PATH)
        try:
            response = requests.post(url, json={"name": name}, timeout=self.timeout_s)
        except requests.exceptions.RequestException as error:
            raise self._request_error(error, "Failed to create framily") from error

        if response.status_code != 201:
            transient = response.status_code >= 500
            raise FrameApiError(
                f"Failed to create framily (status={response.status_code}): {response.text}",
                transient=transient,
                status_code=response.status_code,
            )

        payload = self._safe_json(response, "Failed to parse create framily response")
        framily_code = payload.get("framily_code")
        frame_token = payload.get("frame_token")

        if not framily_code or not frame_token:
            raise FrameApiError(
                "Invalid create framily response. Missing framily_code or frame_token.",
                transient=False,
            )

        return str(framily_code), str(frame_token)

    def check_framily(self, framily_code: str, frame_token: str) -> bool:
        url = self._url(FRAMILY_CHECK_PATH)
        payload = {"framily_code": framily_code, "frame_token": frame_token}

        try:
            response = requests.post(url, json=payload, timeout=self.timeout_s)
        except requests.exceptions.RequestException as error:
            raise self._request_error(error, "Failed to check framily") from error

        if response.status_code != 200:
            transient = response.status_code >= 500
            raise FrameApiError(
                f"Failed to check framily (status={response.status_code}): {response.text}",
                transient=transient,
                status_code=response.status_code,
            )

        body = self._safe_json(response, "Failed to parse framily check response")
        return bool(body.get("initiated", False))

    def fetch_picture(self, framily_code: str, frame_token: str) -> FetchResult:
        url = self._url(PICTURE_FETCH_PATH)
        payload = {"framily_code": framily_code, "frame_token": frame_token}

        try:
            response = requests.post(url, json=payload, timeout=self.timeout_s)
        except requests.exceptions.RequestException as error:
            raise self._request_error(error, "Failed to fetch picture") from error

        if response.status_code == 204:
            return FetchResult(status=FetchStatus.NO_CONTENT, content=None)

        if response.status_code == 200:
            return FetchResult(status=FetchStatus.IMAGE, content=response.content)

        transient = response.status_code >= 500
        raise FrameApiError(
            f"Failed to fetch picture (status={response.status_code}): {response.text}",
            transient=transient,
            status_code=response.status_code,
        )
