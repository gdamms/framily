from __future__ import annotations

import os
from pathlib import Path


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if not value:
        return default

    try:
        return int(value)
    except ValueError:
        return default


def _env_path(name: str, default: Path) -> Path:
    value = os.getenv(name)
    if not value:
        return default
    return Path(value)


FRAMILY_HOME = _env_path("FRAMILY_HOME", Path("/home/framily"))

FLASK_ADDRESS = os.getenv("FRAMILY_FLASK_ADDRESS", "0.0.0.0")
FLASK_PORT = _env_int("FRAMILY_FLASK_PORT", 80)

CONFIG_PATH = _env_path("FRAMILY_CONFIG_PATH", FRAMILY_HOME / "config.json")
CONFIG_LOCK_PATH = _env_path("FRAMILY_CONFIG_LOCK_PATH", FRAMILY_HOME / "config.lock")

EPD_INFO_PATH = _env_path("FRAMILY_EPD_INFO_PATH", FRAMILY_HOME / "epd" / "epd_info.json")
EPD_IMAGE_PATH = _env_path("FRAMILY_EPD_IMAGE_PATH", FRAMILY_HOME / "epd" / "epd_img.png")
TEMPLATE_FOLDER = _env_path("FRAMILY_TEMPLATE_FOLDER", FRAMILY_HOME / "framily_flask" / "templates")

CON_WIFI = os.getenv("FRAMILY_WIFI_CONNECTION", "mywifi")
CON_HOTSPOT = os.getenv("FRAMILY_HOTSPOT_CONNECTION", "myhotspot")
WLAN_IF = os.getenv("FRAMILY_WLAN_IF", "wlan0")
HOTSPOT_DOMAIN = os.getenv("FRAMILY_HOTSPOT_DOMAIN", "framily.lan")

DNS_CONFIG_PATH = _env_path(
    "FRAMILY_DNS_CONFIG_PATH",
    Path("/etc/NetworkManager/dnsmasq-shared.d/framily.conf"),
)
DISPATCHER_LOCK_PATH = _env_path("FRAMILY_DISPATCHER_LOCK_PATH", Path("/run/framily.lock"))

LOG_LEVEL = os.getenv("FRAMILY_LOG_LEVEL", "INFO")
LOG_FILE_PATH = _env_path("FRAMILY_LOG_FILE_PATH", Path("/var/log/framily-frame.log"))

FRAMILY_CREATE_PATH = "/api/v1/framily/create"
FRAMILY_CHECK_PATH = "/api/v1/framily/check"
PICTURE_FETCH_PATH = "/api/v1/pictures/fetch"

FRAME_DEFAULT_NAME = os.getenv("FRAMILY_FRAME_DEFAULT_NAME", "My Framily")

REQUEST_TIMEOUT_SECONDS = _env_int("FRAMILY_REQUEST_TIMEOUT_SECONDS", 10)
REQUEST_RETRY_ATTEMPTS = _env_int("FRAMILY_REQUEST_RETRY_ATTEMPTS", 5)
REQUEST_RETRY_BACKOFF_BASE_SECONDS = _env_int("FRAMILY_RETRY_BACKOFF_BASE_SECONDS", 2)
REQUEST_RETRY_MAX_BACKOFF_SECONDS = _env_int("FRAMILY_RETRY_MAX_BACKOFF_SECONDS", 60)

FRAMILY_MEMBER_CHECK_INTERVAL_SECONDS = _env_int("FRAMILY_MEMBER_CHECK_INTERVAL_SECONDS", 5)
FRAME_FETCH_INTERVAL_SECONDS = _env_int("FRAMILY_FRAME_FETCH_INTERVAL_SECONDS", 60)

HOTSPOT_FAILURE_THRESHOLD = _env_int("FRAMILY_HOTSPOT_FAILURE_THRESHOLD", 30)
HOTSPOT_FAILURE_WINDOW_SECONDS = _env_int("FRAMILY_HOTSPOT_FAILURE_WINDOW_SECONDS", 24 * 60 * 60)

HOTSPOT_SSID_PREFIX = os.getenv("FRAMILY_HOTSPOT_SSID_PREFIX", "Framily-")
HOTSPOT_SSID_SUFFIX_LENGTH = _env_int("FRAMILY_HOTSPOT_SSID_SUFFIX_LENGTH", 4)
HOTSPOT_PASSWORD_LENGTH = _env_int("FRAMILY_HOTSPOT_PASSWORD_LENGTH", 8)
