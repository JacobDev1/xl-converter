import os, shutil
from send2trash import send2trash
from VARIABLES import (
    ALLOWED_RESAMPLING, ALLOWED_INPUT_IMAGE_MAGICK,
    IMAGE_MAGICK_PATH,
    AVIFDEC_PATH,
    DJXL_PATH,
    DISABLE_LOGS
)
import TaskStatus
from Process import Process
from Pathing import Pathing

# Methods for converting files
class Convert():
    def __init__(self):
        self.p = Process()
        self.path = Pathing()
    
    def convert(self, encoder_path, src, dst, args = [], n = None):
        """Universal method for all encoders."""
        command = f'\"{encoder_path}\" \"{src}\" {" ".join(args) + " " if args else ""}\"{dst}\"'
        self.p.runProcess(command)
        if n != None:   self.log(command, n)
    
    def getDecoder(self, ext):
        """Return appropriate decoder path for the specified extension.
        
        Args:
            ext - file extension
        """
        ext = ext.lower()   # Safeguard in case of a mistake

        match ext:
            case "png":
                return IMAGE_MAGICK_PATH
            case "jxl":
                return DJXL_PATH
            case "avif":
                return AVIFDEC_PATH
            case _:
                if ext in ALLOWED_INPUT_IMAGE_MAGICK:
                    return IMAGE_MAGICK_PATH
                else:
                    print(f"[Convert - getDecoder()] Decoder for {ext} was not found")
                    return None

    def optimize(self, bin_path, src, args = [], n = None):
        """Run a binary while targeting a single file."""
        command = f'\"{bin_path}\" {" ".join(args) + " " if args else ""}\"{src}\"'
        self.p.runProcess(command)
        if n != None:   self.log(command, n)
    
    def leaveOnlySmallestFile(self, paths: [], new_path):
        """Delete all except the smallest file."""
        
        # Probe files
        sizes = []
        for i in paths:
            sizes.append(os.path.getsize(i))
        
        # Detect smallest
        smallest_format_index = 0
        item_count = len(paths)
        for i in range(1, item_count):
            if sizes[i] < sizes[smallest_format_index]:
                smallest_format_index = i
        
        # Clean-up and rename
        for i in range(item_count):
            if i != smallest_format_index:
                os.remove(paths[i])
            else:
                if paths[i] != new_path:
                    os.rename(paths[i], new_path)
    
    def log(self, msg, n = None):
        if DISABLE_LOGS:
            return
        
        if n == None:
            print(msg)
        else:
            print(f"[Worker #{n}] {msg}")