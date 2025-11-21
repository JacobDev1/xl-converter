import logging
from typing import Literal
import re
import os

from data.constants import (
    ALLOWED_INPUT_IMAGE_MAGICK,
    IMAGE_MAGICK_PATH,
    AVIFDEC_PATH,
    DJXL_PATH,
    JXLINFO_PATH,
    AVIFENC_PATH,
    JPEGTRAN_PATH,
)
from core.process import runProcess2
from core.exceptions import GenericException, CancellationException
import data.task_status as task_status

logger = logging.getLogger(__name__)

def runBinary(
    bin_path: str,
    args: list[str],
    src_path: str,
    dst_path: str | None = None,
    args_after_input: bool = False,
    delete_if_canceled: list[str] = [],
) -> (str, str):
    """A universal method for running binaries.

    Args:
        bin_path: the absolute path to the binary
        args: a list of str argument
        src_path: the absolute path to the source file
        dst_path: an absolute path to the destination file
        args_after_input: insert args after input instead of before
        delete_if_canceled: a list of files to delete if a task is canceled
    
    Returns:
        (stdout, stderr)

    Raises:
        CancellationException: if task_status is canceled
    """
    cmd = [bin_path]
    if args_after_input:
        cmd.extend([src_path, *parseArgs(args)])
    else:
        cmd.extend([*parseArgs(args), src_path])

    if dst_path is not None:
        cmd.append(dst_path)

    stdout, stderr = runProcess2(*cmd)

    if task_status.wasCanceled():
        for file in delete_if_canceled:
            if not os.path.isfile(file):
                continue
            
            try:
                os.remove(file)
            except OSError as e:
                logging.error(f"[runBinary] Failed to remove tmp file. {e}")
        raise CancellationException()

    return (stdout, stderr)

def runJPEGtran(
    args: list[str],
    src_path: str,
    dst_path: str,
) -> (str, str):
    """Runs jpegtran.

    Args:
        args: a list of str argument
        src_path: source path. Needs to be a JPEG image.
        dst_path: output path. Should have a .jpg extension
    
    Returns:
        (stdout, stderr)

    Raises:
        CancellationException: if task_status is canceled
    """
    stdout, stderr = runProcess2(JPEGTRAN_PATH, *parseArgs(args), "-outfile", dst_path, src_path)

    if task_status.wasCanceled():
        raise CancellationException()

    return (stdout, stderr)

def getExtensionJxl(src_path: str) -> Literal["jpg", "png"]:
    """Assign extension based on If JPEG reconstruction data is available. Only use If src format is jxl."""
    if "JPEG bitstream reconstruction data available" in runProcess2(JXLINFO_PATH, src_path)[0]:
        return "jpg"
    else:
        return "png"

def parseArgs(args):
    """Splits arguments by spaces and flattens them into a list."""
    tmp = []
    for arg in args:
        tmp.extend(arg.split())
    return tmp

def getDecoder(ext: str) -> str:
    """Return appropriate decoder path for the specified extension."""
    ext = ext.lower()   # Safeguard in case of a mistake

    match ext:
        case "png":
            return IMAGE_MAGICK_PATH
        case "jxl":
            return DJXL_PATH
        case "avif":
            return AVIFDEC_PATH
        case _:
            if ext in ALLOWED_INPUT_IMAGE_MAGICK:
                return IMAGE_MAGICK_PATH
            else:
                raise GenericException("C4", f"Decoder for {ext} was not found")

def getDecoderArgs(decoder_path: str, threads: int) -> list:
    if decoder_path == AVIFDEC_PATH:
        return [f"-j {threads}"]
    elif decoder_path == DJXL_PATH:
        return [f"--num_threads={threads}"]
    else:
        return []

def getImageRes(image_path: str) -> (int, int):
    """Returns resolution of an image or (-1, -1) if one cannot be determined."""
    out, err = runBinary(
        IMAGE_MAGICK_PATH,
        ["identify", "-ping", "-format", "%[page]"],
        f"{image_path}[0]",
    )
    res_match = re.match(r"^(\d+)x(\d+)(?=\D|$)", out)

    if not res_match:
        logging.error(f"[getImageResMp] Cannot determine resolution. {err}")
        return (-1, -1)

    try:
        width = int(res_match.group(1))
        height = int(res_match.group(2))
    except (AttributeError, ValueError):
        logging.error(f"[getImageResMp] Failed to parse resolution. {out}")
        return (-1, -1)

    if min(width, height) < 1:
        logging.error(f"[getImageResMp] Cannot determine resolution. {err}")
        return (-1, -1)

    return (width, height)

def getImageResMp(image_path: str) -> float:
    """Returns resolution of an image or -1 if one cannot be determined. This is a wrapper around getImageRes."""
    width, height = getImageRes(image_path)

    if min(width, height) < 1:  # Prevent div by zero
        return -1
    else:
        return width * height / 1_000_000

def getImageCount(image_path: str) -> (int, str):
    """Returns image count (frame or page count) and stderr. If it cannot be determined, returns -1."""
    out, err = runBinary(
        IMAGE_MAGICK_PATH,
        ["identify", "-ping", "-format", "%n\n"],
        image_path    # Do not specify index (e.g. image.webp[0]). Otherwise, it will return 1 regardless of page count.
    )
    pages_m = re.search(r"\d+", out)
    if not pages_m:
        logger.error(f"[getImageCount] Cannot determine image count. {err}")
        return (-1, err)
    
    try:
        pages_int = int(pages_m.group(0))
    except (ValueError, AttributeError) as e:
        logger.error(f"[getImageCount] Parsing failed. {e}")
        return (-1, err)
    
    return (pages_int, err)

def cleanUp(file_paths: list[str]) -> None:
    """Deletes file(s). Does not raise an exception."""
    for file_path in file_paths:
        if not os.path.isfile(file_path):
            continue
        
        try:
            os.remove(file_path)
        except OSError as e:
            logging.error(f"[cleanUp] Failed to remove a file. {e}")
