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
from core.pathing import getUniqueTmpFilePath
from core.convert import getDecoder, runBinary
from core.exceptions import FileException

logger = logging.getLogger(__name__)

class Proxy():
    def __init__(self):
        self.proxy_path = None

    def isProxyNeeded(self, file_format: str, src_ext: str, jpegli: bool = False, downscaling_enabled: bool = False) -> bool:
        if file_format == "Smallest Lossless":
            return True

        if file_format == "PNG":
            return False

        if downscaling_enabled:
            if src_ext in ALLOWED_INPUT_IMAGE_MAGICK:
                return False
            else:
                return True

        match file_format:
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
            case "Lossless JPEG Transcoding":
                return False
            case "JPEG Reconstruction":
                return False
            case "PNG Optimization":
                return False
            case _:
                raise FileException("Proxy0", f"Unrecognized format ({file_format})")
        
        return True

    def generate(self, src: str, src_ext: str, dst_dir: str, file_name: str, n: int, mutex: QMutex) -> str:
        """Generate a proxy image. Can raise CancellationException and FileException."""
        with QMutexLocker(mutex):
            self.proxy_path = getUniqueTmpFilePath(dst_dir, "png")
    
        stdout, stderr = runBinary(
            getDecoder(src_ext),
            [],
            src,
            self.proxy_path,
            delete_if_canceled=[self.proxy_path]
        )

        if not os.path.isfile(self.proxy_path):
            raise FileException("Proxy1", f"Generating proxy failed. {stderr}")
        
        return self.proxy_path

    def getPath(self) -> str | None:
        return self.proxy_path
    
    def proxyExists(self) -> bool:
        return self.proxy_path is not None

    def cleanUp(self, raising: bool = True) -> None:
        """Delete a proxy If one exists."""
        if self.proxy_path is None:
            return

        try:
            if os.path.isfile(self.proxy_path):     # In case path was assigned but no output was generated.
                os.remove(self.proxy_path)
        except OSError as e:
            if raising:
                raise FileException("Proxy2", f"Failed to clean up proxy. {e}")
            else:
                logger.error(f"Failed to clean up proxy. {e}")
        finally:
            self.proxy_path = None
