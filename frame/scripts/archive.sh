#!/bin/sh

set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname "$0")" && pwd)
FRAMILY_ARCHIVE_DIR="$SCRIPT_DIR/.."
FRAMILY_ARCHIVE_FILE="$FRAMILY_ARCHIVE_DIR/framily.tar.gz"

TMP_ARCHIVE_FILE=$(mktemp)
trap 'rm -f "$TMP_ARCHIVE_FILE"' EXIT

tar -czf "$TMP_ARCHIVE_FILE" \
    -C "$FRAMILY_ARCHIVE_DIR" \
    --exclude="framily.tar.gz" \
    --exclude=".git" \
    --exclude="__pycache__" \
    --exclude="*.pyc" \
    --exclude="tmp" \
    --exclude="config.json" \
    --exclude="framily.log*" \
    --exclude="agent.lock" \
    --exclude="agent.recheck" \
    .

mv "$TMP_ARCHIVE_FILE" "$FRAMILY_ARCHIVE_FILE"
