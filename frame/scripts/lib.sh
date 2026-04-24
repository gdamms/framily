#!/bin/sh

set -eu

# Load environment variables from config.env
set -a  # Automatically export all variables
. "/opt/framily/config.env"
set +a  # Stop automatically exporting variables

log() {
    # Simple logging function to prefix messages with [framily]
    echo "[framily] $*"
}

require_root() {
    # Check if the script is being run as root
    if [ "$(id -u)" -ne 0 ]; then
        log "This script must be run as root."
        exit 1
    fi
}

command_exists() {
    # Check if a command exists
    command -v "$1" >/dev/null 2>&1
}
