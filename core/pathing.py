import re
import random
import os
from pathlib import Path

def stripPathToFilename(path):
    """Dissect path into its parts.
    
    argument:
        path - D:/images/image.png
    returns:
        0 - image
        1 - png
        2 - D:/images
        3 - D:/images/image.png
    """
    f_dir = os.path.split(path)[0]
    f_name = Path(path).stem
    f_ext = Path(path).suffix

    return (f_name, f_ext[1:], f_dir, os.path.abspath(path))

def getUniqueFilePath(dir, file_name: str, ext: str, add_rnd = False):
    """Get a unique file name within a directory."""

    rnd_str = "_" + "".join(random.choice("0123456789abcdef") for _ in range(3)) if add_rnd else ""     # hex
    path = os.path.join(dir,f"{file_name}{rnd_str}.{ext}")

    prev = re.search(r"\([0-9]{1,}\)$", file_name)  	# Detect a previously renamed file
    n = int(prev.group(0)[1:-1]) if prev else 1			# Parse previously assigned number
    
    strip_p = prev and len(file_name) >= len(prev.group(0))                     # bool
    spacing = "" if strip_p else " "											# Add spacing to files without parenthesis
    new_file_name = file_name[:-len(prev.group(0))] if strip_p else file_name	# Strip parenthesis

    while os.path.isfile(path):
        path = os.path.join(dir,f"{new_file_name}{spacing}({n}){rnd_str}.{ext}")
        n += 1

    return path

def getPathGIF(output_dir, item_name, mode):
    """Single-purpose method for decoding GIF to PNG with ImageMagick."""
    new_path = os.path.join(output_dir, f"{item_name}.png")
    match mode:
        case "Rename":
            if os.path.isfile(os.path.join(output_dir, f"{item_name}-0.png")):
                n = 0
                while os.path.isfile(os.path.join(output_dir, f"{item_name} ({n})-0.png")):
                    n += 1
                new_path = os.path.join(output_dir, f"{item_name} ({n}).png")
            return new_path
        case "Replace":
            return new_path

def getExtension(_format):
    """Get file extension for the specified format."""
    match _format :
        case "JPEG XL":
            return "jxl"
        case "PNG":
            return "png"
        case "AVIF":
            return "avif"
        case "WEBP":
            return "webp"
        case "JPG":
            return "jpg"
        case "Smallest Lossless":   # Handled in Worker
            return None
        case _:
            print(f"[Pathing - getExtension()] No extension declared for {_format}")
