#!/bin/sh

set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname "$0")" && pwd)
# shellcheck source=./lib.sh
. "$SCRIPT_DIR/lib.sh"

require_root

systemctl daemon-reload
systemctl enable framily-epd.service
systemctl enable framily-web.service
systemctl start framily-epd.service
systemctl start framily-web.service
systemctl restart NetworkManager.service
