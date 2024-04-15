from core.exceptions import GenericException

def checkForConflicts(ext: str, file_format: str, downscaling=False) -> bool:
    """
    Raises exceptions and returns True If any conflicts occur. 
    
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
                if file_format in ("JPEG XL", "WEBP", "PNG"):
                    conflict = False
            case "apng":
                if file_format in ("JPEG XL"):
                    conflict = False
        
        if conflict:
            raise GenericException("CF0", f"Animation is not supported for {ext.upper()} -> {file_format}")

        # Downscaling
        if downscaling:
            conflict = True
            raise GenericException("CF1", f"Downscaling is not supported for animation")
    else:
        conflict = False
    
    return conflict