#!/bin/bash
set -euo pipefail

LIBAVIF_TAG="v1.3.0"
LIBYUV_COMMIT="4db2af62d"        # Update this commit hash when changing LIBAVIF_TAG. It can be found in libavif/ext/libyuv.cmd
LIBXML2_TAG="v2.14.4"            # libavif/ext/libxml2.cmd
AOM_AV1_TAG="v3.13.1"
SVT_AV1_PSY_TAG="v3.0.2"

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
    ninja \
    jpeg-turbo \
    cmake \
    make \
    yasm \
    webp \
    zlib \
    libpng \
    libiconv
# webp includes libsharpyuv

# Prepare repo
cd "${TEMP_DIR}"
git clone --depth 1 -b "${LIBAVIF_TAG}" https://aomedia.googlesource.com/libavif

cd libavif/ext/

# Build aom
git clone -b "${AOM_AV1_TAG}" --depth 1 https://aomedia.googlesource.com/aom aom
for arch in x86_64 arm64; do
    cmake_flags=(
        -G Ninja
        -S aom
        -B "aom/build.libaom.${arch}"
        -DCMAKE_OSX_DEPLOYMENT_TARGET=11.0
        -DCMAKE_OSX_ARCHITECTURES="${arch}"
        -DAOM_TARGET_CPU="${arch}"
        -DCMAKE_C_COMPILER="/opt/local/bin/clang-mp-17"
        -DCMAKE_CXX_COMPILER="/opt/local/bin/clang++-mp-17"
        -DBUILD_SHARED_LIBS=OFF
        -DCONFIG_PIC=1
        -DCMAKE_BUILD_TYPE=Release
        -DENABLE_DOCS=0
        -DENABLE_EXAMPLES=0
        -DENABLE_TESTDATA=0
        -DENABLE_TESTS=0
        -DENABLE_TOOLS=0
        -DCMAKE_ASM_NASM_COMPILER="$(which yasm)"
    )

    if [ "${arch}" = "x86_64" ]; then
        cmake_flags+=(
            -DCMAKE_TOOLCHAIN_FILE="${TEMP_DIR}/libavif/ext/aom/build/cmake/toolchains/x86_64-macos.cmake"
            -DHAVE_NEON=0
        )
    fi

    cmake "${cmake_flags[@]}"
    cmake --build "aom/build.libaom.${arch}" --config Release --parallel
done

mkdir aom/build.libaom
lipo -create \
    aom/build.libaom.x86_64/libaom.a \
    aom/build.libaom.arm64/libaom.a \
    -output aom/build.libaom/libaom.a

# Build svt-av1-psy
git clone -b "${SVT_AV1_PSY_TAG}" --depth 1 https://github.com/psy-ex/svt-av1-psy.git SVT-AV1
cd SVT-AV1
for arch in x86_64 arm64; do
    cd Build/linux
    ./build.sh \
        --cc="/opt/local/bin/clang-mp-17" \
        --cxx="/opt/local/bin/clang++-mp-17" \
        --gen=Ninja \
        --target_system="Darwin" \
        disable-native \
        release \
        static \
        no-apps \
        -- \
        -DCMAKE_OSX_DEPLOYMENT_TARGET=11.0 \
        -DCMAKE_SYSTEM_PROCESSOR="${arch}" \
        -DCMAKE_OSX_ARCHITECTURES="${arch}"

    cd ../..
    mkdir -p "build.svtav1.${arch}"
    cp "Bin/Release/libSvtAv1Enc.a" "build.svtav1.${arch}/"
done

mkdir -p Bin/Release
lipo -create \
    build.svtav1.x86_64/libSvtAv1Enc.a \
    build.svtav1.arm64/libSvtAv1Enc.a \
    -output Bin/Release/libSvtAv1Enc.a
mkdir -p include/svt-av1
cp Source/API/*.h include/svt-av1

# Build libyuv
cd "${TEMP_DIR}/libavif/ext"
git clone --single-branch https://chromium.googlesource.com/libyuv/libyuv
cd libyuv
# Commit id from libavif/ext/libyuv.cmd
git checkout "${LIBYUV_COMMIT}"
cd ..

# Patch NEON64 object creation when cross-compiling for arm64 on x86_64.
gsed -i 's/if(arch_lowercase STREQUAL "aarch64" OR arch_lowercase STREQUAL "arm64")/if(arch_lowercase STREQUAL "aarch64" OR arch_lowercase STREQUAL "arm64" OR DEFINED CMAKE_OSX_ARCHITECTURES AND CMAKE_OSX_ARCHITECTURES STREQUAL "arm64")/g' libyuv/CMakeLists.txt

for arch in x86_64 arm64; do
    cmake_args=(
        -G Ninja
        -S libyuv
        -B "libyuv/build.${arch}"
        -DCMAKE_BUILD_TYPE=Release
        -DCMAKE_POSITION_INDEPENDENT_CODE=OFF
        -DCMAKE_OSX_DEPLOYMENT_TARGET=11.0
        -DCMAKE_C_COMPILER="/opt/local/bin/clang-mp-17"
        -DCMAKE_CXX_COMPILER="/opt/local/bin/clang++-mp-17"
        -DCMAKE_PREFIX_PATH="/opt/local"
        -DJPEG_LIBRARY="/opt/local/lib/libjpeg.a"
        -DJPEG_INCLUDE_DIR="/opt/local/include"
        -DCMAKE_SYSTEM_NAME="Darwin"
        -DCMAKE_OSX_ARCHITECTURES="${arch}"
        -DCMAKE_SYSTEM_PROCESSOR="${arch}"
    )

    if [ "${arch}" = "arm64" ]; then
        cmake_args+=(
           -DCMAKE_C_FLAGS="-DLIBYUV_NEON=1"
           -DCMAKE_CXX_FLAGS="-DLIBYUV_NEON=1"
        )
    fi

    cmake "${cmake_args[@]}"
    cmake --build "libyuv/build.${arch}" --config Release --target yuv --parallel
done

mkdir -p libyuv/build
lipo -create \
    libyuv/build.x86_64/libyuv.a \
    libyuv/build.arm64/libyuv.a \
    -output libyuv/build/libyuv.a

# Build libxml2
git clone -b "${LIBXML2_TAG}" --depth 1 https://github.com/GNOME/libxml2.git
cmake -G Ninja \
    -S libxml2 \
    -B libxml2/build.libavif/ \
    -DCMAKE_OSX_DEPLOYMENT_TARGET=11.0 \
    -DCMAKE_OSX_ARCHITECTURES="arm64;x86_64" \
    -DBUILD_SHARED_LIBS=OFF \
    -DCMAKE_PREFIX_PATH="/opt/local" \
    -DCMAKE_C_COMPILER="/opt/local/bin/clang-mp-17" \
    -DCMAKE_CXX_COMPILER="/opt/local/bin/clang++-mp-17" \
    -DCMAKE_INSTALL_PREFIX=libxml2/install.libavif \
    -DIconv_LIBRARY="/opt/local/lib/libiconv.a" \
    -DLIBXML2_WITH_PYTHON=OFF \
    -DLIBXML2_WITH_ZLIB=OFF \
    -DLIBXML2_WITH_LZMA=OFF
cmake --build libxml2/build.libavif --config Release --parallel
cmake --install libxml2/build.libavif

# Build libavif
# One arch at a time because doing both is less stable.
for arch in x86_64 arm64; do
    build_dir="${TEMP_DIR}/build-${arch}"
    mkdir -p "${build_dir}"
    cd "${build_dir}"

    # Library paths are hardcoded because .dylib get prioritized over .a.
    cmake -G Ninja \
        -DCMAKE_OSX_DEPLOYMENT_TARGET=11.0 \
        -DCMAKE_C_COMPILER="/opt/local/bin/clang-mp-17" \
        -DCMAKE_CXX_COMPILER="/opt/local/bin/clang++-mp-17" \
        -DCMAKE_PREFIX_PATH="/opt/local" \
        -DCMAKE_OSX_ARCHITECTURES="${arch}" \
        -DCMAKE_BUILD_TYPE=Release \
        -DBUILD_SHARED_LIBS=0 \
        -DAVIF_BUILD_APPS=1 \
        -DAVIF_LIBYUV=LOCAL \
        -DAVIF_LIBSHARPYUV=SYSTEM \
        -DLIBSHARPYUV_LIBRARY="/opt/local/lib/libsharpyuv.a" \
        -DLIBSHARPYUV_INCLUDE_DIR="/opt/local/include/webp" \
        -DAVIF_JPEG=SYSTEM \
        -DJPEG_LIBRARY="/opt/local/lib/libjpeg.a" \
        -DJPEG_INCLUDE_DIR="/opt/local/include" \
        -DAVIF_ZLIBPNG=SYSTEM \
        -DZLIB_LIBRARY="/opt/local/lib/libz.a" \
        -DZLIB_INCLUDE_DIR="/opt/local/include" \
        -DPNG_LIBRARY="/opt/local/lib/libpng.a" \
        -DPNG_INCLUDE_DIR="/opt/local/include" \
        -DAVIF_LIBXML2=LOCAL \
        -DCMAKE_EXE_LINKER_FLAGS="/opt/local/lib/libiconv.a" \
        -DAVIF_CODEC_SVT=LOCAL \
        -DAVIF_CODEC_AOM=SYSTEM \
        -DAOM_INCLUDE_DIR="${TEMP_DIR}/libavif/ext/aom" \
        -DAOM_LIBRARY="${TEMP_DIR}/libavif/ext/aom/build.libaom.${arch}/libaom.a" \
        -DCMAKE_POLICY_VERSION_MINIMUM=3.5 \
        "${TEMP_DIR}/libavif"

    ninja avifenc avifdec
done

mkdir -p "${OUTPUT_DIR}"
for binary in avifenc avifdec; do
    lipo -create \
        "${TEMP_DIR}/build-x86_64/${binary}" \
        "${TEMP_DIR}/build-arm64/${binary}" \
        -output "${OUTPUT_DIR}/${binary}"
done
echo "Binaries copied to: ${OUTPUT_DIR}"
