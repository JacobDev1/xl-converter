from core.exceptions import GenericException

def checkForConflicts(ext: str, _format: str, downscaling: dict) -> bool:
    """Raises exceptions and returns True If any conflicts occur."""
    if ext in ("gif", "apng"):
        conflict = True

        # Animation
        match ext:
            case "gif":
                if _format in ("JPEG XL", "WEBP", "PNG"):
                    conflict = False
            case "apng":
                if _format in ("JPEG XL"):
                    conflict = False
        
        if conflict:
            raise GenericException("cf.", f"Animation is not supported for {_format} - stopped the process")

        # Downscaling
        if downscaling:
            conflict = True
            raise GenericException("cf.", f"Downscaling is not supported for animation - stopped the process")
    else:
        conflict = False
    
    return conflict