#!/bin/bash
set -e

WIFI="mywifi"
HOTSPOT="myhotspot"
IFACE="wlan0"

echo "Checking for permissions..."
if [ "$(id -u)" -ne 0 ]; then
    echo "Please run as root (e.g. sudo $0)"
    exit 1
fi

echo "Removing existing connections..."
nmcli -t -f NAME,TYPE connection show | grep 802-11-wireless | cut -d: -f1 | while read -r CON; do
    echo "Deleting $CON..."
    nmcli connection delete "$CON"
done

echo "Creating Wi-Fi client connection..."
nmcli connection add type wifi ifname "$IFACE" con-name "$WIFI" ssid "CHANGE_ME_SSID"
nmcli connection modify "$WIFI" wifi-sec.key-mgmt wpa-psk
nmcli connection modify "$WIFI" wifi-sec.psk "CHANGE_ME_PASSWORD"
nmcli connection modify "$WIFI" connection.autoconnect yes
nmcli connection modify "$WIFI" connection.autoconnect-priority 20

echo "Creating hotspot fallback..."
nmcli connection add type wifi ifname "$IFACE" con-name "$HOTSPOT" ssid "PiHotspot"
nmcli connection modify "$HOTSPOT" 802-11-wireless.mode ap
nmcli connection modify "$HOTSPOT" 802-11-wireless.band bg
nmcli connection modify "$HOTSPOT" ipv4.method shared
nmcli connection modify "$HOTSPOT" wifi-sec.key-mgmt wpa-psk
nmcli connection modify "$HOTSPOT" wifi-sec.psk "raspberry"
nmcli connection modify "$HOTSPOT" connection.autoconnect yes
nmcli connection modify "$HOTSPOT" connection.autoconnect-priority 10

echo "Creating dnsmasq configuration..."
cp /home/framily/dnsmasq/framily.conf /etc/NetworkManager/dnsmasq-shared.d/framily.conf

echo "Creating dispatcher scripts..."
cp /home/framily/dispatcher/framily.py /etc/NetworkManager/dispatcher.d/framily.py
chmod +x /etc/NetworkManager/dispatcher.d/framily.py

echo "Reloading NetworkManager..."
systemctl restart NetworkManager

echo "DONE."
