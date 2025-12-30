#!/bin/bash
set -euo pipefail

IMAGEMAGICK_TAG="7.1.2-3"
LIBHEIF_TAG="v1.20.2"
LIBAOM_TAG="v3.12.1"
RUN_DIR=$(pwd)
OUTPUT_DIR="${RUN_DIR}/bin/macos/imagemagick"
TEMP_DIR=$(mktemp -d)
SCRIPT_DIR="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" && pwd )"
LIBHEIF_PREFIX="${TEMP_DIR}/libheif-prefix"
BUNDLED_PATHS=""
BUNDLE_SEARCH_PATHS=("${LIBHEIF_PREFIX}/lib" "/opt/local/lib")

source "${SCRIPT_DIR}/_shared.sh"
trap 'cleanup "${TEMP_DIR}"' EXIT
check_env
check_packages \
    pkgconf \
    libomp \
    imath \
    glib2 \
    gettext \
    webp \
    openjpeg \
    lcms2 \
    fontconfig \
    freetype \
    libjpeg-turbo \
    libjxl \
    liblqr \
    libpng \
    tiff \
    libtool

export MACOSX_DEPLOYMENT_TARGET=11.0

# Build libaom for libheif
cd "${TEMP_DIR}"
git clone -b "${LIBAOM_TAG}" --depth 1 https://aomedia.googlesource.com/aom
export CC="/opt/local/bin/clang-mp-17"
export CXX="/opt/local/bin/clang++-mp-17"
for arch in x86_64 arm64; do
    cmake \
        -G Ninja \
        -S aom \
        -B "aom/build.${arch}" \
        -DBUILD_SHARED_LIBS=OFF \
        -DCMAKE_OSX_ARCHITECTURES="${arch}" \
        -DAOM_TARGET_CPU="${arch}" \
        -DCMAKE_OSX_DEPLOYMENT_TARGET="${MACOSX_DEPLOYMENT_TARGET}" \
        -DCONFIG_PIC=1 \
        -DCMAKE_BUILD_TYPE=Release \
        -DENABLE_DOCS=0 \
        -DENABLE_EXAMPLES=0 \
        -DENABLE_TESTDATA=0 \
        -DENABLE_TESTS=0 \
        -DENABLE_TOOLS=0
    cmake --build "aom/build.${arch}" --config Release --parallel
done

mkdir -p "${TEMP_DIR}/aom/build"
lipo -create \
    "${TEMP_DIR}/aom/build.x86_64/libaom.a" \
    "${TEMP_DIR}/aom/build.arm64/libaom.a" \
    -output "${TEMP_DIR}/aom/build/libaom.a"

# Build libheif without non-free codecs (HEVC, AVC etc.)
cd "${TEMP_DIR}"
git clone --depth 1 -b "${LIBHEIF_TAG}" https://github.com/strukturag/libheif.git
cd libheif/
mkdir build && cd build/
export CC="/opt/local/bin/clang-mp-17"
export CXX="/opt/local/bin/clang++-mp-17"
cmake \
    -DCMAKE_INSTALL_PREFIX="${LIBHEIF_PREFIX}" \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_OSX_ARCHITECTURES="x86_64;arm64" \
    -DBUILD_SHARED_LIBS=ON \
    -DCMAKE_MACOSX_RPATH=ON \
    -DCMAKE_INSTALL_NAME_DIR="@rpath" \
    -DCMAKE_INSTALL_RPATH="@loader_path" \
    -DCMAKE_INSTALL_RPATH_USE_LINK_PATH=OFF \
    -DAOM_LIBRARY="${TEMP_DIR}/aom/build/libaom.a" \
    -DAOM_INCLUDE_DIR="${TEMP_DIR}/aom" \
    -DWITH_GDK_PIXBUF=OFF \
    -DWITH_KVAZAAR=OFF \
    -DWITH_KVAZAAR_PLUGIN=OFF \
    -DWITH_LIBDE265=OFF \
    -DWITH_LIBDE265_PLUGIN=OFF \
    -DWITH_UVG266=OFF \
    -DWITH_UVG266_PLUGIN=OFF \
    -DWITH_VVDEC=OFF \
    -DWITH_VVDEC_PLUGIN=OFF \
    -DWITH_VVENC=OFF \
    -DWITH_VVENC_PLUGIN=OFF \
    -DWITH_X265=OFF \
    -DWITH_X265_PLUGIN=OFF \
    -DWITH_OPENJPH_ENCODER=OFF \
    -DWITH_OpenH264_DECODER=OFF \
    -DWITH_OpenH264_DECODER_PLUGIN=OFF \
    -DWITH_DAV1D=OFF \
    -DWITH_DAV1D_PLUGIN=OFF \
    -DWITH_EXAMPLES=OFF \
    -DWITH_FFMPEG_DECODER=OFF \
    -DWITH_FFMPEG_DECODER_PLUGIN=OFF \
    -DWITH_RAV1E=OFF \
    -DWITH_RAV1E_PLUGIN=OFF \
    -DWITH_SvtEnc=OFF \
    -DWITH_SvtEnc_PLUGIN=OFF \
    -DWITH_SvtEnc_PLUGIN=OFF \
    -DCMAKE_POLICY_VERSION_MINIMUM=3.5 \
    ..
make -j$(sysctl -n hw.logicalcpu)
make install

export PKG_CONFIG_PATH="${LIBHEIF_PREFIX}/lib/pkgconfig${PKG_CONFIG_PATH:+:${PKG_CONFIG_PATH}}"
export CPPFLAGS="-I${LIBHEIF_PREFIX}/include${CPPFLAGS:+ ${CPPFLAGS}}"
export LDFLAGS="-Wl,-headerpad_max_install_names,-rpath,@executable_path/lib,-rpath,@loader_path -L${LIBHEIF_PREFIX}/lib${LDFLAGS:+ ${LDFLAGS}}"

# Build
git clone --depth 1 -b "${IMAGEMAGICK_TAG}" https://github.com/ImageMagick/ImageMagick.git "${TEMP_DIR}/ImageMagick"
build_dirs=()
for arch in x86_64 arm64; do
    build_dir="${TEMP_DIR}/build-${arch}"
    build_dirs+=("${build_dir}")

    mkdir -p "${build_dir}"
    cd "${build_dir}"

    export CC="/opt/local/bin/clang-mp-17 -arch ${arch}"
    export CXX="/opt/local/bin/clang++-mp-17 -arch ${arch}"

    # --enable-static has to stay because it prevents libMagickCore-7.Q16HDRI.10.dylib and libMagickWand-7.Q16HDRI.10.dylib from being created. They are a hassle to bundle.
    "${TEMP_DIR}/ImageMagick/configure" \
        --enable-static \
        --disable-shared \
        --enable-hdri \
        --with-quantum-depth=16 \
        --with-modules \
        --without-perl \
        --without-magick-plus-plus \
        --with-png \
        --with-jpeg \
        --with-tiff \
        --with-webp \
        --with-jxl \
        --with-zstd \
        --with-bzlib \
        --with-lzma \
        --with-openjp2 \
        --with-heic \
        --without-raw \
        --disable-opencl \
        --without-wmf \
        --without-uhdr \
        --without-djvu \
        --without-openexr \
        --without-raqm \
        --without-jbig \
        --without-gvc \
        --without-pango \
        --without-rsvg \
        --without-raqm \
        --host="${arch}-apple-darwin"

    make -j$(sysctl -n hw.logicalcpu)
done

# Combine binaries
mkdir -p "${OUTPUT_DIR}"
mkdir -p "${OUTPUT_DIR}/lib"
lipo -create \
    "${build_dirs[0]}/utilities/magick" \
    "${build_dirs[1]}/utilities/magick" \
    -output "${OUTPUT_DIR}/magick"

expand_special_path() {
    local token="$1"
    local binary="$2"
    local suffix
    case "${token}" in
        @loader_path|@loader_path/*)
            suffix="${token#@loader_path}"
            suffix="${suffix#/}"
            local loader_dir
            loader_dir="$(dirname "${binary}")"
            if [[ -n "${suffix}" ]]; then
                printf "%s/%s\n" "${loader_dir}" "${suffix}"
            else
                printf "%s\n" "${loader_dir}"
            fi
            ;;
        @executable_path|@executable_path/*)
            suffix="${token#@executable_path}"
            suffix="${suffix#/}"
            if [[ -n "${suffix}" ]]; then
                printf "%s/%s\n" "${OUTPUT_DIR}" "${suffix}"
            else
                printf "%s\n" "${OUTPUT_DIR}"
            fi
            ;;
        *)
            printf "%s\n" "${token}"
            ;;
    esac
}
strip_external_rpaths() {
    local binary="$1"
    local existing
    existing="$(collect_rpaths "${binary}")"

    [[ -z "${existing}" ]] && return

    while IFS= read -r rpath; do
        [[ -z "${rpath}" ]] && continue
        case "${rpath}" in
            @loader_path*|@executable_path*)
                continue
                ;;
        esac

        install_name_tool -delete_rpath "${rpath}" "${binary}" 2> /dev/null || true
    done <<< "${existing}"
}

resolve_dependency() {
    local binary="$1"
    local dep="$2"
    local loader_dir
    loader_dir="$(dirname "${binary}")"
    local base_name
    base_name="$(basename "${dep}")"
    local rpaths
    rpaths="$(collect_rpaths "${binary}")"

    case "${dep}" in
        @loader_path*|@executable_path*)
            local expanded
            expanded="$(expand_special_path "${dep}" "${binary}")"
            if [[ -n "${expanded}" && -f "${expanded}" ]]; then
                printf "%s\n" "${expanded}"
                return 0
            fi
            ;;
        @rpath/*)
            local suffix="${dep#@rpath/}"
            while IFS= read -r rpath; do
                local expanded
                expanded="$(expand_special_path "${rpath}" "${binary}")"
                if [[ -n "${expanded}" && -f "${expanded}/${suffix}" ]]; then
                    printf "%s\n" "${expanded}/${suffix}"
                    return 0
                fi
            done <<< "${rpaths}"
            ;;
        /*)
            if [[ -f "${dep}" ]]; then
                printf "%s\n" "${dep}"
                return 0
            fi
            ;;
    esac

    local candidate
    for candidate in "${BUNDLE_SEARCH_PATHS[@]}" "${loader_dir}" "${OUTPUT_DIR}/lib"; do
        [[ -z "${candidate}" ]] && continue
        if [[ -f "${candidate}/${base_name}" ]]; then
            printf "%s/%s\n" "${candidate}" "${base_name}"
            return 0
        fi
    done

    return 1
}

bundle_binary() {
    local binary="$1"
    local lib_dir="$2"

    if [[ ":${BUNDLED_PATHS}:" == *"
${binary}
"* ]]; then
        return
    fi
    BUNDLED_PATHS="${BUNDLED_PATHS}
${binary}"
    
    chmod +w "${binary}"

    local deps
    deps=$(otool -L "${binary}" | sed 1d | grep -v ':$' | awk '{print $1}' | sort -u)
    
    while IFS= read -r dep; do
        [[ -z "${dep}" ]] && continue

        if [[ "${dep}" == /usr/lib/* ||
            "${dep}" == /System/* ||
            "${dep}" == "${binary}" ]]; then
            continue
        fi

        local source_path
        if ! source_path="$(resolve_dependency "${binary}" "${dep}")"; then
            warning "Unable to resolve dependency ${dep} for ${binary}"
            continue
        fi

        local lib_name
        lib_name="$(basename "${dep}")"
        local lib_target="${lib_dir}/${lib_name}"

        if [[ ! -f "${lib_target}" ]]; then
            cp "${source_path}" "${lib_target}"
            chmod +w "${lib_target}"
            install_name_tool -id "@loader_path/${lib_name}" "${lib_target}"
            strip_external_rpaths "${lib_target}"
        fi

        if [[ "${binary}" == *.dylib ]]; then
            install_name_tool -change "${dep}" "@loader_path/${lib_name}" "${binary}"
        else
            install_name_tool -change "${dep}" "@executable_path/lib/${lib_name}" "${binary}"
        fi

        bundle_binary "${lib_target}" "${lib_dir}"

    done <<< "${deps}"

    strip_external_rpaths "${binary}"
}

update_ids() {
    local lib_dir="$1"
    for dylib in "${lib_dir}"/*.dylib; do
        [[ -f "${dylib}" ]] || continue
        install_name_tool -id "@loader_path/$(basename "${dylib}")" "${dylib}"
    done
}

collect_rpaths() {
    local binary="$1"
    otool -l "${binary}" | awk '
        $1 == "cmd" && $2 == "LC_RPATH" {
            getline
            getline
            if ($1 == "path") {
                print $2
            }
        }
    '
}

binary_minimum_version() {
    local binary="$1"
    otool -l "${binary}" | awk '
        $1 == "cmd" && $2 == "LC_BUILD_VERSION" { mode=1; next }
        mode == 1 && $1 == "minos" { print $2; exit }
        $1 == "cmd" && $2 == "LC_VERSION_MIN_MACOS" { mode=2; next }
        mode == 2 && $1 == "version" { print $2; exit }
    '
}

check_deployment_target() {
    local binary="$1"
    local expected="$2"
    local actual
    actual="$(binary_minimum_version "${binary}")"
    if [[ -n "${actual}" && "${actual}" != "${expected}" ]]; then
        warning "${binary} has deployment target ${actual}, expected ${expected}."
        return 1
    fi
    return 0
}

validate() {
    # Main executable
    local exe_deps=$(otool -L "${OUTPUT_DIR}/magick" \
        | sed 1d \
        | awk '{print $1}' \
        | grep '^/' \
        | grep -Ev '^/(usr/lib/|System)' \
        | grep -Fv "${OUTPUT_DIR}/magick" \
        || true)

    if [[ -n "${exe_deps}" ]]; then
        warning "The magick binary has external dependencies. It will not work on another system."
        warning "Disallowed dependencies: ${exe_deps}"
    fi

    local exe_bad_rpaths
    exe_bad_rpaths="$(collect_rpaths "${OUTPUT_DIR}/magick" | grep -Ev '^(@loader_path|@executable_path)' || true)"
    local has_bad_minos=false
    if [[ -n "${exe_bad_rpaths}" ]];  then
        warning "The magick binary contains unexpected rpaths: ${exe_bad_rpaths}"
    fi

    if ! check_deployment_target "${OUTPUT_DIR}/magick" "${MACOSX_DEPLOYMENT_TARGET}"; then
        has_bad_minos=true
    fi

    # lib
    local has_external=false
    local has_bad_rpath=false
    for dylib in "${OUTPUT_DIR}/lib/"*.dylib; do
        local dylib_deps=$(otool -L "${dylib}" \
            | sed 1d \
            | awk '{print $1}' \
            | grep '^/' \
            | grep -Ev '^/(usr/lib/|System)' \
            || true)
        if [[ -n "${dylib_deps}" ]]; then
            has_external=true
        fi

        local dylib_bad_rpaths
        dylib_bad_rpaths="$(collect_rpaths "${dylib}" | grep -Ev '^(@loader_path|@executable_path)' || true)"
        if [[ -n "${dylib_bad_rpaths}" ]]; then
            has_bad_rpath=true
        fi

        if ! check_deployment_target "${dylib}" "${MACOSX_DEPLOYMENT_TARGET}"; then
            has_bad_minos=true
        fi
    done

    if [[ "${has_external}" == "true" ]]; then
        warning "External dependencies present. This bundle will not work on another system."
    fi

    if [[ "${has_bad_rpath}" == "true" ]]; then
        warning "Some dylibs contain unexpected rpaths."
    fi

    if [[ "${has_bad_minos}" == "true" ]]; then
        warning "Put 'macosx_deployment_target ${MACOSX_DEPLOYMENT_TARGET}' in '/opt/local/etc/macports/macports.conf', then reinstall the libraries with 'sudo port -s upgrade --force <libname>'"
    fi
}

bundle_binary "${OUTPUT_DIR}/magick" "${OUTPUT_DIR}/lib"
update_ids "${OUTPUT_DIR}/lib"
validate

echo "Build artifacts copied to: ${OUTPUT_DIR}"
