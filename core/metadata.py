import platform
import tempfile
import os
import logging
import shutil

from data.constants import (
    EXIFTOOL_PATH,
    IMAGE_MAGICK_PATH,
    CJXL_PATH,
    AVIFENC_PATH,
    OXIPNG_PATH
)
from core.process import runProcess2
from core.exceptions import GenericException, FileException

class Data:
    exiftool_available: None | bool = None   # None - unchecked; False - not available; True - available;
    exiftool_err_msg: str = ""

def runExifTool(src: str, dst: str, et_args: list[str]) -> None:
    """Runs ExifTool.

    Args:
        src: str - absolute path to source
        dst: str - absolute path to destination
        et_args: list[str] - ExifTool arguments

    Example:
        runExifTool(
            "/path/to/src.jpg",
            "/path/to/dst.jxl",
            ["-all=", "-overwrite_original", "$dst"],
        )
    """
    # Prepare args
    cmd = et_args
    for idx, val in enumerate(cmd):
        match val:
            case "$src":
                cmd[idx] = src
            case "$dst":
                cmd[idx] = dst
    
    # Run
    _runExifTool(*cmd)

def _runExifTool(*args):
    """For internal use only."""
    match platform.system():
        case "Windows":
            try:
                with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", delete=False, suffix=".txt") as tmp_file:
                    tmp_file_path = tmp_file.name
                    tmp_file_name = os.path.basename(tmp_file_path)
                    tmp_file_dir = os.path.dirname(tmp_file_path)

                    tmp_file.write("\n".join(args))
            except Exception as e:
                raise FileException("M0", f"Failed to create an argfile. {e}")
            
            runProcess2(EXIFTOOL_PATH, "-charset", "filename=UTF8", "-@", tmp_file_name, cwd=tmp_file_dir)

            try:
                os.unlink(tmp_file_path)
            except Exception as e:
                raise FileException("M1", f"Failed to clean up an argfile. {e}")
            # ExifTool does not support UTF-8 paths on Windows, unless you put them in an argfile.
        case "Linux":
            runProcess2("exiftool", *args)
        case "Darwin":
            runProcess2(EXIFTOOL_PATH, *args)
        case _:
            logging.error("[metadata - _runExifTool] Not implemented")

def isExifToolAvailable() -> tuple[bool, str]:
    """Checks if ExifTool is available and caches the result.

    Returns:
        tuple[bool, str]: (is_available, error_msg)
    """
    if Data.exiftool_available is not None:
        return (Data.exiftool_available, Data.exiftool_err_msg)

    match platform.system():
        case "Linux":
            Data.exiftool_available = shutil.which("exiftool") is not None
            if Data.exiftool_available == False:
                Data.exiftool_err_msg = "ExifTool not found. Please install ExifTool on your system and restart the program."
        case "Windows":
            proc_output = runProcess2(EXIFTOOL_PATH, "-ver")
            if proc_output[0].strip() == "" or "assertion failed" in proc_output[1]:
                Data.exiftool_available = False
                Data.exiftool_err_msg = "Please reinstall this program in a location without special characters to use ExifTool."
            else:
                Data.exiftool_available = True
        case _:     # Darwin
            Data.exiftool_available = True
   
    return (Data.exiftool_available, Data.exiftool_err_msg)
        
def getArgs(encoder, mode, jpg_to_jxl_lossless=False) -> list[str]:
    """Return metadata arguments for the specified encoder.

    Example Usage:
        args = []
        args.extend(getArgs(encoder, mode))
    """
    match mode:
        case "Encoder - Wipe":
            if encoder == CJXL_PATH:
                if not jpg_to_jxl_lossless:
                    return ["-x strip=exif", "-x strip=xmp", "-x strip=jumbf"]    
                else:
                    return []
            elif encoder == IMAGE_MAGICK_PATH:
                return ["-strip"]
            elif encoder == AVIFENC_PATH:
                return  ["--ignore-exif", "--ignore-xmp"]
            else:
                return []   # DJXL, CJPEGLI, AVIFDEC - unavailable or undocumented
        case "Encoder - Preserve":
            return []   # Encoders preserve metadata by default
        case _:
            return []
