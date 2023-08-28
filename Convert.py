import os, random, subprocess
from send2trash import send2trash
from VARIABLES import DEBUG

# Methods for converting files

class Convert():
    def __init__(self):
        pass
    
    def getUniqueFilePath(self, dir, file_name: str, ext: str, add_rnd = False):
        # Generate Random String
        rnd = ""
        if add_rnd:
            for i in range(3):
                rnd += str(hex(random.randint(0, 0xf)))[2:]  # Yes, it's random and a hex number. There are no actual words generated.
        
        # Setup Path
        path = ""
        if add_rnd:
            path = os.path.join(dir,f"{file_name}_{rnd}.{ext}")
        else:
            path = os.path.join(dir,f"{file_name}.{ext}")

        # Check for uniqueness
        n = 1
        while os.path.isfile(path):
            if add_rnd:
                path = os.path.join(dir,f"{file_name}_{rnd}.{ext}")
            else:
                path = os.path.join(dir,f"{file_name} ({n}).{ext}")
            n += 1
        return path
    
    def convert(self, encoder_path, src, dst, args = [], n = None):
        # Handle commands with or without arguments
        command = ""
        if len(args):
            command = f'\"{encoder_path}\" \"{src}\" {" ".join(args)} \"{dst}\"'
        else:
            command = f'\"{encoder_path}\" \"{src}\" \"{dst}\"'
        
        # Run
        if DEBUG:
            subprocess.run(command, shell=True)
        else:
            subprocess.run(command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

        # Log
        if n != None:
            self.log(command, n)

    def optimize(self, bin_path, src, args = [], n = None):
        command = ""
        if len(args):
            command = f'\"{bin_path}\" {" ".join(args)} \"{src}\"'
        else:
            command = f'\"{bin_path}\" \"{src}\"'

        subprocess.run(command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

        if n != None:
            self.log(command, n)

    def delete(self, path, trash = False):
        try:
            if trash:   send2trash(path)
            else:       os.remove(path)
        except OSError as err:
            print(f"[Error] Deleting file failed {err}")
            return False
        return True
    
    def round(self, size):
        """Outputs rounded size in KiB"""
        return round(size/1024,1) 

    def log(self, msg, n):
        print(f"[Worker #{n}] {msg}")
    
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