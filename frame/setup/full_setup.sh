#!/bin/sh

set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname "$0")" && pwd)

run_step() {
  step_script="$1"
  echo "[framily-setup] Running ${step_script}"
  sh "$SCRIPT_DIR/${step_script}"
}

run_step "10_preflight.sh"
run_step "20_dependencies.sh"
run_step "30_deploy_files.sh"
run_step "40_network.sh"
run_step "50_services.sh"
run_step "60_verify.sh"

echo "[framily-setup] Full setup completed successfully"
