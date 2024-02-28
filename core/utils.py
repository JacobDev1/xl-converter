import os
from pathlib import Path
from typing import List, Any

import qdarktheme

def scanDir(path):
    """Recursively scan a directory for files"""
    files = []
    for i in Path(path).rglob("*"):
        if os.path.isdir(i) == False:
            files.append(os.path.abspath(i))    # Convert POSIX path to str
    return files    # table

def setTheme(theme="dark"):
    match theme:
        case "dark":
            qdarktheme.setup_theme(corner_shape="sharp", custom_colors={"primary":"#F18000"})
        case "light":
            qdarktheme.setup_theme("light", corner_shape="sharp", custom_colors={"primary":"#EF7202"})

def removeDuplicates(data: List[Any]):
    new_data = []
    [new_data.append(n) for n in data if n not in new_data]
    return new_data

def listToFilter(title: str, ext: List[str]):
    """Convert a list of extensions into a name filter for file dialogs."""
    last_idx = len(ext) - 1

    output = f"{title} ("
    for i in range(last_idx):
        output += f"*.{ext[i]} "

    output += f"*.{ext[last_idx]})" # Last one (no space at the end)
    return output

def dictToList(data: dict):
    """Convert a dictionary into a list."""
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