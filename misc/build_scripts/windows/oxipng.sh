#!/usr/bin/env bash
set -euo pipefail

OXIPNG_TAG="v9.1.5"

RUN_DIR=$(pwd)
OUTPUT_DIR="${RUN_DIR}/bin/win/oxipng"
TEMP_DIR=$(mktemp -d)
SCRIPT_DIR="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" && pwd )"

source "${SCRIPT_DIR}/_shared.sh"
trap 'cleanup "${TEMP_DIR}"' EXIT

check_msys2
check_packages \
    git \
    base-devel \
    mingw-w64-x86_64-rust

# Build
cd "${TEMP_DIR}"
git clone --depth 1 -b "${OXIPNG_TAG}" https://github.com/shssoichiro/oxipng.git oxipng
cd oxipng/
cargo build --release --target x86_64-pc-windows-gnu

mkdir -p "${OUTPUT_DIR}"
cp target/x86_64-pc-windows-gnu/release/oxipng.exe "${OUTPUT_DIR}"
cd "${OUTPUT_DIR}"

echo "Binaries copied to: ${OUTPUT_DIR}"
