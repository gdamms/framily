#!/bin/sh

set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname "$0")" && pwd)
# shellcheck source=./lib.sh
. "$SCRIPT_DIR/lib.sh"

require_root

run_step() {
    step_script="$1"
    log "Running ${step_script}"
    sh "$SCRIPT_DIR/${step_script}"
    if [ $? -ne 0 ]; then
        log "Step ${step_script} failed. Aborting installation."
        exit 1
    fi
}

# Run the setup steps in order
run_step "10_preflight.sh"
run_step "20_dependencies.sh"
run_step "30_deploy_files.sh"
run_step "40_network.sh"
run_step "50_start.sh"
