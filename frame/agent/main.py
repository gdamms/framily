import fcntl
import json
import os
import tempfile
import threading
import time
from pathlib import Path
from typing import Callable

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
    get_ip_address,
    get_wifi,
    load_config,
    make_qr,
    save_config,
    save_message,
    set_wifi,
    start_hotspot,
    start_wifi,
)

logger = get_logger("agent")

FRAME_CREATE_PATH = "/api/v1/frame/create"
FRAME_CHECK_PATH = "/api/v1/frame/check"
FRAME_DELETE_PATH = "/api/v1/frame/delete"
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

# While the framily has no visible pictures yet, retry the fetch on this much
# shorter cadence instead of waiting out the full (often multi-minute) fetch
# interval - so the frame picks up the first uploaded photo promptly.
NO_PICTURE_RETRY_SECONDS = 10

# While parked in hotspot mode waiting for credentials, how often to retry
# the already-saved Wi-Fi profile (if any). Handles a transient outage (e.g.
# router reboot) recovering on its own without the user having to
# re-provision through the setup UI.
HOTSPOT_WIFI_RETRY_SECONDS = 5 * 60

# Set by the recheck watcher whenever config.json or agent.recheck changes,
# so the agent can react to a Wi-Fi credentials submission or a NetworkManager
# dispatcher nudge without waiting out a long sleep.
recheck_event = threading.Event()


class FrameApiError(Exception):
    def __init__(self, message: str, transient: bool = True, not_found: bool = False):
        super().__init__(message)
        self.transient = transient
        # True when the server responded 404, i.e. the framily_code/frame_token
        # pair is no longer valid (most likely the framily was deleted). Callers
        # use this to point the user at the web UI's reset button instead of a
        # generic connectivity error.
        self.not_found = not_found


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


# --- Display -----------------------------------------------------------------
#
# The panel is a 6-color e-ink display (black/white/yellow/red/blue/green) -
# any color outside that exact palette gets dithered into speckles, so all
# drawing here sticks to pure BLACK/WHITE plus BLUE as a single accent.
# Every screen is built for the panel's native landscape canvas and laid out
# as a group of blocks whose total height is measured first, then centered -
# rather than fixed y-offsets - so it stays centered regardless of font
# metrics, and shrink-to-fit text so a long SSID/password/URL/code never
# overflows.

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
BLUE = (0, 0, 255)

_FONT_CACHE: dict[tuple[str, int], ImageFont.FreeTypeFont] = {}


def _font(weight: str, size: int) -> ImageFont.FreeTypeFont:
    key = (weight, size)
    if key not in _FONT_CACHE:
        name = "DejaVuSans-Bold.ttf" if weight == "bold" else "DejaVuSans.ttf"
        _FONT_CACHE[key] = ImageFont.truetype(name, size)
    return _FONT_CACHE[key]


def _fit_font(draw, text, weight, max_width, max_size, min_size=14):
    """Largest font size (down to min_size) that keeps text within max_width."""
    size = max_size
    while size > min_size:
        font = _font(weight, size)
        if draw.textlength(text, font=font) <= max_width:
            return font
        size -= 2
    return _font(weight, min_size)


def _text_height(draw, text, font):
    bbox = draw.multiline_textbbox((0, 0), text, font=font, align="center")
    return bbox[3] - bbox[1]


def _draw_top(draw, text, font, y, cx, fill=BLACK):
    """Draw text horizontally centered on cx, top edge at y. Returns its height."""
    draw.multiline_text((cx, y), text, font=font, fill=fill, anchor="ma", align="center")
    return _text_height(draw, text, font)


def _fitted_lines_height(draw, lines, weight, max_width, max_size, gap=6, min_size=14):
    """Each line gets its own shrink-to-fit font, so e.g. a long password
    doesn't force a short SSID line down to the same tiny size."""
    fonts = [_fit_font(draw, line, weight, max_width, max_size, min_size) for line in lines]
    heights = [_text_height(draw, line, font) for line, font in zip(lines, fonts)]
    return fonts, sum(heights) + gap * (len(lines) - 1)


def _draw_fitted_lines(draw, lines, fonts, y, cx, gap=6):
    for line, font in zip(lines, fonts):
        y += _draw_top(draw, line, font, y, cx) + gap
    return y


def _wifi_icon(draw, cx, cy, size=100, fill=BLACK, width=7):
    dot_r = size * 0.09
    draw.ellipse((cx - dot_r, cy - dot_r, cx + dot_r, cy + dot_r), fill=fill)
    for r in (size * 0.42, size * 0.68, size * 0.94):
        bbox = (cx - r, cy - r, cx + r, cy + r)
        draw.arc(bbox, start=215, end=325, fill=fill, width=width)


def _photo_icon(draw, cx, cy, size=100, fill=BLACK, width=6):
    w, h = size, size * 0.72
    left, top = cx - w / 2, cy - h / 2
    draw.rounded_rectangle((left, top, left + w, top + h), radius=8, outline=fill, width=width)
    sun_r = h * 0.16
    draw.ellipse(
        (left + w * 0.18 - sun_r, top + h * 0.28 - sun_r, left + w * 0.18 + sun_r, top + h * 0.28 + sun_r),
        outline=fill, width=max(2, width - 2),
    )
    draw.line(
        (left + w * 0.08, top + h * 0.92, left + w * 0.4, top + h * 0.55, left + w * 0.62, top + h * 0.78,
         left + w * 0.8, top + h * 0.6, left + w * 0.95, top + h * 0.85),
        fill=fill, width=width, joint="curve",
    )


def _new_canvas():
    epd_info = json.loads(EPD_INFO_PATH.read_text())
    width, height = epd_info["width"], epd_info["height"]
    img = Image.new("RGB", (width, height), WHITE)
    return img, ImageDraw.Draw(img)


def _write_epd_image(write: Callable[[Path], object]) -> None:
    """Write via a temp file in the same directory, then atomically rename it
    over EPD_IMAGE_PATH. epd/main.py's watcher already treats a moved-in file
    as the render trigger (see its on_moved handling) - writing in place
    instead would let it catch the file mid-write (empty/truncated) and try
    to render a partial image."""
    fd, tmp_name = tempfile.mkstemp(dir=EPD_IMAGE_PATH.parent, suffix=EPD_IMAGE_PATH.suffix)
    os.close(fd)
    tmp_path = Path(tmp_name)
    try:
        write(tmp_path)
        os.chmod(tmp_path, 0o644)
        tmp_path.replace(EPD_IMAGE_PATH)
    except BaseException:
        tmp_path.unlink(missing_ok=True)
        raise


def display_hotspot():
    ssid, password = get_hotspot()

    if WEB_PORT == 80:
        server_url = f"http://{HOTSPOT_DOMAIN}/"
    elif WEB_PORT == 443:
        server_url = f"https://{HOTSPOT_DOMAIN}/"
    else:
        server_url = f"http://{HOTSPOT_DOMAIN}:{WEB_PORT}/"

    img, draw = _new_canvas()
    width, height = img.size
    cx = width // 2
    margin = 60
    col_w = (width - margin * 2) / 2
    left_cx = margin + col_w / 2
    right_cx = margin + col_w + col_w / 2
    detail_max_width = col_w - 40

    title_font = _font("bold", 34)
    sub_font = _font("bold", 22)
    title = "Set Up Your Frame"
    left_sub = "1. Scan to join Wi-Fi"
    right_sub = "2. Scan to finish setup"
    left_lines = [f"SSID: {ssid}", f"Password: {password}"]
    right_lines = [server_url]

    qr_size = 190
    gap_after_title = 16
    gap_after_rule = 22
    gap_after_sub = 16
    gap_after_qr = 20
    detail_gap = 6

    title_h = _text_height(draw, title, title_font)
    sub_h = _text_height(draw, left_sub, sub_font)
    left_fonts, left_detail_h = _fitted_lines_height(draw, left_lines, "regular", detail_max_width, 22, gap=detail_gap)
    right_fonts, right_detail_h = _fitted_lines_height(draw, right_lines, "regular", detail_max_width, 22, gap=detail_gap)
    detail_h = max(left_detail_h, right_detail_h)

    total_h = (
        title_h + gap_after_title + 2 + gap_after_rule
        + sub_h + gap_after_sub + qr_size + gap_after_qr + detail_h
    )
    y = (height - total_h) / 2

    y += _draw_top(draw, title, title_font, y, cx) + gap_after_title
    draw.line((margin + 20, y, width - margin - 20, y), fill=BLUE, width=3)
    y += 2 + gap_after_rule

    sub_y = y
    _draw_top(draw, left_sub, sub_font, sub_y, left_cx)
    _draw_top(draw, right_sub, sub_font, sub_y, right_cx)
    y += sub_h + gap_after_sub

    qr_y = y
    wifi_qr = make_qr(f"WIFI:T:WPA;S:{ssid};P:{password};;", qr_size)
    url_qr = make_qr(server_url, qr_size)
    img.paste(wifi_qr, (int(left_cx - qr_size / 2), int(qr_y)))
    img.paste(url_qr, (int(right_cx - qr_size / 2), int(qr_y)))
    for col_cx in (left_cx, right_cx):
        draw.rectangle(
            (col_cx - qr_size / 2 - 1, qr_y - 1, col_cx + qr_size / 2 + 1, qr_y + qr_size + 1),
            outline=BLACK, width=1,
        )
    y += qr_size + gap_after_qr

    _draw_fitted_lines(draw, left_lines, left_fonts, y, left_cx, gap=detail_gap)
    _draw_fitted_lines(draw, right_lines, right_fonts, y, right_cx, gap=detail_gap)

    draw.line((width / 2, sub_y - 4, width / 2, y + detail_h + 4), fill=BLACK, width=1)

    _write_epd_image(img.save)


def display_connecting_wifi():
    img, draw = _new_canvas()
    width, height = img.size
    cx, cy = width // 2, height // 2

    title_font = _font("bold", 32)
    sub_font = _font("regular", 20)
    title = "Connecting to Wi-Fi"
    sub = "This should only take a moment..."

    icon_size = 100
    gap_icon_title = 34
    gap_title_sub = 14
    title_h = _text_height(draw, title, title_font)
    sub_h = _text_height(draw, sub, sub_font)

    total_h = icon_size + gap_icon_title + title_h + gap_title_sub + sub_h
    top = cy - total_h / 2

    _wifi_icon(draw, cx, top + icon_size * 0.75, size=icon_size)

    y = top + icon_size + gap_icon_title
    y += _draw_top(draw, title, title_font, y, cx) + gap_title_sub
    _draw_top(draw, sub, sub_font, y, cx)

    _write_epd_image(img.save)


def display_framily_info(config: dict):
    framily_code = config.get("framily_code", "")

    img, draw = _new_canvas()
    width, height = img.size
    cx, cy = width // 2, height // 2

    label = "FRAMILY CODE"
    spaced_code = " ".join(framily_code)
    hint = "Open the Framily app and join with this code"
    status = "Waiting for a member to join..."

    label_font = _font("bold", 22)
    code_font = _fit_font(draw, spaced_code, "bold", width - 240, 100, min_size=48)
    hint_font = _font("regular", 24)
    status_font = _font("regular", 20)

    label_h = _text_height(draw, label, label_font)
    code_bbox = draw.textbbox((0, 0), spaced_code, font=code_font)
    code_w, code_h = code_bbox[2] - code_bbox[0], code_bbox[3] - code_bbox[1]
    pad_x, pad_y = 55, 32
    box_w, box_h = code_w + pad_x * 2, code_h + pad_y * 2
    hint_h = _text_height(draw, hint, hint_font)
    status_h = _text_height(draw, status, status_font)

    gap1, gap2, gap3 = 22, 34, 14
    total_h = label_h + gap1 + box_h + gap2 + hint_h + gap3 + status_h
    y = cy - total_h / 2

    y += _draw_top(draw, label, label_font, y, cx) + gap1

    box_top = y
    draw.rounded_rectangle(
        (cx - box_w / 2, box_top, cx + box_w / 2, box_top + box_h), radius=18, outline=BLUE, width=4
    )
    draw.text((cx, box_top + box_h / 2), spaced_code, font=code_font, fill=BLACK, anchor="mm")
    y += box_h + gap2

    y += _draw_top(draw, hint, hint_font, y, cx) + gap3
    _draw_top(draw, status, status_font, y, cx)

    _write_epd_image(img.save)


def display_upload_first_image(config: dict):
    framily_code = config.get("framily_code", "")

    img, draw = _new_canvas()
    width, height = img.size
    cx, cy = width // 2, height // 2

    badge = f"FRAMILY  {framily_code}" if framily_code else ""
    title = "Waiting for your first photo"
    sub = "Upload one from the Framily app"

    badge_font = _font("bold", 18)
    title_font = _font("bold", 30)
    sub_font = _font("regular", 20)

    icon_size = 100
    gap_icon_title = 30
    gap_title_sub = 12
    title_h = _text_height(draw, title, title_font)
    sub_h = _text_height(draw, sub, sub_font)

    total_h = icon_size + gap_icon_title + title_h + gap_title_sub + sub_h
    top = cy - total_h / 2 + (18 if badge else 0)

    if badge:
        _draw_top(draw, badge, badge_font, 28, cx)

    _photo_icon(draw, cx, top + icon_size / 2, size=icon_size)

    y = top + icon_size + gap_icon_title
    y += _draw_top(draw, title, title_font, y, cx) + gap_title_sub
    _draw_top(draw, sub, sub_font, y, cx)

    _write_epd_image(img.save)


# --- Backend API -------------------------------------------------------------

def _post(server_url: str, path: str, payload: dict, timeout: float = 10):
    url = URL(server_url) / path
    try:
        response = url.post(json=payload, timeout=timeout)
    except requests.exceptions.RequestException as e:
        raise FrameApiError(f"Error connecting to the server: {e}", transient=True) from e

    if not response.ok:
        transient = response.status_code >= 500
        not_found = response.status_code == 404
        raise FrameApiError(
            f"Request failed ({response.status_code}): {response.text}",
            transient=transient,
            not_found=not_found,
        )

    return response


def _terminal_failure_message(default: str, e: FrameApiError) -> str:
    """Message to persist when a session gives up for good. A 404 means the
    framily_code/frame_token pair the frame is holding is no longer valid on
    the server (most likely the framily was deleted) - point the user at the
    web UI's reset button instead of a generic error."""
    if e.not_found:
        return (
            "This framily no longer exists on the server - it may have been "
            "deleted. Use the Reset Framily button below to register a new one."
        )
    return default


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


def delete_framily(config: dict) -> dict:
    """Delete the currently-registered framily server-side (cascades to its
    memberships and picture visibilities), then forget local registration so
    the frame behaves as if this were its first run. Called from
    apply_pending_delete() when the web UI's Reset Framily action requests it."""
    framily_code = config.get("framily_code", "")
    frame_token = config.get("frame_token", "")
    if framily_code and frame_token:
        try:
            _post(config.get("server_url", ""), FRAME_DELETE_PATH, {
                "framily_code": framily_code,
                "frame_token": frame_token,
            })
        except FrameApiError as e:
            if not e.not_found:
                raise
            # Already gone server-side - nothing left to clean up.

    config["framily_code"] = ""
    config["frame_token"] = ""
    config["message"] = ""
    config["pending_delete"] = False
    save_config(config)
    logger.info("Framily deleted server-side and local registration cleared.")
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
        "ip_address": get_ip_address() or None,
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


def fetch_image(config: dict, retries: int = MAX_CONSECUTIVE_FAILURES) -> bool:
    """Returns True if a picture was fetched and displayed, False if the
    framily has no visible pictures yet (204). Callers use this to poll again
    sooner than the normal fetch interval while there's nothing to show."""
    try:
        response = _post(config.get("server_url", ""), FRAME_FETCH_PATH, {
            "framily_code": config.get("framily_code", ""),
            "frame_token": config.get("frame_token", ""),
        })
    except FrameApiError as e:
        if retries > 0:
            logger.warning(f"Fetch failed ({retries} retries left): {e}")
            return fetch_image(config, retries - 1)
        else:
            logger.error(f"Fetch failed after {MAX_CONSECUTIVE_FAILURES} retries: {e}")
            raise FrameApiError(f"Error fetching picture: {e}", transient=e.transient, not_found=e.not_found) from e

    if response.status_code == 204:
        logger.info("No pictures available for this framily.")
        display_upload_first_image(config)
        clear_message()
        return False

    _write_epd_image(lambda p: p.write_bytes(response.content))
    logger.info("Picture fetched and saved successfully.")
    clear_message()
    return True


# --- Session / state machine ------------------------------------------------

def run_fetch_loop(config: dict) -> None:
    """Runs until a non-transient failure or MAX_CONSECUTIVE_FAILURES
    consecutive transient failures give up on the session."""
    while True:
        try:
            got_picture = fetch_image(config)
        except FrameApiError as e:
            save_message(_terminal_failure_message(f"Failed to fetch picture: {e}", e))
            return

        report_status(config)
        if got_picture:
            interval_minutes = fetch_settings(config)
            wait_for_recheck(interval_minutes * 60)
        else:
            wait_for_recheck(NO_PICTURE_RETRY_SECONDS)
        config = load_config()


def apply_wifi_update(config: dict) -> dict:
    """Push wifi_ssid/wifi_password to NetworkManager if the web UI flagged
    them as changed. Unlike the old pending_wifi_* fields, the credentials
    stay in the config after being applied - only the flag is cleared."""
    if not config.get("wifi_should_update"):
        return config

    ssid = config.get("wifi_ssid", "")
    password = config.get("wifi_password", "")
    config["wifi_should_update"] = False
    save_config(config)
    if not ssid:
        return config

    logger.info(f"Applying updated Wi-Fi credentials for SSID '{ssid}'.")
    set_wifi(ssid, password)
    return config


def apply_pending_delete(config: dict) -> dict:
    """Act on a Reset Framily request from the web UI. Retries on the next
    tick (via the caller's normal poll cadence) if the server can't be
    reached right now, e.g. while still in hotspot mode."""
    if not config.get("pending_delete"):
        return config

    try:
        return delete_framily(config)
    except FrameApiError as e:
        logger.warning(f"Failed to delete framily server-side, will retry: {e}")
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
                save_message(_terminal_failure_message(f"Framily does not exist or token is invalid: {e}", e))
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


def retry_saved_wifi() -> None:
    """Called periodically while parked in hotspot mode. If the Wi-Fi profile
    already has credentials saved from a previous setup, try bringing it up -
    the outage that pushed us into hotspot mode might have been transient
    (e.g. the router rebooting) and Wi-Fi could be back even though nobody
    submitted new credentials. Falls straight back to hotspot if it doesn't
    pan out, so the setup UI never goes dark."""
    ssid, _ = get_wifi()
    if not ssid:
        return
    logger.info(f"Hotspot mode: retrying saved Wi-Fi network '{ssid}'.")
    start_wifi()
    if determine_mode() != "wifi":
        logger.info("Retry failed, staying in hotspot mode.")
        start_hotspot()


def main_loop() -> None:
    last_mode = None
    next_wifi_retry = 0.0
    while True:
        try:
            config = load_config()
            mode = determine_mode()

            if mode != last_mode:
                logger.info(f"Network mode: {last_mode} -> {mode}")

            if mode == "hotspot":
                if last_mode != "hotspot":
                    display_hotspot()
                    next_wifi_retry = time.monotonic() + HOTSPOT_WIFI_RETRY_SECONDS
                last_mode = mode
                config = apply_wifi_update(config)
                config = apply_pending_delete(config)
                if time.monotonic() >= next_wifi_retry:
                    next_wifi_retry = time.monotonic() + HOTSPOT_WIFI_RETRY_SECONDS
                    retry_saved_wifi()
                wait_for_recheck(UNSTEADY_POLL_SECONDS)
                continue

            if mode == "wifi":
                last_mode = mode
                config = apply_wifi_update(config)
                config = apply_pending_delete(config)
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
