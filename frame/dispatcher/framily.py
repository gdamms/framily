#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
import time

sys.path.append("/home/framily")

from frame_core.api import FetchStatus, FrameApiClient, FrameApiError
from frame_core.config import ConfigStore, FrameState
from frame_core.display import (
    render_connecting_wifi,
    render_framily_info,
    render_hotspot,
    render_waiting_first_image,
    save_image_bytes,
)
from frame_core.lock import LockUnavailableError, hold_lock
from frame_core.logging import get_logger
from frame_core.network import (
    CommandError,
    configure_hotspot_dns_mapping,
    generate_hotspot_credentials,
    get_active_connection_name,
    set_hotspot_credentials,
    start_hotspot_connection,
)
from frame_core.settings import (
    CON_HOTSPOT,
    CON_WIFI,
    DISPATCHER_LOCK_PATH,
    FLASK_PORT,
    FRAME_FETCH_INTERVAL_SECONDS,
    FRAMILY_MEMBER_CHECK_INTERVAL_SECONDS,
    HOTSPOT_DOMAIN,
    REQUEST_RETRY_ATTEMPTS,
    REQUEST_RETRY_BACKOFF_BASE_SECONDS,
    REQUEST_RETRY_MAX_BACKOFF_SECONDS,
    WLAN_IF,
)


logger = get_logger(__name__)
store = ConfigStore()


def _setup_url() -> str:
    if FLASK_PORT == 80:
        return f"http://{HOTSPOT_DOMAIN}/"
    if FLASK_PORT == 443:
        return f"https://{HOTSPOT_DOMAIN}/"
    return f"http://{HOTSPOT_DOMAIN}:{FLASK_PORT}/"


def _retry_delay(attempt_number: int) -> int:
    delay = REQUEST_RETRY_BACKOFF_BASE_SECONDS ** max(0, attempt_number - 1)
    return min(delay, REQUEST_RETRY_MAX_BACKOFF_SECONDS)


def _run_with_retries(operation, description: str):
    last_error: FrameApiError | None = None

    for attempt in range(1, REQUEST_RETRY_ATTEMPTS + 1):
        try:
            return operation()
        except FrameApiError as error:
            last_error = error
            if attempt >= REQUEST_RETRY_ATTEMPTS or not error.transient:
                break

            delay = _retry_delay(attempt)
            logger.warning(
                "%s failed (attempt %s/%s): %s. Retrying in %ss",
                description,
                attempt,
                REQUEST_RETRY_ATTEMPTS,
                error,
                delay,
            )
            time.sleep(delay)

    if last_error is None:
        raise RuntimeError(f"{description} failed before execution")
    raise last_error


def _enter_hotspot_mode(message: str | None = None, update_failure: bool = False) -> None:
    if update_failure and message:
        store.record_failure(message, state=FrameState.ERROR)
    elif message:
        store.save_message(message)

    ssid, password = generate_hotspot_credentials()
    set_hotspot_credentials(ssid, password)
    store.set_hotspot_credentials(ssid, password)

    start_hotspot_connection()
    configure_hotspot_dns_mapping(WLAN_IF)

    store.set_state(FrameState.HOTSPOT)
    render_hotspot(ssid, password, _setup_url())
    logger.info("Hotspot mode enabled with generated credentials")


def _handle_runtime_failure(message: str) -> bool:
    snapshot = store.record_failure(message, state=FrameState.ERROR)
    logger.error(
        "%s (consecutive_failures=%s, failure_duration_s=%s)",
        message,
        snapshot.consecutive_failures,
        snapshot.failure_duration_s,
    )

    if snapshot.should_enter_hotspot:
        _enter_hotspot_mode(update_failure=False)
        return True

    return False


def _wait_for_framily_membership(client: FrameApiClient, framily_code: str, frame_token: str) -> bool:
    store.set_state(FrameState.WAITING_FOR_MEMBER)

    while True:
        render_framily_info(framily_code)

        try:
            initiated = _run_with_retries(
                lambda: client.check_framily(framily_code, frame_token),
                "Framily check",
            )
        except FrameApiError as error:
            if _handle_runtime_failure(f"Framily check failed: {error}"):
                return False

            time.sleep(FRAMILY_MEMBER_CHECK_INTERVAL_SECONDS)
            continue

        store.mark_success(state=FrameState.WAITING_FOR_MEMBER)
        if initiated:
            return True

        time.sleep(FRAMILY_MEMBER_CHECK_INTERVAL_SECONDS)


def _fetch_images_loop(client: FrameApiClient, framily_code: str, frame_token: str) -> None:
    store.set_state(FrameState.FETCHING_IMAGES)

    while True:
        try:
            result = _run_with_retries(
                lambda: client.fetch_picture(framily_code, frame_token),
                "Picture fetch",
            )
        except FrameApiError as error:
            if _handle_runtime_failure(f"Picture fetch failed: {error}"):
                return

            time.sleep(FRAME_FETCH_INTERVAL_SECONDS)
            continue

        store.mark_success(state=FrameState.FETCHING_IMAGES)
        if result.status == FetchStatus.NO_CONTENT:
            render_waiting_first_image(framily_code)
        elif result.content is not None:
            save_image_bytes(result.content)

        time.sleep(FRAME_FETCH_INTERVAL_SECONDS)


def _ensure_registration(client: FrameApiClient) -> tuple[str, str] | None:
    config = store.load()
    framily_code = str(config.get("framily_code", "") or "")
    frame_token = str(config.get("frame_token", "") or "")
    if framily_code and frame_token:
        return framily_code, frame_token

    while True:
        try:
            framily_code, frame_token = _run_with_retries(
                lambda: client.create_framily(),
                "Framily creation",
            )
        except FrameApiError as error:
            if _handle_runtime_failure(f"Framily creation failed: {error}"):
                return None

            time.sleep(FRAMILY_MEMBER_CHECK_INTERVAL_SECONDS)
            continue

        store.update(framily_code=framily_code, frame_token=frame_token)
        store.mark_success(state=FrameState.WAITING_FOR_MEMBER)
        render_framily_info(framily_code)
        return framily_code, frame_token


def wifi_up() -> None:
    render_connecting_wifi()
    store.set_state(FrameState.CONNECTING_WIFI)

    config = store.load()
    server_url = str(config.get("server_url", "") or "").strip()
    if not server_url:
        _enter_hotspot_mode("Server URL not configured. Please set it up.")
        return

    client = FrameApiClient(server_url)
    registration = _ensure_registration(client)
    if registration is None:
        return

    framily_code, frame_token = registration
    if not _wait_for_framily_membership(client, framily_code, frame_token):
        return

    _fetch_images_loop(client, framily_code, frame_token)


def hotspot_up() -> None:
    _enter_hotspot_mode()


def _handle_dispatch_event(interface: str, action: str) -> None:
    if action != "up" or interface != WLAN_IF:
        logger.debug("Ignoring dispatcher event: interface=%s action=%s", interface, action)
        return

    connection = get_active_connection_name()
    logger.info("Dispatcher event for %s: active connection=%s", interface, connection)

    if connection == CON_HOTSPOT:
        hotspot_up()
        return

    if connection == CON_WIFI:
        wifi_up()
        return

    logger.info("No managed active connection detected, skipping")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Framily NetworkManager dispatcher")
    parser.add_argument("interface", type=str, help="Network interface receiving event")
    parser.add_argument("action", type=str, help="Connection action")
    args = parser.parse_args()

    try:
        with hold_lock(DISPATCHER_LOCK_PATH, non_blocking=True):
            _handle_dispatch_event(args.interface, args.action)
    except LockUnavailableError:
        logger.info("Skipping dispatcher execution because another instance is already running")
    except CommandError as error:
        logger.error("Dispatcher command failed: %s", error)
