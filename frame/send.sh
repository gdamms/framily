#!/bin/sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname "$0")" && pwd)
TARGET=${1:-framily@10.42.54.236}
RUN_SETUP=${RUN_SETUP:-0}

echo "[framily-deploy] Syncing frame directory to ${TARGET}:/home/framily/"
scp -r "$SCRIPT_DIR"/* "$TARGET:/home/framily/"

if [ "$RUN_SETUP" = "1" ]; then
	echo "[framily-deploy] Running full setup on target"
	ssh "$TARGET" "sudo sh /home/framily/frame/setup/full_setup.sh"
fi
