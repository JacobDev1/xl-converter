#!/bin/bash
set -euo pipefail

OXIPNG_TAG="v10.2.0"

RUN_DIR=$(pwd)
OUTPUT_DIR="${RUN_DIR}/bin/macos"
TEMP_DIR=$(mktemp -d)
SCRIPT_DIR="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" && pwd )"

source "${SCRIPT_DIR}/_shared.sh"
trap 'cleanup "${TEMP_DIR}"' EXIT

check_env
check_commands \
    git \
    rustup \
    cargo \
    lipo
rustup target add x86_64-apple-darwin aarch64-apple-darwin

# Build
git clone --depth 1 -b "${OXIPNG_TAG}" https://github.com/shssoichiro/oxipng.git "${TEMP_DIR}/oxipng"
cd "${TEMP_DIR}/oxipng"
export MACOSX_DEPLOYMENT_TARGET=11.0
cargo build --release --target x86_64-apple-darwin
cargo build --release --target aarch64-apple-darwin

# Merge into a universal binary
mkdir -p "${OUTPUT_DIR}"
lipo -create \
    target/x86_64-apple-darwin/release/oxipng \
    target/aarch64-apple-darwin/release/oxipng \
    -output "${OUTPUT_DIR}/oxipng"
chmod +x "${OUTPUT_DIR}/oxipng"

echo "Binary copied to: ${OUTPUT_DIR}"
