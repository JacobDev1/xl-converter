#!/bin/bash
set -euo pipefail

LIBJXL_TAG="v0.12.0"
JPEGLI_COMMIT="031a0077f5799a6041004267fc12b956c1f52a20"  # Full commit hash
RUN_DIR=$(pwd)
OUTPUT_DIR="${RUN_DIR}/bin/macos"
TEMP_DIR=$(mktemp -d)
SCRIPT_DIR="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" && pwd )"

source "${SCRIPT_DIR}/_shared.sh"
trap 'cleanup "${TEMP_DIR}"' EXIT

check_env
check_commands \
    git
check_packages \
    llvm \
    coreutils \
    cmake \
    giflib \
    libjpeg-turbo \
    libpng \
    ninja \
    zlib \
    brotli

# Build libjxl
git clone --depth 1 -b "${LIBJXL_TAG}" https://github.com/libjxl/libjxl.git "${TEMP_DIR}/libjxl"
cd "${TEMP_DIR}/libjxl"
./deps.sh
for arch in x86_64 arm64; do
    build_dir="${TEMP_DIR}/libjxl/build-${arch}"
    mkdir -p "${build_dir}"
    cd "${build_dir}"

    export PKG_CONFIG_PATH="/opt/local/lib/pkgconfig"
    export LDFLAGS="-L/opt/local/lib"
    export CPPFLAGS="-I/opt/local/include"

    cmake -G Ninja \
        -DCMAKE_BUILD_TYPE=Release \
        -DCMAKE_OSX_DEPLOYMENT_TARGET=11.0 \
        -DCMAKE_OSX_ARCHITECTURES="${arch}" \
        -DCMAKE_PREFIX_PATH="/opt/local" \
        -DCMAKE_C_COMPILER="/opt/local/bin/clang-mp-17" \
        -DCMAKE_CXX_COMPILER="/opt/local/bin/clang++-mp-17" \
        -DBUILD_SHARED_LIBS=OFF \
        -DBUILD_TESTING=OFF \
        -DJPEGXL_ENABLE_BENCHMARK=OFF \
        -DJPEGXL_ENABLE_PLUGINS=OFF \
        -DJPEGXL_ENABLE_MANPAGES=OFF \
        -DJPEGXL_FORCE_SYSTEM_BROTLI=OFF \
        -DJPEGXL_FORCE_SYSTEM_GTEST=ON \
        -DJPEGXL_ENABLE_TOOLS=ON \
        -DJPEGXL_ENABLE_OPENEXR=OFF \
        -DJPEGXL_ENABLE_JPEGLI_LIBJPEG=OFF \
        -DJPEGXL_ENABLE_TCMALLOC=OFF \
        -DJPEGXL_ENABLE_VIEWERS=OFF \
        -DJPEGXL_ENABLE_DEVTOOLS=OFF \
        -DCMAKE_POLICY_VERSION_MINIMUM=3.5 \
        -DGIF_LIBRARY="/opt/local/lib/giflib5/lib/libgif.a" \
        -DGIF_INCLUDE_DIR="/opt/local/include/giflib5" \
        -DZLIB_LIBRARY="/opt/local/lib/libz.a" \
        -DZLIB_INCLUDE_DIR="/opt/local/include" \
        -DJPEG_LIBRARY="/opt/local/lib/libjpeg.a" \
        -DJPEG_INCLUDE_DIR="/opt/local/include" \
        -DPNG_LIBRARY="/opt/local/lib/libpng.a" \
        -DPNG_PNG_INCLUDE_DIR="/opt/local/include" \
        "${TEMP_DIR}/libjxl"

    ninja cjxl djxl jxlinfo
done
mkdir -p "${OUTPUT_DIR}"
for binary in cjxl djxl jxlinfo; do
    lipo -create \
        "${TEMP_DIR}/libjxl/build-x86_64/tools/${binary}" \
        "${TEMP_DIR}/libjxl/build-arm64/tools/${binary}" \
        -output "${OUTPUT_DIR}/${binary}"
done

# Build jpegli
git init "${TEMP_DIR}/jpegli"
cd "${TEMP_DIR}/jpegli"
git remote add origin https://github.com/google/jpegli.git
git fetch --depth 1 origin ${JPEGLI_COMMIT}
git switch --detach ${JPEGLI_COMMIT}
git submodule update --init --recursive --depth 1 --recommend-shallow \
    third_party/highway \
    third_party/lcms \
    third_party/libpng \
    third_party/zlib \
    third_party/libjpeg-turbo
for arch in x86_64 arm64; do
    build_dir="${TEMP_DIR}/jpegli/build-${arch}"
    mkdir -p "${build_dir}"
    cd "${build_dir}"

    export PKG_CONFIG_PATH="/opt/local/lib/pkgconfig"
    export LDFLAGS="-L/opt/local/lib"
    export CPPFLAGS="-I/opt/local/include"

    cmake -G Ninja \
        -DCMAKE_BUILD_TYPE=Release \
        -DCMAKE_OSX_DEPLOYMENT_TARGET=11.0 \
        -DCMAKE_OSX_ARCHITECTURES="${arch}" \
        -DCMAKE_PREFIX_PATH="/opt/local" \
        -DCMAKE_C_COMPILER="/opt/local/bin/clang-mp-17" \
        -DCMAKE_CXX_COMPILER="/opt/local/bin/clang++-mp-17" \
        -DJPEGLI_STATIC=ON \
        -DBUILD_TESTING=OFF \
        -DJPEGLI_ENABLE_TOOLS=ON \
        -DJPEGLI_ENABLE_JPEGLI_LIBJPEG=OFF \
        -DJPEGLI_ENABLE_BENCHMARK=OFF \
        -DJPEGLI_ENABLE_FUZZERS=OFF \
        -DJPEGLI_ENABLE_JNI=OFF \
        -DJPEGLI_ENABLE_SJPEG=OFF \
        -DJPEGLI_ENABLE_OPENEXR=OFF \
        -DJPEGLI_ENABLE_DEVTOOLS=OFF \
        -DJPEGLI_ENABLE_DOXYGEN=OFF \
        -DCMAKE_POLICY_VERSION_MINIMUM=3.5 \
        -DGIF_LIBRARY="/opt/local/lib/giflib5/lib/libgif.a" \
        -DGIF_INCLUDE_DIR="/opt/local/include/giflib5" \
        -DZLIB_LIBRARY="/opt/local/lib/libz.a" \
        -DZLIB_INCLUDE_DIR="/opt/local/include" \
        -DJPEG_LIBRARY="/opt/local/lib/libjpeg.a" \
        -DJPEG_INCLUDE_DIR="/opt/local/include" \
        -DPNG_LIBRARY="/opt/local/lib/libpng.a" \
        -DPNG_PNG_INCLUDE_DIR="/opt/local/include" \
        "${TEMP_DIR}/jpegli"

    ninja cjpegli
done
lipo -create \
    "${TEMP_DIR}/jpegli/build-x86_64/tools/cjpegli" \
    "${TEMP_DIR}/jpegli/build-arm64/tools/cjpegli" \
    -output "${OUTPUT_DIR}/cjpegli"

echo "Binaries copied to: ${OUTPUT_DIR}"
