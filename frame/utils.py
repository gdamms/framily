import subprocess
from pathlib import Path
import json
import qrcode
from PIL import Image


FLASK_ADDRESS = "0.0.0.0"
FLASK_PORT = 80
CONFIG_PATH = Path("/home/framily/config.json")
TEMPLATE_FOLDER = Path("/home/framily/framily_flask/templates")
EPD_INFO_PATH = Path('/home/framily/epd/epd_info.json')
EPD_IMAGE_PATH = Path('/home/framily/epd/epd_img.png')
CON_WIFI = "mywifi"
CON_HOTSPOT = "myhotspot"
WLAN_IF = "wlan0"
HOTSPOT_DOMAIN = "framily.lan"
DNS_CONFIG_PATH = Path("/etc/dnsmasq.d/framily.conf")


DEFAULT_CONFIG = {
    "server_url": "",
    "framily_code": "",
    "frame_token": "",
    "message": "",
}


def run(cmd: list[str] | str) -> str:
    shell = isinstance(cmd, str)

    try:
        completed = subprocess.run(
            cmd,
            shell=shell,
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as e:
        print(e.stderr.strip(), flush=True)
        return e.stdout.strip()

    return completed.stdout.strip()


def set_wifi(ssid: str, password: str, start: bool = True) -> None:
    run(['nmcli', 'connection', 'modify', CON_WIFI, 'wifi.ssid', ssid])
    run(['nmcli', 'connection', 'modify', CON_WIFI, 'wifi-sec.psk', password])
    if start:
        start_wifi()


def get_wifi() -> tuple[str, str]:
    ssid = run(['nmcli', '-g', '802-11-wireless.ssid', 'connection', 'show', CON_WIFI])
    password = run(['nmcli', '-s', '-g', '802-11-wireless-security.psk', 'connection', 'show', CON_WIFI])
    return ssid, password


def start_wifi():
    run(['nmcli', 'connection', 'up', CON_WIFI])


def set_hotspot(ssid: str, password: str, start: bool = True) -> None:
    run(['nmcli', 'connection', 'modify', CON_HOTSPOT, 'wifi.ssid', ssid])
    run(['nmcli', 'connection', 'modify', CON_HOTSPOT, 'wifi-sec.psk', password])
    if start:
        start_hotspot()


def get_hotspot() -> tuple[str, str]:
    ssid = run(['nmcli', '-g', '802-11-wireless.ssid', 'connection', 'show', CON_HOTSPOT])
    password = run(['nmcli', '-s', '-g', '802-11-wireless-security.psk', 'connection', 'show', CON_HOTSPOT])
    address = run(['ip', '-br', 'addr', 'show', WLAN_IF])
    address = address.split()[2].split('/')[0]  # Extract the IP address

    # Set DNS to resolve the hotspot domain to the local IP address
    resolv_conf = f"address=/{HOTSPOT_DOMAIN}/{address}\n"
    DNS_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    DNS_CONFIG_PATH.write_text(resolv_conf)
    run(['systemctl', 'restart', 'dnsmasq'])

    return ssid, password


def start_hotspot():
    run(['nmcli', 'connection', 'up', CON_HOTSPOT])


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        return DEFAULT_CONFIG

    try:
        config = json.loads(CONFIG_PATH.read_text())
    except (json.JSONDecodeError, OSError):
        return DEFAULT_CONFIG

    return {
        "server_url": config.get("server_url", ""),
        "framily_code": config.get("framily_code", ""),
        "frame_token": config.get("frame_token", ""),
        "message": config.get("message", ""),
    }

def save_config(config: dict) -> None:
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)


def reset_config() -> None:
    save_config(DEFAULT_CONFIG)


def make_qr(data: str, size: int = 150) -> Image.Image:
    qr = qrcode.make(data, border=0)
    return qr.resize((size, size))

def save_message(message: str) -> None:
    config = load_config()
    config["message"] = message
    save_config(config)
