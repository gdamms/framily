#!/usr/bin/env python3
import argparse
import time
from PIL import Image, ImageDraw, ImageFont
import json
import requests
from urlpath import URL
from dotenv import load_dotenv

load_dotenv("/opt/framily/config.env")

import sys
sys.path.append("/opt/framily")

from utils import HOTSPOT_DOMAIN, get_hotspot, EPD_INFO_PATH, EPD_IMAGE_PATH, make_qr, WEB_PORT, run, CON_HOTSPOT, CON_WIFI, load_config, save_config, save_message, start_hotspot


FRAMILY_CREATE_PATH = "/api/v1/framily/create"
FRAMILY_CHECK_PATH = "/api/v1/framily/check"
PICTURE_FETCH_PATH = "/api/v1/pictures/fetch"


def display_hotspot():
    ssid, password = get_hotspot()

    epd_info = json.loads(EPD_INFO_PATH.read_text())
    width, height = epd_info["width"], epd_info["height"]

    if WEB_PORT == 80:
        server_url = f"http://{HOTSPOT_DOMAIN}/"
    elif WEB_PORT == 443:
        server_url = f"https://{HOTSPOT_DOMAIN}/"
    else:
        server_url = f"http://{HOTSPOT_DOMAIN}:{WEB_PORT}/"
    wifi_qr_data = f"WIFI:T:WPA;S:{ssid};P:{password};;"

    wifi_qr = make_qr(wifi_qr_data)
    url_qr = make_qr(server_url)

    img = Image.new("RGB", (height, width), "white")
    draw = ImageDraw.Draw(img)
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

    img.save(EPD_IMAGE_PATH)  # Send image to the e-ink display


def hotspot_up():
    display_hotspot()


def display_connecting_wifi():
    epd_info = json.loads(EPD_INFO_PATH.read_text())
    width, height = epd_info["width"], epd_info["height"]

    img = Image.new("RGB", (height, width), "white")
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype("DejaVuSans.ttf", 30)
    margin = 50

    draw.text((margin, 50), "Connecting to Wi-Fi...", font=font, fill="black")

    img.save(EPD_IMAGE_PATH)  # Send image to the e-ink display


def display_framily_info():
    config = load_config()
    framily_code = config.get("framily_code", "")

    epd_info = json.loads(EPD_INFO_PATH.read_text())
    width, height = epd_info["width"], epd_info["height"]

    img = Image.new("RGB", (height, width), "white")
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype("DejaVuSans.ttf", 30)
    margin = 50

    draw.text((margin, 50), "Framily Code:", font=font, fill="black")
    draw.text((margin, 100), framily_code, font=font, fill="black")

    img.save(EPD_IMAGE_PATH)  # Send image to the e-ink display


def display_upload_first_image():
    config = load_config()
    framily_code = config.get("framily_code", "")
    epd_info = json.loads(EPD_INFO_PATH.read_text())
    width, height = epd_info["width"], epd_info["height"]

    img = Image.new("RGB", (height, width), "white")
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype("DejaVuSans.ttf", 30)
    margin = 50

    draw.text((margin, 50), f"Framily {framily_code}:\nWaiting for first image...", font=font, fill="black")

    img.save(EPD_IMAGE_PATH)  # Send image to the e-ink display


def create_framily():
    config = load_config()
    server_url = config.get("server_url", "")
    server_url = URL(server_url)

    create_url = server_url / FRAMILY_CREATE_PATH

    try:
        response = create_url.post(json={'name': 'My Framily'})
        if not response.ok:
            print(f"Failed to create framily: {response.text}")
            save_message(f"Failed to create framily. Please check the server URL and try again. (Status: {response.status_code} - {response.text})")
            start_hotspot()
            exit()
    except requests.exceptions.ConnectionError as e:
        print(f"Error connecting to the server: {e}")
        save_message(f"Error connecting to the server: {e}. Please check the server URL and try again.")
        start_hotspot()
        exit()

    response_json = response.json()
    framily_code = response_json.get("framily_code")
    frame_token = response_json.get("frame_token")
    if not framily_code or not frame_token:
        print("Invalid response from server. Missing framily_code or frame_token.")
        save_message("Invalid response from server. Please check the server URL and try again.")
        start_hotspot()
        exit()

    config["framily_code"] = framily_code
    config["frame_token"] = frame_token
    save_config(config)
    print("Framily created successfully.")


def check_framily():
    config = load_config()
    server_url = config.get("server_url", "")
    framily_code = config.get("framily_code", "")
    framily_token = config.get("frame_token", "")

    server_url = URL(server_url)
    check_url = server_url / FRAMILY_CHECK_PATH

    try:
        response = check_url.post(json={
            "framily_code": framily_code,
            "frame_token": framily_token
        })
        if not response.ok:
            print(f"Framily does not exist or token is invalid: {response.text}")
            save_message("Framily does not exist or token is invalid. Please check the server URL and try again.")
            start_hotspot()
            exit()
    except requests.exceptions.ConnectionError as e:
        print(f"Error connecting to the server: {e}")
        save_message(f"Error connecting to the server: {e}. Please check the server URL and try again.")
        start_hotspot()
        exit()

    response_json = response.json()
    return response_json.get("initiated", False)


def fetch_image():
    config = load_config()
    server_url = config.get("server_url", "")
    framily_code = config.get("framily_code", "")
    framily_token = config.get("frame_token", "")

    server_url = URL(server_url)
    fetch_url = server_url / PICTURE_FETCH_PATH

    try:
        response = fetch_url.post(json={
            "framily_code": framily_code,
            "frame_token": framily_token
        }, timeout=10)

        if response.ok:
            if response.status_code == 204:
                print("No pictures available for this framily.")
                display_upload_first_image()
            elif response.status_code == 200:
                with open(EPD_IMAGE_PATH, "wb") as f:
                    f.write(response.content)
                print("Picture fetched and saved successfully.")
        else:
            print(f"Failed to fetch picture: {response.text}")
            save_message(f"Failed to fetch picture. Please check the server URL and try again. (Status: {response.status_code} - {response.text})")
            start_hotspot()
            exit()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching picture: {e}")
        save_message(f"Error fetching picture: {e}. Please check the server URL and try again.")
        start_hotspot()
        exit()


def start_framily():
    config = load_config()

    framily_code = config.get("framily_code", "")
    frame_token = config.get("frame_token", "")

    if not framily_code or not frame_token:
        create_framily()
        display_framily_info()

    while not check_framily():
        display_framily_info()
        time.sleep(5)

    while True:
        fetch_image()
        time.sleep(60)


def wifi_up():
    display_connecting_wifi()

    config = load_config()

    server_url = config.get("server_url", "")
    if not server_url:
        save_message("Server URL not configured, please set it up.")
        start_hotspot()
        return

    start_framily()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Framily Dispatcher")
    parser.add_argument("interface", type=str, help="Network interface to monitor (e.g., wlan0)")
    parser.add_argument("action", type=str, help="Connection action (e.g., up, down)")
    args = parser.parse_args()

    with open("/tmp/dispatcher.log", "a") as f:
        f.write(f"Interface: {args.interface}, Action: {args.action}\n")

    if args.action != "up" or args.interface != "wlan0":
        exit(0)

    connection = run("nmcli -t -f NAME connection show --active | head -n1")

    if connection == CON_HOTSPOT:
        hotspot_up()
    elif connection == CON_WIFI:
        wifi_up()
