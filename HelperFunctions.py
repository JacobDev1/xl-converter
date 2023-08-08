import os, re, platform
from pathlib import Path

def stripPathToFilename(path):                              # D:/images/image.png
    """Dissect an absolute path into file name, extension and its directory"""
    fp_split = re.split(r"\\|/", path)
    f_name_split = fp_split[len(fp_split)-1].split(".")     # directory/[file.jxl]
    f_name = ".".join(f_name_split[:-1])        # picture
    f_ext = f_name_split[len(f_name_split)-1]   # .jxl
    f_dir = "/".join(fp_split[:-1])             # D:/Images
    abs_path = path                             # D:/Images/picture.jxl
    if platform.system() == "Windows":
        abs_path = abs_path.replace('/','\\')   # Required for deleting files on Windows to work
        f_dir = f_dir.replace('/','\\')
    return (f_name,f_ext, f_dir, abs_path)

def scanDir(path):
    """Recursively scan a directory for files"""
    files = []
    for i in Path(path).rglob("*"):
        if os.path.isdir(i) == False:
            files.append(os.path.abspath(i))    # Convert POSIX path to str
    return files    # table