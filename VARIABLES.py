import os, platform

PROGRAM_FOLDER = os.path.dirname(os.path.realpath(__file__))

CJXL_PATH = "cjxl"
DJXL_PATH = "djxl"
# MOZJPG_PATH = "mozjpeg"
# AVIF_PATH = ""
# CWEBP_PATH = ""
# DWEBP_PATH = ""

if platform.system() == "Windows":
    CJXL_PATH = os.path.abspath(os.path.join(PROGRAM_FOLDER,"bin/win/cjxl.exe"))
    DJXL_PATH = os.path.abspath(os.path.join(PROGRAM_FOLDER,"bin/win/djxl.exe"))
elif platform.system() == "Linux":
    CJXL_PATH = f"{PROGRAM_FOLDER}/bin/linux/cjxl"
    DJXL_PATH = f"{PROGRAM_FOLDER}/bin/linux/djxl"

# Proper usage is "if 'extension'.lower() in ALLOWED_INPUT:"
ALLOWED_INPUT_DJXL = ["jxl"]
ALLOWED_INPUT_CJXL = ["jpg","jpeg","jfif","png","gif"]
ALLOWED_INPUT = ALLOWED_INPUT_DJXL + ALLOWED_INPUT_CJXL