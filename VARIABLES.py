import os, platform

PROGRAM_FOLDER = os.path.dirname(os.path.realpath(__file__))

CJXL_PATH = "cjxl"
DJXL_PATH = "djxl"
IMAGE_MAGICK_PATH = "magick"
AVIFENC_PATH = "avifenc"
AVIFDEC_PATH = "avifdec"
OXIPNG_PATH = "oxipng"

# Proper usage is "if 'extension'.lower() in ALLOWED_INPUT:"
ALLOWED_INPUT_DJXL = ["jxl"]
ALLOWED_INPUT_CJXL = ["jpg","jpeg","jfif","png","gif"]
ALLOWED_INPUT_IMAGE_MAGICK = ["jpg","jpeg","jfif","png","gif","avif", "heif", "heifs", "heic", "heics", "avci", "avcs", "hif", "webp","tiff","jp2","bmp"]     # Before adding more, make sure the included ImageMagick works with it. Some formats (like FLIF) seem not to have been included
ALLOWED_INPUT_AVIFENC = ["jpg","jpeg","png"]
ALLOWED_INPUT_AVIFDEC = ["avif"]
ALLOWED_INPUT_OXIPNG = ["png"]
ALLOWED_INPUT = []

if platform.system() == "Windows":
    CJXL_PATH = os.path.abspath(os.path.join(PROGRAM_FOLDER,"bin/win/cjxl.exe"))
    DJXL_PATH = os.path.abspath(os.path.join(PROGRAM_FOLDER,"bin/win/djxl.exe"))
    IMAGE_MAGICK_PATH = os.path.abspath(os.path.join(PROGRAM_FOLDER,"bin/win/magick.exe"))
    AVIFENC_PATH = os.path.abspath(os.path.join(PROGRAM_FOLDER,"bin/win/avifenc.exe"))
    AVIFDEC_PATH = os.path.abspath(os.path.join(PROGRAM_FOLDER,"bin/win/avifdec.exe"))
    OXIPNG_PATH = os.path.abspath(os.path.join(PROGRAM_FOLDER,"bin/win/oxipng.exe"))
elif platform.system() == "Linux":
    CJXL_PATH = f"{PROGRAM_FOLDER}/bin/linux/cjxl"
    DJXL_PATH = f"{PROGRAM_FOLDER}/bin/linux/djxl"
    IMAGE_MAGICK_PATH = f"{PROGRAM_FOLDER}/bin/linux/magick"
    AVIFENC_PATH = f"{PROGRAM_FOLDER}/bin/linux/avifenc"
    AVIFDEC_PATH = f"{PROGRAM_FOLDER}/bin/linux/avifdec"
    OXIPNG_PATH = f"{PROGRAM_FOLDER}/bin/linux/oxipng"

tmp = ALLOWED_INPUT_DJXL + ALLOWED_INPUT_CJXL + ALLOWED_INPUT_IMAGE_MAGICK + ALLOWED_INPUT_AVIFENC + ALLOWED_INPUT_AVIFDEC + ALLOWED_INPUT_OXIPNG
[ALLOWED_INPUT.append(n) for n in tmp if n not in ALLOWED_INPUT]    # Remove duplicates