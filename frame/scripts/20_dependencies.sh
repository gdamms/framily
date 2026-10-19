#!/bin/sh

set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname "$0")" && pwd)
# shellcheck source=./lib.sh
. "$SCRIPT_DIR/lib.sh"

require_root

log "Installing required system packages"
apt-get update
apt-get install -y \
    python3-pip \
    python3-pil \
    python3-flask \
    python3-requests \
    python3-dotenv \
    python3-watchdog \
    fonts-dejavu \
    network-manager \
    bluez \
    dbus

log "Installing required Python packages"
pip3 install --break-system-packages --upgrade urlpath

# bless's BlueZ backend only ever calls into dbus_next (pure Python, has a
# piwheels wheel) at runtime; it just imports a couple of type/constant
# definitions from bleak, never bleak's own BLE client/scanner code. But
# bleak's own metadata unconditionally requires dbus-fast on Linux, and
# piwheels only builds dbus-fast wheels for armv7l/aarch64 - never armv6l
# (Pi Zero/Pi 1), so a normal `pip install bless` forces a from-source
# Cython compile of dbus-fast that can take the better part of an hour on
# that hardware. Installing bleak and bless with --no-deps and providing
# their actual runtime dependencies directly skips that entirely.
pip3 install --break-system-packages dbus_next typing_extensions
pip3 install --break-system-packages --no-deps bleak bless

# Allow SPI connection
raspi-config nonint do_spi 0
