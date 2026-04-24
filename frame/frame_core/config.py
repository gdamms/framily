from __future__ import annotations

import fcntl
import json
import os
import time
from contextlib import contextmanager
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from frame_core.settings import (
    CONFIG_LOCK_PATH,
    CONFIG_PATH,
    HOTSPOT_FAILURE_THRESHOLD,
    HOTSPOT_FAILURE_WINDOW_SECONDS,
)


class FrameState(str, Enum):
    UNCONFIGURED = "unconfigured"
    CONNECTING_WIFI = "connecting_wifi"
    WAITING_FOR_MEMBER = "waiting_for_member"
    FETCHING_IMAGES = "fetching_images"
    HOTSPOT = "hotspot"
    ERROR = "error"


DEFAULT_CONFIG: dict[str, Any] = {
    "server_url": "",
    "framily_code": "",
    "frame_token": "",
    "message": "",
    "state": FrameState.UNCONFIGURED.value,
    "last_error": "",
    "last_error_at": 0,
    "last_success_at": 0,
    "consecutive_failures": 0,
    "failure_since": 0,
    "hotspot_ssid": "",
    "hotspot_password": "",
}


@dataclass(frozen=True)
class FailureSnapshot:
    consecutive_failures: int
    failure_duration_s: int
    should_enter_hotspot: bool


class ConfigStore:
    def __init__(self, path: Path = CONFIG_PATH, lock_path: Path = CONFIG_LOCK_PATH):
        self.path = path
        self.lock_path = lock_path

    @contextmanager
    def _locked(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)

        with open(self.lock_path, "w", encoding="utf-8") as lock_file:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
            yield

    def _normalize(self, config: dict[str, Any]) -> dict[str, Any]:
        normalized = dict(DEFAULT_CONFIG)
        normalized.update(config)
        return normalized

    def _read_unlocked(self) -> dict[str, Any]:
        if not self.path.exists():
            return dict(DEFAULT_CONFIG)

        try:
            config = json.loads(self.path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return dict(DEFAULT_CONFIG)

        if not isinstance(config, dict):
            return dict(DEFAULT_CONFIG)

        return self._normalize(config)

    def _write_unlocked(self, config: dict[str, Any]) -> None:
        normalized = self._normalize(config)
        temp_path = self.path.with_suffix(f"{self.path.suffix}.tmp")
        temp_path.write_text(json.dumps(normalized, indent=2, sort_keys=True), encoding="utf-8")
        os.replace(temp_path, self.path)

    def load(self) -> dict[str, Any]:
        with self._locked():
            return self._read_unlocked()

    def save(self, config: dict[str, Any]) -> None:
        with self._locked():
            self._write_unlocked(config)

    def update(self, **values: Any) -> dict[str, Any]:
        with self._locked():
            config = self._read_unlocked()
            config.update(values)
            self._write_unlocked(config)
            return dict(config)

    def reset(self) -> dict[str, Any]:
        with self._locked():
            self._write_unlocked(dict(DEFAULT_CONFIG))
            return dict(DEFAULT_CONFIG)

    def clear_registration(self) -> dict[str, Any]:
        return self.update(
            framily_code="",
            frame_token="",
            state=FrameState.UNCONFIGURED.value,
        )

    def set_state(self, state: FrameState) -> dict[str, Any]:
        return self.update(state=state.value)

    def save_message(self, message: str) -> dict[str, Any]:
        return self.update(message=message)

    def clear_message(self) -> dict[str, Any]:
        return self.update(message="")

    def set_hotspot_credentials(self, ssid: str, password: str) -> dict[str, Any]:
        return self.update(hotspot_ssid=ssid, hotspot_password=password)

    def mark_success(self, state: FrameState | None = None) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "consecutive_failures": 0,
            "failure_since": 0,
            "last_success_at": int(time.time()),
            "message": "",
        }
        if state is not None:
            payload["state"] = state.value
        return self.update(**payload)

    def record_failure(self, message: str, state: FrameState = FrameState.ERROR) -> FailureSnapshot:
        with self._locked():
            config = self._read_unlocked()
            now = int(time.time())
            failure_since = int(config.get("failure_since") or now)
            consecutive_failures = int(config.get("consecutive_failures") or 0) + 1
            duration = now - failure_since

            should_enter_hotspot = (
                consecutive_failures >= HOTSPOT_FAILURE_THRESHOLD
                or duration >= HOTSPOT_FAILURE_WINDOW_SECONDS
            )

            config.update(
                {
                    "state": state.value,
                    "message": message,
                    "last_error": message,
                    "last_error_at": now,
                    "consecutive_failures": consecutive_failures,
                    "failure_since": failure_since,
                }
            )
            self._write_unlocked(config)

        return FailureSnapshot(
            consecutive_failures=consecutive_failures,
            failure_duration_s=duration,
            should_enter_hotspot=should_enter_hotspot,
        )


DEFAULT_STORE = ConfigStore()


def load_config() -> dict[str, Any]:
    return DEFAULT_STORE.load()


def save_config(config: dict[str, Any]) -> None:
    DEFAULT_STORE.save(config)


def reset_config() -> dict[str, Any]:
    return DEFAULT_STORE.reset()


def save_message(message: str) -> dict[str, Any]:
    return DEFAULT_STORE.save_message(message)
