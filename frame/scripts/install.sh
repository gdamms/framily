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
    for svc in framily-epd.service framily-web.service framily-agent.service; do
        if systemctl is-active --quiet "$svc" 2>/dev/null; then
            log "Stopping $svc..."
            systemctl stop "$svc"
        fi
    done
}

merge_config_env() {
    # Overlay every KEY=VALUE line from the preserved old config.env ($1)
    # onto the freshly extracted template ($2): existing keys keep the old
    # (possibly user-customized) value, and any key that's new in the
    # template since $1 was written is left at its template default. A
    # naive whole-file preserve would silently drop newly introduced keys
    # on every upgrade, breaking scripts/services that expect them.
    old="$1"
    target="$2"
    [ -f "$old" ] || return 0

    while IFS= read -r line || [ -n "$line" ]; do
        case "$line" in
            ''|'#'*) continue ;;
        esac
        key="${line%%=*}"
        if grep -q "^${key}=" "$target" 2>/dev/null; then
            tmp=$(mktemp)
            grep -v "^${key}=" "$target" > "$tmp"
            printf '%s\n' "$line" >> "$tmp"
            mv "$tmp" "$target"
        else
            printf '%s\n' "$line" >> "$target"
        fi
    done < "$old"
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

if [ -f "$preserve_dir/config.env" ]; then
    log "Merging existing config.env (keeping customized values, adding any new keys)"
    merge_config_env "$preserve_dir/config.env" "$FRAMILY_OPT/config.env"
fi
if [ -f "$preserve_dir/config.json" ]; then
    log "Preserving existing config.json"
    cp -p "$preserve_dir/config.json" "$FRAMILY_OPT/config.json"
fi
rm -rf "$preserve_dir"

log "Running setup..."
sh "$FRAMILY_OPT/scripts/setup.sh"

if [ "$downloaded" -eq 1 ]; then
    rm -f "$ARCHIVE_PATH"
fi

log "Framily installation completed successfully!"
