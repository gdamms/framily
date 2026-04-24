from __future__ import annotations

import random
import re
import string
import subprocess
from dataclasses import dataclass
from typing import Sequence

from frame_core.logging import get_logger
from frame_core.settings import (
    CON_HOTSPOT,
    CON_WIFI,
    DNS_CONFIG_PATH,
    HOTSPOT_DOMAIN,
    HOTSPOT_PASSWORD_LENGTH,
    HOTSPOT_SSID_PREFIX,
    HOTSPOT_SSID_SUFFIX_LENGTH,
    WLAN_IF,
)


logger = get_logger(__name__)


@dataclass(frozen=True)
class CommandResult:
    returncode: int
    stdout: str
    stderr: str


class CommandError(RuntimeError):
    def __init__(self, cmd: Sequence[str] | str, result: CommandResult):
        message = (
            f"Command failed ({result.returncode}): {cmd}. "
            f"stdout={result.stdout!r}, stderr={result.stderr!r}"
        )
        super().__init__(message)
        self.cmd = cmd
        self.result = result


def run_command(cmd: Sequence[str] | str, check: bool = True) -> CommandResult:
    shell = isinstance(cmd, str)
    completed = subprocess.run(
        cmd,
        shell=shell,
        check=False,
        capture_output=True,
        text=True,
    )
    result = CommandResult(
        returncode=completed.returncode,
        stdout=completed.stdout.strip(),
        stderr=completed.stderr.strip(),
    )

    if check and result.returncode != 0:
        raise CommandError(cmd, result)

    return result


def run_command_output(cmd: Sequence[str] | str, check: bool = True) -> str:
    return run_command(cmd, check=check).stdout


def get_active_connection_name() -> str:
    output = run_command_output(["nmcli", "-t", "-f", "NAME", "connection", "show", "--active"], check=False)
    for line in output.splitlines():
        value = line.strip()
        if value:
            return value
    return ""


def set_wifi_credentials(ssid: str, password: str) -> None:
    run_command(["nmcli", "connection", "modify", CON_WIFI, "wifi.ssid", ssid])
    run_command(["nmcli", "connection", "modify", CON_WIFI, "wifi-sec.psk", password])


def get_wifi_credentials() -> tuple[str, str]:
    ssid = run_command_output(
        ["nmcli", "-g", "802-11-wireless.ssid", "connection", "show", CON_WIFI],
        check=False,
    )
    password = run_command_output(
        ["nmcli", "-s", "-g", "802-11-wireless-security.psk", "connection", "show", CON_WIFI],
        check=False,
    )
    return ssid, password


def start_wifi_connection() -> None:
    run_command(["nmcli", "connection", "up", CON_WIFI])


def set_hotspot_credentials(ssid: str, password: str) -> None:
    run_command(["nmcli", "connection", "modify", CON_HOTSPOT, "wifi.ssid", ssid])
    run_command(["nmcli", "connection", "modify", CON_HOTSPOT, "wifi-sec.psk", password])


def get_hotspot_credentials() -> tuple[str, str]:
    ssid = run_command_output(
        ["nmcli", "-g", "802-11-wireless.ssid", "connection", "show", CON_HOTSPOT],
        check=False,
    )
    password = run_command_output(
        ["nmcli", "-s", "-g", "802-11-wireless-security.psk", "connection", "show", CON_HOTSPOT],
        check=False,
    )
    return ssid, password


def _ipv4_for_interface(interface_name: str = WLAN_IF) -> str:
    output = run_command_output(["ip", "-4", "-o", "addr", "show", "dev", interface_name], check=False)
    match = re.search(r"\binet\s+(\d+\.\d+\.\d+\.\d+)/", output)
    if match:
        return match.group(1)
    return "10.42.0.1"


def configure_hotspot_dns_mapping(interface_name: str = WLAN_IF) -> None:
    address = _ipv4_for_interface(interface_name)
    DNS_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    DNS_CONFIG_PATH.write_text(f"address=/{HOTSPOT_DOMAIN}/{address}\n", encoding="utf-8")

    dns_result = run_command(["systemctl", "restart", "dnsmasq"], check=False)
    if dns_result.returncode != 0:
        logger.warning("Could not restart dnsmasq: %s", dns_result.stderr)


def start_hotspot_connection() -> None:
    run_command(["nmcli", "connection", "up", CON_HOTSPOT])


def generate_hotspot_credentials() -> tuple[str, str]:
    charset = string.ascii_uppercase + string.digits
    suffix = "".join(random.choice(charset) for _ in range(HOTSPOT_SSID_SUFFIX_LENGTH))
    password = "".join(random.choice(charset) for _ in range(HOTSPOT_PASSWORD_LENGTH))
    ssid = f"{HOTSPOT_SSID_PREFIX}{suffix}"
    return ssid, password
