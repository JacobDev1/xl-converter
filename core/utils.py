import shutil
import os
import logging
from pathlib import Path
from typing import List, Any

def scanDir(path: str) -> list:
    """Recursively scan a directory for files. Returns paths or raises FileNotFoundError If a directory was not found."""
    if not os.path.exists(path):
        raise FileNotFoundError(path)

    files = []
    for i in Path(path).rglob("*"):
        if os.path.isdir(i) == False:
            files.append(os.path.abspath(i))    # Convert POSIX path to str
    return files

def removeDuplicates(data: List[Any]):
    new_data = []
    [new_data.append(n) for n in data if n not in new_data]
    return new_data

def listToFilter(title: str, ext: List[str]):
    """Convert a list of extensions into a name filter for file dialogs."""
    if len(ext) == 0:
        return f"All Files (*)"
    
    last_idx = len(ext) - 1

    output = f"{title} ("
    for i in range(last_idx):
        output += f"*.{ext[i]} "

    output += f"*.{ext[last_idx]})" # Last one (no space at the end)
    return output

def dictToList(data: dict):
    """Convert a dictionary into a list of tuples."""
    result = []
    for k, v in data.items():
        if isinstance(v, dict):
            v = dictToList(v)
        result.append(
            (k, v)
        )
    return result

def clip(val, _min, _max):
    """Limit value to a given range."""
    if val > _max:
        return _max
    elif val < _min:
        return _min
    else:
        return val

def getFreeSpaceLeft(path: str) -> int:
    """Returns free space left on the device in bytes, or -1 if it cannot be determined."""
    try:
        total, used, free = shutil.disk_usage(path)
        return free
    except Exception as e:
        logging.error(f"[getFreeSpaceLeft] {e}")
        return -1