import os, random, subprocess
from send2trash import send2trash
from VARIABLES import DEBUG, IMAGE_MAGICK_PATH

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
        command = f'\"{encoder_path}\" \"{src}\" {" ".join(args) + " " if args else ""}\"{dst}\"'
        
        if DEBUG:   subprocess.run(command, shell=True)
        else:       subprocess.run(command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

        if n != None:   self.log(command, n)

    def optimize(self, bin_path, src, args = [], n = None):
        command = f'\"{bin_path}\" {" ".join(args) + " " if args else ""}\"{src}\"'

        if DEBUG:   subprocess.run(command, shell=True)
        else:       subprocess.run(command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

        if n != None:   self.log(command, n)

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

    def log(self, msg, n = None):
        if n == None:
            print(msg)
        else:
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
    
    # Prototype functions for resizing
    # def downscaleByPercent(self, src, dst, amount=10, n=None):
    #     """Resize the image by percentage. Keeps the same aspect ratio."""
    #     args = [
    #         f"-resize {100 - amount}%"
    #     ]

    #     self.convert(IMAGE_MAGICK_PATH, src, dst, args, n)

    # def downscaleToMaxPixelSize(self, src, dst, max_w, max_h, n=None):
    #     args = [
    #         f"-resize {max_w}x{max_h}"
    #     ]

    #     self.convert(IMAGE_MAGICK_PATH, src, dst, args, n)
    
    # Sample implementation. To be moved into Worker.py and made to calc size based on desired output format (e.g. AVIF)
    # def downscaleToMaxFileSize(self, src, dst, max_size, step=10, n=None):
    #     """Downscale image to fit under a certain file size.

    #         max_size - takes KiB (e.g. 500 KiB)
    #         step - takes % (e.g. 10%). Keep between 5% - 10%
    #     """
    #     amount = step
    #     while True:
    #         self.downscaleByPercent(src, dst, amount, n)

    #         print(f"[DEBUG] {amount}; {os.path.getsize(dst) / 1024}")
    #         if (os.path.getsize(dst) / 1024) > max_size:
    #             amount += step
    #             if amount < 1:
    #                 self.log("[Error] Cannot downscale to less than 1%", n)
    #                 return False
    #             self.delete(dst)
    #             continue
    #         else:
    #             return True
