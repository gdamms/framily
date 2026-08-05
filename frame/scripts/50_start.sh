#!/bin/sh

set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname "$0")" && pwd)
# shellcheck source=./lib.sh
. "$SCRIPT_DIR/lib.sh"

require_root

systemctl daemon-reload
systemctl enable framily-epd.service
systemctl enable framily-web.service
systemctl enable framily-agent.service
systemctl restart framily-epd.service
systemctl restart framily-web.service
systemctl restart framily-agent.service
systemctl restart NetworkManager.service
