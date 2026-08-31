#!/usr/bin/env bash
set -euo pipefail

# Mirrored due to older versions getting removed from sourceforge.
EXIFTOOL_TAG="13.59"
EXIFTOOL_DOWNLOAD_URL="https://github.com/JacobDev1/xl-converter-testing/releases/download/mirror-deps-0/exiftool-${EXIFTOOL_TAG}-windows-x86_64.zip"
EXIFTOOL_EXPECTED_SHA256="44b512b25af500724ba579d0a53c8fc5851628b692dd5e5d94ae4a15c2cba9ec"

RUN_DIR=$(pwd)
OUTPUT_DIR="${RUN_DIR}/bin/win/exiftool"
TEMP_DIR=$(mktemp -d)
SCRIPT_DIR="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" && pwd )"

source "${SCRIPT_DIR}/_shared.sh"
trap 'cleanup "${TEMP_DIR}"' EXIT

check_msys2
check_commands 7z git wget sha256sum

# Prepare
cd "$TEMP_DIR"
wget "$EXIFTOOL_DOWNLOAD_URL" -O exiftool.zip
exiftool_actual_sha256=$(sha256sum exiftool.zip | awk '{print $1}')
if [ "$exiftool_actual_sha256" != "$EXIFTOOL_EXPECTED_SHA256" ]; then
  echo "Error: Checksum mismatch."
  exit 1
fi
7z x exiftool.zip
cd "exiftool-${EXIFTOOL_TAG}_64"
mv "exiftool(-k).exe" exiftool.exe
rm -f ./exiftool_files/Licenses_Strawberry_Perl.zip     # 0.5 MB saved
rm -f ./README.txt

# Move
mkdir -p "$OUTPUT_DIR"
mv "${TEMP_DIR}"/exiftool-"${EXIFTOOL_TAG}"_64/* "${OUTPUT_DIR}"
