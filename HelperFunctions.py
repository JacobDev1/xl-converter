import os, re, platform
from pathlib import Path

def stripPathToFilename(path):                              # D:/images/image.png
    """Dissect an absolute path into file name, extension and its directory"""
    fp_split = re.split(r"\\|/", path)
    f_name_split = fp_split[len(fp_split)-1].split(".")     # directory/[file.jxl]
    f_name = ".".join(f_name_split[:-1])        # 0 - picture
    f_ext = f_name_split[len(f_name_split)-1]   # 1 - .jxl
    f_dir = "/".join(fp_split[:-1])             # 2 - D:/Images
    abs_path = path                             # 3 - D:/Images/picture.jxl
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

def burstThreadPool(workers_n, cores_a):
        """Returns a list of how many threads each worker can use. workers_n - number of workers. cores_a - available cores."""
        if workers_n >= cores_a:
            return []
        
        if workers_n == 1:
            return [cores_a]
        else:
            thread_pool = []
            
            # Fill in thread_pool
            for i in range(workers_n):
                thread_pool.append(1)
            
            # Spread out threads
            n = 0
            while sum(thread_pool) < cores_a:
                thread_pool[n] += 1
                n += 1

            return thread_pool