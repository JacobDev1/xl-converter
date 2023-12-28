import os
from data.constants import (
    ALLOWED_INPUT_IMAGE_MAGICK,
    IMAGE_MAGICK_PATH,
    AVIFDEC_PATH,
    DJXL_PATH,
    JXLINFO_PATH,
    CONVERT_LOGS
)
from core.process import runProcess, runProcessOutput

def convert(encoder_path, src, dst, args = [], n = None):
    """Universal method for all encoders."""
    runProcess(encoder_path, src, *parseArgs(args), dst)
    if n != None:   log((encoder_path, src, *parseArgs(args), dst), n)

def optimize(bin_path, src, args = [], n = None):
    """Run a binary targeting a source."""
    runProcess(bin_path, *parseArgs(args), src)
    if n != None:   log((bin_path, *parseArgs(args), src), n)

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

def getDecoder(ext):
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
                print(f"[Convert - getDecoder()] Decoder for {ext} was not found")
                return None

def leaveOnlySmallestFile(paths: [], new_path):
    """Delete all except the smallest file."""
    
    # Probe files
    sizes = []
    try:
        for i in paths:
            sizes.append(os.path.getsize(i))
    except OSError as err:
        log("[Convert - leaveOnlySmallestFile()] Getting file size failed")
        for i in paths:
            try:
                os.remove(i)
            except OSError as err:
                log("[Convert - leaveOnlySmallestFile()] Deleting file failed")
        return

    # Detect smallest
    smallest_format_index = 0
    item_count = len(paths)
    for i in range(1, item_count):
        if sizes[i] < sizes[smallest_format_index]:
            smallest_format_index = i
    
    # Clean up and rename
    for i in range(item_count):
        if i != smallest_format_index:
            try:
                os.remove(paths[i])
            except OSError as e:
                log("[Convert - leaveOnlySmallestFile()] Deleting file failed")
        else:
            if paths[i] != new_path:
                os.rename(paths[i], new_path)

def log(msg, n = None):
    if not CONVERT_LOGS:
        return
    
    if n == None:
        print(msg)
    else:
        print(f"[Worker #{n}] {msg}")