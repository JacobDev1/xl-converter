#!/usr/bin/python3

import sys
import os
import time
import logging

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QTabWidget,
)
from PySide6.QtCore import (
    QThreadPool,
    QMutex
)
from PySide6.QtGui import (
    QIcon,
    QShortcut,
    QKeySequence
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
from data import Items
from data import fonts
import data.task_status as task_status
from data.thread_manager import ThreadManager

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setWindowTitle("XL Converter")
        self.setWindowIcon(QIcon(ICON_SVG))

        self.tabs = QTabWidget(self)
        self.setAcceptDrops(True)
        self.tabs.setFont(fonts.MAIN_TABS)

        self.threadpool = QThreadPool.globalInstance()
        self.thread_manager = ThreadManager(self.threadpool)
        self.items = Items()
        self.progress_dialog = ProgressDialog(parent=self, title="Converting...", default_text="Starting the conversion...\n", cancelable=True)
        self.progress_dialog.canceled.connect(task_status.cancel)
        self.n = Notifications()

        # Tabs
        self.settings_tab = SettingsTab()
        settings = self.settings_tab.getSettings()

        self.input_tab = InputTab(settings)
        self.input_tab.convert.connect(self.convert)
        self.settings_tab.signals.disable_sorting.connect(self.input_tab.disableSorting)
        self.settings_tab.signals.save_file_list.connect(self.input_tab.saveFileList)
        self.settings_tab.signals.load_file_list.connect(self.input_tab.loadFileList)

        self.output_tab = OutputTab(self.threadpool.maxThreadCount(), settings)
        self.output_tab.convert.connect(self.convert)
        self.settings_tab.signals.enable_jxl_effort_10.connect(self.output_tab.setJxlEffort10Enabled)

        self.modify_tab = ModifyTab(settings)
        self.modify_tab.convert.connect(self.convert)
        self.settings_tab.signals.custom_resampling.connect(self.modify_tab.toggleCustomResampling)

        self.about_tab = AboutTab()

        # Misc.
        self.exception_view = ExceptionView(settings, parent=self)
        self.exception_view.dont_show_again.connect(self.settings_tab.setExceptionsEnabled)
        self.settings_tab.signals.no_exceptions.connect(self.exception_view.setDontShowAgain)

        # Size Policy
        self.resize(700, 352)
        
        MAX_WIDTH = 825
        MAX_HEIGHT = 320
        self.output_tab.setMaximumSize(MAX_WIDTH, MAX_HEIGHT)
        self.modify_tab.setMaximumSize(MAX_WIDTH, MAX_HEIGHT)
        self.settings_tab.setMaximumSize(MAX_WIDTH, MAX_HEIGHT)
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
            return

        self.items.appendCompletedItem(n)
        self.items.appendCompletionTime(time.time())
        self.progress_dialog.setLabelText(self.items.getStatusText())
        self.progress_dialog.setValue(self.items.getCompletedItemCount())

        logging.debug(f"Active Threads: {self.threadpool.activeThreadCount()}")

        if self.items.getCompletedItemCount() == self.items.getItemCount():
            self.setUIEnabled(True)
            self.progress_dialog.finished()

            # Post conversion routines
            if not self.exception_view.isEmpty() and not self.settings_tab.getSettings()["no_exceptions"]:
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
            if os.path.isabs(params["custom_output_dir_path"]): # Relative paths are handled in the Worker
                try:
                    os.makedirs(params["custom_output_dir_path"], exist_ok=True)
                except OSError as err:
                    self.n.notifyDetailed("Access Error", f"Make sure the path is accessible\nand that you have write permissions.", str(err))
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
        if params["downscaling"]["enabled"] and params["format"] == "Smallest Lossless":
            self.n.notify("Downscaling Disabled", "Downscaling was set to disabled,\nbecause it's not available for Smallest Lossless")
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
        self.items.parseData(*self.input_tab.file_view.getItemPaths())
        if self.items.getItemCount() == 0:
            return
        
        # Setup commonpath
        if params["keep_dir_struct"] and params["custom_output_dir"]:
            commonpath = self.items.getCommonPath()
        else:
            commonpath = None

        # Set progress dialog
        self.progress_dialog.setRange(0, self.items.getItemCount())
        self.progress_dialog.show()

        # Configure Multithreading
        self.thread_manager.configure(
            params["format"],
            self.items.getItemCount(),
            self.output_tab.getUsedThreadCount()
        )

        # Start workers
        task_status.reset()
        self.setUIEnabled(False)
        mutex = QMutex()

        for i in range(self.items.getItemCount()):
            worker = Worker(i,
                self.items.getItem(i),
                commonpath,
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