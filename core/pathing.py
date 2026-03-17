import re
import os
import stat
from pathlib import Path
import logging
import string
from threading import Lock
import secrets
import platform

from core.exceptions import GenericException

class UniquePathStore():
    """Thread-safe class for storing already used paths to check for uniqueness."""
    _paths = set()
    _lock = Lock()

    @classmethod
    def add(cls, path: str) -> None:
        with cls._lock:
            cls._paths.add(path)

    @classmethod
    def exists(cls, path: str) -> bool:
        with cls._lock:
            return path in cls._paths

    @classmethod
    def clear(cls) -> None:
        with cls._lock:
            cls._paths = set()

def getUniqueFilePath(output_dir: str, file_name: str, file_ext: str) -> str:
    """
    Returns a unique file name path within a directory. Uses UniquePathStore to prevent non-unique combinations.
    
    Params:
        - output_dir - the directory where the file needs to be unique
        - file_name - the original name of the file
        - file_ext - the file extension (without dot)
    """

    path = os.path.join(output_dir,f"{file_name}.{file_ext}")

    prev = re.search(r"\([0-9]{1,}\)$", file_name)  	# Detect a previously renamed file
    n = int(prev.group(0)[1:-1]) if prev else 1			# Parse previously assigned number
    
    strip_p = prev and len(file_name) >= len(prev.group(0))                     # bool
    spacing = "" if strip_p else " "											# Add spacing to files without parenthesis
    new_file_name = file_name[:-len(prev.group(0))] if strip_p else file_name	# Strip parenthesis

    while os.path.isfile(path) or UniquePathStore.exists(path):
        path = os.path.join(output_dir, f"{new_file_name}{spacing}({n}).{file_ext}")
        n += 1

    UniquePathStore.add(path)
    return path

def getUniqueTmpFilePath(output_dir: str, file_ext: str) -> str:
    """"Returns a unique file name path within a directory. Uses UniquePathStore to prevent non-unique combinations."""
    def getPath(output_dir: str, file_ext: str):
        # secrets.token_hex(nbytes)
        # nbytes * 2 == sequence length
        # 16 ^ (2 * nbytes) == number of combinations
        return os.path.join(output_dir, f"tmp_{secrets.token_hex(4)}.{file_ext}")

    path = getPath(output_dir, file_ext)
    while os.path.isfile(path) or UniquePathStore.exists(path):
        path = getPath(output_dir, file_ext)
    
    return path

def getExtension(_format):
    """Get file extension for the specified format."""
    match _format :
        case "JPEG XL":
            return "jxl"
        case "PNG":
            return "png"
        case "AVIF":
            return "avif"
        case "WebP":
            return "webp"
        case "JPEG":
            return "jpg"
        case "Smallest Lossless":   # Handled in Worker
            return None
        case _:
            raise GenericException("PG0", f"No extension declared for {_format}")

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

def isANSICompatible(path: str) -> bool:
    try:
        path.encode("cp1252")
        return True
    except UnicodeEncodeError:
        return False

def removeFile(path: str, ignore_missing: bool = True) -> None:
    """Removes a single file. Ignores the Read-only attribute and non-existent files. Raises the same exceptions as `os.remove`."""
    if ignore_missing and not os.path.isfile(path):
        return
    try:
        os.remove(path)
    except PermissionError:
        if platform.system() == "Windows":
            # Clear Read-only and try again
            os.chmod(path, stat.S_IWRITE)
            os.remove(path)
        else:
            raise

def _pathCompareKey(path: str) -> str:
    try:
        normalized_path = str(Path(path).resolve(strict=False))
    except (OSError, RuntimeError):
        try:
            normalized_path = os.path.abspath(path)
        except OSError:
            normalized_path = str(path)

    return os.path.normcase(normalized_path)

# Replacement for os.path.samefile; more reliable on virtual drives on Windows.
# https://github.com/JacobDev1/xl-converter/issues/134
def isSamePath(path1: str, path2: str) -> bool:
    """Resolves and compares paths."""
    return _pathCompareKey(path1) == _pathCompareKey(path2)
