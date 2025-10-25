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

export MACOSX_DEPLOYMENT_TARGET=11.0
export ARCHFLAGS="-arch x86_64 -arch arm64"
export CFLAGS="${ARCHFLAGS}"
export CXXFLAGS="${ARCHFLAGS}"
export LDFLAGS="${ARCHFLAGS}"

# Bootstrap cpanm and download ExifTool
curl -fsSL https://cpanmin.us -o "${CPANM_PATH}"
chmod +x "${CPANM_PATH}"
git clone --depth 1 -b "${EXIFTOOL_TAG}" https://github.com/exiftool/exiftool "${TEMP_DIR}/exiftool"
cd "${TEMP_DIR}/exiftool"
chmod +x ./build_tag_lookup && ./build_tag_lookup

if ! file -b "${PERL_PATH}" | grep -qi "universal binary"; then
  echo "Perl is not universal. Reinstall it with +universal, and try again."
  exit 1
fi

# Packages to include in the bundle
# Reference: https://github.com/exiftool/exiftool/blob/master/META.json
perl_packages=(
  IO::Compress::Brotli IO::Uncompress::Brotli Archive::Zip Compress::Zlib IO::Compress::Bzip2 IO::Compress::RawDeflate IO::Uncompress::RawInflate Compress::Raw::Lzma
  Digest::SHA Digest::MD5 Digest::SHA Time::Piece POSIX::strptime Time::HiRes
  Unicode::LineBreak
)

cpan_prefix="${TEMP_DIR}/vendor"
mkdir -p "${cpan_prefix}"
"${PERL_PATH}" \
  "${CPANM_PATH}" \
  -L "${cpan_prefix}" \
  --notest --quiet --no-interactive \
  PAR::Packer Module::ScanDeps \
  "${perl_packages[@]}"

export PERL5LIB="${cpan_prefix}/lib/perl5"
export PATH="${cpan_prefix}/bin:${PATH}"

pp_packages=()
for p in "${perl_packages[@]}"; do
  pp_packages+=(-M "$p")
done

"${PERL_PATH}" \
  -S pp \
  -I lib -a "lib/=lib" \
  "${pp_packages[@]}" \
  -o "${TEMP_DIR}/exiftool.universal" \
  exiftool

if ! file -b "${TEMP_DIR}/exiftool.universal" | grep -qi "universal binary"; then
  echo "Warning, the bundle is not a universal binary."
fi

mkdir -p "${OUTPUT_DIR}"
mv "${TEMP_DIR}/exiftool.universal" "${OUTPUT_DIR}/exiftool"
echo "Build artifacts copied to: ${OUTPUT_DIR}"
