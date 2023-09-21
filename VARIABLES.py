import os, platform

VERSION = "0.9"
DEBUG = False    # More verbose output
CONFIG_LOCATION = ""    # Filled below

PROGRAM_FOLDER = os.path.dirname(os.path.realpath(__file__))

CJXL_PATH = "cjxl"
DJXL_PATH = "djxl"
IMAGE_MAGICK_PATH = "magick"
AVIFENC_PATH = "avifenc"
AVIFDEC_PATH = "avifdec"
OXIPNG_PATH = "oxipng"

# Proper usage is "if 'extension'.lower() in ALLOWED_INPUT:"
ALLOWED_INPUT_DJXL = ["jxl"]
ALLOWED_INPUT_CJXL = ["jpg","jpeg","jfif", "jif", "png","apng","gif"]
ALLOWED_INPUT_IMAGE_MAGICK = ["jpg","jpeg","jfif", "jif", "png","gif", "heif", "heifs", "heic", "heics", "avci", "avcs", "hif", "webp","tiff","jp2","bmp", "ico"]     # Before adding more, make sure the included ImageMagick works with it. Some formats (like FLIF) seem not to have been included
ALLOWED_INPUT_AVIFENC = ["jpg","jpeg","jfif", "jif", "png"]
ALLOWED_INPUT_AVIFDEC = ["avif"]
ALLOWED_INPUT_OXIPNG = ["png"]
ALLOWED_INPUT = []
ALLOWED_RESAMPLING = ("Point", "Cubic", "Hermite", "Box", "Gaussian", "Catrom", "Triangle", "Quadratic", "Mitchell", "CubicSpline", "Lanczos", "Hamming", "Parzen", "Blackman", "Kaiser", "Welsh", "Hanning", "Bartlett", "Bohman")

JPEG_ALIASES = ["jpg","jpeg","jfif", "jif"] # Used by CJXL, before adding more verify support

if platform.system() == "Windows":
    CJXL_PATH = os.path.join(PROGRAM_FOLDER,"bin/win/cjxl.exe")
    DJXL_PATH = os.path.join(PROGRAM_FOLDER,"bin/win/djxl.exe")
    IMAGE_MAGICK_PATH = os.path.join(PROGRAM_FOLDER,"bin/win/magick.exe")
    AVIFENC_PATH = os.path.join(PROGRAM_FOLDER,"bin/win/avifenc.exe")
    AVIFDEC_PATH = os.path.join(PROGRAM_FOLDER,"bin/win/avifdec.exe")
    OXIPNG_PATH = os.path.join(PROGRAM_FOLDER,"bin/win/oxipng.exe")

    CONFIG_LOCATION = os.path.normpath(os.path.expanduser("~/AppData/Local/xl-converter"))
elif platform.system() == "Linux":
    CJXL_PATH = f"{PROGRAM_FOLDER}/bin/linux/cjxl"
    DJXL_PATH = f"{PROGRAM_FOLDER}/bin/linux/djxl"
    IMAGE_MAGICK_PATH = f"{PROGRAM_FOLDER}/bin/linux/magick"
    AVIFENC_PATH = f"{PROGRAM_FOLDER}/bin/linux/avifenc"
    AVIFDEC_PATH = f"{PROGRAM_FOLDER}/bin/linux/avifdec"
    OXIPNG_PATH = f"{PROGRAM_FOLDER}/bin/linux/oxipng"

    CONFIG_LOCATION = os.path.expanduser('~/.config/xl-converter')

tmp = ALLOWED_INPUT_DJXL + ALLOWED_INPUT_CJXL + ALLOWED_INPUT_IMAGE_MAGICK + ALLOWED_INPUT_AVIFENC + ALLOWED_INPUT_AVIFDEC + ALLOWED_INPUT_OXIPNG
[ALLOWED_INPUT.append(n) for n in tmp if n not in ALLOWED_INPUT]    # Remove duplicates