#!/bin/bash

EXIFTOOL_TAG="13.52"

RUN_DIR=$(pwd)
OUTPUT_DIR="${RUN_DIR}/bin/win/exiftool"
TEMP_DIR=$(mktemp -d)
SCRIPT_DIR="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" && pwd )"

source "${SCRIPT_DIR}/_shared.sh"

trap 'cleanup "${TEMP_DIR}"' EXIT
set -euo pipefail
check_msys2
check_commands 7z git wget

# Prepare
cd "$TEMP_DIR"
# Mirrored due to older versions getting removed from sourceforge.
wget "https://github.com/JacobDev1/xl-converter-testing/releases/download/mirror-deps-0/exiftool-${EXIFTOOL_TAG}-windows-x86_64.zip" -O exiftool.zip
7z x exiftool.zip
cd "exiftool-${EXIFTOOL_TAG}_64"
mv "exiftool(-k).exe" exiftool.exe
rm -f ./exiftool_files/Licenses_Strawberry_Perl.zip     # 0.5 MB saved
rm -f ./README.txt

# Move
mkdir -p "$OUTPUT_DIR"
mv "${TEMP_DIR}"/exiftool-"${EXIFTOOL_TAG}"_64/* "${OUTPUT_DIR}"
