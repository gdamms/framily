import asyncio
import json
from typing import Optional

from bless import (
    BlessGATTCharacteristic,
    BlessServer,
    GATTAttributePermissions,
    GATTCharacteristicProperties,
)
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from logging_setup import get_logger
from utils import (
    AGENT_RECHECK_PATH,
    CONFIG_PATH,
    get_ble_local_name,
    load_config,
    save_config,
)

logger = get_logger("ble")

# Custom GATT service the mobile app scans for to find unprovisioned (or
# reprovisionable - it's always advertising, see run()) frames. Exact UUIDs
# don't matter beyond staying consistent with the frontend's BLE client.
SERVICE_UUID = "7e6a1000-a2f0-4a9e-8f3c-1a2b3c4d5e00"
SSID_CHAR_UUID = "7e6a1001-a2f0-4a9e-8f3c-1a2b3c4d5e00"
PASSWORD_CHAR_UUID = "7e6a1002-a2f0-4a9e-8f3c-1a2b3c4d5e00"
SERVER_URL_CHAR_UUID = "7e6a1003-a2f0-4a9e-8f3c-1a2b3c4d5e00"
SUBMIT_CHAR_UUID = "7e6a1004-a2f0-4a9e-8f3c-1a2b3c4d5e00"
STATUS_CHAR_UUID = "7e6a1005-a2f0-4a9e-8f3c-1a2b3c4d5e00"

# In-memory staging for the three data characteristics - only committed to
# config.json (where frame/agent/main.py's apply_wifi_update() picks them
# up) once `submit` is written, so a partially-filled-in form on the phone
# never triggers a Wi-Fi join attempt.
_pending = {"ssid": "", "password": "", "server_url": ""}


# Conservative cap on the status payload's message field. BLE's default ATT
# MTU is only 23 bytes (20 usable) until the client negotiates a larger one;
# most modern phones do, but this keeps the payload safe even if that
# negotiation doesn't happen, rather than relying on it.
MAX_STATUS_MESSAGE_LENGTH = 80


def _status_payload(config: dict) -> bytes:
    message = config.get("provisioning_message", "")
    if len(message) > MAX_STATUS_MESSAGE_LENGTH:
        message = message[:MAX_STATUS_MESSAGE_LENGTH - 1] + "…"
    return json.dumps({
        "status": config.get("provisioning_status", "idle"),
        "message": message,
        "framily_code": config.get("framily_code", ""),
        "created_new_framily": config.get("provisioning_created_new", False),
    }).encode("utf-8")


def _read_request(characteristic: BlessGATTCharacteristic, **kwargs) -> bytearray:
    return characteristic.value


def _write_request(characteristic: BlessGATTCharacteristic, value: bytearray, **kwargs) -> None:
    characteristic.value = value
    uuid = characteristic.uuid
    text = bytes(value).decode("utf-8", errors="replace")

    if uuid == SSID_CHAR_UUID:
        _pending["ssid"] = text
    elif uuid == PASSWORD_CHAR_UUID:
        _pending["password"] = text
    elif uuid == SERVER_URL_CHAR_UUID:
        _pending["server_url"] = text
    elif uuid == SUBMIT_CHAR_UUID:
        logger.info(f"Provisioning submit received (ssid={_pending['ssid']!r}, server_url={_pending['server_url']!r}).")
        config = load_config()
        config["wifi_ssid"] = _pending["ssid"]
        config["wifi_password"] = _pending["password"]
        config["server_url"] = _pending["server_url"]
        config["wifi_should_update"] = True
        # Clear any stale result from a previous attempt so the app doesn't
        # briefly see the last session's outcome before the agent reacts.
        config["provisioning_status"] = "idle"
        config["provisioning_message"] = ""
        config["provisioning_created_new"] = False
        save_config(config)
        AGENT_RECHECK_PATH.touch(exist_ok=True)


class ConfigChangeHandler(FileSystemEventHandler):
    """Watches CONFIG_PATH's parent directory (same rationale as the agent's
    own recheck watcher and the EPD image watcher: watching a single file
    directly is unreliable across watchdog backends) for provisioning status
    changes written by frame/agent/main.py, and relays them over the
    `status` characteristic.

    Unlike the agent's own recheck watcher, watching CONFIG_PATH here is
    safe: this process never writes to it itself (only to _pending, staged
    in memory), so there's no risk of self-triggering."""

    def __init__(self, server: BlessServer, loop: asyncio.AbstractEventLoop):
        self.server = server
        self.loop = loop
        self.last_payload: Optional[bytes] = None

    def _maybe_notify(self, path: str) -> None:
        if path != str(CONFIG_PATH):
            return
        payload = _status_payload(load_config())
        if payload == self.last_payload:
            return
        self.last_payload = payload
        asyncio.run_coroutine_threadsafe(self._update(payload), self.loop)

    async def _update(self, payload: bytes) -> None:
        characteristic = self.server.get_characteristic(STATUS_CHAR_UUID)
        if characteristic is None:
            return
        characteristic.value = bytearray(payload)
        self.server.update_value(SERVICE_UUID, STATUS_CHAR_UUID)

    def on_modified(self, event):
        if not event.is_directory:
            self._maybe_notify(event.src_path)

    def on_created(self, event):
        if not event.is_directory:
            self._maybe_notify(event.src_path)

    def on_moved(self, event):
        if not event.is_directory:
            self._maybe_notify(event.dest_path)


async def run() -> None:
    loop = asyncio.get_event_loop()
    server = BlessServer(name=get_ble_local_name())
    server.read_request_func = _read_request
    server.write_request_func = _write_request

    await server.add_new_service(SERVICE_UUID)

    write_props = GATTCharacteristicProperties.write
    write_perms = GATTAttributePermissions.writeable
    for char_uuid in (SSID_CHAR_UUID, PASSWORD_CHAR_UUID, SERVER_URL_CHAR_UUID, SUBMIT_CHAR_UUID):
        await server.add_new_characteristic(SERVICE_UUID, char_uuid, write_props, None, write_perms)

    status_props = GATTCharacteristicProperties.read | GATTCharacteristicProperties.notify
    status_perms = GATTAttributePermissions.readable
    await server.add_new_characteristic(
        SERVICE_UUID, STATUS_CHAR_UUID, status_props,
        bytearray(_status_payload(load_config())), status_perms,
    )

    await server.start()
    logger.info(f"BLE peripheral advertising as '{server.name}'.")

    # Runs for the lifetime of the process (unlike the old hotspot, BLE is a
    # separate radio from Wi-Fi and never needs to be started/stopped in
    # coordination with network state - see frame/agent/main.py's
    # determine_mode()/main_loop()).
    handler = ConfigChangeHandler(server, loop)
    observer = Observer()
    observer.schedule(handler, path=str(CONFIG_PATH.parent), recursive=False)
    observer.start()

    try:
        while True:
            await asyncio.sleep(3600)
    finally:
        observer.stop()
        observer.join()


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
