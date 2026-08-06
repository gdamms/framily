import subprocess
from pathlib import Path
import json
import qrcode
from PIL import Image
import os

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
    CON_HOTSPOT = os.environ["FRAMILY_HOTSPOT"]
    WLAN_IF = os.environ["FRAMILY_IFACE"]
    HOTSPOT_DOMAIN = os.environ["FRAMILY_DOMAIN"]
    DNS_CONFIG_PATH = Path(os.environ["FRAMILY_DNSMASQ_PATH"])
except KeyError as e:
    raise RuntimeError(f"Missing required environment variable: {e}") from e


DEFAULT_CONFIG = {
    "server_url": "",
    "framily_code": "",
    "frame_token": "",
    "message": "",
    "pending_wifi_ssid": "",
    "pending_wifi_password": "",
    "pending_delete": False,
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


def get_wifi() -> tuple[str, str]:
    # Short timeout: this is a pure read called from web request threads and
    # should never take more than a moment.
    ssid = run(['nmcli', '-g', '802-11-wireless.ssid', 'connection', 'show', CON_WIFI], timeout=5)
    password = run(['nmcli', '-s', '-g', '802-11-wireless-security.psk', 'connection', 'show', CON_WIFI], timeout=5)
    return ssid, password


def start_wifi():
    run(['nmcli', 'connection', 'up', CON_WIFI])


def set_hotspot(ssid: str, password: str, start: bool = True) -> None:
    run(['nmcli', 'connection', 'modify', CON_HOTSPOT, 'wifi.ssid', ssid])
    run(['nmcli', 'connection', 'modify', CON_HOTSPOT, 'wifi-sec.psk', password])
    if start:
        start_hotspot()


def get_hotspot() -> tuple[str, str]:
    ssid = run(['nmcli', '-g', '802-11-wireless.ssid', 'connection', 'show', CON_HOTSPOT], timeout=5)
    password = run(['nmcli', '-s', '-g', '802-11-wireless-security.psk', 'connection', 'show', CON_HOTSPOT], timeout=5)
    address = run(['ip', '-br', 'addr', 'show', WLAN_IF], timeout=5)
    address = address.split()[2].split('/')[0]  # Extract the IP address

    # Set DNS to resolve the hotspot domain to the local IP address
    resolv_conf = f"address=/{HOTSPOT_DOMAIN}/{address}\n"
    DNS_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    DNS_CONFIG_PATH.write_text(resolv_conf)

    return ssid, password


def start_hotspot():
    run(['nmcli', 'connection', 'up', CON_HOTSPOT])


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
        "pending_wifi_ssid": config.get("pending_wifi_ssid", ""),
        "pending_wifi_password": config.get("pending_wifi_password", ""),
        "pending_delete": config.get("pending_delete", False),
    }

def save_config(config: dict) -> None:
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)


def make_qr(data: str, size: int = 190) -> Image.Image:
    # A small quiet-zone border (not 0) keeps the code reliably scannable by
    # phone cameras. NEAREST resize keeps module edges crisp - any blurring
    # would get dithered into speckles by the e-ink panel's 6-color quantizer.
    qr = qrcode.make(data, border=2)
    return qr.resize((size, size), Image.NEAREST)

def save_message(message: str) -> None:
    config = load_config()
    config["message"] = message
    save_config(config)


def clear_message() -> None:
    save_message("")
