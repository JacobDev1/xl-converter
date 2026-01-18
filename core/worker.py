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
from core.pathing import getUniqueFilePath, getExtension, getOutputDir, getUniqueTmpFilePath, removeFile
from core.convert import getDecoder, getDecoderArgs, getExtensionJxl, runBinary, cleanUp, runOxipng
from core.downscale import downscale, decodeAndDownscale
import core.metadata as metadata
import data.task_status as task_status
from core.exceptions import CancellationException, GenericException, FileException
import core.conflicts as conflicts
from core.utils import getFreeSpaceLeft, remove
import core.lossless_jpeg as lossless_jpeg
from core.ram_optimizer import RAMOptimizer
import core.timestamps as timestamps

class WorkerSignals(QObject):
    started = Signal(int)
    completed = Signal(int, bool)
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
            mutex: QMutex,
            signals: WorkerSignals,
        ):
        super().__init__()
        self.signals = signals
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
        self.skipped = False
        self.lossless_jpeg = False

        # Misc.
        self.scl_params = None
        self.anchor_path = anchor_path        # keep_dir_struct
        self.src_timestamps = None
    
    def logException(self, id_str: str, msg: str):
        self.signals.exception.emit(id_str, msg, str(self.org_item_abs_path))

    @Slot()
    def run(self):
        if task_status.wasCanceled():
            self.signals.canceled.emit(self.n)
            return
        else:
            self.signals.started.emit(self.n)

        try:
            self.runChecks()
            self.setupConversion()

            if self.skip:
                self.skipped = True
                return
            
            self.runDynamicRamOptimizer()

            match self.params["format"]:
                case "Lossless JPEG Transcoding":
                    self.losslesslyTranscodeJPEG()
                case "JPEG Reconstruction":
                    self.reconstructJPEG()
                case "Smallest Lossless":
                    self.smallestLossless()
                case "PNG Optimization":
                    self.PNGOptimization()
                case _:
                    self.convert()
            
            self.finishConversion()
            self.postConversionRoutines()
        except CancellationException:
            self.signals.canceled.emit(self.n)
            return
        except (GenericException, FileException) as err:
            self.logException(err.id, err.msg)
        except OSError as err:
            self.logException("OSError", str(err))
        except Exception as err:
            self.logException("Exception", str(err))
        finally:
            self.proxy.cleanUp(raising=False)     # Cleans up proxy if it wasn't cleaned up before. A no-op if no proxy exists.
            self.signals.completed.emit(self.n, self.skipped)
    
    def runChecks(self):
        # Input was moved / deleted
        if os.path.isfile(self.org_item_abs_path) == False:
            raise FileException("C0", "File not found")

        # Compatibility
        conflicts.checkForConflicts(
            self.item_ext,
            self.org_item_abs_path,
            self.params["format"],
            self.params["downscaling"]["enabled"],
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
            if self.output_ext != "jpg" and not self.params["jxl_png_fallback"]:
                raise FileException("S4", "Reconstruction data not found.")
        elif self.params["format"] == "Lossless JPEG Transcoding":
            if self.item_ext not in JPEG_ALIASES:
                raise FileException("S5", "Only JPEG images are allowed.")
            self.output_ext = "jxl"
        elif self.params["format"] == "PNG Optimization":
            if self.item_ext != "png":
                raise FileException("S7", "Only PNG images are allowed.")
            self.output_ext = "png"
        else:
            self.output_ext = getExtension(self.params["format"])
        
        # Assign output path
        with QMutexLocker(self.mutex):
            self.output = getUniqueTmpFilePath(self.output_dir, self.output_ext)
        
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
                "megapixels": self.params["downscaling"]["megapixels"],
                "resample": self.params["downscaling"]["resample"],
                "n": self.n,
            }
        
        # Get timestamps
        if self.params["misc"]["keep_timestamps"]:
            try:
                self.src_timestamps = timestamps.getTimestamps(self.org_item_abs_path)
            except (OSError, Exception) as e:
                self.logException("S6", f"Cannot extract timestamps from source. {e}")

    def convert(self):
        args = []
        encoder = None

        # Prepare args
        match self.params["format"]:
            case "JPEG XL":
                args = ["" for i in range(4)]   # Legacy

                if self.params["lossless"]:
                    args[0] = "-q 100"
                    if self.settings["jxl_auto_lossless_jpeg"]:
                        args[2] = "--lossless_jpeg=1"
                        if self.item_ext in JPEG_ALIASES:
                            self.lossless_jpeg = True
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
                    f"-j {self.available_threads}",
                ]
                match self.settings["avif_encoder"]:
                    case "AOM AV1":
                        args.append("-c aom")
                        if self.params["aom_av1_chroma_subsampling"] != "Default":
                            args.append(f"-y {self.params['aom_av1_chroma_subsampling'].replace(':', '')}")
                        if self.settings["avif_aom_iq_tune"]:  # libaom version >= v3.12.0
                            args.append("-a tune=iq")
                    case "SVT-AV1-PSY":             # Assuming SVT-AV1 was swapped before compilation
                        args.append("-c svt")
                        args.append("-y 420")       # SVT-AV1 only supports YUV:4:2:0
                        args.append("-a tune=4")    # Still image tuning
                    case _:
                        raise GenericException("C4", "Unrecognized AVIF encoder.")

                if self.settings["avif_bit_depth"] != "Auto":
                    args.append(f"-d {self.settings['avif_bit_depth']}")

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
        args.extend(metadata.getArgs(encoder, self.params["misc"]["keep_metadata"], self.lossless_jpeg))

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

            if self.params["format"] == "PNG":
                decodeAndDownscale(self.scl_params, self.item_ext, self.params["misc"]["keep_metadata"], self.mutex)
            else:
                downscale(self.scl_params, self.mutex)
        else:   # No downscaling
            if self.params["format"] == "JPEG XL" and self.params["intelligent_effort"]:
                with QMutexLocker(self.mutex):
                    path_e7 = getUniqueTmpFilePath(self.output_dir, "jxl")
                    path_e9 = getUniqueTmpFilePath(self.output_dir, "jxl")
                
                args[1] = "-e 7"
                runBinary(encoder, args, self.item_abs_path, path_e7, delete_if_canceled=[path_e7])

                args[1] = "-e 9"
                runBinary(encoder, args, self.item_abs_path, path_e9, delete_if_canceled=[path_e7, path_e9])

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
                stdout, stderr = runBinary(encoder, args, self.item_abs_path, self.output, args_after_input=(encoder == IMAGE_MAGICK_PATH))
                if not os.path.isfile(self.output):
                    if self.lossless_jpeg and "JPEG bitstream reconstruction data could not be created" in stderr:
                        err_msg = 'The JPEG image could not be transcoded (unsupported type or too much tail data). Enabling the "Normalize" option may help. Set "Format / Mode" to "Lossless JPEG Transcoding" to use it.'
                    else:
                        err_msg = f"[{os.path.basename(encoder)}] {stderr}"

                    raise FileException("C3", err_msg)

    def runExifTool(self):
        # Apply metadata (ExifTool)
        if (
            not self.lossless_jpeg and
            self.params["misc"]["keep_metadata"].startswith("ExifTool")
        ):
            cur_mode = self.params["misc"]["keep_metadata"]
            try:
                metadata.runExifTool(
                    self.org_item_abs_path,
                    self.output,
                    self.settings["exiftool_args"][cur_mode].strip().split(" "),
                )
            except KeyError as e:
                self.logException("E2", f"ExifTool mode not mapped. {e}")

    def finishConversion(self):
        if self.proxy.proxyExists():
            try:
                self.proxy.cleanUp()
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
                        self.skipped = True
                        os.remove(self.output)
                    else:
                        os.rename(self.output, self.final_output)
                else:
                    if mode == "Replace":
                        if (
                            (self.settings["keep_if_larger"] or self.settings["copy_if_larger"]) and
                            os.path.getsize(self.org_item_abs_path) < os.path.getsize(self.output) and
                            (os.path.isfile(self.final_output) and os.path.samefile(self.org_item_abs_path, self.final_output))
                        ):
                            self.final_output = getUniqueFilePath(self.output_dir, self.item_name, self.output_ext)
                        elif (
                            not self.params["custom_output_dir"] and
                            self.params["delete_original"] and
                            (os.path.isfile(self.final_output) and os.path.samefile(self.org_item_abs_path, self.final_output))
                        ):
                            if self.params["delete_original_mode"] == "To Trash":
                                send2trash(self.final_output)
                            elif self.params["delete_original_mode"] == "Permanently":
                                removeFile(self.final_output)
                        else:
                            removeFile(self.final_output)
                    elif mode == "Rename" or mode == "Skip":
                        self.final_output = getUniqueFilePath(self.output_dir, self.item_name, self.output_ext)
                    
                    os.rename(self.output, self.final_output)

                # Copy original
                if (
                    self.settings["copy_if_larger"] and
                    os.path.getsize(self.org_item_abs_path) < os.path.getsize(self.final_output) and
                    self.params["format"] not in ("Lossless JPEG Transcoding", "JPEG Reconstruction", "PNG") and
                    not os.path.samefile(self.org_item_abs_path, self.final_output)
                ):
                    os.remove(self.final_output)
                    self.final_output = getUniqueFilePath(self.output_dir, self.item_name, self.item_ext)
                    shutil.copyfile(self.org_item_abs_path, self.final_output)  # Avoid preserving "Read-only" attribute on Windows, as it will conflict with preserving time attributes later on.
        except OSError as err:
            raise FileException("F1", f"Conversion could not finish. {err}")

    def postConversionRoutines(self):
        if not os.path.isfile(self.final_output):    # Checking if renaming was successful
            raise FileException("P2", "Output not found.")

        # Delete original
        if (
            (
                not self.settings["keep_if_larger"] or
                os.path.getsize(self.org_item_abs_path) > os.path.getsize(self.final_output)
            ) and
            not os.path.samefile(self.org_item_abs_path, self.final_output)
        ):
            try:
                if self.params["delete_original"]:
                    if self.params["delete_original_mode"] == "To Trash":
                        send2trash(self.org_item_abs_path)
                    elif self.params["delete_original_mode"] == "Permanently":
                        removeFile(self.org_item_abs_path)
            except OSError as err:
                raise FileException("P1", f"Failed to delete original file. {err}")

        # Apply timestamps
        if self.params["misc"]["keep_timestamps"] and self.src_timestamps:
            try:
                timestamps.applyTimestamps(self.final_output, self.src_timestamps)
            except (OSError, Exception) as err:
                raise FileException("P0", f"Failed to apply timestamps. {err}")

    def runDynamicRamOptimizer(self) -> None:
        with QMutexLocker(self.mutex):
            if not RAMOptimizer.isEnabled():
                return

            self.available_threads = RAMOptimizer.run(
                self.available_threads,
                self.org_item_abs_path,
                self.params["format"],
                self.settings["avif_encoder"],
                self.params["effort"],
                self.params["jxl_modular"],
                self.params["lossless"],
                self.params["intelligent_effort"],
            )

    def smallestLossless(self):
        # Populate path pool
        path_pool = {}
        with QMutexLocker(self.mutex):
            for key in self.params["smallest_format_pool"]:
                if self.params["smallest_format_pool"][key]:
                    path_pool[key] = getUniqueTmpFilePath(self.output_dir, key)

        if len(path_pool) == 0:
            raise GenericException("SL0", "No formats selected.")

        # Set arguments
        args = {
            "png": [
                "-o 4" if self.params["max_compression"] else "-o 2",
                f"-t {self.available_threads}",
                "--np", "--nc",
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

        # Allow bit depth reduction
        if self.params["smallest_format_pool"]["webp"]:
            args["jxl"].append("--override_bitdepth=8")
        else:
            args["png"].append("--nb")
        
        # Handle metadata
        if self.settings["jxl_auto_lossless_jpeg"]:
            self.lossless_jpeg = self.item_ext in JPEG_ALIASES
        args["jxl"].extend([f"--lossless_jpeg={1 if self.lossless_jpeg else 0}"])

        args["png"].extend(metadata.getArgs(OXIPNG_PATH, self.params["misc"]["keep_metadata"]))
        args["webp"].extend(metadata.getArgs(IMAGE_MAGICK_PATH, self.params["misc"]["keep_metadata"]))
        args["jxl"].extend(metadata.getArgs(CJXL_PATH, self.params["misc"]["keep_metadata"], self.lossless_jpeg))

        # Generate files
        delete_if_canceled = list(path_pool.values())
        if self.proxy.proxyExists():
            delete_if_canceled.append(self.proxy.getPath())

        def _runBinary(encoder_path: str, args: str, src: str, dst: str | None = None, args_after_input=False, delete_if_canceled: list[str] = []) -> None:
            out, err = runBinary(encoder_path, args, src, dst, args_after_input=args_after_input, delete_if_canceled=delete_if_canceled)
            if dst is not None and not os.path.isfile(dst):
                cleanUp(delete_if_canceled)
                raise FileException("SL5", str(err))

        if "png" in path_pool:
            try:
                shutil.copy(self.item_abs_path, path_pool["png"])
            except OSError as err:
                raise FileException("SL1", f"Failed to copy file. {err}")
            _runBinary(OXIPNG_PATH, args["png"], path_pool["png"], delete_if_canceled=delete_if_canceled)
        
        if "webp" in path_pool:
            _runBinary(IMAGE_MAGICK_PATH, args["webp"], self.item_abs_path, path_pool["webp"], args_after_input=True, delete_if_canceled=delete_if_canceled)

        if "jxl" in path_pool:
            src = self.org_item_abs_path if self.lossless_jpeg else self.item_abs_path
            _runBinary(CJXL_PATH, args["jxl"], src, path_pool["jxl"], delete_if_canceled=delete_if_canceled)

        # Get file sizes
        file_sizes = {}
        try:
            for key in path_pool:
                file_sizes[key] = os.path.getsize(path_pool[key])
        except OSError as err:
            cleanUp(list(path_pool.values()))
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

    def losslesslyTranscodeJPEG(self):
        def _normalize() -> str:
            """Normalizes a JPEG image and returns path to it.
            
            Exceptions:
            FileException: if normalization fails
            """
            with QMutexLocker(self.mutex):
                _normalized_path = getUniqueTmpFilePath(self.output_dir, "jpg")
            success, stdout, stderr = lossless_jpeg.normalizeJPEG(
                self.org_item_abs_path,
                _normalized_path,
            )
            if not success:
                raise FileException("lossless_jpeg_2", f"Normalizing failed. {stderr}")
            return _normalized_path

        def _transcode() -> (bool, str):
            """
            Returns:
            (success, stderr)
            """
            success, stdout, stderr = lossless_jpeg.transcodeJPEGtoJPEGXL(
                self.item_abs_path,
                self.output,
                self.params["effort"],
                self.available_threads,
            )
            return (success, stderr)

        def _verify() -> None:
            """Verifies reconstruction data and checksum.
            
            Exceptions:
            FileException: if verification fails
            """
            with QMutexLocker(self.mutex):
                verify_tmp_path = getUniqueTmpFilePath(self.output_dir, "jpg")
            success, stdout, stderr = lossless_jpeg.verifyJPEGXLReconstructionData(
                self.output,
                self.item_abs_path,
                verify_tmp_path,
                self.available_threads,
            )

            if not success:
                remove(self.output, exc_id="lossless_jpeg_1")
                raise FileException("lossless_jpeg_0", f"Verification failed. {stderr}")

        # Main part
        self.lossless_jpeg = True
        normalized_jpeg_path = None

        if (self.params["jxl_normalize_enable"] and self.params["jxl_normalize_when"] == "Always"):
            normalized_jpeg_path = self.item_abs_path = _normalize()
        
        success, stderr = _transcode()
        if not success:

            failed, err_id, err_msg = False, "", ""
            if normalized_jpeg_path is None and (self.params["jxl_normalize_enable"] and self.params["jxl_normalize_when"] == "On Fail"):   # Normalize == On Fail
                normalized_jpeg_path = self.item_abs_path = _normalize()
                success, stderr = _transcode()
                failed, err_id, err_msg = not success, "lossless_jpeg_3", f"Transcoding failed. Image may be CMYK or of other unsupported type.\n\n{stderr}"
            elif normalized_jpeg_path is not None:  # Normalize == Always
                failed, err_id, err_msg = True, "lossless_jpeg_4", f"Transcoding failed. Image may be CMYK or of other unsupported type.\n\n{stderr}"
            else:                                   # Normalize off
                failed, err_id, err_msg = True, "lossless_jpeg_5", f"Transcoding failed most likely due to the limitations of Lossless JPEG Transcoding. Enabling \"Normalize\" may help; however you should review the documentation before doing so.\n\n{stderr}"

            if failed:
                if normalized_jpeg_path:
                    remove(normalized_jpeg_path, exc_id="lossless_jpeg_6")
                    normalized_jpeg_path = None
                raise FileException(err_id, err_msg)

        if self.params["jxl_verify"]:
            _verify()
        
        if normalized_jpeg_path:
            remove(normalized_jpeg_path, exc_id="lossless_jpeg_7")

    def reconstructJPEG(self):
        self.lossless_jpeg = True
        success, stdout, stderr = lossless_jpeg.reconstructJPEGfromJPEGXL(
            self.org_item_abs_path,
            self.output,
            self.available_threads,
        )

        if not success:
            raise FileException("reconstruct_0", f"Reconstruction failed. {stderr}")
    
    def PNGOptimization(self):
        args = [
            f"-o {self.params['effort']}",
            f"-t {self.available_threads}",
            "--np", "--nc",
        ]
        args.extend(
            metadata.getArgs(OXIPNG_PATH, self.params["misc"]["keep_metadata"])
        )
        stdout, stderr = runOxipng(
            args,
            self.item_abs_path,
            self.output,
        )
        if not os.path.isfile(self.output):
            raise FileException("png_opt_0", f"Optimization failed. {stderr}")
