#!/bin/bash
set -euo pipefail

LIBJPEG_TURBO_TAG="3.2.0"
RUN_DIR=$(pwd)
OUTPUT_DIR="${RUN_DIR}/bin/macos"
TEMP_DIR=$(mktemp -d)
SCRIPT_DIR="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" && pwd )"

source "${SCRIPT_DIR}/_shared.sh"
trap 'cleanup "${TEMP_DIR}"' EXIT

check_env
check_commands \
    git \
    cmake \
    ninja \
    nasm \
    lipo

# Build
cd "${TEMP_DIR}"
git clone --depth 1 -b "${LIBJPEG_TURBO_TAG}" https://github.com/libjpeg-turbo/libjpeg-turbo.git "${TEMP_DIR}/libjpeg-turbo"

# Compile one arch at a time. Cannot do both with one cmake call due to assembly code.
for arch in x86_64 arm64; do
    build_dir="${TEMP_DIR}/build-${arch}"
    mkdir -p "${build_dir}"
    pushd "${build_dir}" > /dev/null

    cmake -G "Ninja" \
        -DCMAKE_BUILD_TYPE=Release \
        -DENABLE_STATIC=TRUE \
        -DCMAKE_OSX_ARCHITECTURES="${arch}" \
        -DCMAKE_OSX_DEPLOYMENT_TARGET=11.0 \
        "${TEMP_DIR}/libjpeg-turbo"

    ninja jpegtran-static
    popd > /dev/null
done

# Bundle
mkdir -p "${OUTPUT_DIR}"
lipo -create \
    "${TEMP_DIR}/build-x86_64/jpegtran-static" \
    "${TEMP_DIR}/build-arm64/jpegtran-static" \
    -output "${OUTPUT_DIR}/jpegtran"
chmod +x "${OUTPUT_DIR}/jpegtran"

echo "Binaries copied to: ${OUTPUT_DIR}"
