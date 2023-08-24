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
    def __init__(self, n, item, params):
        super().__init__()
        self.n = n
        self.signals = Signals()
        self.convert = Convert()

        self.params = params
        
        # Item info
        self.item = item    # Original file
        
        self.item_name = item[0]    # These can be reassigned
        self.item_ext = item[1]
        self.item_dir = item[2]
        self.item_abs_path = item[3]
    
    @Slot()
    def run(self):
        if task_status.isCanceled():
            self.signals.canceled.emit(self.n)
            return
        else:
            self.signals.started.emit(self.n)

            if os.path.isfile(self.item[3]) == False:   # If input file is still in the data, but was removed
                print(f"[Worker #{self.n}] File not found ({self.item[3]})")
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
            if self.params["format"] == "JPEG XL":
                output_ext = "jxl"
                if self.item_ext in ALLOWED_INPUT_CJXL:
                    need_proxy = False
            elif self.params["format"] == "PNG":
                output_ext = "png"
                need_proxy = False
            elif self.params["format"] == "AVIF":
                output_ext = "avif"
                if self.item_ext in ALLOWED_INPUT_AVIFENC:
                    need_proxy = False
            elif self.params["format"] == "WEBP":
                output_ext = "webp"
                if self.item_ext in ALLOWED_INPUT_IMAGE_MAGICK:
                    need_proxy = False
            elif self.params["format"] == "JPG":
                output_ext = "jpg"
                if self.item_ext in ALLOWED_INPUT_IMAGE_MAGICK:
                    need_proxy = False

            output = os.path.abspath(os.path.join(output_dir, f"{self.item[0]}.{output_ext}"))
            
            # Check for existing files
            if self.params["if_file_exists"] == "Replace":
                if os.path.isfile(output):
                    os.remove(output)
            elif self.params["if_file_exists"] == "Rename":
                output = self.convert.getUniqueFilePath(output_dir, self.item_name, output_ext, False)    
            elif self.params["if_file_exists"] == "Skip":
                if os.path.isfile(output) and self.params["format"] not in ("Smallest Lossless"):    # Special modes are handled later on
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
                    self.convert.convert.log(f"Proxy cannot be found ({self.item_name}.{self.item_ext})", self.n)
                    self.signals.completed.emit(self.n)
                    return

            # Convert
            if self.params["format"] == "JPEG XL":
                args = [
                        f"-q {self.params['quality']}",
                        f"-e {self.params['effort']}",
                        "--lossless_jpeg=0",
                    ]

                if self.params["lossless"]:
                    args[0] = "-q 100"

                if self.params["intelligent_effort"] and (self.params["quality"] == 100 or self.params["lossless"]):
                    self.params["intelligent_effort"] = False
                    args[1] = "-e 9"

                if self.params["intelligent_effort"]:
                    path_pool = [
                        self.convert.getUniqueFilePath(output_dir,self.item_name + "_e7", output_ext, True),
                        self.convert.getUniqueFilePath(output_dir,self.item_name + "_e9", output_ext, True),
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
                    self.convert.log(f"No supported decoder found for ({self.item_name}.{self.item_ext})")
                    self.signals.completed.emit(self.n)
                    return

                # Decode
                self.convert.convert(decoder_path, self.item_abs_path, output, [], self.n)
                
            elif self.params["format"] == "WEBP":
                args = [
                    f"-quality {self.params['quality']}",
                    "-define webp:thread-level=0",
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
                ]

                self.convert.convert(AVIFENC_PATH, self.item_abs_path, output, args, self.n)
            elif self.params["format"] == "JPG":
                self.convert.convert(IMAGE_MAGICK_PATH, self.item_abs_path, output, [f"-quality {self.params['quality']}"], self.n)
            elif self.params["format"] == "Smallest Lossless":

                # TMP files
                paths = {
                    "png": self.convert.getUniqueFilePath(output_dir, self.item_name + "_t", "png", True),
                    "webp": self.convert.getUniqueFilePath(output_dir, self.item_name + "_t", "webp", True),
                    "jxl": self.convert.getUniqueFilePath(output_dir, self.item_name + "_t", "jxl", True)
                }

                # PNG
                shutil.copy(self.item_abs_path, paths["png"])
                args = ["-o 4" if self.params["max_efficiency"] else "-o 2"]
                self.convert.optimize(OXIPNG_PATH, paths["png"], args, self.n)
                
                # WEBP
                args = [
                "-define webp:thread-level=0",
                "-define webp:method=6",
                "-define webp:lossless=true"
                ]

                self.convert.convert(IMAGE_MAGICK_PATH, self.item_abs_path, paths["webp"], args, self.n)

                # JPEG XL
                args = [
                    "-q 100",
                    "--lossless_jpeg=0",
                    "-e 9" if self.params["max_efficiency"] else "-e 7",
                ]
                self.convert.convert(CJXL_PATH, self.item_abs_path, paths["jxl"], args, self.n)

                # Crunch Numbers
                file_sizes = []
                for i in paths:
                    file_sizes.append((i, os.path.getsize(paths[i])))

                smallest_format = file_sizes[0]
                for i in range(1, len(file_sizes)):
                    if smallest_format[1] > file_sizes[i][1]:
                        smallest_format = file_sizes[i]
                
                print(print(f"[Worker #{self.n}] File Sizes: {file_sizes}"))
                print(print(f"[Worker #{self.n}] Smallest Format: {smallest_format}"))

                # Cleanup
                for i in paths:
                    if i == smallest_format[0]:
                        output_ext = smallest_format[0]
                        output = os.path.join(output_dir, self.item_name + f".{output_ext}")

                        if self.params["if_file_exists"] == "Replace":
                            if os.path.isfile(output):
                                os.remove(output)
                            os.rename(paths[i], output)
                        elif self.params["if_file_exists"] == "Rename":
                            if os.path.isfile(output):
                                num = 1
                                while os.path.isfile(output):
                                    output = os.path.abspath(os.path.join(output_dir, self.item_name + f" ({num})." + output_ext))
                                    num += 1
                            os.rename(paths[i], output)
                        elif self.params["if_file_exists"] == "Skip":
                            os.remove(paths[i])
                    else:
                        os.remove(paths[i])
            else:
                self.convert.log(f"Unknown Format ({self.params['format']})", self.n)
            
            # Delete proxy
            if need_proxy:
                self.convert.delete(self.item_abs_path)
                self.item_abs_path = self.item[3]

            # After Conversion
            if self.params["delete_original"]:
                if os.path.isfile(output):   # In case convertion failed, don't delete the original
                    if self.params["delete_original_mode"] == "To Trash":
                        self.convert.delete(self.item[3], True)
                    elif self.params["delete_original_mode"] == "Permanently":
                        self.convert.delete(self.item[3])
            self.signals.completed.emit(self.n)