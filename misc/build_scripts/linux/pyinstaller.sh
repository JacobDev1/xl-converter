#!/usr/bin/env bash

set -euo pipefail

PYINSTALLER_TAG=v6.11.1
RUN_DIR=$(pwd)
TEMP_DIR=$(mktemp -d)
TARGET_ENV="${TARGET_ENV:-$RUN_DIR/env_build}"
PYINSTALLER_DIR="$TEMP_DIR/pyinstaller"

trap 'rm -rf "${TEMP_DIR}"' EXIT

if [[ ! -x "$TARGET_ENV/bin/python" ]]; then
    echo "Python virtual environment not found at: $TARGET_ENV" >&2
    echo "Create one with: \"python -m venv env_build\" or set the TARGET_ENV variable." >&2
    exit 1
fi
git clone -b "$PYINSTALLER_TAG" --depth 1 https://github.com/pyinstaller/pyinstaller.git "$PYINSTALLER_DIR"
cd "$PYINSTALLER_DIR/bootloader"
"$TARGET_ENV/bin/python" waf all --gcc
cd "$PYINSTALLER_DIR"
"$TARGET_ENV/bin/python" -m pip install .
cd "$RUN_DIR"
