import os, platform

PROGRAM_FOLDER = os.path.dirname(os.path.realpath(__file__))

CJXL_PATH = "cjxl"
DJXL_PATH = "djxl"
IMAGE_MAGICK_PATH = "magick"    # for AVIF, WEBP
# MOZJPG_PATH = "mozjpeg"
# AVIF_PATH = ""
# CWEBP_PATH = ""
# DWEBP_PATH = ""

if platform.system() == "Windows":
    CJXL_PATH = os.path.abspath(os.path.join(PROGRAM_FOLDER,"bin/win/cjxl.exe"))
    DJXL_PATH = os.path.abspath(os.path.join(PROGRAM_FOLDER,"bin/win/djxl.exe"))
    IMAGE_MAGICK_PATH = os.path.abspath(os.path.join(PROGRAM_FOLDER,"bin/win/magick.exe"))
elif platform.system() == "Linux":
    CJXL_PATH = f"{PROGRAM_FOLDER}/bin/linux/cjxl"
    DJXL_PATH = f"{PROGRAM_FOLDER}/bin/linux/djxl"
    IMAGE_MAGICK_PATH = f"{PROGRAM_FOLDER}/bin/win/magick"

# Proper usage is "if 'extension'.lower() in ALLOWED_INPUT:"
ALLOWED_INPUT_DJXL = ["jxl"]
ALLOWED_INPUT_CJXL = ["jpg","jpeg","jfif","png","gif"]
ALLOWED_INPUT_IMAGE_MAGICK = ["jpg","jpeg","jfif","png","gif"]
ALLOWED_INPUT = []

tmp = ALLOWED_INPUT_DJXL + ALLOWED_INPUT_CJXL + ALLOWED_INPUT_IMAGE_MAGICK
[ALLOWED_INPUT.append(n) for n in tmp if n not in ALLOWED_INPUT]    # Remove duplicates