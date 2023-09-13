from VARIABLES import CJXL_PATH, DJXL_PATH, IMAGE_MAGICK_PATH, AVIFENC_PATH, AVIFDEC_PATH, OXIPNG_PATH
from VARIABLES import ALLOWED_INPUT_CJXL, ALLOWED_INPUT_DJXL, PROGRAM_FOLDER, ALLOWED_INPUT_IMAGE_MAGICK, ALLOWED_INPUT_AVIFENC, ALLOWED_INPUT_AVIFDEC, ALLOWED_INPUT, JPEG_ALIASES
from Convert import Convert
import TaskStatus


import os, subprocess, shutil

from PySide6.QtCore import (
    QRunnable,
    QObject,
    Signal,
    Slot
)

class Signals(QObject):
    started = Signal(int)
    completed = Signal(int)
    canceled = Signal(int)

class Worker(QRunnable):
    def __init__(self, n, item, params, burst_thread_pool = []):
        super().__init__()
        self.signals = Signals()
        self.convert = Convert()
        self.params = params

        # Threading
        self.n = n  # Thread number
        self.available_threads = 1
        
        # Original Item info
        self.item = item    # Original file
        
        # Item info - these can be reassigned
        self.item_name = item[0]    
        self.item_ext = item[1].lower()     # lowercase, for original value use self.item[1]
        self.item_dir = item[2]
        self.item_abs_path = item[3]

        # Burst mode (for small data sets)
        if burst_thread_pool:
            self.available_threads = burst_thread_pool[self.n]
            self.convert.log(f"Burst mode active (threads: {self.available_threads})", self.n)
    
    @Slot()
    def run(self):
        if TaskStatus.wasCanceled():
            self.signals.canceled.emit(self.n)
            return

        self.signals.started.emit(self.n)

        # Check If input file is still in the list, but was physically removed
        if os.path.isfile(self.item[3]) == False:   
            print(f"[Worker #{self.n}] File not found ({self.item[3]})")
            self.signals.completed.emit(self.n)
            return

        # Solve conflicts with animated images
        conflict = False
        if self.item_ext in ("gif", "apng"):
            conflict = True

            match self.item_ext:
                case "gif":
                    if self.params["format"] in ("JPEG XL", "WEBP", "PNG"):    # Support GIF
                        conflict = False
                case "apng":
                    if self.params["format"] in ("JPEG XL"):                   # Support APNG
                        conflict = False

            if conflict:
                self.convert.log(f"Animation not supported for {self.params['format']}", self.n)

            if self.params["format"] == "JPEG XL":
                if self.params["effort"] > 7:   # Efforts bigger than 7 cause the encoder to crash when processing APNGs
                    self.params["effort"] = 7
                self.params["intelligent_effort"] = False

            if self.params["downscaling"]["enabled"]:
                conflict = True
                self.convert.log(f"Downscaling not supported for animated media", self.n)

        if conflict:
            self.signals.completed.emit(self.n)
            return

        # Check If "Smallest Lossless" has any formats enabled
        if self.params["format"] == "Smallest Lossless":
            is_empty = True
            for key, value in self.params["smallest_format_pool"].items():
                if value:
                    is_empty = False
            
            if is_empty:
                self.convert.log("Smallest Lossless needs at least one format enabled", self.n)
                self.signals.completed.emit(self.n)
                return

        # Choose Output Dir           
        output_dir = ""
        output = ""
        if self.params["custom_output_dir"]:
            output_dir = self.params["custom_output_dir_path"]
            if os.path.isdir(output_dir) == False:
                os.makedirs(output_dir, exist_ok=True)
        else:
            output_dir = self.item[2]

        # Check If proxy needed / Assign extensions
        output_ext = ""
        need_proxy = True
        match self.params["format"]:
            case "JPEG XL":
                output_ext = "jxl"
                if self.item_ext in ALLOWED_INPUT_CJXL:
                    need_proxy = False          
            case "PNG":
                output_ext = "png"
                need_proxy = False
            case "AVIF":
                output_ext = "avif"
                if self.item_ext in ALLOWED_INPUT_AVIFENC:
                    need_proxy = False
            case "WEBP":
                output_ext = "webp"
                if self.item_ext in ALLOWED_INPUT_IMAGE_MAGICK:
                    need_proxy = False
            case "JPG":
                output_ext = "jpg"
                if self.item_ext in ALLOWED_INPUT_IMAGE_MAGICK:
                    need_proxy = False
        # need_proxy is always True for "Smallest Lossless"
        
        # Assign output paths
        output = self.convert.getUniqueFilePath(output_dir, self.item_name, output_ext, True)   # Initial (temporary) destination
        final_output = os.path.join(output_dir, f"{self.item_name}.{output_ext}")               # Final destination. File from "output" will be renamed to it after conversion to prevent naming collisions

        # If file exists - for decoding GIF only
        if self.item_ext == "gif" and self.params["format"] == "PNG":
            output = self.convert.getPathGIF(output_dir, self.item_name, self.params["if_file_exists"])
            if output == "Skip":
                self.signals.completed.emit(self.n)
                return
            final_output = output

        # Skip If needed
        if self.params["if_file_exists"] == "Skip":
            if os.path.isfile(final_output) and self.params["format"] not in ("Smallest Lossless"):
                self.signals.completed.emit(self.n)
                return
        
        # Downscaling - prepare proxy
        if self.params["downscaling"]["enabled"]:
            need_proxy = True

        # Create Proxy
        if need_proxy:
            proxy_path = self.convert.getUniqueFilePath(output_dir, self.item_name, "png", True)
            
            self.convert.decode(self.item_abs_path, proxy_path, self.item_ext, self.n)
            
            if os.path.isfile(proxy_path):
                self.item_abs_path = proxy_path
            else:
                self.convert.log(f"Proxy cannot be found ({self.item_name}.{self.item_ext})", self.n)
                self.signals.completed.emit(self.n)
                return

        # Downscaling - prepare params
        scl_params = {}
        if self.params["downscaling"]["enabled"]:
            scl_params = {    # "None" values are assigned later on
                "mode": self.params["downscaling"]["mode"],
                "enc": None,
                "jxl_int_e": None,   # An exception to handle intelligent effort
                "src": self.item_abs_path,
                "dst": output,
                "dst_dir": output_dir,
                "name": self.item_name,
                "args": None,
                "max_size": self.params["downscaling"]["file_size"],
                "step": self.params["downscaling"]["file_size_step"],
                "percent": self.params["downscaling"]["percent"],
                "width": self.params["downscaling"]["width"],
                "height": self.params["downscaling"]["height"],
                "shortest_side": self.params["downscaling"]["shortest_side"],
                "longest_side": self.params["downscaling"]["longest_side"],
                "resample": self.params["downscaling"]["resample"],
                "n": self.n,
            }
        
        # Convert
        if self.params["format"] == "JPEG XL":
            args = [
                    f"-q {self.params['quality']}",
                    f"-e {self.params['effort']}",
                    "--lossless_jpeg=0",
                    f"--num_threads={self.available_threads}"
                ]

            if self.params["lossless"]:
                args[0] = "-q 100"
                args[3] = "--lossless_jpeg=1"   # JPG reconstruction

            # For lossless best Effort is always 9
            if self.params["intelligent_effort"] and (self.params["quality"] == 100 or self.params["lossless"]):
                self.params["intelligent_effort"] = False
                args[1] = "-e 9"

            # Set downscaling params
            if self.params["downscaling"]["enabled"]:
                scl_params["enc"] = CJXL_PATH
                if self.params["intelligent_effort"]:   scl_params["jxl_int_e"] = True
                scl_params["args"] = args

            if self.params["downscaling"]["enabled"] and self.params["intelligent_effort"]:
                self.convert.downscale(scl_params)
            elif self.params["intelligent_effort"]:
                path_pool = [
                    self.convert.getUniqueFilePath(output_dir,self.item_name + "_e7", "jxl", True),
                    self.convert.getUniqueFilePath(output_dir,self.item_name + "_e9", "jxl", True),
                ]
                args[1] = "-e 7"
                self.convert.convert(CJXL_PATH, self.item_abs_path, path_pool[0], args, self.n)

                if TaskStatus.wasCanceled():
                    self.convert.delete(path_pool[0])
                    self.signals.canceled.emit(self.n)
                    return

                args[1] = "-e 9"
                self.convert.convert(CJXL_PATH, self.item_abs_path, path_pool[1], args, self.n)

                self.convert.leaveOnlySmallestFile(path_pool, output)
            else:
                if self.params["downscaling"]["enabled"]:
                    self.convert.downscale(scl_params)
                else:
                    self.convert.convert(CJXL_PATH, self.item_abs_path, output, args, self.n)                
            
            if self.params["lossless_if_smaller"] and self.params["lossless"] == False:
                if self.params["intelligent_effort"]:
                    args[1] = "-e 9"
                args[0] = "-q 100"

                lossless_path = self.convert.getUniqueFilePath(self.item_dir, self.item_name + "_l", "jxl", True)
                self.convert.convert(CJXL_PATH, self.item_abs_path, lossless_path, args, self.n)

                path_pool = [
                    output,
                    lossless_path
                ]
                self.convert.leaveOnlySmallestFile(path_pool, output)

        elif self.params["format"] == "PNG":            
            if self.params["downscaling"]["enabled"]:
                scl_params["args"] = []
                self.convert.decodeAndDownscale(scl_params, self.item_ext)
            else:
                self.convert.decode(self.item_abs_path, output, self.item_ext, self.n)
            
        elif self.params["format"] == "WEBP":
            multithreading = 1 if self.available_threads > 1 else 0
            args = [
                f"-quality {self.params['quality']}",
                f"-define webp:thread-level={multithreading}",
                "-define webp:method=6"
                ]

            if self.params["lossless"]:
                args.pop(0) # Remove quality
                args.append("-define webp:lossless=true")

            if self.params["downscaling"]["enabled"]:
                scl_params["enc"] = IMAGE_MAGICK_PATH
                scl_params["args"] = args
                self.convert.downscale(scl_params)
            else:
                self.convert.convert(IMAGE_MAGICK_PATH, self.item_abs_path, output, args, self.n)

            if self.params["lossless_if_smaller"] and self.params["lossless"] == False:
                args.pop(0) # Remove quality
                args.append("-define webp:lossless=true")

                lossless_path = self.convert.getUniqueFilePath(self.item_dir, self.item_name + "_l", "webp", True)
                self.convert.convert(IMAGE_MAGICK_PATH, self.item_abs_path, lossless_path, args, self.n)

                path_pool = [
                    output,
                    lossless_path
                ]

                self.convert.leaveOnlySmallestFile(path_pool, output)

        elif self.params["format"] == "AVIF":
            args = [
                "--min 0",
                "--max 63",
                "-a end-usage=q",
                f"-a cq-level={self.params['quality']}",
                f"-s {self.params['effort']}" if not self.params["intelligent_effort"] else "-s 0",
                f"-j {self.available_threads}"
            ]

            if self.params["downscaling"]["enabled"]:
                scl_params["enc"] = AVIFENC_PATH
                scl_params["args"] = args
                self.convert.downscale(scl_params)
            else:
                self.convert.convert(AVIFENC_PATH, self.item_abs_path, output, args, self.n)
                    
        elif self.params["format"] == "JPG":
            args = [f"-quality {self.params['quality']}"]

            if self.params["downscaling"]["enabled"]:
                scl_params["enc"] = IMAGE_MAGICK_PATH
                scl_params["args"] = args
                self.convert.downscale(scl_params)
            else:
                self.convert.convert(IMAGE_MAGICK_PATH, self.item_abs_path, output, args, self.n)
        elif self.params["format"] == "Smallest Lossless":

            # Populate path pool
            path_pool = {}
            for key in self.params["smallest_format_pool"]:     # Iterate through formats ("png", "webp", "jxl")
                if self.params["smallest_format_pool"][key]:    # If format enabled
                    path_pool[key] = self.convert.getUniqueFilePath(output_dir, self.item_name, key, True) # Add format

            # Check if no formats selected
            if len(path_pool) == 0:
                self.convert.log("No formats selected for Smallest Lossless", self.n)
                self.signals.completed.emit(self.n)
                return

            # Set arguments
            webp_thread_level = 1 if self.available_threads > 1 else 0
            args = {
                "png": [
                    "-o 4" if self.params["max_compression"] else "-o 2",
                    f"-t {self.available_threads}"
                    ],
                "webp": [
                    f"-define webp:thread-level={webp_thread_level}",
                    "-define webp:method=6",
                    "-define webp:lossless=true"
                ],
                "jxl": [
                    "-q 100",
                    "-e 9" if self.params["max_compression"] else "-e 7",
                    f"--num_threads={self.available_threads}"
                ]
            }

            # Generate files
            for key in path_pool:
                if key == "png":
                    shutil.copy(self.item_abs_path, path_pool["png"])
                    self.convert.optimize(OXIPNG_PATH, path_pool["png"], args["png"], self.n)
                elif key == "webp":
                    self.convert.convert(IMAGE_MAGICK_PATH, self.item_abs_path, path_pool["webp"], args["webp"], self.n)
                elif key == "jxl":
                    src = self.item_abs_path
                    if self.item_ext in JPEG_ALIASES:  # Exception for handling JPG reconstruction
                        src = self.item[3]
                    self.convert.convert(CJXL_PATH, src, path_pool["jxl"], args["jxl"], self.n)

            # Get file sizes
            file_sizes = {}
            for key in path_pool:
                file_sizes[key] = os.path.getsize(path_pool[key])

            # Get smallest item
            sm_f_key = None # Smallest format key
            for key in path_pool:
                if sm_f_key == None:
                    sm_f_key = key
                else:
                    if file_sizes[key] < file_sizes[sm_f_key]:
                        sm_f_key = key

            # Remove bigger files
            for key in path_pool:
                if key != sm_f_key:
                    self.convert.delete(path_pool[key])
            
            # Handle the smallest file
            output = path_pool[sm_f_key]
            final_output = os.path.join(output_dir, f"{self.item_name}.{sm_f_key}")
            output_ext = sm_f_key
            
            # Log
            self.convert.log(f"File Sizes: {file_sizes}", self.n)
            self.convert.log(f"Smallest Format: {sm_f_key}", self.n)

        else:
            self.convert.log(f"Unknown Format ({self.params['format']})", self.n)

        # Clean-up proxy
        if need_proxy:
            self.convert.delete(self.item_abs_path) # self.item_abs_path points at a proxy
            self.item_abs_path = self.item[3]
        
        # Check for existing files
        if self.item_ext == "gif" and self.params["format"] == "PNG":
            pass    # Already handled
        elif os.path.isfile(output):    # In case conversion failed
            match self.params["if_file_exists"]:
                case "Replace":
                    if os.path.isfile(final_output):
                        self.convert.delete(final_output)
                    os.rename(output, final_output)
                case "Rename":
                    final_output = self.convert.getUniqueFilePath(output_dir, self.item_name, output_ext, False)
                    os.rename(output, final_output)
                case "Skip":    # Only for "Smallest Lossless", other cases were handled before
                    if self.params["format"] == "Smallest Lossless":
                        if os.path.isfile(final_output):
                            self.convert.delete(output)
                        else:
                            os.rename(output, final_output)

        if os.path.isfile(final_output):    # In case renaming failed
            # Apply attributes
            if self.params["misc"]["attributes"]:
                self.convert.copyAttributes(self.item[3], final_output)

            # After Conversion
            if self.params["delete_original"]:
                if self.params["delete_original_mode"] == "To Trash":
                    self.convert.delete(self.item[3], True)
                elif self.params["delete_original_mode"] == "Permanently":
                    self.convert.delete(self.item[3])

        self.signals.completed.emit(self.n)