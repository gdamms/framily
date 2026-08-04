#!/bin/sh
# Framily frame installer. Meant to be piped to sh, or run locally from a
# folder that already has framily.tar.gz sitting next to it.
#
# Production install (fetches the latest tarball from main):
#   curl -sL https://raw.githubusercontent.com/gdamms/framily/main/frame/scripts/install.sh | sh
#
# Local/dev install: copy this file and framily.tar.gz into the same folder
# on the frame and run `sh install.sh` there. The local tarball is used as-is
# and nothing is downloaded, so you can iterate without cutting a release.

set -eu

FRAMILY_OPT="/opt/framily"
ARCHIVE_URL="https://raw.githubusercontent.com/gdamms/framily/main/frame/framily.tar.gz"
ARCHIVE_PATH="$(pwd)/framily.tar.gz"

log() {
    echo "[framily] $*"
}

require_root() {
    if [ "$(id -u)" -ne 0 ]; then
        log "This script must be run as root. Please run with sudo or as root user."
        exit 1
    fi
}

command_exists() {
    command -v "$1" >/dev/null 2>&1
}

stop_services() {
    for svc in framily-epd.service framily-web.service; do
        if systemctl is-active --quiet "$svc" 2>/dev/null; then
            log "Stopping $svc..."
            systemctl stop "$svc"
        fi
    done
}

require_root

if ! command_exists tar; then
    log "tar is not installed. Please install tar and try again."
    exit 1
fi

downloaded=0
if [ -f "$ARCHIVE_PATH" ]; then
    log "Found $ARCHIVE_PATH, using it instead of downloading."
else
    if ! command_exists curl; then
        log "curl is not installed. Please install curl and try again."
        exit 1
    fi
    log "Downloading Framily archive..."
    curl -sL -o "$ARCHIVE_PATH" "$ARCHIVE_URL"
    downloaded=1
fi

stop_services

log "Installing to $FRAMILY_OPT..."
preserve_dir=$(mktemp -d)
for f in config.env config.json; do
    if [ -f "$FRAMILY_OPT/$f" ]; then
        cp -p "$FRAMILY_OPT/$f" "$preserve_dir/$f"
    fi
done

mkdir -p "$FRAMILY_OPT"
tar -xzf "$ARCHIVE_PATH" -C "$FRAMILY_OPT"

for f in config.env config.json; do
    if [ -f "$preserve_dir/$f" ]; then
        log "Preserving existing $f"
        cp -p "$preserve_dir/$f" "$FRAMILY_OPT/$f"
    fi
done
rm -rf "$preserve_dir"

log "Running setup..."
sh "$FRAMILY_OPT/scripts/setup.sh"

if [ "$downloaded" -eq 1 ]; then
    rm -f "$ARCHIVE_PATH"
fi

log "Framily installation completed successfully!"
