import fcntl
import json
import threading
import time

import requests
from PIL import Image, ImageDraw, ImageFont
from urlpath import URL
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from logging_setup import get_logger
from utils import (
    AGENT_LOCK_PATH,
    AGENT_RECHECK_PATH,
    CON_HOTSPOT,
    CON_WIFI,
    EPD_IMAGE_PATH,
    EPD_INFO_PATH,
    HOTSPOT_DOMAIN,
    WEB_PORT,
    clear_message,
    get_active_connection,
    get_hotspot,
    load_config,
    make_qr,
    save_config,
    save_message,
    set_wifi,
    start_hotspot,
)

logger = get_logger("agent")

FRAME_CREATE_PATH = "/api/v1/frame/create"
FRAME_CHECK_PATH = "/api/v1/frame/check"
FRAME_STATUS_PATH = "/api/v1/frame/status"
FRAME_SETTINGS_PATH = "/api/v1/frame/settings"
FRAME_FETCH_PATH = "/api/v1/frame/fetch"

# Used if the server can't be reached to fetch the real fetch interval.
DEFAULT_INTERVAL_MINUTES = 5
MIN_INTERVAL_MINUTES = 1
MAX_INTERVAL_MINUTES = 60

# How many consecutive transient failures (network errors, 5xx) we tolerate
# before giving up on the current Wi-Fi session and falling back to hotspot
# mode. A single blip should never be enough to kick the frame out of Wi-Fi.
MAX_CONSECUTIVE_FAILURES = 4

# How often we re-check network state / pending config while not in a
# steady fetch loop (hotspot mode, waiting for framily members, transitions).
UNSTEADY_POLL_SECONDS = 5

# Set by the recheck watcher whenever config.json or agent.recheck changes,
# so the agent can react to a Wi-Fi credentials submission or a NetworkManager
# dispatcher nudge without waiting out a long sleep.
recheck_event = threading.Event()


class FrameApiError(Exception):
    def __init__(self, message: str, transient: bool = True):
        super().__init__(message)
        self.transient = transient


def acquire_lock():
    """Refuse to run a second instance concurrently. Returns the open lock
    file handle, which must stay referenced for the lifetime of the process
    (closing/GC'ing it releases the lock)."""
    lock_file = open(AGENT_LOCK_PATH, "w")
    try:
        fcntl.flock(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        logger.error("Another agent instance already holds the lock. Exiting.")
        raise SystemExit(1)
    return lock_file


class RecheckHandler(FileSystemEventHandler):
    def __init__(self, watch_paths, event):
        self.watch_paths = {str(p) for p in watch_paths}
        self.event = event

    def _maybe_set(self, event):
        if event.src_path in self.watch_paths:
            self.event.set()

    def on_modified(self, event):
        self._maybe_set(event)

    def on_created(self, event):
        self._maybe_set(event)


def start_recheck_watcher() -> Observer:
    # Deliberately NOT watching CONFIG_PATH here: the agent writes config.json
    # itself on every successful fetch (clear_message()) and on other routine
    # bookkeeping, so watching it would make the agent's own writes
    # self-trigger a "wake up now" - defeating the configured fetch interval
    # entirely (this is exactly what was spamming fetches back-to-back).
    # AGENT_RECHECK_PATH is a separate file, touched only by external actors
    # (the web UI after writing new intent, the dispatcher on a network
    # transition) that genuinely want the agent to react early.
    AGENT_RECHECK_PATH.touch(exist_ok=True)
    handler = RecheckHandler([AGENT_RECHECK_PATH], recheck_event)
    observer = Observer()
    observer.schedule(handler, path=str(AGENT_RECHECK_PATH.parent), recursive=False)
    observer.start()
    return observer


def wait_for_recheck(timeout: float) -> None:
    recheck_event.wait(timeout=timeout)
    recheck_event.clear()


# --- Display ---------------------------------------------------------------

def _new_canvas():
    epd_info = json.loads(EPD_INFO_PATH.read_text())
    width, height = epd_info["width"], epd_info["height"]
    img = Image.new("RGB", (height, width), "white")
    return img, ImageDraw.Draw(img)


def display_hotspot():
    ssid, password = get_hotspot()

    if WEB_PORT == 80:
        server_url = f"http://{HOTSPOT_DOMAIN}/"
    elif WEB_PORT == 443:
        server_url = f"https://{HOTSPOT_DOMAIN}/"
    else:
        server_url = f"http://{HOTSPOT_DOMAIN}:{WEB_PORT}/"
    wifi_qr_data = f"WIFI:T:WPA;S:{ssid};P:{password};;"

    wifi_qr = make_qr(wifi_qr_data)
    url_qr = make_qr(server_url)

    img, draw = _new_canvas()
    font = ImageFont.truetype("DejaVuSans.ttf", 30)
    margin = 50

    draw.text((margin, 50), "Connect to the Pi", font=font, fill="black")
    img.paste(wifi_qr, (margin, 100))
    draw.text(
        (margin + wifi_qr.width + 40, 100),
        f"SSID:\n{ssid}\n\nPassword:\n{password}",
        font=font,
        fill="black",
    )

    draw.text((margin, 100 + wifi_qr.height + 40), "Open this URL", font=font, fill="black")
    draw.text((margin, 100 + wifi_qr.height + 90), server_url, font=font, fill="black")
    img.paste(url_qr, (margin, 100 + wifi_qr.height + 140))

    img.save(EPD_IMAGE_PATH)


def display_connecting_wifi():
    img, draw = _new_canvas()
    font = ImageFont.truetype("DejaVuSans.ttf", 30)
    draw.text((50, 50), "Connecting to Wi-Fi...", font=font, fill="black")
    img.save(EPD_IMAGE_PATH)


def display_framily_info(config: dict):
    img, draw = _new_canvas()
    font = ImageFont.truetype("DejaVuSans.ttf", 30)
    draw.text((50, 50), "Framily Code:", font=font, fill="black")
    draw.text((50, 100), config.get("framily_code", ""), font=font, fill="black")
    img.save(EPD_IMAGE_PATH)


def display_upload_first_image(config: dict):
    img, draw = _new_canvas()
    font = ImageFont.truetype("DejaVuSans.ttf", 30)
    framily_code = config.get("framily_code", "")
    draw.text((50, 50), f"Framily {framily_code}:\nWaiting for first image...", font=font, fill="black")
    img.save(EPD_IMAGE_PATH)


# --- Backend API -------------------------------------------------------------

def _post(server_url: str, path: str, payload: dict, timeout: float = 10):
    url = URL(server_url) / path
    try:
        response = url.post(json=payload, timeout=timeout)
    except requests.exceptions.RequestException as e:
        raise FrameApiError(f"Error connecting to the server: {e}", transient=True) from e

    if not response.ok:
        transient = response.status_code >= 500
        raise FrameApiError(f"Request failed ({response.status_code}): {response.text}", transient=transient)

    return response


def retry_transient(func, *args, max_attempts=MAX_CONSECUTIVE_FAILURES, **kwargs):
    """Call func(*args, **kwargs). On a transient FrameApiError, retry with a
    short backoff up to max_attempts times before re-raising. A non-transient
    error re-raises immediately."""
    attempt = 0
    while True:
        try:
            return func(*args, **kwargs)
        except FrameApiError as e:
            attempt += 1
            if not e.transient or attempt >= max_attempts:
                raise
            wait = min(30, 2**attempt)
            logger.warning(f"{func.__name__} failed ({attempt}/{max_attempts}), retrying in {wait}s: {e}")
            wait_for_recheck(wait)


def create_framily(config: dict) -> dict:
    response = _post(config.get("server_url", ""), FRAME_CREATE_PATH, {"name": "My Framily"})
    data = response.json()
    framily_code = data.get("framily_code")
    frame_token = data.get("frame_token")
    if not framily_code or not frame_token:
        raise FrameApiError("Invalid response from server: missing framily_code/frame_token", transient=False)

    config["framily_code"] = framily_code
    config["frame_token"] = frame_token
    config["message"] = ""
    save_config(config)
    logger.info("Framily created successfully.")
    return config


def check_framily(config: dict) -> bool:
    response = _post(config.get("server_url", ""), FRAME_CHECK_PATH, {
        "framily_code": config.get("framily_code", ""),
        "frame_token": config.get("frame_token", ""),
    })
    initiated = response.json().get("initiated", False)
    if initiated:
        clear_message()
    return initiated


def report_status(config: dict) -> None:
    """Best-effort: failures here shouldn't block the frame from displaying
    pictures."""
    try:
        epd_info = json.loads(EPD_INFO_PATH.read_text())
    except (OSError, json.JSONDecodeError):
        return

    payload = {
        "framily_code": config.get("framily_code", ""),
        "frame_token": config.get("frame_token", ""),
        "resolution_width": epd_info.get("width"),
        "resolution_height": epd_info.get("height"),
    }
    try:
        _post(config.get("server_url", ""), FRAME_STATUS_PATH, payload)
    except FrameApiError as e:
        logger.warning(f"Failed to report status: {e}")


def fetch_settings(config: dict) -> float:
    """Interval (in minutes) the frame should wait between picture fetches.
    Falls back to DEFAULT_INTERVAL_MINUTES if the server can't be reached or
    returns a nonsensical value, since a missed settings fetch shouldn't stop
    the frame or make it sleep for an absurd amount of time."""
    try:
        response = _post(config.get("server_url", ""), FRAME_SETTINGS_PATH, {
            "framily_code": config.get("framily_code", ""),
            "frame_token": config.get("frame_token", ""),
        })
    except FrameApiError as e:
        logger.warning(f"Failed to fetch settings, using default interval: {e}")
        return DEFAULT_INTERVAL_MINUTES

    interval = response.json().get("interval_minutes", DEFAULT_INTERVAL_MINUTES)
    if not isinstance(interval, (int, float)) or interval <= 0:
        logger.warning(f"Server returned invalid interval_minutes={interval!r}, using default.")
        return DEFAULT_INTERVAL_MINUTES

    clamped = max(MIN_INTERVAL_MINUTES, min(MAX_INTERVAL_MINUTES, interval))
    if clamped != interval:
        logger.warning(f"Clamping interval_minutes {interval} -> {clamped}")
    return clamped


def fetch_image(config: dict) -> None:
    try:
        response = _post(config.get("server_url", ""), FRAME_FETCH_PATH, {
            "framily_code": config.get("framily_code", ""),
            "frame_token": config.get("frame_token", ""),
        })
    except FrameApiError as e:
        raise FrameApiError(f"Error fetching picture: {e}", transient=e.transient) from e

    if response.status_code == 204:
        logger.info("No pictures available for this framily.")
        display_upload_first_image(config)
    else:
        EPD_IMAGE_PATH.write_bytes(response.content)
        logger.info("Picture fetched and saved successfully.")
    clear_message()


# --- Session / state machine ------------------------------------------------

def run_fetch_loop(config: dict) -> None:
    """Runs until a non-transient failure or MAX_CONSECUTIVE_FAILURES
    consecutive transient failures give up on the session."""
    consecutive_failures = 0
    while True:
        try:
            fetch_image(config)
            consecutive_failures = 0
        except FrameApiError as e:
            consecutive_failures += 1
            logger.warning(f"Fetch failed ({consecutive_failures}/{MAX_CONSECUTIVE_FAILURES}): {e}")
            if not e.transient or consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                save_message(f"Failed to fetch picture: {e}")
                return

        interval_minutes = fetch_settings(config)
        wait_for_recheck(interval_minutes * 60)
        config = load_config()


def apply_pending_wifi(config: dict) -> dict:
    if config.get("pending_wifi_reset"):
        logger.info("Clearing stored Wi-Fi credentials (reset requested).")
        config["pending_wifi_reset"] = False
        save_config(config)
        set_wifi("", "", start=False)
        return config

    ssid = config.get("pending_wifi_ssid", "")
    password = config.get("pending_wifi_password", "")
    if not ssid:
        return config

    logger.info(f"Applying pending Wi-Fi credentials for SSID '{ssid}'.")
    config["pending_wifi_ssid"] = ""
    config["pending_wifi_password"] = ""
    save_config(config)
    set_wifi(ssid, password)
    return config


def run_wifi_session(config: dict) -> None:
    display_connecting_wifi()

    if not config.get("server_url"):
        save_message("Server URL not configured, please set it up.")
        start_hotspot()
        return

    if not config.get("framily_code") or not config.get("frame_token"):
        try:
            config = retry_transient(create_framily, config)
        except FrameApiError as e:
            logger.error(f"Failed to create framily: {e}")
            save_message(f"Failed to create framily: {e}")
            start_hotspot()
            return
        display_framily_info(config)

    consecutive_check_failures = 0
    while True:
        try:
            initiated = check_framily(config)
            consecutive_check_failures = 0
        except FrameApiError as e:
            consecutive_check_failures += 1
            logger.warning(f"check_framily failed ({consecutive_check_failures}/{MAX_CONSECUTIVE_FAILURES}): {e}")
            if not e.transient or consecutive_check_failures >= MAX_CONSECUTIVE_FAILURES:
                save_message(f"Framily does not exist or token is invalid: {e}")
                start_hotspot()
                return
            initiated = False

        if initiated:
            break
        display_framily_info(config)
        wait_for_recheck(5)

    report_status(config)
    # run_fetch_loop() only returns once it has given up (persistent or
    # exhausted-retries failure) - fall back to hotspot so the frame can be
    # reprovisioned instead of going dark with no path back.
    run_fetch_loop(config)
    start_hotspot()


def determine_mode() -> str | None:
    active = get_active_connection()
    if active == CON_HOTSPOT:
        return "hotspot"
    if active == CON_WIFI:
        return "wifi"
    return None


def main_loop() -> None:
    last_mode = None
    while True:
        try:
            config = load_config()
            mode = determine_mode()

            if mode != last_mode:
                logger.info(f"Network mode: {last_mode} -> {mode}")

            if mode == "hotspot":
                if last_mode != "hotspot":
                    display_hotspot()
                last_mode = mode
                config = apply_pending_wifi(config)
                wait_for_recheck(UNSTEADY_POLL_SECONDS)
                continue

            if mode == "wifi":
                last_mode = mode
                config = apply_pending_wifi(config)
                run_wifi_session(config)
                last_mode = None  # force a re-render / re-check next tick
                continue

            last_mode = mode
            wait_for_recheck(UNSTEADY_POLL_SECONDS)
        except Exception:
            # Belt-and-suspenders: nothing above should raise outside of
            # FrameApiError, but if it does, log it and keep the agent alive
            # rather than letting an unexpected bug silently kill the loop.
            logger.exception("Unhandled error in agent main loop, continuing.")
            time.sleep(UNSTEADY_POLL_SECONDS)


def main() -> None:
    acquire_lock()
    observer = start_recheck_watcher()
    try:
        main_loop()
    finally:
        observer.stop()
        observer.join()


if __name__ == "__main__":
    main()
