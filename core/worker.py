from data.constants import (
    CJXL_PATH,
    JPEG_ALIASES,
    AVIFENC_PATH,
    IMAGE_MAGICK_PATH,
    OXIPNG_PATH
)

from core.proxy import Proxy
from core.utils import delete
from core.pathing import getUniqueFilePath, getPathGIF, getExtension
from core.conflicts import Conflicts
from core.convert import convert, getDecoder, getExtensionJxl, optimize, leaveOnlySmallestFile
from core.downscale import downscale, decodeAndDownscale
import core.metadata as metadata
import data.task_status as task_status

import os, shutil, copy

from PySide6.QtCore import (
    QRunnable,
    QObject,
    Signal,
    Slot,
    QMutexLocker
)

class Signals(QObject):
    started = Signal(int)
    completed = Signal(int)
    canceled = Signal(int)
    exception = Signal(str)

class Worker(QRunnable):
    def __init__(self, n, item, params, available_threads, mutex):
        super().__init__()
        self.signals = Signals()
        self.params = copy.deepcopy(params)

        # Convert modules
        self.proxy = Proxy()
        self.conflicts = Conflicts()

        # Threading
        self.n = n  # Thread number
        self.available_threads = available_threads
        self.mutex = mutex
        
        # Original Item info
        self.item = item    # Original file
        
        # Item info - these can be reassigned
        self.item_name = item[0]    
        self.item_ext = item[1].lower()     # lowercase, for original value use self.item[1]
        self.item_dir = item[2]
        self.item_abs_path = item[3]
    
    def exception(self, msg):
        self.signals.exception.emit(f"{msg} ({self.item_name}.{self.item_ext})")

    @Slot()
    def run(self):
        if task_status.wasCanceled():
            self.signals.canceled.emit(self.n)
            return
        
        self.signals.started.emit(self.n)

        # Check If input file is still in the list, but was physically removed
        if os.path.isfile(self.item[3]) == False:   
            self.exception(f"File not found")
            self.signals.completed.emit(self.n)
            return

        # Check for conflicts - GIFs and APNGs
        self.conflicts.checkForConflicts(self.item_ext, self.params["format"], self.params["intelligent_effort"], self.params["effort"], self.params["downscaling"]["enabled"])
        
        if self.conflicts.conflictOccurred():
            for i in self.conflicts.getConflictsMsg():
                self.exception(i)
            self.signals.completed.emit(self.n)
            return
        
        if self.conflicts.jxlConflictOccurred():
            # Normalize values
            self.params["effort"] = self.conflicts.jxlGetNormEffort(self.params["effort"])
            self.params["intelligent_effort"] = self.conflicts.jxlGetNormIntEffort(self.params["intelligent_effort"])
            for i in self.conflicts.getConflictsMsg():
                self.exception(i)

        # Choose Output Dir           
        output_dir = ""
        if self.params["custom_output_dir"]:
            output_dir = self.params["custom_output_dir_path"]

            if not os.path.isabs(output_dir):   # If path relative
                output_dir = os.path.join(self.item_dir, output_dir)

            try:
                os.makedirs(output_dir, exist_ok=True)
            except OSError as err:
                self.exception(err)
                self.signals.completed.emit(self.n)
                return
        else:
            output_dir = self.item[2]

        # Assign output paths
        output_ext = getExtension(self.params["format"])
        if self.params["format"] == "PNG" and self.item_ext == "jxl" and self.params["reconstruct_jpg"]:
            output_ext = getExtensionJxl(self.item_abs_path)  # Reverse JPG reconstruction
        
        output = None
        with QMutexLocker(self.mutex):
            output = getUniqueFilePath(output_dir, self.item_name, output_ext, True)        # Initial output
        final_output = os.path.join(output_dir, f"{self.item_name}.{output_ext}")           # After conversion: output -> final_output 

        # If file exists - for decoding GIF only
        if self.item_ext == "gif" and self.params["format"] == "PNG":
            if self.params["if_file_exists"] == "Skip":
                self.signals.completed.emit(self.n)
                return

            output = getPathGIF(output_dir, self.item_name, self.params["if_file_exists"])
            final_output = output

        # Skip If needed
        if self.params["if_file_exists"] == "Skip":
            if os.path.isfile(final_output) and self.params["format"] not in ("Smallest Lossless"):
                self.signals.completed.emit(self.n)
                return
        
        # Create Proxy
        if self.proxy.isProxyNeeded(self.params["format"], self.item_ext, self.params["downscaling"]["enabled"]):

            if not self.proxy.generate(self.item_abs_path, self.item_ext, output_dir, self.item_name, self.n):
                self.exception(f"Proxy could not be generated ({self.proxy.getPath()})")
                self.signals.completed.emit(self.n)
                return
            
            self.item_abs_path = self.proxy.getPath()     # Redirect the source

        # Downscaling - prepare params
        scl_params = {}
        if self.params["downscaling"]["enabled"]:
            scl_params = {    # "None" values are assigned later on
                "mode": self.params["downscaling"]["mode"],
                "enc": None,
                "format": self.params["format"],    # To recognize intelligent effort
                "jxl_int_e": None,   # An exception to handle intelligent effort
                "src": self.item_abs_path,
                "dst": output,
                "dst_dir": output_dir,
                "name": self.item_name,
                "args": None,
                "max_size": self.params["downscaling"]["file_size"],
                "step": self.params["downscaling"]["file_size_step"],
                "step_fast": self.params["downscaling"]["file_size_step_fast"],
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
                args[2] = "--lossless_jpeg=1"   # JPG reconstruction

            # For lossless best Effort is always 9
            if self.params["intelligent_effort"] and (self.params["quality"] == 100 or self.params["lossless"]):
                self.params["intelligent_effort"] = False
                args[1] = "-e 9"
            
            # Handle metadata
            args.extend(metadata.getArgs(CJXL_PATH, self.params["misc"]["keep_metadata"]))

            # Set downscaling params
            if self.params["downscaling"]["enabled"]:
                scl_params["enc"] = CJXL_PATH
                if self.params["intelligent_effort"]:   scl_params["jxl_int_e"] = True
                scl_params["args"] = args

            if self.params["downscaling"]["enabled"] and self.params["intelligent_effort"]:
                downscale(scl_params)
            elif self.params["intelligent_effort"]:
                path_pool = [
                    getUniqueFilePath(output_dir,self.item_name + "_e7", "jxl", True),
                    getUniqueFilePath(output_dir,self.item_name + "_e9", "jxl", True),
                ]
                args[1] = "-e 7"
                convert(CJXL_PATH, self.item_abs_path, path_pool[0], args, self.n)

                if task_status.wasCanceled():
                    delete(path_pool[0])
                    self.signals.canceled.emit(self.n)
                    return

                args[1] = "-e 9"
                convert(CJXL_PATH, self.item_abs_path, path_pool[1], args, self.n)

                leaveOnlySmallestFile(path_pool, output)
            else:
                if self.params["downscaling"]["enabled"]:
                    downscale(scl_params)
                else:
                    convert(CJXL_PATH, self.item_abs_path, output, args, self.n)                
            
            if self.params["lossless_if_smaller"] and self.params["lossless"] == False:
                if self.params["intelligent_effort"]:
                    args[1] = "-e 9"
                args[0] = "-q 100"

                lossless_path = getUniqueFilePath(self.item_dir, self.item_name + "_l", "jxl", True)
                convert(CJXL_PATH, self.item_abs_path, lossless_path, args, self.n)

                path_pool = [
                    output,
                    lossless_path
                ]
                leaveOnlySmallestFile(path_pool, output)

        elif self.params["format"] == "PNG":
            if self.params["downscaling"]["enabled"]:
                decodeAndDownscale(scl_params, self.item_ext, self.params["misc"]["keep_metadata"])
            else:
                decoder = getDecoder(self.item_ext)

                # Handle metadata
                args = metadata.getArgs(decoder, self.params["misc"]["keep_metadata"])

                convert(decoder, self.item_abs_path, output, args, self.n)
            
        elif self.params["format"] == "WEBP":
            multithreading = 1 if self.available_threads > 1 else 0
            args = [
                f"-quality {self.params['quality']}",
                f"-define webp:thread-level={multithreading}",      # Currently unused. Does not seem to have any effect.
                "-define webp:method=6"
                ]

            if self.params["lossless"]:
                args.pop(0) # Remove quality
                args.append("-define webp:lossless=true")

            # Handle Metadata
            args.extend(metadata.getArgs(IMAGE_MAGICK_PATH, self.params["misc"]["keep_metadata"]))

            if self.params["downscaling"]["enabled"]:
                scl_params["enc"] = IMAGE_MAGICK_PATH
                scl_params["args"] = args
                downscale(scl_params)
            else:
                convert(IMAGE_MAGICK_PATH, self.item_abs_path, output, args, self.n)

            if self.params["lossless_if_smaller"] and self.params["lossless"] == False:
                args.pop(0) # Remove quality
                args.append("-define webp:lossless=true")

                lossless_path = getUniqueFilePath(self.item_dir, self.item_name + "_l", "webp", True)
                convert(IMAGE_MAGICK_PATH, self.item_abs_path, lossless_path, args, self.n)

                path_pool = [
                    output,
                    lossless_path
                ]

                leaveOnlySmallestFile(path_pool, output)

        elif self.params["format"] == "AVIF":
            args = [
                "--min 0",
                "--max 63",
                "-a end-usage=q",
                f"-a cq-level={self.params['quality']}",
                f"-s {self.params['effort']}",
                f"-j {self.available_threads}"
            ]

            # Handle metadata
            args.extend(metadata.getArgs(AVIFENC_PATH, self.params["misc"]["keep_metadata"]))

            if self.params["downscaling"]["enabled"]:
                scl_params["enc"] = AVIFENC_PATH
                scl_params["args"] = args
                downscale(scl_params)
            else:
                convert(AVIFENC_PATH, self.item_abs_path, output, args, self.n)
                    
        elif self.params["format"] == "JPG":
            args = [f"-quality {self.params['quality']}"]

            # Handle Metadata
            args.extend(metadata.getArgs(IMAGE_MAGICK_PATH, self.params["misc"]["keep_metadata"]))

            if self.params["downscaling"]["enabled"]:
                scl_params["enc"] = IMAGE_MAGICK_PATH
                scl_params["args"] = args
                downscale(scl_params)
            else:
                convert(IMAGE_MAGICK_PATH, self.item_abs_path, output, args, self.n)
        elif self.params["format"] == "Smallest Lossless":

            # Populate path pool
            path_pool = {}
            with QMutexLocker(self.mutex):
                for key in self.params["smallest_format_pool"]:     # Iterate through formats ("png", "webp", "jxl")
                    if self.params["smallest_format_pool"][key]:    # If format enabled
                        path_pool[key] = getUniqueFilePath(output_dir, self.item_name, key, True) # Add format

            # Check if no formats selected
            if len(path_pool) == 0:
                self.exception("No formats selected for Smallest Lossless")
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

            # Handle metadata
            args["png"].extend(metadata.getArgs(OXIPNG_PATH, self.params["misc"]["keep_metadata"]))
            args["webp"].extend(metadata.getArgs(IMAGE_MAGICK_PATH, self.params["misc"]["keep_metadata"]))
            args["jxl"].extend(metadata.getArgs(CJXL_PATH, self.params["misc"]["keep_metadata"]))

            # Generate files
            for key in path_pool:
                if key == "png":
                    shutil.copy(self.item_abs_path, path_pool["png"])
                    optimize(OXIPNG_PATH, path_pool["png"], args["png"], self.n)
                elif key == "webp":
                    convert(IMAGE_MAGICK_PATH, self.item_abs_path, path_pool["webp"], args["webp"], self.n)
                elif key == "jxl":
                    src = self.item_abs_path
                    if self.item_ext in JPEG_ALIASES:  # Exception for handling JPG reconstruction
                        src = self.item[3]
                    convert(CJXL_PATH, src, path_pool["jxl"], args["jxl"], self.n)

            # Get file sizes
            file_sizes = {}
            try:
                for key in path_pool:
                    file_sizes[key] = os.path.getsize(path_pool[key])
            except OSError as err:
                # Clean-up and exit
                for key in path_pool:
                    delete(path_pool[key])
                self.exception("Generating formats failed")
                self.signals.completed.emit(self.n)

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
                    delete(path_pool[key])
            
            # Handle the smallest file
            output = path_pool[sm_f_key]
            final_output = os.path.join(output_dir, f"{self.item_name}.{sm_f_key}")
            output_ext = sm_f_key
        else:
            self.exception(f"Unknown Format ({self.params['format']})")

        # Clean-up proxy
        if self.proxy.proxyExists():
            self.proxy.cleanup()
            self.item_abs_path = self.item[3]
        
        # Check for existing files
        with QMutexLocker(self.mutex):
            if self.item_ext == "gif" and self.params["format"] == "PNG":
                pass    # Already handled
            elif os.path.isfile(output):    # Checking if conversion was successful
                mode = self.params["if_file_exists"]
                if mode == "Skip" and self.params["format"] == "Smallest Lossless": # Only for "Smallest Lossless", other cases were handled before
                    if os.path.isfile(final_output):
                        delete(output)
                    else:
                        os.rename(output, final_output)
                else:
                    if mode == "Replace":
                        if os.path.isfile(final_output):
                            delete(final_output)
                    elif mode == "Rename" or mode == "Skip":
                        final_output = getUniqueFilePath(output_dir, self.item_name, output_ext, False)
                    
                    os.rename(output, final_output)

        # Post conversion routines
        if os.path.isfile(final_output):    # Checking if renaming was successful
            # Apply metadata (ExifTool)
            metadata.runExifTool(self.item[3], final_output, self.params["misc"]["keep_metadata"])

            # Apply attributes
            if self.params["misc"]["attributes"]:
                metadata.copyAttributes(self.item[3], final_output)

            # After Conversion
            if self.params["delete_original"]:
                if self.params["delete_original_mode"] == "To Trash":
                    delete(self.item[3], True)
                elif self.params["delete_original_mode"] == "Permanently":
                    delete(self.item[3])
        elif self.item_ext != "gif":        # If conversion failed (GIF naming is handled differently)
            self.exception("Conversion failed")

        self.signals.completed.emit(self.n)