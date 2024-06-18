import os
import logging

from PySide6.QtCore import (
    QMutexLocker,
    QMutex,
)

from data.constants import (
    ALLOWED_INPUT_CJXL,
    ALLOWED_INPUT_CJPEGLI,
    ALLOWED_INPUT_AVIFENC,
    ALLOWED_INPUT_IMAGE_MAGICK,
)
from core.pathing import getUniqueFilePath
from core.convert import convert, getDecoder
from core.exceptions import FileException

class Proxy():
    def __init__(self):
        self.proxy_path = None

    def isProxyNeeded(self, _format: str, src_ext: str, jpegli: bool = False, downscaling_enabled: bool = False) -> bool:
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
            case "WebP":
                if src_ext in ALLOWED_INPUT_IMAGE_MAGICK:
                    return False
            case "JPEG":
                if jpegli:
                    if src_ext in ALLOWED_INPUT_CJPEGLI:
                        return False
                else:
                    if src_ext in ALLOWED_INPUT_IMAGE_MAGICK:
                        return False
            case "Smallest Lossless":
                return True
            case "Lossless JPEG Recompression":
                return False
            case "JPEG Reconstruction":
                return False
            case _:
                raise FileException("Proxy0", f"Unrecognized format ({src_ext})")
        
        return True

    def generate(self, src: str, src_ext: str, dst_dir: str, file_name: str, n: int, mutex: QMutex) -> str:
        """Generate a proxy image."""
        with QMutexLocker(mutex):
            self.proxy_path = getUniqueFilePath(dst_dir, file_name, "png", True)
    
        convert(getDecoder(src_ext), src, self.proxy_path, [], n)

        if not os.path.isfile(self.proxy_path):
            raise FileException("Proxy1", f"Generating proxy failed. Output not found.")
        
        return self.proxy_path

    def getPath(self) -> str | None:
        return self.proxy_path
    
    def proxyExists(self) -> bool:
        return self.proxy_path is not None

    def cleanup(self) -> None:
        """Delete a proxy If one exists."""
        if self.proxy_path is not None:
            try:
                os.remove(self.proxy_path)
            except OSError as e:
                raise FileException("Proxy2", f"Failed to clean up proxy. {e}")
        self.proxy_path = None