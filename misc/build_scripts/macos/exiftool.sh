#!/bin/bash
set -euo pipefail

EXIFTOOL_TAG="13.39"

RUN_DIR=$(pwd)
OUTPUT_DIR="${RUN_DIR}/bin/macos"
TEMP_DIR=$(mktemp -d)
SCRIPT_DIR="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" && pwd )"

source "${SCRIPT_DIR}/_shared.sh"
trap 'cleanup "${TEMP_DIR}"' EXIT

check_env
check_commands curl git

pull_prebuilt() {
    local arch="$1"
    local output="$2"
    local url="https://github.com/JacobDev1/exiftool-macos-build/releases/download/${EXIFTOOL_TAG}/exiftool-macos-${arch}.tar.xz"
    local tmp="$(mktemp -t exiftool.XXXXXX)"
    
    curl -fsSL "${url}" -o "${tmp}"
    tar -xJf "${tmp}" -O > "${output}"
    rm -f "${tmp}"
}

x86_64_slice="${TEMP_DIR}/exiftool.x86_64"
arm64_slice="${TEMP_DIR}/exiftool.arm64"
exiftool_bin="${TEMP_DIR}/exiftool_build_export"

pull_prebuilt arm64 "${arm64_slice}"
pull_prebuilt x86_64 "${x86_64_slice}"
lipo -create "${x86_64_slice}" "${arm64_slice}" -output "${exiftool_bin}"

# Building for arm64 host on x86_64 requires patching XS modules and the loader.
# This is very difficult and unmaintainable.
# Building for x86_64 host on arm64 with Rosetta2 resulted in warnings during XS compilation.
# Builds are done in the CI due to issues with cross-crosscompiling.

mkdir -p "${OUTPUT_DIR}"
mv "${exiftool_bin}" "${OUTPUT_DIR}/exiftool"
chmod +x "${OUTPUT_DIR}/exiftool"
echo "The build artifact copied to: ${OUTPUT_DIR}"
