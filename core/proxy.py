from data.constants import ALLOWED_INPUT_CJXL, ALLOWED_INPUT_AVIFENC, ALLOWED_INPUT_IMAGE_MAGICK
from core.utils import delete
from core.pathing import getUniqueFilePath
from core.convert import convert, getDecoder

import os

class Proxy():
    def __init__(self):
        self.proxy_path = None

    def isProxyNeeded(self, _format, src_ext, downscaling_enabled=False):
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
                if src_ext in ALLOWED_INPUT_IMAGE_MAGICK:
                    return False
            case "Smallest Lossless":
                return True
            case _:
                print(f"[Proxy - isProxyNeeded()] Uncredognized format ({src_ext})")
        
        return True

    def generate(self, src, src_ext, dst_dir, file_name, n):
        """Generate a proxy image."""
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
        """Deletes a proxy If one was generated"""
        if self.proxy_path != None:
            delete(self.proxy_path)
            self.proxy_path = None