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

if [[ -x "/opt/local/bin/clang-mp-17" ]]; then
    export CC="/opt/local/bin/clang-mp-17"
fi
unset ARCHFLAGS CFLAGS LDFLAGS
export MACOSX_DEPLOYMENT_TARGET=11.0

git clone -b "$PYINSTALLER_TAG" --depth 1 https://github.com/pyinstaller/pyinstaller.git "$PYINSTALLER_DIR"
cd "$PYINSTALLER_DIR/bootloader"
"$TARGET_ENV/bin/python" waf all --universal2 --clang
cd "$PYINSTALLER_DIR"
"$TARGET_ENV/bin/python" -m pip install .
cd "$RUN_DIR"
