#!/bin/sh

set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname "$0")" && pwd)
FRAMILY_ARCHIVE_DIR="$SCRIPT_DIR/.."
FRAMILY_ARCHIVE_FILE="$FRAMILY_ARCHIVE_DIR/framily.tar.gz"

tar -czf "$FRAMILY_ARCHIVE_FILE" \
    -C "$FRAMILY_ARCHIVE_DIR" \
    --exclude="framily.tar.gz" \
    --exclude=".git" \
    --exclude="__pycache__" \
    --exclude="*.pyc" \
    --exclude="tmp" \
    --exclude="config.json" \
    .
