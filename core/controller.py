import logging
import textwrap
import os
from typing import Any
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum, auto
import time

from PySide6.QtCore import (
    QThreadPool,
    QMutex,
    Signal,
    Slot,
    QObject,
)

from data.time_left import TimeLeft
from data.thread_manager import ThreadManager
from data.items import Items
from data.process_manager import ProcessManager
import data.task_status as task_status
from core.worker import Worker, WorkerSignals
from core.pathing import UniquePathStore
from core.metadata import isExifToolAvailable

class CheckFlags(Enum):
    # Currently unused
    DUMMY_FLAG = auto()

@dataclass
class CheckStatus:
    allowed_to_proceed: bool = True
    display_error: bool = False
    error_title: str = ""
    error_description: str = ""
    flags: list[CheckFlags] = field(default_factory=list)

    def setError(self, title: str, description: str, allowed_to_proceed: bool = False, display_error: bool = True) -> None:
        self.display_error = display_error
        self.error_title = title
        self.error_description = description
        self.allowed_to_proceed = allowed_to_proceed
    
    def addFlags(self, *new_flags: CheckFlags) -> None:
        for new_flag in new_flags:
            if new_flag not in self.flags:
                self.flags.append(new_flag)

class Controller(QObject):
    processing_started = Signal()
    processing_finished = Signal()      # finished / canceled
    exception = Signal(str, str, str)
    update_progress_line1 = Signal(str)
    update_progress_line2 = Signal(str)
    update_progress_value = Signal(int)

    def __init__(self, threadpool: QThreadPool) -> None:
        super().__init__()
        # Components
        self.threadpool = threadpool
        self.time_left = TimeLeft()
        self.thread_manager = ThreadManager(self.threadpool)
        self.items = Items()
        self.mutex = QMutex()

        # Flags
        self.finish_emitted = False     # debounce

        # Signals
        self.worker_signals = WorkerSignals()
        self.worker_signals.started.connect(self.workerStarted)
        self.worker_signals.completed.connect(self.workerCompleted)
        self.worker_signals.canceled.connect(self.workerCanceled)
        self.worker_signals.exception.connect(self.exception)
        self.time_left.update_time_left.connect(self.update_progress_line2)

        # Misc.
        self.start_time = None

    def checkProcessingRequirements(self,
        input_tab_item_count: int,
        sm_is_format_pool_empty: bool,
        output_tab_settings: dict[str, Any],
        modify_tab_settings: dict[str, Any],
        settings_tab_settings: dict[str, Any],
    ) -> CheckStatus:
        """Performs pre-conversion checks. Remember to parse data before."""
        output = CheckStatus()

        if input_tab_item_count == 0:
            output.setError(
                "Empty List",
                "File list is empty.\nDrag and drop images (or folders) onto the program to add them.",
            )
            return output

        if output_tab_settings["custom_output_dir"]:
            custom_dir_path = Path(output_tab_settings["custom_output_dir_path"]) 
            if custom_dir_path.is_absolute(): # Relative paths are handled in the Worker
                try:
                    os.makedirs(custom_dir_path, exist_ok=True)
                except OSError as err:
                    output.setError(
                        "Access Error",
                        f"Make sure the output path is accessible\nand you have write permissions to it.\n{textwrap.fill(str(err), width=75)}"
                    )
                    return output
            else:
                if output_tab_settings["keep_dir_struct"]:
                    output.setError(
                        "Path Conflict",
                        "A relative path cannot be combined with \"Keep Folder Structure\".\nEnter an absolute path (or choose one by clicking on the button with 3 dots)."
                    )
                    return output

        if output_tab_settings["format"] == "Smallest Lossless" and sm_is_format_pool_empty:
            output.setError(
                "Format Error",
                "Select at least one format."
            )
            return output

        if output_tab_settings["format"] == "PNG Optimization":
            if not modify_tab_settings["misc"]["keep_metadata"].startswith("Encoder"):
                output.setError(
                    "Metadata Mode Unavailable",
                    "ExifTool is unavailable for PNG Optimization.\nGo to Modify tab, and pick an Encoder metadata mode."
                )
                return output

        if self.items.getItemCount() == 0:
            output.setError(
                "Data Error",
                "Something went wrong.\nParsed data is empty"
            )
            return output
        
        thread_count = self.threadpool.activeThreadCount()
        if thread_count > 0:
            output.setError(
                "Still Processing",
                f"{'A thread' if thread_count == 1 else str(thread_count) + ' threads'} from the last session {'is' if thread_count == 1 else 'are'} still finishing.\nWait a moment before trying again."
            )
            return output

        if modify_tab_settings["misc"]["keep_metadata"].startswith("ExifTool"):
            # ExifTool available
            exiftool_available = isExifToolAvailable()
            if not exiftool_available[0]:
                output.setError(
                    "ExifTool Unavailable",
                    exiftool_available[1],
                )
                return output
            
            # ExifTool args empty
            cur_mode = modify_tab_settings["misc"]["keep_metadata"]
            et_args = settings_tab_settings["exiftool_args"][cur_mode].strip().split(" ")
            if len(et_args) == 1 and et_args[0] == "":
                msg = f"Argument list for \"{cur_mode}\" is empty."
                msg += "\nChange metadata mode or add arguments in Settings -> ExifTool." if cur_mode == "ExifTool - Custom" else "\nReset it to default in Settings -> ExifTool."
                output.setError(
                    "ExifTool Error",
                    msg,
                )
                return output
        elif (
            output_tab_settings["format"] == "JPEG" and
            settings_tab_settings["jpg_encoder"] == "JPEGLI" and
            modify_tab_settings["misc"]["keep_metadata"] == "Encoder - Preserve"
        ):
            output.setError(
                "Metadata Mode Unavailable",
                "The `Encoder - Preserve` metadata mode is unavailable for JPEGLI.\nGo to Modify tab, and pick `ExifTool - Preserve` to keep metadata."
            )
            return output

        return output

    def parseData(self, order: str, input_tab_items) -> None:
        """Prepares data for startProcessing(...)"""
        self.items.clear()
        self.items.parseData(order, *input_tab_items)

    def startProcessing(self,
        output_tab_settings: dict[str, Any],
        modify_tab_settings: dict[str, Any],
        settings_tab_settings: dict[str, Any],
        used_thread_count: int,
    ) -> None:
        """Starts the conversion."""

        # Setup
        self.thread_manager.configure(
            self.items.getItemCount(),
            used_thread_count,
            settings_tab_settings["ram_optimizer"],
            settings_tab_settings["ram_optimizer_rules"],
            output_tab_settings["format"],
            settings_tab_settings["avif_encoder"],
            output_tab_settings["effort"],
            output_tab_settings["jxl_modular"],
            output_tab_settings["lossless"],
            output_tab_settings["intelligent_effort"],
        )
        task_status.reset()
        ProcessManager.clear()
        UniquePathStore.clear()
        self.finish_emitted = False

        # Loader
        workers = []
        params = output_tab_settings | modify_tab_settings
        for i in range(self.items.getItemCount()):
            abs_path, anchor_path = self.items.getItem(i)
            worker = Worker(
                i,
                abs_path,
                anchor_path,
                params,
                settings_tab_settings,
                self.thread_manager.getAvailableThreads(i),
                self.mutex,
                self.worker_signals,
            )
            workers.append(worker)
        
        for worker in workers:
            self.threadpool.start(worker)

        self.time_left.startCounting(self.items.getItemCount())
        self.processing_started.emit()
        self.update_progress_line1.emit("Starting the conversion...")   # Needs to stay after processing_started.emit()
        self.start_time = time.time()

    def finishProcessing(self) -> None:
        if self.finish_emitted:
            return
        self.finish_emitted = True
        self.time_left.stopCounting()
        self.processing_finished.emit()
        ProcessManager.clear()
        if self.start_time is not None:
            logging.info(f"Processing took {round(time.time() - self.start_time, 2)} seconds.")

    def getItemCount(self) -> int:
        return self.items.getItemCount()
   
    def getCompletedItemCount(self) -> int:
        return self.items.getCompletedItemCount()
    
    def cancel(self):
        task_status.cancel()
        ProcessManager.terminateAll()
        self.start_time = None

    @Slot(int)
    def workerStarted(self, n: int) -> None:
        logging.debug(f"[Worker #{n}] Started")

    @Slot(int)
    def workerCompleted(self, n: int, skipped: bool) -> None:
        self.items.addCompletedItem()
        if not skipped:
            self.time_left.addCompletedItem()
        else:
            self.time_left.addSkippedItem()
        self.update_progress_line1.emit(f"Converted {self.items.getCompletedItemCount()} out of {self.items.getItemCount()} images")
        self.update_progress_value.emit(self.items.getCompletedItemCount())

        if self.items.getCompletedItemCount() >= self.items.getItemCount() or task_status.wasCanceled():
            self.finishProcessing()
        
        logging.debug(f"Active Workers: {self.threadpool.activeThreadCount()}")
        logging.debug(f"[Worker #{n}] Completed")

    @Slot(int)
    def workerCanceled(self, n: int) -> None:
        self.finishProcessing()
        logging.debug(f"[Worker #{n}] Canceled")
