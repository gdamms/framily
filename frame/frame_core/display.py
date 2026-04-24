from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

import qrcode
from PIL import Image, ImageDraw, ImageFont

from frame_core.settings import EPD_IMAGE_PATH, EPD_INFO_PATH


def make_qr(data: str, size: int = 150) -> Image.Image:
    qr = qrcode.make(data, border=0)
    return qr.resize((size, size))


def _safe_font(size: int = 30) -> ImageFont.ImageFont:
    try:
        return ImageFont.truetype("DejaVuSans.ttf", size)
    except OSError:
        return ImageFont.load_default()


def _canvas_size() -> tuple[int, int]:
    if not EPD_INFO_PATH.exists():
        return 480, 800

    try:
        epd_info = json.loads(EPD_INFO_PATH.read_text(encoding="utf-8"))
        width = int(epd_info.get("width", 800))
        height = int(epd_info.get("height", 480))
    except (ValueError, OSError, json.JSONDecodeError):
        return 480, 800

    return height, width


def _save_atomically(img: Image.Image, path: Path = EPD_IMAGE_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.NamedTemporaryFile(dir=path.parent, suffix=".png", delete=False) as temp_file:
        temp_path = Path(temp_file.name)

    try:
        img.save(temp_path)
        os.replace(temp_path, path)
    finally:
        if temp_path.exists():
            temp_path.unlink(missing_ok=True)


def save_image_bytes(data: bytes, path: Path = EPD_IMAGE_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.NamedTemporaryFile(dir=path.parent, suffix=".img", delete=False) as temp_file:
        temp_file.write(data)
        temp_path = Path(temp_file.name)

    os.replace(temp_path, path)


def _new_canvas() -> Image.Image:
    width, height = _canvas_size()
    return Image.new("RGB", (width, height), "white")


def render_connecting_wifi() -> None:
    img = _new_canvas()
    draw = ImageDraw.Draw(img)
    font = _safe_font(30)

    draw.text((50, 50), "Connecting to Wi-Fi...", font=font, fill="black")
    _save_atomically(img)


def render_framily_info(framily_code: str) -> None:
    img = _new_canvas()
    draw = ImageDraw.Draw(img)
    font = _safe_font(30)

    draw.text((50, 50), "Framily Code:", font=font, fill="black")
    draw.text((50, 100), framily_code or "(pending)", font=font, fill="black")
    _save_atomically(img)


def render_waiting_first_image(framily_code: str) -> None:
    img = _new_canvas()
    draw = ImageDraw.Draw(img)
    font = _safe_font(30)

    draw.text(
        (50, 50),
        f"Framily {framily_code or '(pending)'}:\nWaiting for first image...",
        font=font,
        fill="black",
    )
    _save_atomically(img)


def render_hotspot(ssid: str, password: str, setup_url: str) -> None:
    img = _new_canvas()
    draw = ImageDraw.Draw(img)
    font = _safe_font(30)

    wifi_qr = make_qr(f"WIFI:T:WPA;S:{ssid};P:{password};;")
    url_qr = make_qr(setup_url)

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
    draw.text((margin, 100 + wifi_qr.height + 90), setup_url, font=font, fill="black")
    img.paste(url_qr, (margin, 100 + wifi_qr.height + 140))

    _save_atomically(img)
