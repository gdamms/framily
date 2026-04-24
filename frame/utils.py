from __future__ import annotations

from typing import Any

from frame_core.config import DEFAULT_CONFIG, DEFAULT_STORE
from frame_core.display import make_qr
from frame_core.network import (
    configure_hotspot_dns_mapping,
    get_hotspot_credentials,
    get_wifi_credentials,
    run_command_output,
    set_hotspot_credentials,
    set_wifi_credentials,
    start_hotspot_connection,
    start_wifi_connection,
)
from frame_core.settings import (
    CONFIG_PATH,
    CON_HOTSPOT,
    CON_WIFI,
    DNS_CONFIG_PATH,
    EPD_IMAGE_PATH,
    EPD_INFO_PATH,
    FLASK_ADDRESS,
    FLASK_PORT,
    HOTSPOT_DOMAIN,
    TEMPLATE_FOLDER,
    WLAN_IF,
)


def run(cmd: list[str] | str) -> str:
    return run_command_output(cmd, check=False)


def set_wifi(ssid: str, password: str, start: bool = True) -> None:
    set_wifi_credentials(ssid, password)
    if start:
        start_wifi()


def get_wifi() -> tuple[str, str]:
    return get_wifi_credentials()


def start_wifi() -> None:
    start_wifi_connection()


def set_hotspot(ssid: str, password: str, start: bool = True) -> None:
    set_hotspot_credentials(ssid, password)
    if start:
        start_hotspot()


def get_hotspot() -> tuple[str, str]:
    configure_hotspot_dns_mapping(WLAN_IF)
    return get_hotspot_credentials()


def start_hotspot() -> None:
    start_hotspot_connection()


def load_config() -> dict[str, Any]:
    return DEFAULT_STORE.load()


def save_config(config: dict[str, Any]) -> None:
    DEFAULT_STORE.save(config)


def reset_config() -> None:
    DEFAULT_STORE.reset()


def save_message(message: str) -> None:
    DEFAULT_STORE.save_message(message)
