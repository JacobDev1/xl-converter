import os
import logging
import re

from PySide6.QtCore import (
    QMutexLocker,
)

from data.constants import (
    ALLOWED_INPUT_CJXL,
    ALLOWED_INPUT_CJPEGLI,
    ALLOWED_INPUT_AVIFENC,
    ALLOWED_INPUT_IMAGE_MAGICK,
    IMAGE_MAGICK_PATH,
)
from core.pathing import getUniqueFilePath
from core.convert import convert, getDecoder
from core.process import runProcessOutput
from core.exceptions import FileException

class Proxy():
    def __init__(self):
        self.proxy_path = None

    def isProxyNeeded(self, _format, src_ext, jpegli=False, downscaling_enabled=False):
        if _format == "PNG":
            return False

        if downscaling_enabled:
            if src_ext in ALLOWED_INPUT_IMAGE_MAGICK:
                return False
            else:
                return True

        match _format:
            case "JPEG XL":
                if src_ext in ALLOWED_INPUT_CJXL:
                    return False          
            case "AVIF":
                if src_ext in ALLOWED_INPUT_AVIFENC:
                    return False
            case "WEBP":
                if src_ext in ALLOWED_INPUT_IMAGE_MAGICK:
                    return False
            case "JPG":
                if jpegli:
                    if src_ext in ALLOWED_INPUT_CJPEGLI:
                        return False
                else:
                    if src_ext in ALLOWED_INPUT_IMAGE_MAGICK:
                        return False
            case "Smallest Lossless":
                return True
            case _:
                logging.error(f"[Proxy] Unrecognized format ({src_ext})")
        
        return True

    def generate(self, src, src_ext, dst_dir, file_name, n, mutex):
        """Generate a proxy image."""
        if src_ext in ("tif", "tiff"):
            try:
                layers_re = re.search(r"\d+", runProcessOutput(IMAGE_MAGICK_PATH, "identify", "-format", "%n\n", src).decode("utf-8"))
                layers_n = int(layers_re.group(0))
            except Exception:
                raise FileException("Proxy_0", "Cannot detect the number of pages.")

            if layers_n != 1:
                raise FileException("Proxy_1", "TIFFs with multiple pages are not supported.")
        
        with QMutexLocker(mutex):
            self.proxy_path = getUniqueFilePath(dst_dir, file_name, "png", True)
    
        convert(getDecoder(src_ext), src, self.proxy_path, [], n)

        if not os.path.isfile(self.proxy_path):
            return False
        
        return True

    def getPath(self):
        return self.proxy_path
    
    def proxyExists(self):
        if self.proxy_path == None:
            return False
        else:
            return True

    def cleanup(self):
        """Delete a proxy If one exists."""
        if self.proxy_path != None:
            os.remove(self.proxy_path)
        self.proxy_path = None