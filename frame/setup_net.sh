#!/bin/sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname "$0")" && pwd)

echo "[framily-setup] setup_net.sh is now a compatibility wrapper to setup/40_network.sh"
exec sh "$SCRIPT_DIR/setup/40_network.sh"
