#!/usr/bin/python3

import sys, os, time

from variables import (
    PROGRAM_FOLDER,
    ICON_SVG,
    THREAD_LOGS
)
from ui.settings_tab import SettingsTab
from ui.input_tab import InputTab
from ui.about_tab import AboutTab
from ui.output_tab import OutputTab
from ui.modify_tab import ModifyTab
from core.worker import Worker
from data import Items
from core.utils import setTheme, clip
import data.task_status as task_status
from ui.notifications import Notifications

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QTabWidget,
    QProgressDialog,
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

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setWindowTitle("XL Converter")
        self.setWindowIcon(QIcon(ICON_SVG))
        self.resize(650,300)

        self.tab = QTabWidget(self)
        self.setAcceptDrops(True)

        self.threadpool = QThreadPool.globalInstance()
        self.items = Items()
        self.progress_dialog = None
        self.n = Notifications()
        self.exceptions = []

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

        self.modify_tab = ModifyTab(settings)
        self.modify_tab.convert.connect(self.convert)
        self.settings_tab.signals.custom_resampling.connect(self.modify_tab.toggleCustomResampling)

        self.about_tab = AboutTab()

        # Layout
        self.tab.addTab(self.input_tab, "Input")
        self.tab.addTab(self.output_tab, "Output")
        self.tab.addTab(self.modify_tab, "Modify")
        self.tab.addTab(self.settings_tab, "Settings")
        self.tab.addTab(self.about_tab, "About")

        # Shortcuts
        select_tab_sc = []
        for i in range(clip(self.tab.count(), 0, 9)):
            select_tab_sc.append(QShortcut(QKeySequence(f"Alt+{i+1}"), self))
            select_tab_sc[i].activated.connect(lambda i=i: self.tab.setCurrentIndex(i))   # Notice the `i=i`

        self.setCentralWidget(self.tab)

    def start(self, n):
        if THREAD_LOGS:
            print(f"[Worker #{n}] Started")
    
    def complete(self, n):
        if THREAD_LOGS:
            print(f"[Worker #{n}] Finished")

        if self.progress_dialog.wasCanceled():
            self.setUIEnabled(True)
            return

        self.items.appendCompletedItem(n)
        self.items.appendCompletionTime(time.time())
        self.progress_dialog.setLabelText(self.items.getStatusText())
        self.progress_dialog.setValue(self.items.getCompletedItemCount())

        if THREAD_LOGS:
            print(f"Active Threads: {self.threadpool.activeThreadCount()}")

        if self.items.getCompletedItemCount() == self.items.getItemCount():
            self.setUIEnabled(True)
            self.progress_dialog.close()

            # Post conversion routines
            if self.exceptions and not self.settings_tab.getSettings()["no_exceptions"]:
                self.n.notifyDetailed("Exceptions Occured", "Exceptions occured during conversion.", '\n'.join(self.exceptions))
            
            if self.output_tab.isClearAfterConvChecked():
                self.input_tab.clearInput()

    def cancel(self, n):
        if THREAD_LOGS:
            print(f"[Worker #{n}] Canceled")
    
        self.setUIEnabled(True)

    def _safetyChecks(self, params):
        if self.input_tab.file_view.topLevelItemCount() == 0:
            self.n.notify("Empty List", "You haven't added any files.\nDrag and drop images (or folders) onto the program to add them.")
            return False

        # Check Permissions
        if params["custom_output_dir"]:
            if os.path.isabs(params["custom_output_dir_path"]): # Relative paths are handled in the Worker
                try:
                    os.makedirs(params["custom_output_dir_path"], exist_ok=True)
                except OSError as err:
                    self.n.notifyDetailed("Access Error", f"Make sure the path is accessible\nand that you have write permissions.", str(err))
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
        # params["settings"] = self.settings_tab.getSettings()

        if not self._safetyChecks(params):
            return

        # Reset and Parse data
        self.exceptions = []
        self.items.clear()
        self.items.parseData(self.input_tab.file_view.invisibleRootItem())
        if self.items.getItemCount() == 0:
            return
        
        # Set progress dialog
        self.progress_dialog = QProgressDialog("Converting Images...", "Cancel", 0, self.items.getItemCount(), self)
        self.progress_dialog.setWindowTitle("XL Converter")
        self.progress_dialog.setMinimumWidth(350)
        self.progress_dialog.show()
        self.progress_dialog.canceled.connect(task_status.cancel)

        # Configure Multithreading
        threads_per_worker = 1

        match params["format"]:
            case "AVIF":    # Use encoder-based multithreading 
                threads_per_worker = self.output_tab.getUsedThreadCount()
                self.threadpool.setMaxThreadCount(1)
            case _:
                self.threadpool.setMaxThreadCount(self.output_tab.getUsedThreadCount())

        # Start workers
        task_status.reset()
        self.setUIEnabled(False)
        mutex = QMutex()

        for i in range(0, self.items.getItemCount()):
            worker = Worker(i, self.items.getItem(i), params, threads_per_worker, mutex)
            worker.signals.started.connect(self.start)
            worker.signals.completed.connect(self.complete)
            worker.signals.canceled.connect(self.cancel)
            worker.signals.exception.connect(self.exception)
            self.threadpool.start(worker)

    def exception(self, msg):
        self.exceptions.append(msg)

    def setUIEnabled(self, n):
        self.tab.setEnabled(n)
    
    def closeEvent(self, e):
        self.settings_tab.wm.saveState()
        self.output_tab.saveState()
        self.modify_tab.wm.saveState()
        self.about_tab.beforeExit()

        if self.threadpool.activeThreadCount() > 0:
            return -1
    
    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            e.accept()
        else:
            e.ignore()
    
    def dropEvent(self, e):
        self.tab.setCurrentIndex(0)
        self.input_tab.file_view.dropEvent(e)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec())