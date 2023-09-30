import os, random, subprocess, shutil, re
from send2trash import send2trash
from VARIABLES import DEBUG, IMAGE_MAGICK_PATH, ALLOWED_RESAMPLING, ALLOWED_INPUT_IMAGE_MAGICK, AVIFDEC_PATH, DJXL_PATH
import TaskStatus

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
        
        prev = re.search(r"\([0-9]{1,}\)$", file_name)
        if prev != None:   # Detect a previously renamed file
            n = int(prev.group(0)[1:-1])

        while os.path.isfile(path):
            if add_rnd:
                path = os.path.join(dir,f"{file_name}_{rnd}.{ext}")
            else:
                if prev != None and len(file_name) > len(prev.group(0)):
                    spacing = "" if file_name[len(file_name) - len(prev.group(0)) - 1] != " " else ""  # Add spacing to "file(1)", not "file (1)"
                    path = os.path.join(dir,f"{file_name[:-len(prev.group(0))]}{spacing}({n}).{ext}")
                else:
                    path = os.path.join(dir,f"{file_name} ({n}).{ext}")
            n += 1
        return path
    
    def getPathGIF(self, output_dir, item_name, mode):
        """Single-purpose helper method for decoding GIF to PNG for ImageMagick.
        
        Returns either path or "Skip"
        """
        new_path = os.path.join(output_dir, f"{item_name}.png")
        match mode:
            case "Rename":
                if os.path.isfile(os.path.join(output_dir, f"{item_name}-0.png")):
                    n = 0
                    while os.path.isfile(os.path.join(output_dir, f"{item_name} ({n})-0.png")):
                        n += 1
                    new_path = os.path.join(output_dir, f"{item_name} ({n}).png")
                return new_path
            case "Replace":
                return new_path
            case "Skip":
                return "Skip"

    def convert(self, encoder_path, src, dst, args = [], n = None):
        """Universal method for all encoders."""
        command = f'\"{encoder_path}\" \"{src}\" {" ".join(args) + " " if args else ""}\"{dst}\"'
        
        if DEBUG:   subprocess.run(command, shell=True)
        else:       subprocess.run(command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

        if n != None:   self.log(command, n)

    def getDecoder(self, ext):
        """Helper function, use within this class only. Returns encoder for specific format.
        
            ext - extension
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
                    return None

    def decode(self, src, dst, src_ext, n = None):
        """Decode to PNG.
        
            src - source path
            dst - destination path
            src_ext - source extension
            n - worker number
        """
        encoder_path = self.getDecoder(src_ext)

        if encoder_path == None:
            self.log(f"Cannot find decoder for {src_ext}", n)
            return False
        else:
            self.convert(encoder_path, src, dst, [], n)
            return True
    
    def decodeAndDownscale(self, params, ext):
        """Decode to PNG with downscaling support."""
        params["enc"] = self.getDecoder(ext)

        if params["enc"] == None:
            self.log(f"Cannot find decoder for {ext}", n)
            return False
        else:
            self.downscale(params)
            return True

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
    
    def downscaleTemplate(self, src, dst, _args, resample="Default", n=None):
        """Template - for use within this class only."""
        if TaskStatus.wasCanceled():
            return

        args = []
        if resample != "Default" and resample in ALLOWED_RESAMPLING:
            args.append(f"-filter {resample}")  # Needs to come first
        args.extend(_args)

        self.convert(IMAGE_MAGICK_PATH, src, dst, args, n)

    def downscaleByPercent(self, src, dst, amount=10, resample="Default", n=None):
        self.downscaleTemplate(src, dst, [f"-resize {100 - amount}%"], resample, n)

    def downscaleToMaxRes(self, src, dst, max_w, max_h, resample="Default", n=None):
        self.downscaleTemplate(src, dst, [f"-resize {max_w}x{max_h}"], resample, n)

    def downscaleToShortestSide(self, src, dst, max_res, resample="Default", n=None):
        self.downscaleTemplate(src, dst, [f"-resize \"{max_res}x{max_res}^>\""], resample, n)

    def downscaleToLongestSide(self, src, dst, max_res, resample="Default", n=None):
        self.downscaleTemplate(src, dst, [f"-resize \"{max_res}x{max_res}>\""], resample, n)
            
    def downscaleToMaxFileSize(self, params):
        """Downscale image to fit under a certain file size."""
        if TaskStatus.wasCanceled():
            return False

        # Prepare data
        amount = params["step"]
        proxy_src = self.getUniqueFilePath(params["dst_dir"], params["name"], "png", True)
        shutil.copy(params["src"], proxy_src)

        # Downscale until it's small enough
        while True:
            if TaskStatus.wasCanceled():
                self.delete(proxy_src)
                self.delete(params["dst"])
                return False

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
                
                if TaskStatus.wasCanceled():
                    self.delete(proxy_src)
                    self.delete(params["dst"])
                    return False

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
        """A wrapper for all downscaling methods. Keeps the same aspect ratio.
        
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
            case "Shortest Side":
                self.downscaleToShortestSide(params["src"], params["dst"], params["shortest_side"], params["resample"], params["n"])
            case "Longest Side":
                self.downscaleToLongestSide(params["src"], params["dst"], params["longest_side"], params["resample"], params["n"])
            case _:
                self.log(f"[Error] Downscaling mode not recognized ({params['mode']})")

    def copyAttributes(self, src, dst):
        """Copy all attributes from one file onto another."""
        try:
            shutil.copystat(src, dst)
        except OSError as e:
            self.log(f"[Error] copystat failed ({e})")