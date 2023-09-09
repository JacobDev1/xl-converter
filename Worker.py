from VARIABLES import CJXL_PATH, DJXL_PATH, IMAGE_MAGICK_PATH, AVIFENC_PATH, AVIFDEC_PATH, OXIPNG_PATH
from VARIABLES import ALLOWED_INPUT_CJXL, ALLOWED_INPUT_DJXL, PROGRAM_FOLDER, ALLOWED_INPUT_IMAGE_MAGICK, ALLOWED_INPUT_AVIFENC, ALLOWED_INPUT_AVIFDEC, ALLOWED_INPUT
from Convert import Convert

import os, subprocess, shutil

from PySide6.QtCore import (
    QRunnable,
    QObject,
    Signal,
    Slot
)

class TaskStatus():
    def __init__(self):
        self.canceled = False

    def isCanceled(self):
        return self.canceled

    def cancel(self):
        self.canceled = True
    
    def reset(self):
        self.canceled = False

task_status = TaskStatus()

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
        if task_status.isCanceled():
            self.signals.canceled.emit(self.n)
            return

        self.signals.started.emit(self.n)

        # Check If input file is still in the list, but was physically removed
        if os.path.isfile(self.item[3]) == False:   
            print(f"[Worker #{self.n}] File not found ({self.item[3]})")
            self.signals.completed.emit(self.n)
            return

        # Solve conflicts with overlapping formats
        conflict = False
        if self.item_ext == "gif":
            match self.params["format"]:
                case "AVIF":
                    conflict = True
                    self.convert.log(f"Animated AVIF not supported",self.n)
                case "JPG":
                    conflict = True
                    self.convert.log(f"JPG doesn't support animation",self.n)
                case "Smallest Lossless":
                    conflict = True
                    self.convert.log(f"Smallest Lossless doesn't support animation",self.n)
                case "JPEG XL":
                    # Hotfix
                    if self.params["effort"] > 7:   # Efforts bigger than 7 cause the encoder to crash when processing GIFs
                        self.params["effort"] = 7
                    self.params["intelligent_effort"] = False
        elif self.item_ext == "apng":
            if self.params["format"] != "JPEG XL":
                conflict = True
                self.convert.log(f"{self.params['format']} encoder doesn't support APNG ({self.item_name}.{self.item_ext})",self.n)
            else:
                if self.params["effort"] > 7:   # Efforts bigger than 7 cause the encoder to crash when processing APNGs
                    self.params["effort"] = 7
                    self.params["intelligent_effort"] = False
        
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
        final_output = os.path.join(output_dir, f"{self.item_name}.{output_ext}")               # The output previous var will be renamed to
        # It is done this way to avoid mutlithreaded 
        
        # Skip If needed
        if self.params["if_file_exists"] == "Skip":
            if os.path.isfile(final_output) and self.params["format"] not in ("Smallest Lossless"):
                self.signals.completed.emit(self.n)
                return
        
        # Create Proxy
        if need_proxy:
            proxy_path = self.convert.getUniqueFilePath(output_dir, self.item_name, "png", True)
            
            if self.item_ext == "png":
                shutil.copy(self.item_abs_path, proxy_path)     # For Smallest Lossless
            elif self.item_ext == "jxl":
                self.convert.convert(DJXL_PATH, self.item_abs_path, proxy_path, [], self.n)
            elif self.item_ext == "avif":
                self.convert.convert(AVIFDEC_PATH, self.item_abs_path, proxy_path, [], self.n)
            elif self.item_ext in ALLOWED_INPUT:
                self.convert.convert(IMAGE_MAGICK_PATH, self.item_abs_path, proxy_path, [], self.n)
            else:
                self.convert.log(f"Proxy cannot be created ({self.item_name}.{self.item_ext})", self.n)
                self.signals.completed.emit(self.n)
                return
            
            if os.path.isfile(proxy_path):
                self.item_abs_path = proxy_path
            else:
                self.convert.log(f"Proxy cannot be found ({self.item_name}.{self.item_ext})", self.n)
                self.signals.completed.emit(self.n)
                return

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

            if self.params["intelligent_effort"] and (self.params["quality"] == 100 or self.params["lossless"]):
                self.params["intelligent_effort"] = False
                args[1] = "-e 9"

            if self.params["intelligent_effort"]:
                path_pool = [
                    self.convert.getUniqueFilePath(output_dir,self.item_name + "_e7", "jxl", True),
                    self.convert.getUniqueFilePath(output_dir,self.item_name + "_e9", "jxl", True),
                ]
                args[1] = "-e 7"
                self.convert.convert(CJXL_PATH, self.item_abs_path, path_pool[0], args, self.n)
                args[1] = "-e 9"
                self.convert.convert(CJXL_PATH, self.item_abs_path, path_pool[1], args, self.n)

                self.convert.leaveOnlySmallestFile(path_pool, output)
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
            decoder_path = ""
            input_ext = self.item[1].lower()
            
            # Set Encoder
            if input_ext == "jxl":
                decoder_path = DJXL_PATH
            elif input_ext == "avif":
                decoder_path = AVIFDEC_PATH
            elif input_ext in ALLOWED_INPUT_IMAGE_MAGICK:
                decoder_path = IMAGE_MAGICK_PATH
            else:
                self.convert.log(f"No supported decoder found for ({self.item_name}.{self.item_ext})", self.n)
                self.signals.completed.emit(self.n)
                return

            # Decode
            self.convert.convert(decoder_path, self.item_abs_path, output, [], self.n)
            
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

            self.convert.convert(AVIFENC_PATH, self.item_abs_path, output, args, self.n)
        elif self.params["format"] == "JPG":
            self.convert.convert(IMAGE_MAGICK_PATH, self.item_abs_path, output, [f"-quality {self.params['quality']}"], self.n)
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
                    "--lossless_jpeg=0",
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
                    self.convert.convert(CJXL_PATH, self.item_abs_path, path_pool["jxl"], args["jxl"], self.n)
            
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
        
        # Check for existing files
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
            
        # Clean-up proxy
        if need_proxy:
            self.convert.delete(self.item_abs_path)
            self.item_abs_path = self.item[3]

        # After Conversion
        if self.params["delete_original"]:
            if os.path.isfile(final_output):   # In case convertion failed, don't delete the original
                if self.params["delete_original_mode"] == "To Trash":
                    self.convert.delete(self.item[3], True)
                elif self.params["delete_original_mode"] == "Permanently":
                    self.convert.delete(self.item[3])
        self.signals.completed.emit(self.n)