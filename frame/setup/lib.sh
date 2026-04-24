#!/bin/sh

set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname "$0")" && pwd)
FRAME_DIR=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)

SERVICE_USER=${SERVICE_USER:-framily}
SERVICE_HOME=${SERVICE_HOME:-/home/${SERVICE_USER}}
WLAN_IF=${WLAN_IF:-wlan0}

WIFI_CON=${WIFI_CON:-mywifi}
HOTSPOT_CON=${HOTSPOT_CON:-myhotspot}
HOTSPOT_SSID=${HOTSPOT_SSID:-PiHotspot}
HOTSPOT_PASSWORD=${HOTSPOT_PASSWORD:-raspberry}
WIFI_PLACEHOLDER_SSID=${WIFI_PLACEHOLDER_SSID:-CHANGE_ME_SSID}
WIFI_PLACEHOLDER_PASSWORD=${WIFI_PLACEHOLDER_PASSWORD:-CHANGE_ME_PASSWORD}

log() {
  echo "[framily-setup] $*"
}

require_root() {
  if [ "$(id -u)" -ne 0 ]; then
    log "Please run as root (sudo)."
    exit 1
  fi
}

command_exists() {
  command -v "$1" >/dev/null 2>&1
}

ensure_service_user() {
  if ! id "$SERVICE_USER" >/dev/null 2>&1; then
    log "Creating user $SERVICE_USER"
    useradd -m -s /bin/bash "$SERVICE_USER"
  fi
}

ensure_path_layout() {
  mkdir -p "$SERVICE_HOME" "$SERVICE_HOME/epd" "$SERVICE_HOME/framily_flask" "$SERVICE_HOME/dispatcher" "$SERVICE_HOME/dnsmasq"
  chown -R "$SERVICE_USER:$SERVICE_USER" "$SERVICE_HOME"
}

sync_frame_files() {
  log "Syncing frame files to $SERVICE_HOME"
  rsync -a --delete \
    --exclude '__pycache__/' \
    "$FRAME_DIR/" "$SERVICE_HOME/"
  chown -R "$SERVICE_USER:$SERVICE_USER" "$SERVICE_HOME"
}

install_dependencies() {
  log "Installing required system packages"
  apt-get update
  apt-get install -y \
    python3-pil \
    python3-qrcode \
    python3-flask \
    python3-inotify \
    python3-requests \
    fonts-dejavu \
    python3-pip \
    network-manager \
    dnsmasq \
    rsync

  log "Installing required Python packages"
  pip3 install --break-system-packages --upgrade urlpath
}

initialize_config_files() {
  CONFIG_PATH="$SERVICE_HOME/config.json"
  EPD_INFO_PATH="$SERVICE_HOME/epd/epd_info.json"

  if [ ! -f "$CONFIG_PATH" ]; then
    log "Initializing config.json"
    cat > "$CONFIG_PATH" <<'EOF'
{
  "server_url": "",
  "framily_code": "",
  "frame_token": "",
  "message": "",
  "state": "unconfigured",
  "last_error": "",
  "last_error_at": 0,
  "last_success_at": 0,
  "consecutive_failures": 0,
  "failure_since": 0,
  "hotspot_ssid": "",
  "hotspot_password": ""
}
EOF
    chown "$SERVICE_USER:$SERVICE_USER" "$CONFIG_PATH"
    chmod 600 "$CONFIG_PATH"
  fi

  if [ ! -f "$EPD_INFO_PATH" ]; then
    log "Initializing epd_info.json"
    cat > "$EPD_INFO_PATH" <<'EOF'
{
  "width": 800,
  "height": 480
}
EOF
    chown "$SERVICE_USER:$SERVICE_USER" "$EPD_INFO_PATH"
  fi
}

nmcli_connection_exists() {
  nmcli -t -f NAME connection show | grep -Fx "$1" >/dev/null 2>&1
}

configure_network_profiles() {
  log "Configuring NetworkManager profiles"

  if ! nmcli_connection_exists "$WIFI_CON"; then
    nmcli connection add type wifi ifname "$WLAN_IF" con-name "$WIFI_CON" ssid "$WIFI_PLACEHOLDER_SSID"
  fi
  nmcli connection modify "$WIFI_CON" wifi-sec.key-mgmt wpa-psk
  nmcli connection modify "$WIFI_CON" wifi-sec.psk "$WIFI_PLACEHOLDER_PASSWORD"
  nmcli connection modify "$WIFI_CON" connection.autoconnect yes
  nmcli connection modify "$WIFI_CON" connection.autoconnect-priority 20

  if ! nmcli_connection_exists "$HOTSPOT_CON"; then
    nmcli connection add type wifi ifname "$WLAN_IF" con-name "$HOTSPOT_CON" ssid "$HOTSPOT_SSID"
  fi
  nmcli connection modify "$HOTSPOT_CON" 802-11-wireless.mode ap
  nmcli connection modify "$HOTSPOT_CON" 802-11-wireless.band bg
  nmcli connection modify "$HOTSPOT_CON" ipv4.method shared
  nmcli connection modify "$HOTSPOT_CON" wifi-sec.key-mgmt wpa-psk
  nmcli connection modify "$HOTSPOT_CON" wifi-sec.psk "$HOTSPOT_PASSWORD"
  nmcli connection modify "$HOTSPOT_CON" connection.autoconnect yes
  nmcli connection modify "$HOTSPOT_CON" connection.autoconnect-priority 10
}

install_dns_and_dispatcher() {
  log "Installing dnsmasq mapping and NetworkManager dispatcher"

  mkdir -p /etc/NetworkManager/dnsmasq-shared.d
  install -m 0644 "$SERVICE_HOME/dnsmasq/framily.conf" /etc/NetworkManager/dnsmasq-shared.d/framily.conf

  mkdir -p /etc/NetworkManager/dispatcher.d
  install -m 0755 "$SERVICE_HOME/dispatcher/framily.py" /etc/NetworkManager/dispatcher.d/framily.py
}

install_service_unit() {
  SERVICE_NAME="$1"

  case "$SERVICE_NAME" in
    epd.service)
      install -m 0644 "$SERVICE_HOME/epd/epd.service" "/etc/systemd/system/${SERVICE_NAME}"
      ;;
    flask.service)
      install -m 0644 "$SERVICE_HOME/framily_flask/flask.service" "/etc/systemd/system/${SERVICE_NAME}"
      ;;
    *)
      log "Unsupported service: $SERVICE_NAME"
      return 1
      ;;
  esac
}

install_systemd_units() {
  log "Installing systemd services"
  install_service_unit epd.service
  install_service_unit flask.service

  systemctl daemon-reload
  systemctl enable epd.service flask.service
}

restart_core_services() {
  log "Restarting core services"
  systemctl restart NetworkManager
  systemctl restart dnsmasq || true
  systemctl restart epd.service
  systemctl restart flask.service
}

restart_single_service() {
  SERVICE_NAME="$1"
  log "Restarting service ${SERVICE_NAME}"
  systemctl daemon-reload
  systemctl enable "$SERVICE_NAME"
  systemctl restart "$SERVICE_NAME"
}

run_validation() {
  log "Running post-setup validation"

  systemctl is-active NetworkManager >/dev/null
  systemctl is-active epd.service >/dev/null
  systemctl is-active flask.service >/dev/null

  if ! nmcli_connection_exists "$WIFI_CON"; then
    log "Missing wifi connection profile $WIFI_CON"
    exit 1
  fi

  if ! nmcli_connection_exists "$HOTSPOT_CON"; then
    log "Missing hotspot connection profile $HOTSPOT_CON"
    exit 1
  fi

  if [ ! -x /etc/NetworkManager/dispatcher.d/framily.py ]; then
    log "Dispatcher script not installed"
    exit 1
  fi

  log "Validation passed"
}
