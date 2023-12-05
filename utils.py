import os, re, platform
from pathlib import Path

import qdarktheme
from send2trash import send2trash

def delete(path, trash=False):
    """Delete a file (or move to trash)."""
    try:
        if trash:
            send2trash(path)
        else:
            os.remove(path)
    except OSError as err:
        print(f"[Error] Failed to delete the file ({path})\n{err}")
        return False
    return True

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

def removeDuplicates(data: []):
    new_data = []
    [new_data.append(n) for n in data if n not in new_data]
    return new_data

def listToFilter(title: str, ext: []):
    """Convert a list of extensions into a name filter for file dialogs."""
    last_idx = len(ext) - 1

    output = f"{title} ("
    for i in range(last_idx):
        output += f"*.{ext[i]} "

    output += f"*.{ext[last_idx]})" # Last one (no space at the end)
    return output

def clip(val, _min, _max):
    """Limit value to a given range."""
    if val > _max:
        return _max
    elif val < _min:
        return _min
    else:
        return val