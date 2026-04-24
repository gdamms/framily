#!/bin/sh

set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname "$0")" && pwd)
# shellcheck source=./lib.sh
. "$SCRIPT_DIR/lib.sh"

require_root

install -m 0644 "$FRAMILY_EPD_SRC" "$FRAMILY_EPD_DEST"
install -m 0644 "$FRAMILY_WEB_SRC" "$FRAMILY_WEB_DEST"
install -m 0644 "$FRAMILY_DISPATCHER_SRC" "$FRAMILY_DISPATCHER_DEST"
install -m 0644 "$FRAMILY_CLI_SRC" "$FRAMILY_CLI_DEST"

chmod +x "$FRAMILY_DISPATCHER_DEST"
chmod +x "$FRAMILY_CLI_DEST"
