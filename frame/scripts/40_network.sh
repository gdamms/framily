#!/bin/sh

set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname "$0")" && pwd)
# shellcheck source=./lib.sh
. "$SCRIPT_DIR/lib.sh"

require_root

connection_exists() {
    nmcli -t -f NAME connection show | grep -Fxq "$1"
}

if connection_exists "$FRAMILY_WIFI"; then
    log "Wi-Fi connection '$FRAMILY_WIFI' already exists, leaving it untouched."
else
    log "Creating Wi-Fi client connection..."
    nmcli connection add type wifi ifname "$FRAMILY_IFACE" con-name "$FRAMILY_WIFI" ssid "$FRAMILY_WIFI_SSID"
    nmcli connection modify "$FRAMILY_WIFI" wifi-sec.key-mgmt wpa-psk
    nmcli connection modify "$FRAMILY_WIFI" wifi-sec.psk "$FRAMILY_WIFI_PASSWORD"
    nmcli connection modify "$FRAMILY_WIFI" connection.autoconnect yes
    nmcli connection modify "$FRAMILY_WIFI" connection.autoconnect-priority 20
fi

if connection_exists "$FRAMILY_HOTSPOT"; then
    log "Hotspot connection '$FRAMILY_HOTSPOT' already exists, leaving it untouched."
else
    log "Creating hotspot fallback..."
    nmcli connection add type wifi ifname "$FRAMILY_IFACE" con-name "$FRAMILY_HOTSPOT" ssid "$FRAMILY_HOTSPOT_SSID"
    nmcli connection modify "$FRAMILY_HOTSPOT" 802-11-wireless.mode ap
    nmcli connection modify "$FRAMILY_HOTSPOT" 802-11-wireless.band bg
    nmcli connection modify "$FRAMILY_HOTSPOT" ipv4.method shared
    nmcli connection modify "$FRAMILY_HOTSPOT" wifi-sec.key-mgmt wpa-psk
    nmcli connection modify "$FRAMILY_HOTSPOT" wifi-sec.psk "$FRAMILY_HOTSPOT_PASSWORD"
    nmcli connection modify "$FRAMILY_HOTSPOT" connection.autoconnect yes
    nmcli connection modify "$FRAMILY_HOTSPOT" connection.autoconnect-priority 10
fi
