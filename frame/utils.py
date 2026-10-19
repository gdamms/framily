import subprocess
from pathlib import Path
import json
import os
import uuid

from logging_setup import get_logger

logger = get_logger("utils")


try:
    WEB_ADDRESS = os.environ["FRAMILY_WEB_ADDRESS"]
    WEB_PORT = int(os.environ["FRAMILY_WEB_PORT"])
    CONFIG_PATH = Path(os.environ["FRAMILY_CONFIG_PATH"])
    TEMPLATE_FOLDER = Path(os.environ["FRAMILY_TEMPLATE_FOLDER"])
    EPD_INFO_PATH = Path(os.environ["FRAMILY_EPD_INFO_PATH"])
    EPD_IMAGE_PATH = Path(os.environ["FRAMILY_EPD_IMAGE_PATH"])
    CON_WIFI = os.environ["FRAMILY_WIFI"]
    WLAN_IF = os.environ["FRAMILY_IFACE"]
except KeyError as e:
    raise RuntimeError(f"Missing required environment variable: {e}") from e


DEFAULT_CONFIG = {
    "server_url": "",
    "framily_code": "",
    "frame_token": "",
    "message": "",
    "wifi_ssid": "",
    "wifi_password": "",
    "wifi_should_update": False,
    "pending_delete": False,
    # Machine-readable mirror of the BLE provisioning flow's progress,
    # relayed to the app by frame/ble/main.py's `status` characteristic -
    # kept separate from "message" (free text meant for the web UI/e-ink).
    "provisioning_status": "idle",
    "provisioning_message": "",
    # True only for the session that actually called create_framily() (i.e.
    # framily_code/frame_token were empty beforehand) - lets the app tell a
    # brand-new frame from one that was just reprovisioned onto new Wi-Fi.
    "provisioning_created_new": False,
}

# Default timeout for subprocess calls (mostly nmcli). Generous enough to
# cover a real Wi-Fi association attempt, but bounded so a wedged nmcli can
# never hang a caller (e.g. a Flask request thread) forever.
DEFAULT_RUN_TIMEOUT_SECONDS = 20

# Single-instance lock for framily-agent.service.
AGENT_LOCK_PATH = CONFIG_PATH.parent / "agent.lock"
# Touched by the NetworkManager dispatcher hook (and by config writes) to
# wake the agent's poll loop early instead of waiting out a long sleep.
AGENT_RECHECK_PATH = CONFIG_PATH.parent / "agent.recheck"


def run(cmd: list[str] | str, timeout: float = DEFAULT_RUN_TIMEOUT_SECONDS) -> str:
    shell = isinstance(cmd, str)

    try:
        completed = subprocess.run(
            cmd,
            shell=shell,
            check=True,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.CalledProcessError as e:
        logger.warning(f"Command failed: {cmd!r}: {e.stderr.strip()}")
        return e.stdout.strip()
    except subprocess.TimeoutExpired:
        logger.warning(f"Command timed out after {timeout}s: {cmd!r}")
        return ""

    return completed.stdout.strip()


def set_wifi(ssid: str, password: str, start: bool = True) -> None:
    run(['nmcli', 'connection', 'modify', CON_WIFI, 'wifi.ssid', ssid])
    run(['nmcli', 'connection', 'modify', CON_WIFI, 'wifi-sec.psk', password])
    if start:
        start_wifi()


def start_wifi():
    run(['nmcli', 'connection', 'up', CON_WIFI])


def get_ip_address() -> str:
    """Current IP address on WLAN_IF, or "" if it can't be determined (e.g.
    not associated to a network yet)."""
    output = run(['ip', '-br', 'addr', 'show', WLAN_IF], timeout=5)
    parts = output.split()
    if len(parts) < 3:
        return ""
    return parts[2].split('/')[0]


def get_active_connection() -> str:
    """Name of the currently active connection on WLAN_IF (empty if none)."""
    return run(['nmcli', '-t', '-f', 'NAME', 'connection', 'show', '--active'], timeout=5).split("\n")[0]


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        return dict(DEFAULT_CONFIG)

    try:
        config = json.loads(CONFIG_PATH.read_text())
    except (json.JSONDecodeError, OSError):
        return dict(DEFAULT_CONFIG)

    return {
        "server_url": config.get("server_url", ""),
        "framily_code": config.get("framily_code", ""),
        "frame_token": config.get("frame_token", ""),
        "message": config.get("message", ""),
        "wifi_ssid": config.get("wifi_ssid", ""),
        "wifi_password": config.get("wifi_password", ""),
        "wifi_should_update": config.get("wifi_should_update", False),
        "pending_delete": config.get("pending_delete", False),
        "provisioning_status": config.get("provisioning_status", "idle"),
        "provisioning_message": config.get("provisioning_message", ""),
        "provisioning_created_new": config.get("provisioning_created_new", False),
    }

def save_config(config: dict) -> None:
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)


BLUETOOTH_ADDRESS_PATH = Path("/sys/class/bluetooth/hci0/address")


def get_ble_local_name() -> str:
    """Short, stable per-device BLE advertising name (`Framily-XXXX`),
    derived from the Bluetooth adapter's MAC address so it needs no
    persisted state and stays the same across reboots. Also drawn on the
    e-ink screen, so a user with several unprovisioned frames nearby can
    match the app's scan result to the physical device in front of them."""
    try:
        address = BLUETOOTH_ADDRESS_PATH.read_text().strip()
        suffix = address.replace(":", "")[-4:].upper()
    except OSError:
        suffix = f"{uuid.getnode():012X}"[-4:]
    return f"Framily-{suffix}"


def save_message(message: str) -> None:
    config = load_config()
    config["message"] = message
    save_config(config)


def clear_message() -> None:
    save_message("")
