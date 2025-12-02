#!/bin/bash
set -euo pipefail

EXIFTOOL_TAG="13.39"

PERL_PATH="/opt/local/bin/perl5.40"
RUN_DIR=$(pwd)
OUTPUT_DIR="${RUN_DIR}/bin/macos"
TEMP_DIR=$(mktemp -d)
SCRIPT_DIR="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" && pwd )"
CPANM_PATH="${TEMP_DIR}/cpanm"

source "${SCRIPT_DIR}/_shared.sh"
trap 'cleanup "${TEMP_DIR}"' EXIT

check_env
check_commands curl git

# Bootstrap cpanm and download ExifTool
curl -fsSL https://cpanmin.us -o "${CPANM_PATH}"
chmod +x "${CPANM_PATH}"
git clone --depth 1 -b "${EXIFTOOL_TAG}" https://github.com/exiftool/exiftool "${TEMP_DIR}/exiftool"
cd "${TEMP_DIR}/exiftool"
chmod +x ./build_tag_lookup && ./build_tag_lookup

# Packages to include in the bundle
# Reference: https://github.com/exiftool/exiftool/blob/master/META.json
perl_packages=(
    IO::Compress::Brotli IO::Uncompress::Brotli Archive::Zip Compress::Zlib IO::Compress::Bzip2 IO::Compress::RawDeflate IO::Uncompress::RawInflate Compress::Raw::Lzma
    Digest::MD5 Digest::SHA Time::Piece POSIX::strptime Time::HiRes
    Unicode::LineBreak
)

build_exiftool() {
    local target_arch="$1"
    local output="$2"
    local cpan_prefix="${TEMP_DIR}/vendor_${target_arch}"

    export MACOSX_DEPLOYMENT_TARGET=11.0

    mkdir -p "${cpan_prefix}"
    arch -"${target_arch}" \
        "${PERL_PATH}" \
        "${CPANM_PATH}" \
        -L "${cpan_prefix}" \
        --notest --quiet --no-interactive \
        PAR::Packer Module::ScanDeps \
        "${perl_packages[@]}"

    export PERL5LIB="${cpan_prefix}/lib/perl5"
    export PATH="${cpan_prefix}/bin:${PATH}"

    local pp_packages=()
    for p in "${perl_packages[@]}"; do
        pp_packages+=(-M "$p")
    done

    arch -"${target_arch}" \
        "${PERL_PATH}" \
        -S pp \
        -I lib -a "lib/" \
        "${pp_packages[@]}" \
        -o "${output}" \
        exiftool
}

is_rosetta_available() {
    [ "$(uname -m)" != "arm64" ] && return 0
    /usr/bin/arch -x86_64 /usr/bin/true > /dev/null 2>&1 && return 0
    return 1
}

pull_arm64_prebuild() {
    # TODO
    local output="$1"
}

x86_64_slice="${TEMP_DIR}/exiftool.x86_64"
arm64_slice="${TEMP_DIR}/exiftool.arm64"
exiftool_bin="${TEMP_DIR}/exiftool_build_export"

case "$(uname -m)" in
    x86_64)
        build_exiftool x86_64 "${x86_64_slice}"
        # pull_arm64_prebuild "${arm64_slice}"
        # lipo -create "${x86_64_slice}" "${arm64_slice}" -output "${exiftool_bin}"
        mv "$x86_64_slice" "$exiftool_bin"
        echo "Generated binary will be thin. This script is a work-in-progress."
        ;;
    arm64)
        if is_rosetta_available; then
            build_exiftool x86_64 "${x86_64_slice}"
            build_exiftool arm64 "${arm64_slice}"
            lipo -create "${x86_64_slice}" "${arm64_slice}" -output "${exiftool_bin}"
        elif [[ "${THIN_BINARY:-0}" != "1" ]]; then
            warning "Install Rosetta and try again or export THIN_BINARY=1 to compile for native arch only."
            exit 1
        else
            build_exiftool arm64 "${arm64_slice}"
            mv "${arm64_slice}" "${exiftool_bin}"
            warning "The exiftool binary will not run on Intel macOS!"
        fi
        ;;
    *)
        echo "Unsupported host architecture"
        exit 1
        ;;
esac


mkdir -p "${OUTPUT_DIR}"
mv "${exiftool_bin}" "${OUTPUT_DIR}/exiftool"
echo "The build artifact copied to: ${OUTPUT_DIR}"
