import os
import platform
import sys
import logging

from core.utils import removeDuplicates

VERSION = "0.9.8"
VERSION_FILE_URL = "https://codepoems.eu/downloads/xl-converter/version.json"   # Used by UpdateChecker; example in misc/version.json

logging.basicConfig(
    level=logging.WARNING,    # DEBUG, INFO, WARNING, ERROR, CRITICAL
    stream=sys.stderr,
    encoding="utf-8",
    format="[%(levelname)s] %(message)s",
)

# Filled below
CONFIG_LOCATION = ""
PROGRAM_FOLDER = sys._MEIPASS if getattr(sys, "frozen", False) else os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
ICON_SVG = os.path.join(PROGRAM_FOLDER, "icons/logo.svg")
LICENSE_PATH = os.path.join(PROGRAM_FOLDER, "LICENSE.txt")
LICENSE_3RD_PARTY_PATH = os.path.join(PROGRAM_FOLDER, "LICENSE_3RD_PARTY.txt")

CJXL_PATH = "cjxl"
DJXL_PATH = "djxl"
JXLINFO_PATH = "jxlinfo"
CJPEGLI_PATH = "cjpegli"
IMAGE_MAGICK_PATH = "magick"
AVIFENC_PATH = "avifenc"
AVIFDEC_PATH = "avifdec"
OXIPNG_PATH = "oxipng"
EXIFTOOL_PATH = "exiftool"
EXIFTOOL_FOLDER_PATH = ""
EXIFTOOL_BIN_NAME = "exiftool"

if platform.system() == "Windows":
    BASE_PATH = os.path.join(PROGRAM_FOLDER, "bin", "win")

    CJXL_PATH = os.path.join(BASE_PATH, "cjxl.exe")
    DJXL_PATH = os.path.join(BASE_PATH, "djxl.exe")
    JXLINFO_PATH = os.path.join(BASE_PATH, "jxlinfo.exe")
    CJPEGLI_PATH = os.path.join(BASE_PATH, "cjpegli.exe")
    IMAGE_MAGICK_PATH = os.path.join(BASE_PATH, "magick.exe")
    AVIFENC_PATH = os.path.join(BASE_PATH, "avifenc.exe")
    AVIFDEC_PATH = os.path.join(BASE_PATH, "avifdec.exe")
    OXIPNG_PATH = os.path.join(BASE_PATH, "oxipng.exe")

    EXIFTOOL_PATH = os.path.join(BASE_PATH, "exiftool.exe")
    EXIFTOOL_FOLDER_PATH = BASE_PATH
    EXIFTOOL_BIN_NAME = "exiftool.exe"

    CONFIG_LOCATION = os.path.normpath(os.path.expanduser("~/AppData/Local/xl-converter"))
elif platform.system() == "Linux":
    BASE_PATH = f"{PROGRAM_FOLDER}/bin/linux"

    CJXL_PATH = f"{BASE_PATH}/cjxl"
    DJXL_PATH = f"{BASE_PATH}/djxl"
    JXLINFO_PATH = f"{BASE_PATH}/jxlinfo"
    CJPEGLI_PATH = f"{BASE_PATH}/cjpegli"
    IMAGE_MAGICK_PATH = f"{BASE_PATH}/magick"
    AVIFENC_PATH = f"{BASE_PATH}/avifenc"
    AVIFDEC_PATH = f"{BASE_PATH}/avifdec"
    OXIPNG_PATH = f"{BASE_PATH}/oxipng"

    EXIFTOOL_PATH = f"{BASE_PATH}/exiftool/exiftool"
    EXIFTOOL_FOLDER_PATH = f"{BASE_PATH}/exiftool"
    EXIFTOOL_BIN_NAME = "exiftool"

    CONFIG_LOCATION = os.path.expanduser('~/.config/xl-converter')

# Proper usage is "if 'extension'.lower() in ALLOWED_INPUT:"
JPEG_ALIASES = ["jpg", "jpeg", "jfif", "jif", "jpe"] # Used by CJXL for JPEG reconstruction, before adding more verify support
ALLOWED_INPUT_DJXL = ["jxl"]
ALLOWED_INPUT_CJXL = JPEG_ALIASES + ["png", "apng", "gif"]
ALLOWED_INPUT_CJPEGLI = JPEG_ALIASES
ALLOWED_INPUT_IMAGE_MAGICK = JPEG_ALIASES + ["png", "gif", "heif", "heifs", "heic", "heics", "avci", "avcs", "hif", "webp", "jp2", "bmp", "ico"]     # Before adding more, make sure the included ImageMagick works with it. Some formats (like FLIF) seem not to have been included
ALLOWED_INPUT_AVIFENC = JPEG_ALIASES + ["png"]
ALLOWED_INPUT_AVIFDEC = ["avif"]
ALLOWED_INPUT_OXIPNG = ["png"]
ALLOWED_INPUT = removeDuplicates(ALLOWED_INPUT_DJXL + ALLOWED_INPUT_CJXL + ALLOWED_INPUT_IMAGE_MAGICK + ALLOWED_INPUT_AVIFENC + ALLOWED_INPUT_AVIFDEC + ALLOWED_INPUT_OXIPNG)
ALLOWED_RESAMPLING = ("Lanczos", "Point", "Box", "Cubic", "Hermite", "Gaussian", "Catrom", "Triangle", "Quadratic", "Mitchell", "CubicSpline", "Hamming", "Parzen", "Blackman", "Kaiser", "Welsh", "Hanning", "Bartlett", "Bohman")