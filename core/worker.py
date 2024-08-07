import os
import shutil
import copy
from pathlib import Path
from typing import Dict
import platform

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
    DJXL_PATH,
    CJPEGLI_PATH,
    JPEG_ALIASES,
    AVIFENC_PATH,
    IMAGE_MAGICK_PATH,
    OXIPNG_PATH
)

from core.proxy import Proxy
from core.pathing import getUniqueFilePath, getExtension, getOutputDir
from core.convert import convert, getDecoder, getDecoderArgs, getExtensionJxl, optimize
from core.downscale import downscale, decodeAndDownscale
import core.metadata as metadata
import data.task_status as task_status
from core.exceptions import CancellationException, GenericException, FileException
import core.conflicts as conflicts
from core.utils import getFreeSpaceLeft

class Signals(QObject):
    started = Signal(int)
    completed = Signal(int)
    canceled = Signal(int)
    exception = Signal(str, str, str)

class Worker(QRunnable):
    def __init__(self,
            n: int,
            abs_path: Path,
            anchor_path: Path,
            params: Dict,
            settings: Dict,
            available_threads: int,
            mutex: QMutex
        ):
        super().__init__()
        self.signals = Signals()
        self.params = copy.deepcopy(params)
        self.settings = settings    # reference, do not modify

        # Convert modules
        self.proxy = Proxy()

        # Threading
        self.n = n  # Thread number
        self.available_threads = available_threads
        self.mutex = mutex
        
        # Item info - always points to the original file
        self.org_item_abs_path = str(abs_path)         # path -> str cast is done for legacy reasons
        
        # Item info - can be (carefully) reassigned
        self.item_name = abs_path.stem
        self.item_ext = abs_path.suffix[1:].lower()
        self.item_dir = str(abs_path.parent)
        self.item_abs_path = str(abs_path)

        # Destination
        self.output = None          # tmp, gets renamed to final_output
        self.output_dir = None
        self.output_ext = None
        self.final_output = None 

        # Flags
        self.skip = False
        self.jpg_to_jxl_lossless = False
        self.jpeg_rec_data_found = False      # Reconstruction data found

        # Misc.
        self.scl_params = None
        self.anchor_path = anchor_path        # keep_dir_struct
    
    def logException(self, id: str, msg: str):
        self.signals.exception.emit(id, msg, str(Path(self.item_abs_path).name))

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
            
            match self.params["format"]:
                case "Lossless JPEG Recompression":
                    self.losslesslyRecompressJPEG()
                case "JPEG Reconstruction":
                    self.reconstructJPEG()
                case "Smallest Lossless":
                    self.smallestLossless()
                case _:
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
    
    def runChecks(self):
        # Input was moved / deleted
        if os.path.isfile(self.org_item_abs_path) == False:
            raise FileException("C0", "File not found")

        # Compatibility
        conflicts.checkForConflicts(
            self.item_ext,
            self.params["format"],
            self.params["downscaling"]["enabled"],
        )
        conflicts.checkForMultipage(
            self.item_ext,
            self.org_item_abs_path,
        )

    def setupConversion(self):
        # Get Output Dir
        self.output_dir = getOutputDir(
            self.item_dir,
            self.anchor_path,
            self.params["custom_output_dir"],
            self.params["custom_output_dir_path"],
            self.params["keep_dir_struct"]
        )

        try:
            os.makedirs(self.output_dir, exist_ok=True)
        except OSError as err:
            raise FileException("S0", f"Failed to create output directory. {err}")

        # Check available space left
        try:
            input_size = os.path.getsize(self.org_item_abs_path)
        except OSError as e:
            raise FileException("S1", f"Geting file size failed. {e}")

        buffer_space = 10 * 1024 ** 2
        free_space_left = getFreeSpaceLeft(self.output_dir)
        if free_space_left <= input_size * 2 + buffer_space and free_space_left != -1:
            raise FileException("S2", "No space left on device.")

        # Assign output extension
        if self.params["format"] == "JPEG Reconstruction":
            if self.item_ext != "jxl":
                raise FileException("S3", "Only JPEG XL images are allowed.")
            
            self.output_ext = getExtensionJxl(self.item_abs_path)
            self.jpeg_rec_data_found = self.output_ext == "jpg"
            if not self.jpeg_rec_data_found and not self.params["jxl_png_fallback"]:
                raise FileException("S4", "Reconstruction data not found.")
        elif self.params["format"] == "Lossless JPEG Recompression":
            if self.item_ext not in JPEG_ALIASES:
                raise FileException("S5", "Only JPEG images are allowed.")
            self.output_ext = "jxl"
        else:
            self.output_ext = getExtension(self.params["format"])
        
        # Assign output path
        with QMutexLocker(self.mutex):
            self.output = getUniqueFilePath(self.output_dir, self.item_name, self.output_ext, True)
        
        self.final_output = os.path.join(self.output_dir, f"{self.item_name}.{self.output_ext}")

        # Skip If needed
        if self.params["if_file_exists"] == "Skip":
            if os.path.isfile(self.final_output) and self.params["format"] != "Smallest Lossless":
                self.skip = True
                return

        # Create Proxy
        if self.proxy.isProxyNeeded(
            self.params["format"],
            self.item_ext,
            self.settings["jpg_encoder"] == "JPEGLI",
            self.params["downscaling"]["enabled"]
        ):
            self.item_abs_path = self.proxy.generate(self.item_abs_path, self.item_ext, self.output_dir, self.item_name, self.n, self.mutex)    # Redirect the source

        # Setup downscaling params
        if self.params["downscaling"]["enabled"]:
            self.scl_params = {
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

    def convert(self):
        args = []
        encoder = None
        format = self.params["format"]

        # Prepare args
        match format:
            case "JPEG XL":
                args = ["" for i in range(4)]   # Legacy

                if self.params["lossless"]:
                    args[0] = "-q 100"
                    if self.settings["jxl_lossless_jpeg"]:
                        args[2] = "--lossless_jpeg=1"
                        if self.item_ext in JPEG_ALIASES:
                            self.jpg_to_jxl_lossless = True
                    else:
                        args[2] = "--lossless_jpeg=0"
                else:
                    args[0] = f"-q {self.params['quality']}"
                    args[2] = "--lossless_jpeg=0"

                args[1] = f"-e {self.params['effort']}"
                args[3] = f"--num_threads={self.available_threads}"

                if self.params["intelligent_effort"] and (self.params["lossless"] or self.params["jxl_modular"]):
                    self.params["intelligent_effort"] = False
                    args[1] = "-e 9"

                if not self.params["lossless"] and self.params["jxl_modular"]:
                    args.append("--modular=1")

                encoder = CJXL_PATH
            case "AVIF":
                args = [
                    f"-q {self.params['quality']}",
                    f"-s {self.params['effort']}",
                    f"-j {self.available_threads}"
                ]
                if self.params["avif_chroma_subsampling"] != "Default":
                    args.append(f"-y {self.params['avif_chroma_subsampling'].replace(':', '')}")

                encoder = AVIFENC_PATH
            case "JPEG":
                if self.settings["jpg_encoder"] == "JPEGLI":
                    args = [f"-q {self.params['quality']}"]
                    if self.settings["disable_progressive_jpegli"]:
                        args.append("-p 0")
                    if self.params["jpegli_chroma_subsampling"] != "Default":
                        args.append(f"--chroma_subsampling={self.params['jpegli_chroma_subsampling'].replace(':', '')}")

                    encoder = CJPEGLI_PATH
                else:
                    args = [f"-quality {self.params['quality']}"]
                    if self.params["jpg_chroma_subsampling"] != "Default":
                        args.append(f"-sampling-factor {self.params['jpg_chroma_subsampling']}")
                    
                    encoder = IMAGE_MAGICK_PATH
            case "WebP":
                args = []

                if self.params["lossless"]:
                    args.append("-define webp:lossless=true")
                else:
                    args.append(f"-quality {self.params['quality']}")
                
                args.extend([
                    f"-define webp:thread-level={1 if self.available_threads > 1 else 0}",
                    f"-define webp:method={self.params['effort']}"
                ])

                encoder = IMAGE_MAGICK_PATH
            case "PNG":
                encoder = getDecoder(self.item_ext)
                args = getDecoderArgs(encoder, self.available_threads)
            case _:
                raise GenericException("C0", f"Unknown format ({self.params['format']})")

        # Prepare metadata
        args.extend(metadata.getArgs(encoder, self.params["misc"]["keep_metadata"], self.jpg_to_jxl_lossless))

        # Custom arguments
        if self.settings["enable_custom_args"]:
            if encoder == AVIFENC_PATH:
                if self.settings["avifenc_args"]:
                    args.append(self.settings["avifenc_args"])
            elif encoder == CJXL_PATH:
                if self.settings["cjxl_args"]:
                    args.append(self.settings["cjxl_args"])
            elif encoder == CJPEGLI_PATH:
                if self.settings["cjpegli_args"]:
                    args.append(self.settings["cjpegli_args"])
            elif encoder == IMAGE_MAGICK_PATH:
                if self.settings["im_args"]:
                    args.append(self.settings["im_args"])

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
                    path_e7 = getUniqueFilePath(self.output_dir, self.item_name, "jxl", True)
                    path_e9 = getUniqueFilePath(self.output_dir, self.item_name, "jxl", True)
                
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
    
    def runExifTool(self):
        # Apply metadata (ExifTool)
        if (
            self.params["format"] not in ("Lossless JPEG Recompression", "JPEG Reconstruction") and
            self.params["misc"]["keep_metadata"].startswith("ExifTool")
        ):
            exiftool_available = metadata.isExifToolAvailable()
            if exiftool_available[0] == False:
                self.logException("E0", exiftool_available[1])
            else:
                cur_mode = self.params["misc"]["keep_metadata"]
                try:
                    et_args = self.settings["exiftool_args"][cur_mode].strip().split(" ")
                    if len(et_args) == 1 and et_args[0] == "":
                        self.logException("E1", f"Argument list for \"{cur_mode}\" is empty.\nPlease add arguments in Settings -> Advanced -> ExifTool Arguments")
                    else:
                        metadata.runExifTool(
                            self.org_item_abs_path,
                            self.output,
                            et_args,
                        )
                except KeyError as e:
                    self.logException("E2", f"ExifTool mode not mapped. {e}")

    def finishConversion(self):
        if self.proxy.proxyExists():
            try:
                self.proxy.cleanup()
            except OSError as err:
                raise FileException("F0", f"Failed to delete proxy. {err}")
            self.item_abs_path = self.org_item_abs_path   # Redirect the source back to original file
        
        try:
            # Checks
            if not os.path.isfile(self.output):
                raise FileException("F2", "Conversion failed (output not found).")
            if os.path.getsize(self.output) == 0:
                raise FileException("F3", "Conversion failed (output is empty).")
            
            # Apply metadata
            self.runExifTool()  # before getsize()

            # Rename / remove
            with QMutexLocker(self.mutex):
                mode = self.params["if_file_exists"]
                
                if self.params["format"] == "Smallest Lossless" and mode == "Skip":
                    if os.path.isfile(self.final_output):
                        os.remove(self.output)
                    else:
                        os.rename(self.output, self.final_output)
                else:
                    if mode == "Replace":
                        if (
                            (self.settings["keep_if_larger"] or self.settings["copy_if_larger"]) and
                            os.path.getsize(self.org_item_abs_path) < os.path.getsize(self.output) and
                            os.path.samefile(self.org_item_abs_path, self.final_output)
                        ):
                            self.final_output = getUniqueFilePath(self.output_dir, self.item_name, self.output_ext, False)
                        else:
                            if os.path.isfile(self.final_output):
                                os.remove(self.final_output)
                    elif mode == "Rename" or mode == "Skip":
                        self.final_output = getUniqueFilePath(self.output_dir, self.item_name, self.output_ext, False)
                    
                    os.rename(self.output, self.final_output)

                # Copy original
                if (
                    self.settings["copy_if_larger"] and
                    os.path.getsize(self.org_item_abs_path) < os.path.getsize(self.final_output) and
                    self.params["format"] not in ("Lossless JPEG Recompression", "JPEG Reconstruction")
                ):
                    os.remove(self.final_output)
                    self.final_output = getUniqueFilePath(self.output_dir, self.item_name, self.item_ext, False)
                    shutil.copy(self.org_item_abs_path, self.final_output)
        except OSError as err:
            raise FileException("F1", f"Conversion could not finish. {err}")

    def postConversionRoutines(self):
        if not os.path.isfile(self.final_output):    # Checking if renaming was successful
            raise FileException("P2", "Output not found.")

        # Apply attributes
        try:
            if self.params["misc"]["attributes"]:
                shutil.copystat(self.org_item_abs_path, self.final_output)
        except OSError as err:
            raise FileException("P0", f"Failed to apply attributes. {err}")

        # Delete original
        if not self.settings["keep_if_larger"] or os.path.getsize(self.org_item_abs_path) > os.path.getsize(self.final_output):
            try:
                if self.params["delete_original"]:
                    if self.params["delete_original_mode"] == "To Trash":
                        send2trash(self.org_item_abs_path)
                    elif self.params["delete_original_mode"] == "Permanently":
                        os.remove(self.org_item_abs_path)
            except OSError as err:
                raise FileException("P1", f"Failed to delete original file. {err}")

    def smallestLossless(self):
        # Populate path pool
        path_pool = {}
        with QMutexLocker(self.mutex):
            for key in self.params["smallest_format_pool"]:
                if self.params["smallest_format_pool"][key]:
                    path_pool[key] = getUniqueFilePath(self.output_dir, self.item_name, key, True)

        if len(path_pool) == 0:
            raise GenericException("SL0", "No formats selected.")

        # Set arguments
        args = {
            "png": [
                "-o 4" if self.params["max_compression"] else "-o 2",
                f"-t {self.available_threads}"
                ],
            "webp": [
                f"-define webp:thread-level={1 if self.available_threads > 1 else 0}",
                "-define webp:method=6",
                "-define webp:lossless=true"
            ],
            "jxl": [
                "-q 100",
                "-e 9" if self.params["max_compression"] else "-e 7",
                f"--num_threads={self.available_threads}",
            ]
        }

        # Handle metadata
        if self.settings["jxl_lossless_jpeg"]:
            self.jpg_to_jxl_lossless = self.item_ext in JPEG_ALIASES
        args["jxl"].extend([f"--lossless_jpeg={1 if self.jpg_to_jxl_lossless else 0}"])

        args["png"].extend(metadata.getArgs(OXIPNG_PATH, self.params["misc"]["keep_metadata"]))
        args["webp"].extend(metadata.getArgs(IMAGE_MAGICK_PATH, self.params["misc"]["keep_metadata"]))
        args["jxl"].extend(metadata.getArgs(CJXL_PATH, self.params["misc"]["keep_metadata"], self.jpg_to_jxl_lossless))

        # Generate files
        for key in path_pool:
            match key:
                case "png":
                    try:
                        shutil.copy(self.item_abs_path, path_pool["png"])
                    except OSError as err:
                        raise FileException("SL1", f"Failed to copy file. {err}")
                    optimize(OXIPNG_PATH, path_pool["png"], args["png"], self.n)
                case "webp":
                    convert(IMAGE_MAGICK_PATH, self.item_abs_path, path_pool["webp"], args["webp"], self.n)
                case "jxl":
                    if self.jpg_to_jxl_lossless:
                        src = self.org_item_abs_path
                    else:
                        src = self.item_abs_path
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

        # Get the smallest file
        sm_f_key = min(path_pool, key=lambda key: file_sizes[key])

        # Remove bigger files
        for key in path_pool:
            if key != sm_f_key:
                try:
                    os.remove(path_pool[key])
                except OSError as err:
                    raise FileException("SL4", f"Failed to delete tmp files. {err}")

        # Handle the smallest file
        self.output = path_pool[sm_f_key]
        self.output_ext = sm_f_key
        self.final_output = os.path.join(self.output_dir, f"{self.item_name}.{sm_f_key}")

    def losslesslyRecompressJPEG(self):
        args = [
            "--lossless_jpeg=1",
            f"-e {self.params['effort']}",
            f"--num_threads={self.available_threads}",
        ]
        convert(CJXL_PATH, self.item_abs_path, self.output, args, self.n)

    def reconstructJPEG(self):
        convert(DJXL_PATH, self.org_item_abs_path, self.output, [f"--num_threads={self.available_threads}"], self.n)
