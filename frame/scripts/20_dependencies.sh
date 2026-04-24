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
    python3-qrcode \
    python3-flask \
    python3-requests \
    python3-dotenv \
    python3-watchdog \
    fonts-dejavu \
    network-manager

log "Installing required Python packages"
pip3 install --break-system-packages --upgrade urlpath

# Allow SPI connection
raspi-config nonint do_spi 0
