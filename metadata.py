import shutil, platform
from variables import (
    EXIFTOOL_PATH, EXIFTOOL_FOLDER_PATH, EXIFTOOL_BIN_NAME,
    IMAGE_MAGICK_PATH,
    CJXL_PATH,
    DJXL_PATH,
    JXLINFO_PATH,
    AVIFENC_PATH,
    AVIFDEC_PATH,
    OXIPNG_PATH
)
from process import runProcess, runProcessFromPath

def copyAttributes(src, dst):
    """Copy all attributes from one file onto another."""
    try:
        shutil.copystat(src, dst)
    except OSError as e:
        print(f"[Error] copystat failed ({e})")

def _runExifTool(args):
    """For internal use only."""
    if platform.system() == "Windows":
        runProcess(f'\"{EXIFTOOL_PATH}\" {args}')
    elif platform.system() == "Linux":  # Relative path needed for Brotli dependency to work on Linux
        runProcessFromPath(f'./{EXIFTOOL_BIN_NAME} {args}', EXIFTOOL_FOLDER_PATH)

def copyMetadata(src, dst):
    """Copy all metadata from one file onto another."""
    _runExifTool(f'-tagsfromfile \"{src}\" -overwrite_original \"{dst}\"')

def deleteMetadata(dst):
    """Delete all metadata except color profile from a file."""
    _runExifTool(f'-all= --icc_profile:all -tagsFromFile @ -ColorSpace -overwrite_original \"{dst}\"')

def deleteMetadataUnsafe(dst):
    """Deletes every last bit of metadata, even color profile. May mess up an image. Potentially desctructive."""
    _runExifTool(f'-all= -overwrite_original \"{dst}\"')

def runExifTool(src, dst, mode):
    """ExifTool wrapper."""
    match mode:
        case "ExifTool - Safe Wipe":
            deleteMetadata(dst)
        case "ExifTool - Preserve":
            copyMetadata(src, dst)
        case "ExifTool - Unsafe Wipe":
            deleteMetadataUnsafe(dst)

def getArgs(encoder, mode) -> []:
    """Return metadata arguments for the specified encoder.

    Example Usage:
        args = []
        args.extend(getArgs(encoder, mode))
    """
    match mode:
        case "Up to Encoder - Wipe":
            if encoder == CJXL_PATH:
                return []
                # The following is supposed to work, but doesn't. Encoder's source: https://github.com/libjxl/libjxl/blob/6f85806063394d0f32e6a112a37a259214bed4f1/tools/cjxl_main.cc
                # return ["-x strip=exif", "-x strip=xmp", "-x strip=jumbf"]    
                # return ["-x exif=", "-x xmp=", "-x jumbf="]
            elif encoder in (DJXL_PATH, AVIFDEC_PATH):
                return []
            elif encoder == IMAGE_MAGICK_PATH:
                return ["-strip"]
            elif encoder == AVIFENC_PATH:
                return  ["--ignore-exif", "--ignore-xmp"]
            elif encoder == OXIPNG_PATH:
                return ["--strip safe"]
            else:
                print(f"[Metadata - getArgs()] Unrecognized encoder ({encoder})")
        case "Up to Encoder - Preserve":
            return []   # Encoders preserve metadata by default
        case _:
            return []