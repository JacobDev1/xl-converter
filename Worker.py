from VARIABLES import CJXL_PATH, DJXL_PATH, IMAGE_MAGICK_PATH, ALLOWED_INPUT_IMAGE_MAGICK, AVIFENC_PATH, AVIFDEC_PATH

import os, subprocess
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
        self.item = item
        self.params = params
    
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
            if self.params["if_file_exists"] == "Skip":
                pass
            else:
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
                            os.rename(f"{output}_e7",f"{output}")
                            os.remove(f"{output}_e9")
                            print(f"[Worker #{self.n}] Effort 7 is smaller ({round(e7_size/1024,1)} KiB vs {round(e9_size/1024,1)} KiB) ({self.item[3]})")
                        else:
                            os.rename(f"{output}_e9",f"{output}")
                            os.remove(f"{output}_e7")
                            print(f"[Worker #{self.n}] Effort 9 is smaller ({round(e9_size/1024,1)} KiB vs {round(e7_size/1024,1)} KiB) ({self.item[3]})")
                    else:
                        out = subprocess.run(f'\"{CJXL_PATH}\" -q {self.params["quality"]} --lossless_jpeg=0 -e {self.params["effort"]} \"{self.item[3]}\" \"{output}\"', shell=True) # The subprocess needs to be defined here. If you move it to a function, it will cause seg faults.
                        print(f"[Worker #{self.n}] {out}")
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
                elif self.params["format"] == "AVIF":
                    arguments = [
                        "--min 0",
                        "--max 63",
                        "-a end-usage=q",
                        f"-a cq-level={self.params['quality']}",
                        f"-s {self.params['effort']}"
                    ]
                    if self.params["lossless"]:
                        arguments.append("-l")

                    out = subprocess.run(f'\"{AVIFENC_PATH}\" {" ".join(arguments)} \"{self.item[3]}\" \"{output}\"', shell=True)
                    print(f"[Worker #{self.n}] {out}")
                elif self.params["format"] == "JPG":
                    out = subprocess.run(f'\"{IMAGE_MAGICK_PATH}\" -quality {self.params["quality"]} \"{self.item[3]}\" \"{output}\"', shell=True)
                    print(f"[Worker #{self.n}] {out}")
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