#!/bin/bash

LIBAVIF_TAG="v1.4.2"
AOM_AV1_TAG="v3.14.1"
SVT_AV1_PSY_TAG="v3.0.2"

RUN_DIR=$(pwd)
OUTPUT_DIR="${RUN_DIR}/bin/win/libavif"
TEMP_DIR=$(mktemp -d)
SCRIPT_DIR="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" && pwd )"

source "${SCRIPT_DIR}/_shared.sh"

trap 'cleanup "${TEMP_DIR}"' EXIT
set -euo pipefail
check_msys2
check_packages \
    git \
    base-devel \
    mingw-w64-x86_64-toolchain \
    mingw-w64-x86_64-ninja \
    mingw-w64-x86_64-libjpeg-turbo \
    nasm \
    cmake \
    make

# Prepare repo
cd "${TEMP_DIR}"
git clone --depth 1 -b "${LIBAVIF_TAG}" https://aomedia.googlesource.com/libavif

# Update deps.
cd libavif/ext/
sed -i -E "s/v[0-9]+\.[0-9]+\.[0-9]+/${AOM_AV1_TAG}/" aom.cmd
sed -i -E "s#https://gitlab.com/AOMediaCodec/SVT-AV1\.git#https://github.com/psy-ex/svt-av1-psy.git SVT-AV1#" svt.sh
sed -i -E "s/v[0-9]+\.[0-9]+\.[0-9]+/${SVT_AV1_PSY_TAG}/" svt.sh

# Build deps.
sed -i "/cmake.*\.\./ s/\.\./-DCMAKE_POLICY_VERSION_MINIMUM=3.5 &/" libyuv.cmd      # Fix libyuv.cmd
./libyuv.cmd
./libsharpyuv.cmd
./libjpeg.cmd
./zlibpng.cmd
./svt.sh
./aom.cmd

# Build libavif
cd "${TEMP_DIR}/libavif"
mkdir build && cd build/
cmake \
    -DCMAKE_BUILD_TYPE=Release \
    -DBUILD_SHARED_LIBS=0 \
    -DAVIF_BUILD_APPS=1 \
    -DAVIF_LIBYUV=LOCAL \
    -DAVIF_LIBSHARPYUV=LOCAL \
    -DAVIF_JPEG=LOCAL \
    -DAVIF_ZLIBPNG=LOCAL \
    -DAVIF_CODEC_SVT=LOCAL \
    -DAVIF_CODEC_AOM=LOCAL \
    -DCMAKE_POLICY_VERSION_MINIMUM=3.5 \
    ..
cmake --build . --parallel

mkdir -p "${OUTPUT_DIR}"
cp avifenc.exe avifdec.exe "${OUTPUT_DIR}"
bundle_dlls "${OUTPUT_DIR}"
echo "Binaries copied to: ${OUTPUT_DIR}"
