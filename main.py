#!/usr/bin/python3

import sys
import os
import time
import logging
from pathlib import Path

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QTabWidget,
)
from PySide6.QtCore import (
    QThreadPool,
    QMutex,
    QUrl
)
from PySide6.QtGui import (
    QIcon,
    QShortcut,
    QKeySequence,
)

from data.constants import (
    ICON_SVG,
)
from ui import (
    InputTab,
    AboutTab,
    ModifyTab,
    OutputTab,
    SettingsTab,
    Notifications,
    ProgressDialog,
    ExceptionView,
)
from core.worker import Worker
from core.utils import clip
from data import Items, fonts
import data.task_status as task_status
from data.thread_manager import ThreadManager
from data.time_left import TimeLeft
from data.sounds import finished_sound
from data.logging_manager import LoggingManager

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setWindowTitle("XL Converter")
        self.setWindowIcon(QIcon(ICON_SVG))
        self.setAcceptDrops(True)

        # Components
        LoggingManager()    # init singleton
        self.items = Items()
        self.time_left = TimeLeft()
        self.n = Notifications(self)
        self.threadpool = QThreadPool.globalInstance()
        self.thread_manager = ThreadManager(self.threadpool)
        
        self.progress_dialog = ProgressDialog(parent=self, title="Converting...", cancelable=True)
        self.progress_dialog.canceled.connect(task_status.cancel)
        self.time_left.update_time_left.connect(self.progress_dialog.setLabelTextLine2)

        # Tabs
        self.tabs = QTabWidget(self)
        self.tabs.setFont(fonts.MAIN_TABS)
        self.settings_tab = SettingsTab()
        settings = self.settings_tab.getSettings()
        self.input_tab = InputTab(settings)
        self.output_tab = OutputTab(self.threadpool.maxThreadCount(), settings)
        self.modify_tab = ModifyTab(settings)
        self.about_tab = AboutTab()

        self.input_tab.convert.connect(self.convert)
        self.output_tab.convert.connect(self.convert)
        self.modify_tab.convert.connect(self.convert)
        self.settings_tab.signals.disable_sorting.connect(self.input_tab.disableSorting)
        self.settings_tab.signals.enable_jxl_effort_10.connect(self.output_tab.setJxlEffort10Enabled)
        self.settings_tab.signals.custom_resampling.connect(self.modify_tab.toggleCustomResampling)
        self.settings_tab.signals.enable_quality_prec_snap.connect(self.output_tab.enableQualityPrecisionSnapping)
        self.settings_tab.signals.change_jpg_encoder.connect(self.output_tab.onJPGEncoderChanged)

        # Components
        self.exception_view = ExceptionView(settings, parent=self)

        # Size Policy
        self.resize(700, 352)
        
        MAX_WIDTH = 825
        MAX_HEIGHT = 320
        self.output_tab.setMaximumSize(MAX_WIDTH, MAX_HEIGHT)
        self.modify_tab.setMaximumSize(MAX_WIDTH, MAX_HEIGHT)
        self.about_tab.setMaximumSize(MAX_WIDTH, MAX_HEIGHT)

        # Layout
        self.tabs.setStyleSheet("""
            QTabBar::tab { margin-right: 10px; }
            QTabBar::tab:first { margin-left: 12px; }
        """)

        self.tabs.addTab(self.input_tab, "Input")
        self.tabs.addTab(self.output_tab, "Output")
        self.tabs.addTab(self.modify_tab, "Modify")
        self.tabs.addTab(self.settings_tab, "Settings")
        self.tabs.addTab(self.about_tab, "About")

        # Shortcuts
        select_tab_sc = []
        for i in range(clip(self.tabs.count(), 0, 9)):
            select_tab_sc.append(QShortcut(QKeySequence(f"Alt+{i+1}"), self))
            select_tab_sc[i].activated.connect(lambda i=i: self.tabs.setCurrentIndex(i))   # Notice the `i=i`

        self.setCentralWidget(self.tabs)

    def start(self, n):
        logging.debug(f"[Worker #{n}] Started")
    
    def complete(self, n):
        logging.debug(f"[Worker #{n}] Finished")

        if self.progress_dialog.wasCanceled():
            self.setUIEnabled(True)
            self.progress_dialog.finished()
            self.time_left.stopCounting()
            return

        self.items.addCompletedItem()
        self.time_left.addCompletedItem()
        self.progress_dialog.setLabelTextLine1(f"Converted {self.items.getCompletedItemCount()} out of {self.items.getItemCount()} images")
        self.progress_dialog.setValue(self.items.getCompletedItemCount())

        logging.debug(f"Active Threads: {self.threadpool.activeThreadCount()}")

        # Finished
        if self.items.getCompletedItemCount() == self.items.getItemCount():
            settings = self.settings_tab.getSettings()

            self.setUIEnabled(True)
            self.progress_dialog.finished()
            self.time_left.stopCounting()
            if settings["play_sound_on_finish"]:
                finished_sound.play(volume=settings["play_sound_on_finish_vol"])

            if not self.exception_view.isEmpty() and not settings["no_exceptions"]:
                self.exception_view.resizeToContent()
                self.exception_view.show()
            
            if self.output_tab.isClearAfterConvChecked():
                self.input_tab.clearInput()

    def cancel(self, n):
        logging.debug(f"[Worker #{n}] Canceled")
        self.setUIEnabled(True)

    def _safetyChecks(self, params):
        if self.input_tab.file_view.topLevelItemCount() == 0:
            self.n.notify("Empty List", "File list is empty.\nDrag and drop images (or folders) onto the program to add them.")
            return False

        # Check Permissions
        if params["custom_output_dir"]:
            custom_dir_path = Path(params["custom_output_dir_path"]) 
            if custom_dir_path.is_absolute(): # Relative paths are handled in the Worker
                try:
                    os.makedirs(custom_dir_path, exist_ok=True)
                except OSError as err:
                    self.n.notifyDetailed("Access Error", f"Make sure the output path is accessible\nand you have write permissions to it.", str(err))
                    return False
            else:
                if params["keep_dir_struct"]:
                    self.n.notify("Path Conflict", "A relative path cannot be combined with \"Keep Folder Structure\".\nEnter an absolute path (or choose one by clicking on the button with 3 dots).")
                    return False

        # Check If Format Pool Empty
        if params["format"] == "Smallest Lossless" and self.output_tab.smIsFormatPoolEmpty():
            self.n.notify("Format Error", "Select at least one format.")
            return False

        # Check If Downscaling Allowed
        if (
            params["downscaling"]["enabled"] and
            params["format"] in ("Smallest Lossless", "Lossless JPEG Recompression", "JPEG Reconstruction")
        ):
            self.n.notify("Downscaling Disabled", f"Downscaling was set to disabled,\nbecause it's not available for {params['format']}.")
            params["downscaling"]["enabled"] = False
            self.modify_tab.disableDownscaling()
        
        return True

    def convert(self):
        params = self.output_tab.getSettings()
        params.update(self.modify_tab.getSettings())
        settings = self.settings_tab.getSettings()

        if not self._safetyChecks(params):
            return

        # Reset and Parse data
        self.exception_view.close()
        self.exception_view.clear()
        self.exception_view.updateReportHeader(
            self.output_tab.getReportData(),
            self.modify_tab.getReportData(),
        )
        self.items.clear()
        self.items.parseData(*self.input_tab.getItems())
        if self.items.getItemCount() == 0:
            return
        
        # Set progress dialog
        self.progress_dialog.setRange(0, self.items.getItemCount())
        self.progress_dialog.show()
        self.progress_dialog.setLabelTextLine1("Starting the conversion...")
        
        # Misc.
        self.time_left.startCounting(self.items.getItemCount())

        # Configure Multithreading
        self.thread_manager.configure(
            params["format"],
            self.items.getItemCount(),
            self.output_tab.getUsedThreadCount(),
            settings["multithreading_mode"],
        )

        # Start workers
        task_status.reset()
        self.setUIEnabled(False)
        mutex = QMutex()

        for i in range(self.items.getItemCount()):
            abs_path, anchor_path = self.items.getItem(i)
            worker = Worker(
                i,
                abs_path,
                anchor_path,
                params,
                settings,
                self.thread_manager.getAvailableThreads(i),
                mutex
            )
            worker.signals.started.connect(self.start)
            worker.signals.completed.connect(self.complete)
            worker.signals.canceled.connect(self.cancel)
            worker.signals.exception.connect(self.exception_view.addItem)
            self.threadpool.start(worker)

    def setUIEnabled(self, n):
        self.tabs.setEnabled(n)
    
    def closeEvent(self, e):
        self.settings_tab.wm.saveState()
        self.output_tab.saveState()
        self.modify_tab.wm.saveState()
        self.exception_view.close()

        if self.threadpool.activeThreadCount() > 0:
            return -1
    
    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            e.accept()
        else:
            e.ignore()
    
    def dropEvent(self, e):
        self.tabs.setCurrentIndex(0)
        self.input_tab.file_view.dropEvent(e)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    fonts.loadFonts()
    app.setFont(fonts.DEFAULT)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec())