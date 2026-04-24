#!/bin/sh

set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname "$0")" && pwd)
# shellcheck source=./lib.sh
. "$SCRIPT_DIR/lib.sh"

require_root

if ! command_exists systemctl; then
  log "systemctl not found. This setup requires systemd."
  exit 1
fi
