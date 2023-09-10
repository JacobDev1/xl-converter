import os, random, subprocess, shutil
from send2trash import send2trash
from VARIABLES import DEBUG, IMAGE_MAGICK_PATH, ALLOWED_RESAMPLING

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
    
    def downscaleByPercent(self, src, dst, amount=10, resample="Default", n=None):
        """Resize the image by percentage. Keeps the same aspect ratio."""
        args = []
        if resample != "Default" and resample in ALLOWED_RESAMPLING:
            args.append(f"-filter {resample}")
        args.append(f"-resize {100 - amount}%")

        self.convert(IMAGE_MAGICK_PATH, src, dst, args, n)

    def downscaleToMaxRes(self, src, dst, max_w, max_h, resample="Default", n=None):
        args = []
        if resample != "Default" and resample in ALLOWED_RESAMPLING:
            args.append(f"-filter {resample}")
        args.append(f"-resize {max_w}x{max_h}")

        self.convert(IMAGE_MAGICK_PATH, src, dst, args, n)
            
    def downscaleToMaxFileSize(self, params):
        """Downscale image to fit under a certain file size."""

        # Prepare data
        amount = params["step"]
        proxy_src = self.getUniqueFilePath(params["dst_dir"], params["name"], "png", True)
        shutil.copy(params["src"], proxy_src)

        # Downscale until it's small enough
        while True:
            # Normal conversion
            self.convert(params["enc"], proxy_src, params["dst"], params["args"], params["n"])

            # Cap amount
            if amount == 99:
                self.delete(proxy_src)
                return False

            # If bigger - resize
            if (os.path.getsize(params["dst"]) / 1024) > params["max_size"]:
                amount += params["step"]
                if amount > 100:
                    amount = 99 # Cap amount
                    self.log("[Error] Cannot downscale to less than 1%", params["n"])
                    # return False
                
                self.downscaleByPercent(params["src"], proxy_src, amount, params["resample"], params["n"])
            else:
                # JPEG XL - intelligent effort
                if params["jxl_int_e"]: 
                    params["args"][1] = "-e 9"
                    e9_tmp = self.getUniqueFilePath(params["dst_dir"], params["name"], "jxl", True)
                    self.convert(params["enc"], proxy_src, e9_tmp, params["args"], params["n"])
                    if os.path.getsize(e9_tmp) < os.path.getsize(params["dst"]):
                        self.delete(params["dst"])
                        os.rename(e9_tmp, params["dst"])
                    else:
                        self.delete(e9_tmp)

                # Clean-up
                self.delete(proxy_src)
                return True
    
    def downscale(self, params):
        """A wrapper for all downscaling methods.
        
            "mode" - downscaling mode
            "enc" - encoder path
            "jxl_int_e" - An exception to handle intelligent effort
            "src" - source PNG absolute path
            "dst" - destination absolute path
            "dst_dir": - destination directory
            "name" - item name
            "args" - encoder arguments

            Max File Size
            "step" - takes % (e.g. 10%). Keep between 5% - 20%
            "max_size" - desired size - takes KiB (e.g. 500 KiB)

            Percent
            "percent" - downscale by that amount

            Max Size
            "width" - max width in px
            "height" - max height in px
            
            Misc
            "resample": - resampling method
            "n" - worker number
        """
        match params["mode"]:
            case "Max File Size":
                self.downscaleToMaxFileSize(params)
            case "Percent":
                self.downscaleByPercent(params["src"], params["dst"], 100 - params["percent"], params["resample"], params["n"])
            case "Max Resolution":
                self.downscaleToMaxRes(params["src"], params["dst"], params["width"], params["height"], params["resample"], params["n"])
            case _:
                self.log(f"[Error] Downscaling mode not recognized ({params['mode']})")

    def copyAttributes(self, src, dst):
        """Copy all attributes from one file onto another."""
        try:
            shutil.copystat(src, dst)
        except OSError as e:
            self.log(f"[Error] copystat failed ({e})")