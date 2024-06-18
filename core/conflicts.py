import re

from data.constants import (
    IMAGE_MAGICK_PATH,
)
from core.process import runProcessOutput
from core.exceptions import GenericException, FileException

def checkForConflicts(ext: str, file_format: str, downscaling=False) -> None:
    """
    Checks for conflicts with animated images. Raises exceptions and returns True If any conflicts occur. 
    
    Args:
    - ext - extension (without a dot in the beginning and lowercase)
    - file_format - target format (uppercase)
    - downscaling - is downscaling on
    """
    if ext in ("gif", "apng"):
        conflict = True

        # Animation
        match ext:
            case "gif":
                if file_format in ("JPEG XL", "WebP"):
                    conflict = False
            case "apng":
                if file_format in ("JPEG XL"):
                    conflict = False
        
        if conflict:
            raise GenericException("CF0", f"{ext.upper()} -> {file_format} conversion is not supported")

        # Downscaling
        if downscaling:
            raise GenericException("CF1", f"Downscaling is not supported for animation")

def checkForMultipage(src_ext: str, src_abs_path: str) -> None:
    """Raises an exception if an image is multipage."""
    if src_ext in ("tif", "tiff", "heif", "heic"):
        try:
            layers_re = re.search(r"\d+", runProcessOutput(IMAGE_MAGICK_PATH, "identify", "-format", "%n\n", src_abs_path).decode("utf-8"))
            layers_n = int(layers_re.group(0))
        except Exception:
            raise FileException("CF2", "Cannot detect the number of pages.")

        if layers_n != 1:
            raise FileException("CF3", "Multipage images are not supported.")