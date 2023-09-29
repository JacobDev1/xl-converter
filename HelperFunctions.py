import os, re, platform
from pathlib import Path
import qdarktheme

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

def burstThreadPool(workers_n, cores_a):
        """Returns a list of how many threads each worker can use. 
        arguments:
            workers_n - number of workers.
            cores_a - available cores.
        returns (examples):
            burstThreadPool(3, 6) -> [2,2,2]
            burstThreadPool(3, 5) -> [2,2,1]
            burstThreadPool(2, 5) -> [3,2]
        """
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