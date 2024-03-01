import os
import shutil
import copy
from pathlib import Path
from typing import Dict

from PySide6.QtCore import (
    QRunnable,
    QObject,
    Signal,
    Slot,
    QMutexLocker,
    QMutex,
)
from send2trash import send2trash

from data.constants import (
    CJXL_PATH,
    JPEG_ALIASES,
    AVIFENC_PATH,
    IMAGE_MAGICK_PATH,
    OXIPNG_PATH
)

from core.proxy import Proxy
from core.pathing import getUniqueFilePath, getPathGIF, getExtension
from core.conflicts import Conflicts
from core.convert import convert, getDecoder, getExtensionJxl, optimize
from core.downscale import downscale, decodeAndDownscale
import core.metadata as metadata
import data.task_status as task_status
from core.exceptions import CancellationException, GenericException, FileException

class Signals(QObject):
    started = Signal(int)
    completed = Signal(int)
    canceled = Signal(int)
    exception = Signal(str, str, str)

class Worker(QRunnable):
    def __init__(self, n: int, item_path: Path, params: Dict, settings: Dict, available_threads: int, mutex: QMutex):
        super().__init__()
        self.signals = Signals()
        self.params = copy.deepcopy(params)
        self.settings = settings    # reference, do not modify

        # Convert modules
        self.proxy = Proxy()
        self.conflicts = Conflicts()

        # Threading
        self.n = n  # Thread number
        self.available_threads = available_threads
        self.mutex = mutex
        
        # Item info - always points to the original file
        self.org_item_abs_path = str(item_path)         # path -> str cast is done for legacy reasons
        
        # Item info - can be (carefully) reassigned
        self.item_name = item_path.stem
        self.item_ext = item_path.suffix[1:].lower()
        self.item_dir = str(item_path.parent)
        self.item_abs_path = str(item_path)

        # Destination
        self.output = None          # tmp, gets renamed to final_output
        self.output_dir = None
        self.output_ext = None
        self.final_output = None 

        # Misc.
        self.scl_params = None
        self.skip = False
        self.jpg_to_jxl_lossless = False
    
    def logException(self, id, msg):
        self.signals.exception.emit(id, msg, self.org_item_abs_path)

    @Slot()
    def run(self):
        if task_status.wasCanceled():
            self.signals.canceled.emit(self.n)
            return False
        else:
            self.signals.started.emit(self.n)

        try:
            self.runChecks()
            self.setupConversion()

            if self.skip:
                self.signals.completed.emit(self.n)
                return
            
            if self.params["format"] == "Smallest Lossless":
                self.smallestLossless()
            else:
                self.convert()
            
            self.finishConversion()
            self.postConversionRoutines()
        except CancellationException:
            self.signals.canceled.emit(self.n)
            return
        except (GenericException, FileException) as err:
            self.logException(err.id, err.msg)
            self.signals.completed.emit(self.n)
            return
        except OSError as err:
            self.logException("OSError", str(err))
            self.signals.completed.emit(self.n)
            return
        except Exception as err:
            self.logException("Exception", str(err))
            self.signals.completed.emit(self.n)
            return

        self.signals.completed.emit(self.n)
    
    def convert(self):
        args = []
        encoder = None
        format = self.params["format"]

        # Prepare args
        match format:
            case "JPEG XL":
                args = ["" for i in range(4)]   # Legacy reasons

                if self.params["lossless"]:
                    args[0] = "-q 100"
                    args[2] = "--lossless_jpeg=1"
                    if self.item_ext in JPEG_ALIASES:
                        self.jpg_to_jxl_lossless = True
                else:
                    args[0] = f"-q {self.params['quality']}"
                    args[2] = "--lossless_jpeg=0"

                args[1] = f"-e {self.params['effort']}"
                args[3] = f"--num_threads={self.available_threads}"

                if self.params["intelligent_effort"] and (self.params["lossless"] or self.params["jxl_mode"] == "Modular"):
                    self.params["intelligent_effort"] = False
                    args[1] = "-e 9"

                if not self.params["lossless"]:
                    if self.params["jxl_mode"] == "VarDCT":
                        args.append("--modular=0")
                    elif self.params["jxl_mode"] == "Modular":
                        args.append("--modular=1")
                    # Encoder decides by itself when no arguments are passed

                encoder = CJXL_PATH
            case "AVIF":
                args = [
                    f"-q {self.params['quality']}",
                    f"-s {self.params['effort']}",
                    f"-j {self.available_threads}"
                ]

                encoder = AVIFENC_PATH
            case "JPG":
                args = [f"-quality {self.params['quality']}"]
                encoder = IMAGE_MAGICK_PATH
            case "WEBP":
                args = []

                if self.params["lossless"]:
                    args.append("-define webp:lossless=true")
                else:
                    args.append(f"-quality {self.params['quality']}")
                
                args.extend([
                    f"-define webp:thread-level={1 if self.available_threads > 1 else 0}",
                    "-define webp:method=6"
                ])

                encoder = IMAGE_MAGICK_PATH
            case "PNG":
                encoder = getDecoder(self.item_ext)
            case _:
                raise GenericException("C0", f"Unknown Format ({self.params['format']})")

        # Prepare metadata
        args.extend(metadata.getArgs(encoder, self.params["misc"]["keep_metadata"], self.jpg_to_jxl_lossless))

        # Convert & downscale
        if self.params["downscaling"]["enabled"]:
            self.scl_params["enc"] = encoder
            self.scl_params["args"] = args
            self.scl_params["jxl_int_e"] = self.params["intelligent_effort"]

            if format == "PNG":
                decodeAndDownscale(self.scl_params, self.item_ext, self.params["misc"]["keep_metadata"])
            else:
                downscale(self.scl_params)
        else:   # No downscaling
            if format == "JPEG XL" and self.params["intelligent_effort"]:
                with QMutexLocker(self.mutex):
                    path_e7 = getUniqueFilePath(self.output_dir,self.item_name, "jxl", True)
                    path_e9 = getUniqueFilePath(self.output_dir,self.item_name, "jxl", True)
                
                args[1] = "-e 7"
                convert(encoder, self.item_abs_path, path_e7, args, self.n)

                if task_status.wasCanceled():
                    try:
                        os.remove(path_e7)
                    except OSError as err:
                        raise FileException("C1", err)
                    
                    raise CancellationException()

                args[1] = "-e 9"
                convert(encoder, self.item_abs_path, path_e9, args, self.n)

                try:
                    if os.path.getsize(path_e9) < os.path.getsize(path_e7):
                        os.remove(path_e7)
                        os.rename(path_e9, self.output)
                    else:
                        os.remove(path_e9)
                        os.rename(path_e7, self.output)
                except OSError as err:
                    raise FileException("C2", err)
            else:   # Regular conversion
                convert(encoder, self.item_abs_path, self.output, args, self.n)
        
        # Lossless If smaller
        if self.params["lossless_if_smaller"] and format in ("JPEG XL", "WEBP"):
            match format:
                case "WEBP":
                    args[0] = "-define webp:lossless=true"
                case "JPEG XL":
                    args[0] = "-q 100"
                    if self.params["intelligent_effort"]:
                        args[1] = "-e 9"
            
            with QMutexLocker(self.mutex):
                lossless_path = getUniqueFilePath(self.item_dir, self.item_name, self.output_ext, True)
            
            convert(encoder, self.item_abs_path, lossless_path, args, self.n)

            try:
                if os.path.getsize(lossless_path) < os.path.getsize(self.output):
                    os.remove(self.output)
                    os.rename(lossless_path, self.output)
                else:
                    os.remove(lossless_path)
            except OSError as err:
                raise FileException("C3", err)

    def setupConversion(self):
        # Choose Output Dir           
        self.output_dir = ""
        if self.params["custom_output_dir"]:
            self.output_dir = self.params["custom_output_dir_path"]

            if not os.path.isabs(self.output_dir):   # If path relative
                self.output_dir = os.path.join(self.item_dir, self.output_dir)

            try:
                os.makedirs(self.output_dir, exist_ok=True)
            except OSError as err:
                raise FileException("S0", f"Failed to create output directory. {err}")
        else:
            self.output_dir = self.item_dir

        # Assign output paths
        self.output_ext = getExtension(self.params["format"])
        if self.params["format"] == "PNG" and self.item_ext == "jxl" and self.params["reconstruct_jpg"]:
            self.output_ext = getExtensionJxl(self.item_abs_path)  # Reverse JPG reconstruction
        
        self.output = None
        with QMutexLocker(self.mutex):
            self.output = getUniqueFilePath(self.output_dir, self.item_name, self.output_ext, True)        # Initial self.output
        self.final_output = os.path.join(self.output_dir, f"{self.item_name}.{self.output_ext}")           # After conversion: self.output -> self.final_output 

        # If file exists - for decoding GIF only
        if self.item_ext == "gif" and self.params["format"] == "PNG":
            if self.params["if_file_exists"] == "Skip":
                self.skip = True
                return

            self.output = getPathGIF(self.output_dir, self.item_name, self.params["if_file_exists"])
            self.final_output = self.output

        # Skip If needed
        if self.params["if_file_exists"] == "Skip":
            if os.path.isfile(self.final_output) and self.params["format"] not in ("Smallest Lossless"):
                self.skip = True
                return

        # Create Proxy
        if self.proxy.isProxyNeeded(self.params["format"], self.item_ext, self.params["downscaling"]["enabled"]):

            if not self.proxy.generate(self.item_abs_path, self.item_ext, self.output_dir, self.item_name, self.n):
                raise FileException("S1", f"Proxy could not be generated to {self.proxy.getPath()}")
            
            self.item_abs_path = self.proxy.getPath()     # Redirect the source

        # Setup downscaling params
        if self.params["downscaling"]["enabled"]:
            self.scl_params = {    # "None" values are assigned later on
                "mode": self.params["downscaling"]["mode"],
                "enc": None,
                "format": self.params["format"],    # To recognize intelligent effort
                "jxl_int_e": None,   # An exception to handle intelligent effort
                "src": self.item_abs_path,
                "dst": self.output,
                "dst_dir": self.output_dir,
                "name": self.item_name,
                "args": None,
                "max_size": self.params["downscaling"]["file_size"],
                "percent": self.params["downscaling"]["percent"],
                "width": self.params["downscaling"]["width"],
                "height": self.params["downscaling"]["height"],
                "shortest_side": self.params["downscaling"]["shortest_side"],
                "longest_side": self.params["downscaling"]["longest_side"],
                "resample": self.params["downscaling"]["resample"],
                "n": self.n,
            }

    def finishConversion(self):
        if self.proxy.proxyExists():
            try:
                self.proxy.cleanup()
            except OSError as err:
                raise FileException("F1", f"Failed to delete proxy. {err}")
            self.item_abs_path = self.org_item_abs_path   # Redirect the source back to original file
        
        # Check for existing files
        try:
            with QMutexLocker(self.mutex):
                if self.item_ext == "gif" and self.params["format"] == "PNG":
                    pass    # Already handled
                elif os.path.isfile(self.output):    # Checking if conversion was successful
                    mode = self.params["if_file_exists"]
                    
                    if mode == "Skip" and self.params["format"] == "Smallest Lossless": # Only for "Smallest Lossless", other cases were handled before
                        if os.path.isfile(self.final_output):
                            os.remove(self.output)
                        else:
                            os.rename(self.output, self.final_output)
                    else:
                        if mode == "Replace":
                            if os.path.isfile(self.final_output):
                                os.remove(self.final_output)
                        elif mode == "Rename" or mode == "Skip":
                            self.final_output = getUniqueFilePath(self.output_dir, self.item_name, self.output_ext, False)
                        
                        os.rename(self.output, self.final_output)
        except OSError as err:
            raise FileException("F0", f"Could not finish conversion. {err}")

    def postConversionRoutines(self):
        if os.path.isfile(self.final_output):    # Checking if renaming was successful
            
            # Apply metadata
            metadata.runExifTool(self.org_item_abs_path, self.final_output, self.params["misc"]["keep_metadata"])

            # Apply attributes
            try:
                if self.params["misc"]["attributes"]:
                    shutil.copystat(self.org_item_abs_path, self.final_output)
            except OSError as err:
                raise FileException("P0", f"Failed to apply attributes. {err}")

            # After Conversion
            try:
                if self.params["delete_original"]:
                    if self.params["delete_original_mode"] == "To Trash":
                        send2trash(self.org_item_abs_path)
                    elif self.params["delete_original_mode"] == "Permanently":
                        os.remove(self.org_item_abs_path)
            except OSError as err:
                raise FileException("P1", f"Failed to delete original file. {err}")
        elif self.item_ext != "gif":        # If conversion failed (GIF naming is handled differently)
            raise FileException("P2", "Conversion failed, output not found.")

    def runChecks(self):
        # Input was moved / deleted
        if os.path.isfile(self.org_item_abs_path) == False:
            raise FileException("C0", "File not found")

        # Check for UTF-8 characters
        if (
            os.name == "nt" and
            not self.settings["disable_jxl_utf8_check"] and
            (
                self.params["format"] == "JPEG XL" or
                self.item_ext == "jxl" or
                (
                    self.params["format"] == "Smallest Lossless" and
                    self.params["smallest_format_pool"]["jxl"]
                )
            )
        ):
            try:
                self.org_item_abs_path.encode("cp1252")
            except UnicodeEncodeError:
                raise GenericException("C1", "JPEG XL does not support paths with non-ANSI characters on Windows.")

        # Check for conflicts - GIFs and APNGs
        self.conflicts.checkForConflicts(self.item_ext, self.params["format"], self.params["intelligent_effort"], self.params["effort"], self.params["downscaling"]["enabled"])
        
        if self.conflicts.conflictOccurred():
            for i in self.conflicts.getConflictsMsg():
                self.logException("cf.", i)
            raise GenericException("C2", "Conflicts occurred")
        
        if self.conflicts.jxlConflictOccurred():
            # Normalize values
            self.params["effort"] = self.conflicts.jxlGetNormEffort(self.params["effort"])
            self.params["intelligent_effort"] = self.conflicts.jxlGetNormIntEffort(self.params["intelligent_effort"])
            for i in self.conflicts.getConflictsMsg():
                self.logException("cf.", i)
    
    def smallestLossless(self):
        # Populate path pool
        path_pool = {}
        with QMutexLocker(self.mutex):
            for key in self.params["smallest_format_pool"]:     # Iterate through formats ("png", "webp", "jxl")
                if self.params["smallest_format_pool"][key]:    # If format enabled
                    path_pool[key] = getUniqueFilePath(self.output_dir, self.item_name, key, True) # Add format

        # Check if no formats selected
        if len(path_pool) == 0:
            raise GenericException("SL0", "No formats selected for Smallest Lossless")

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
        args["jxl"].extend(metadata.getArgs(CJXL_PATH, self.params["misc"]["keep_metadata"], self.jpg_to_jxl_lossless))

        # Generate files
        for key in path_pool:
            if key == "png":
                try:
                    shutil.copy(self.item_abs_path, path_pool["png"])
                except OSError as err:
                    raise FileException("SL1", err)
                optimize(OXIPNG_PATH, path_pool["png"], args["png"], self.n)
            elif key == "webp":
                convert(IMAGE_MAGICK_PATH, self.item_abs_path, path_pool["webp"], args["webp"], self.n)
            elif key == "jxl":
                src = self.item_abs_path
                if self.item_ext in JPEG_ALIASES:  # Exception for handling JPG reconstruction
                    src = self.org_item_abs_path
                convert(CJXL_PATH, src, path_pool["jxl"], args["jxl"], self.n)

        # Get file sizes
        file_sizes = {}
        try:
            for key in path_pool:
                file_sizes[key] = os.path.getsize(path_pool[key])
        except OSError as err:
            # Clean-up and exit
            try:
                for key in path_pool:
                    os.remove(path_pool[key])
            except OSError as err:
                raise FileException("SL3", f"Failed to delete tmp files. {err}")
            raise FileException("SL2", f"Failed to get file sizes. {err}")

        # Get the smallest item
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
                try:
                    os.remove(path_pool[key])
                except OSError as err:
                    raise FileException("SL4", f"Failed to delete tmp files. {err}")

        # Handle the smallest file
        self.output = path_pool[sm_f_key]
        self.final_output = os.path.join(self.output_dir, f"{self.item_name}.{sm_f_key}")
        self.output_ext = sm_f_key
    
    def log(self, msg):
        print(f"[Worker #{self.n}] {msg} ({self.item_name}.{self.item_ext})")