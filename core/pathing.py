import re
import random
import os
from pathlib import Path
import logging

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
            logging.error(f"[Pathing - getExtension()] No extension declared for {_format}")

def getOutputDir(
        item_dir_path: str,
        item_anchor_path: Path,
        custom_dir: bool,
        custom_dir_path: str,
        keep_dir_struct: bool
    ) -> str:
    """Used in Worker exclusively. Returns output directory. Does not create any dirs on its own."""
    if custom_dir:
        custom_dir_path = str(Path(custom_dir_path))

        if keep_dir_struct:
            try:
                rel_path = Path(item_dir_path).relative_to(item_anchor_path)
                return os.path.join(custom_dir_path, rel_path)
            except Exception as e:
                logging.error(f"[Pathing] Failed to calculate relative path. {e}")
                return custom_dir_path
        else:
            if os.path.isabs(custom_dir_path):  # absolute
                return custom_dir_path
            else:                               # relative
                return os.path.join(item_dir_path, custom_dir_path)
    else:
        return item_dir_path