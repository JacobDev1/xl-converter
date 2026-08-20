#!/usr/bin/env bash
set -euo pipefail

LIBJPEG_TURBO_TAG="3.1.0"
MT_PATH=$(ls -1 "/c/Program Files (x86)/Windows Kits/10/bin/"*"/x64/mt.exe" 2>/dev/null | sort -V | tail -n 1)
RUN_DIR=$(pwd)
OUTPUT_DIR="${RUN_DIR}/bin/win/jpegtran"
TEMP_DIR=$(mktemp -d)
SCRIPT_DIR="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" && pwd )"

source "${SCRIPT_DIR}/_shared.sh"
trap 'cleanup "${TEMP_DIR}"' EXIT

check_msys2
# If your cmake (mingw-w64-x86_64-cmake) is broken and returns no output -- install the generic one with: pacman -S cmake
check_packages \
    git \
    cmake \
    mingw-w64-x86_64-ninja \
    nasm \
    mingw-w64-x86_64-gcc \
    mingw-w64-x86_64-make

if [ -z "$MT_PATH" ]; then
    echo "mt.exe not found. Install Windows SDK through Visual Studio, change MT_PATH in this script, and try again."
    exit 1
fi

# Build
cd "${TEMP_DIR}"
git clone --depth 1 -b "${LIBJPEG_TURBO_TAG}" https://github.com/libjpeg-turbo/libjpeg-turbo.git
cd libjpeg-turbo/
mkdir build && cd build/
cmake -G "Unix Makefiles" \
    -DCMAKE_BUILD_TYPE=Release \
    -DENABLE_STATIC=TRUE \
    ..
make
# make -j$(nproc)

# Bundle
mkdir -p "${OUTPUT_DIR}"
cp jpegtran-static.exe "${OUTPUT_DIR}/jpegtran.exe"
bundle_dlls "${OUTPUT_DIR}"

# Run mt.exe
cat <<EOF > "${TEMP_DIR}/manifest.xml"
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<assembly manifestVersion="1.0" xmlns="urn:schemas-microsoft-com:asm.v1">
    <application>
    <windowsSettings>
        <activeCodePage xmlns="http://schemas.microsoft.com/SMI/2019/WindowsSettings">UTF-8</activeCodePage>
    </windowsSettings>
    </application>
</assembly>
EOF
# Convert LF to CRLF
sed -i "s/$/\r/" "${TEMP_DIR}/manifest.xml"
find "${OUTPUT_DIR}" -type f -name "*.exe" | while read -r exe; do
    "${MT_PATH}" -manifest "${TEMP_DIR}/manifest.xml" -outputresource:"${exe}";#1
done

echo "Binaries copied to: ${OUTPUT_DIR}"
