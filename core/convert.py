import logging

from data.constants import (
    ALLOWED_INPUT_IMAGE_MAGICK,
    IMAGE_MAGICK_PATH,
    AVIFDEC_PATH,
    DJXL_PATH,
    JXLINFO_PATH,
    AVIFENC_PATH
)
from core.process import runProcess, runProcessOutput
from core.exceptions import GenericException

def convert(encoder_path, src, dst, args = [], n = None):
    """Universal method for all encoders."""
    cmd = []
    if encoder_path == AVIFENC_PATH:
        cmd = (encoder_path, *parseArgs(args), src, dst)
    else:
        cmd = (encoder_path, src, *parseArgs(args), dst)
    
    runProcess(*cmd)
    
    if n != None:
        log(cmd, n)

def optimize(bin_path, src, args = [], n = None):
    """Run a binary targeting a source."""
    runProcess(bin_path, *parseArgs(args), src)
    if n != None:
        log((bin_path, *parseArgs(args), src), n)

def getExtensionJxl(src_path):
    """Assign extension based on If JPEG reconstruction data is available. Only use If src format is jxl."""
    if b"JPEG bitstream reconstruction data available" in runProcessOutput(JXLINFO_PATH, src_path):
        return "jpg"
    else:
        return "png"

def parseArgs(args):
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

def log(msg, n = None):
    if n == None:
        logging.info(f"[Convert] {msg}")
    else:
        logging.info(f"[Worker #{n} - Convert] {msg}")