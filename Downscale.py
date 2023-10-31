import shutil, os
import TaskStatus
from Convert import Convert
from Pathing import Pathing
from Metadata import Metadata
from Files import Files
from Proxy import Proxy
from VARIABLES import (
    CJXL_PATH,
    IMAGE_MAGICK_PATH,
    ALLOWED_RESAMPLING,
    ALLOWED_INPUT_IMAGE_MAGICK,
    DOWNSCALE_LOGS
)

class Downscale():
    def __init__(self):
        self.c = Convert()
        self.path = Pathing()
        self.f = Files()
        self.metadata = Metadata()

    def _downscaleTemplate(self, src, dst, _args, resample="Default", n=None):
        """For intenal use only."""
        if TaskStatus.wasCanceled():
            return

        args = []
        if resample != "Default" and resample in ALLOWED_RESAMPLING:
            args.append(f"-filter {resample}")  # Needs to come first
        args.extend(_args)

        self.c.convert(IMAGE_MAGICK_PATH, src, dst, args, n)

    def downscaleByPercent(self, src, dst, amount=10, resample="Default", n=None):
        self._downscaleTemplate(src, dst, [f"-resize {100 - amount}%"], resample, n)

    def downscaleToMaxRes(self, src, dst, max_w, max_h, resample="Default", n=None):
        self._downscaleTemplate(src, dst, [f"-resize {max_w}x{max_h}"], resample, n)

    def downscaleToShortestSide(self, src, dst, max_res, resample="Default", n=None):
        self._downscaleTemplate(src, dst, [f"-resize \"{max_res}x{max_res}^>\""], resample, n)

    def downscaleToLongestSide(self, src, dst, max_res, resample="Default", n=None):
        self._downscaleTemplate(src, dst, [f"-resize \"{max_res}x{max_res}>\""], resample, n)

    def downscaleToMaxFileSize(self, params):
        """Downscale image to fit under a certain file size."""
        # Prepare data
        amount = params["step"]
        proxy_src = self.path.getUniqueFilePath(params["dst_dir"], params["name"], "png", True)
        shutil.copy(params["src"], proxy_src)

        # Int. Effort
        if params["format"] == "JPEG XL" and params["jxl_int_e"]:
            params["args"][1] = "-e 7"

        # Downscale until it's small enough
        while True:
            if TaskStatus.wasCanceled():
                self.f.delete(proxy_src)
                self.f.delete(params["dst"])
                return False

            # Normal conversion
            self.c.convert(params["enc"], proxy_src, params["dst"], params["args"], params["n"])

            # Cap amount
            if amount >= 99:
                self.f.delete(proxy_src)
                return False

            # If bigger - resize
            if (os.path.getsize(params["dst"]) / 1024) > params["max_size"]:
                amount += params["step"]
                if amount > 99:
                    amount = 99 # Cap amount
                    self.log("[Error] Cannot downscale to less than 1%", params["n"])
                
                if TaskStatus.wasCanceled():
                    self.f.delete(proxy_src)
                    self.f.delete(params["dst"])
                    return False

                self.downscaleByPercent(params["src"], proxy_src, amount, params["resample"], params["n"])

            else:
                # JPEG XL - intelligent effort
                if params["format"] == "JPEG XL" and params["jxl_int_e"]:
                    params["args"][1] = "-e 9"
                    e9_tmp = self.path.getUniqueFilePath(params["dst_dir"], params["name"], "jxl", True)

                    self.c.convert(params["enc"], proxy_src, e9_tmp, params["args"], params["n"])

                    if os.path.getsize(e9_tmp) < os.path.getsize(params["dst"]):
                        self.f.delete(params["dst"])
                        os.rename(e9_tmp, params["dst"])
                    else:
                        self.f.delete(e9_tmp)

                # Clean-up
                self.f.delete(proxy_src)
                return True
    
    def downscaleManualModes(self, params):
        """Internal wrapper for all regular downscaling modes."""
        # Set arguments
        args = []
        if params['resample'] != "Default" and params['resample'] in ALLOWED_RESAMPLING:
            args.append(f"-filter {params['resample']}")
        
        match params["mode"]:
            case "Percent":
                args.append(f"-resize {params['percent']}%")
            case "Max Resolution":
                args.append(f"-resize {params['width']}x{params['height']}")
            case "Shortest Side":
                args.append(f"-resize \"{params['shortest_side']}x{params['shortest_side']}^>\"")
            case "Longest Side":
                args.append(f"-resize \"{params['longest_side']}x{params['longest_side']}>\"")
        
        # Downscale
        if params["enc"] == IMAGE_MAGICK_PATH:  # We can just add arguments If the encoder is ImageMagick, since it also handles downscaling
            args.extend(params["args"])
            self.c.convert(IMAGE_MAGICK_PATH, params["src"], params["dst"], args, params["n"])
        else:
            downscaled_path = self.path.getUniqueFilePath(params["dst_dir"], params["name"], "png", True)

            # Downscale
            # Proxy was handled before in Worker.py
            self.c.convert(IMAGE_MAGICK_PATH, params["src"], downscaled_path, args, params["n"])
            
            # Convert
            if params["format"] == "JPEG XL" and params["jxl_int_e"]: 
                params["args"][1] == "-e 7"

            self.c.convert(params["enc"], downscaled_path, params["dst"], params["args"], params["n"])

            # Intelligent Effort
            if params["format"] == "JPEG XL" and params["jxl_int_e"]: 
                params["args"][1] = "-e 9"

                e9_tmp = self.path.getUniqueFilePath(params["dst_dir"], params["name"], "jxl", True)
                self.c.convert(params["enc"], downscaled_path, e9_tmp, params["args"], params["n"])

                if os.path.getsize(e9_tmp) < os.path.getsize(params["dst"]):
                    self.f.delete(params["dst"])
                    os.rename(e9_tmp, params["dst"])
                else:
                    self.f.delete(e9_tmp)

            # Clean-up
            self.f.delete(downscaled_path)
    
    def decodeAndDownscale(self, params, ext, metadata_mode):
        """Decode to PNG with downscaling support."""
        params["enc"] = self.c.getDecoder(ext)
        params["args"] = self.metadata.getArgs(params["enc"], metadata_mode)

        if params["enc"] == IMAGE_MAGICK_PATH:
            self.downscale(params)
        else:
            # Generate proxy
            proxy_path = self.path.getUniqueFilePath(params["dst_dir"], params["name"], "png", True)
            self.c.convert(params["enc"], params["src"], proxy_path, [], params["n"])

            # Downscale
            params["src"] = proxy_path
            params["enc"] = IMAGE_MAGICK_PATH
            self.downscale(params)

            # Clean-up
            self.f.delete(proxy_path)

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
        if TaskStatus.wasCanceled():
            return False
        
        if params["mode"] == "Max File Size":
            self.downscaleToMaxFileSize(params)
        elif params["mode"] in ("Percent", "Max Resolution", "Shortest Side", "Longest Side"):
            self.downscaleManualModes(params)  # To be rename and reworked
        else:
            self.log(f"[Error] Downscaling mode not recognized ({params['mode']})", params["n"])
    
    def log(self, msg, n = None):
        if not DOWNSCALE_LOGS:
            return

        if n == None:
            print(msg)
        else:
            print(f"[Worker #{n}] {msg}")