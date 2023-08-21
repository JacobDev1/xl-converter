from VARIABLES import CJXL_PATH, DJXL_PATH, IMAGE_MAGICK_PATH, ALLOWED_INPUT_IMAGE_MAGICK, AVIFENC_PATH, AVIFDEC_PATH, OXIPNG_PATH

import os, subprocess, shutil
from send2trash import send2trash

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
        self.params = params
        
        self.item = item
        self.item_name = item[0]
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

            # Convert
            
            output_ext = ""
            if self.params["format"] == "JPEG XL":
                output_ext = ".jxl"
            elif self.params["format"] == "PNG":
                output_ext = ".png"
            elif self.params["format"] == "AVIF":
                output_ext = ".avif"
            elif self.params["format"] == "WEBP":
                output_ext = ".webp"
            elif self.params["format"] == "JPG":
                output_ext = ".jpg"

            output = os.path.abspath(os.path.join(output_dir, self.item[0] + output_ext))
            
            if self.params["if_file_exists"] == "Replace":
                if os.path.isfile(output):
                    os.remove(output)
            elif self.params["if_file_exists"] == "Rename":
                if os.path.isfile(output):
                    num = 1
                    while os.path.isfile(output):
                        output = os.path.abspath(os.path.join(output_dir, self.item[0] + f" ({num})" + output_ext))
                        num += 1
            elif self.params["if_file_exists"] == "Skip":
                if os.path.isfile(output) and self.params["format"] not in ("Smallest Lossless"):    # Special modes are handled later on
                    self.signals.completed.emit(self.n)
                    return
            
            if self.params["format"] == "JPEG XL":
                if self.params["lossless"]:
                    self.params["quality"] = 100

                if self.params["intelligent_effort"] and self.params["quality"] == 100:
                    self.params["intelligent_effort"] = False
                    self.params["effort"] = 9

                if self.params["intelligent_effort"]:
                    out = subprocess.run(f'\"{CJXL_PATH}\" -q {self.params["quality"]} --lossless_jpeg=0 -e 7 \"{self.item[3]}\" \"{output}\"_e7', shell=True)
                    print(f"[Worker #{self.n}] {out}")
                    out = subprocess.run(f'\"{CJXL_PATH}\" -q {self.params["quality"]} --lossless_jpeg=0 -e 9 \"{self.item[3]}\" \"{output}\"_e9', shell=True)
                    print(f"[Worker #{self.n}] {out}")

                    e7_size = os.path.getsize(f"{output}_e7")
                    e9_size = os.path.getsize(f"{output}_e9")
                    if e9_size > e7_size:
                        os.rename(f"{output}_e7",output)
                        os.remove(f"{output}_e9")
                        print(f"[Worker #{self.n}] Effort 7 is smaller ({round(e7_size/1024,1)} KiB vs {round(e9_size/1024,1)} KiB) ({self.item[3]})")
                    else:
                        os.rename(f"{output}_e9",output)
                        os.remove(f"{output}_e7")
                        print(f"[Worker #{self.n}] Effort 9 is smaller ({round(e9_size/1024,1)} KiB vs {round(e7_size/1024,1)} KiB) ({self.item[3]})")
                else:
                    out = subprocess.run(f'\"{CJXL_PATH}\" -q {self.params["quality"]} --lossless_jpeg=0 -e {self.params["effort"]} \"{self.item[3]}\" \"{output}\"', shell=True) # The subprocess needs to be defined here. If you move it to a function, it will cause seg faults.
                    print(f"[Worker #{self.n}] {out}")
                
                if self.params["lossless_if_smaller"] and self.params["lossless"] == False:
                    if self.params["intelligent_effort"]:
                        self.params["effort"] = 9
                    out = subprocess.run(f'\"{CJXL_PATH}\" -q 100 --lossless_jpeg=0 -e {self.params["effort"]} \"{self.item[3]}\" \"{output}_l\"', shell=True)
                    print(f"[Worker #{self.n}] {out}")
                    lossy_size = os.path.getsize(output)
                    lossless_size = os.path.getsize(f"{output}_l")
                    if lossless_size < lossy_size:
                        os.remove(output)
                        os.rename(f"{output}_l", output)
                        print(f"[Worker #{self.n}] Lossless is smaller ({round(lossless_size/1024,1)} KiB vs {round(lossy_size/1024,1)} KiB) ({self.item[3]})")
                    else:
                        os.remove(f"{output}_l")
                        print(f"[Worker #{self.n}] Lossy is smaller ({round(lossy_size/1024,1)} KiB vs {round(lossless_size/1024,1)} KiB) ({self.item[3]})")
            elif self.params["format"] == "PNG":
                if self.item[1].lower() == "jxl":
                    out = subprocess.run(f'\"{DJXL_PATH}\" \"{self.item[3]}\" \"{output}\"', shell=True)
                    print(f"[Worker #{self.n}] {out}")
                elif self.item[1].lower() == "avif":
                    out = subprocess.run(f'\"{AVIFDEC_PATH}\" \"{self.item[3]}\" \"{output}\"', shell=True)
                    print(f"[Worker #{self.n}] {out}")
                elif self.item[1].lower() in ALLOWED_INPUT_IMAGE_MAGICK:
                    out = subprocess.run(f'\"{IMAGE_MAGICK_PATH}\" \"{self.item[3]}\" \"{output}\"', shell=True)
                    print(f"[Worker #{self.n}] {out}")
            elif self.params["format"] == "WEBP":
                arguments = [
                    f"-quality {self.params['quality']}",
                    "-define webp:thread-level=0",
                    "-define webp:method=6"
                    ]
                if self.params["lossless"]:
                    arguments.append("-define webp:lossless=true")

                out = subprocess.run(f'\"{IMAGE_MAGICK_PATH}\" \"{self.item[3]}\" {" ".join(arguments)} \"{output}\"', shell=True)
                print(f"[Worker #{self.n}] {out}")

                if self.params["lossless_if_smaller"] and self.params["lossless"] == False:
                    arguments.append("-define webp:lossless=true")
                    out = subprocess.run(f'\"{IMAGE_MAGICK_PATH}\" \"{self.item[3]}\" {" ".join(arguments)} \"WEBP:{output}_l\"', shell=True)   # Remember about "WEBP:" format specifier, otherwise the output will be PNG
                    print(f"[Worker #{self.n}] {out}")
                    lossy_size = os.path.getsize(output)
                    lossless_size = os.path.getsize(f"{output}_l")
                    if lossless_size < lossy_size:
                        os.remove(output)
                        os.rename(f"{output}_l", output)
                        print(f"[Worker #{self.n}] Lossless is smaller ({round(lossless_size/1024,1)} KiB vs {round(lossy_size/1024,1)} KiB) ({self.item[3]})")
                    else:
                        os.remove(f"{output}_l")
                        print(f"[Worker #{self.n}] Lossy is smaller ({round(lossy_size/1024,1)} KiB vs {round(lossless_size/1024,1)} KiB) ({self.item[3]})")
            elif self.params["format"] == "AVIF":
                arguments = [
                    "--min 0",
                    "--max 63",
                    "-a end-usage=q",
                    f"-a cq-level={self.params['quality']}",
                    f"-s {self.params['effort']}" if not self.params["intelligent_effort"] else "-s 0",
                ]
                if self.params["lossless"]:
                    arguments.append("-l")

                out = subprocess.run(f'\"{AVIFENC_PATH}\" {" ".join(arguments)} \"{self.item[3]}\" \"{output}\"', shell=True)
                print(f"[Worker #{self.n}] {out}")
            elif self.params["format"] == "JPG":
                out = subprocess.run(f'\"{IMAGE_MAGICK_PATH}\" -quality {self.params["quality"]} \"{self.item[3]}\" \"{output}\"', shell=True)
                print(f"[Worker #{self.n}] {out}")
            elif self.params["format"] == "Smallest Lossless":
                
                # Set Output Dir
                if self.params["custom_output_dir"]:
                    output_dir = self.params["custom_output_dir_path"]
                    if os.path.isdir(output_dir) == False:
                        os.makedirs(output_dir, exist_ok=True)
                else:
                    output_dir = self.item_dir

                # Create Proxy
                ext = self.item_ext.lower()
                out = ""
                proxy_abs_path = os.path.join(output_dir,self.item_name+"_tmp.png")
                proxy_exists = False
                if ext != "png":
                    if ext == "avif":
                        out = subprocess.run(f'\"{AVIFDEC_PATH}\" \"{self.item_abs_path}\" \"{proxy_abs_path}\"', shell=True)
                    elif ext == "jxl":
                        out = subprocess.run(f'\"{DJXL_PATH}\" \"{self.item_abs_path}\" \"{proxy_abs_path}\"', shell=True)
                    elif ext in ALLOWED_INPUT_IMAGE_MAGICK:
                        out = subprocess.run(f'\"{IMAGE_MAGICK_PATH}\" \"{self.item_abs_path}\" \"PNG:{proxy_abs_path}\"', shell=True)
                    else:
                        print(f"[Worker #{self.n}] Input format not supported ({self.params['format']})")
                        self.signals.completed.emit(self.n)
                        return
                    print(f"[Worker #{self.n}] {out}")
                    print(f"[Worker #{self.n}] Proxy created at ({proxy_abs_path})")
                    self.item_abs_path = proxy_abs_path
                    proxy_exists = True

                # TMP files
                paths = {
                    "png": os.path.join(output_dir,self.item_name + ".png_t"),
                    "webp": os.path.join(output_dir, self.item_name + ".webp_t"),
                    "jxl": os.path.join(output_dir,self.item_name + ".jxl_t")
                }

                # PNG
                shutil.copy(self.item_abs_path, paths["png"])
                out = subprocess.run(f'\"{OXIPNG_PATH}\" {"-o 4" if self.params["max_efficiency"] else "-o 2"} \"{paths["png"]}\"', shell=True)
                print(f"[Worker #{self.n}] {out}")
                
                # WEBP
                arguments = [
                "-define webp:thread-level=0",
                "-define webp:method=6",
                "-define webp:lossless=true"
                ]

                out = subprocess.run(f'\"{IMAGE_MAGICK_PATH}\" \"{self.item_abs_path}\" {" ".join(arguments)} \"WEBP:{paths["webp"]}\"', shell=True)
                print(f"[Worker #{self.n}] {out}")

                # JPEG XL
                out = subprocess.run(f'\"{CJXL_PATH}\" -q 100 --lossless_jpeg=0 {"-e 9" if self.params["max_efficiency"] else "-e 7"} \"{self.item_abs_path}\" \"{paths["jxl"]}\"', shell=True)
                print(f"[Worker #{self.n}] {out}")

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

                if proxy_exists:
                    os.remove(proxy_abs_path)
            else:
                print(f"[Worker #{self.n}] Unknown Format ({self.params['format']})")
            
            # After Conversion
            if self.params["delete_original"]:
                if os.path.isfile(output):   # In case convertion failed, don't delete the original
                    if self.params["delete_original_mode"] == "To Trash":
                        try:
                            send2trash(self.item[3])
                            print(f"[Worker #{self.n}] {self.item[0]}.{self.item[1]} moved to trash")
                        except:
                            print(f"[Worker #{self.n}] Moving file to trash failed ({self.item[3]})")
                    elif self.params["delete_original_mode"] == "Permanently":
                        try:
                            os.remove(self.item[3])
                            print(f"[Worker #{self.n}] {self.item[0]}.{self.item[1]} deleted permanently")
                        except:
                            print(f"[Worker #{self.n}] Deleting file permanently failed ({self.item[3]})")
            self.signals.completed.emit(self.n)