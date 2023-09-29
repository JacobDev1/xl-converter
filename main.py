#!/usr/bin/python3

import sys, os, time

from VARIABLES import PROGRAM_FOLDER, ALLOWED_INPUT, DEBUG
from SettingsTab import SettingsTab # Needs to be declared before other tabs
from InputTab import InputTab
from AboutTab import AboutTab
from OutputTab import OutputTab
from ModifyTab import ModifyTab
from Worker import Worker
from Data import Data
from HelperFunctions import stripPathToFilename, scanDir, burstThreadPool, setTheme
import TaskStatus

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QGridLayout,
    QTabWidget,
    QProgressDialog,
    QMessageBox
)
from PySide6.QtCore import (
    QThreadPool,
    Signal
)

from PySide6.QtGui import (
    QDesktopServices,
    QIcon
)

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setWindowTitle("XL Converter")
        self.setWindowIcon(QIcon(os.path.join(PROGRAM_FOLDER,"icons/logo.svg")))
        self.resize(650,300)

        self.tab = QTabWidget(self)
        self.setAcceptDrops(True)

        self.threadpool = QThreadPool.globalInstance()
        self.data = Data()
        self.progress_dialog = None
        self.notify_dlg = QMessageBox()

        self.settings_tab = SettingsTab()   # Needs to be declared before other tabs
        settings = self.settings_tab.getSettings()

        self.input_tab = InputTab(settings)
        self.settings_tab.signals.disable_sorting.connect(self.input_tab.disableSorting)
        self.input_tab.convert.connect(self.convert)

        self.output_tab = OutputTab(self.threadpool.maxThreadCount())
        self.output_tab.convert.connect(self.convert)

        self.modify_tab = ModifyTab(settings)
        self.modify_tab.convert.connect(self.convert)
        self.settings_tab.signals.all_resampling.connect(self.modify_tab.addResampling)

        self.about_tab = AboutTab()

        # Layout
        self.tab.addTab(self.input_tab, "Input")
        self.tab.addTab(self.output_tab, "Output")
        self.tab.addTab(self.modify_tab, "Modify")
        self.tab.addTab(self.settings_tab, "Settings")
        self.tab.addTab(self.about_tab, "About")
        self.setCentralWidget(self.tab)

    def start(self, n):
        print(f"[Worker #{n}] Started")
    
    def complete(self, n):
        print(f"[Worker #{n}] Finished")

        if self.progress_dialog.wasCanceled():
            if self.tab.isEnabled() == False:
                self.setUIEnabled(True)
            return

        self.data.appendCompletedItem(n)
        self.data.appendCompletionTime(time.time())

        time_left = self.data.getTimeRemaining()
        progress_l = f"Converted {self.data.getCompletedItemsCount()} out of {self.data.getItemCount()} images"
        progress_l += f"\n{time_left} left" if time_left != "" else ""
        self.progress_dialog.setLabelText(progress_l)
        self.progress_dialog.setValue(self.data.getCompletedItemsCount())

        if DEBUG:
            print(f"Active Threads: {self.threadpool.activeThreadCount()}")

        if self.data.getCompletedItemsCount() == self.data.getItemCount():
            self.setUIEnabled(True)
            if self.output_tab.isClearAfterConvChecked():
                self.input_tab.clearInput()

    def cancel(self, n):
        print(f"[Worker #{n}] Canceled")
        if self.tab.isEnabled() == False:
            self.setUIEnabled(True)

    def convert(self):
        if self.input_tab.file_view.topLevelItemCount() == 0:
            return
        
        # Fill in the parameters
        params = self.output_tab.getSettings()
        params.update(self.modify_tab.getSettings())

        # Check Permissions
        if params["custom_output_dir"]:
            if os.path.isabs(params["custom_output_dir_path"]): # Relative paths are handled in the Worker
                try:
                    os.makedirs(params["custom_output_dir_path"], exist_ok=True)
                except OSError as err:
                    self.notifyUser("Access Error", f"Make sure the path is accessible\nand that you have write permissions.{err}\n")
                    return

        # Check If Downscaling Allowed
        if params["downscaling"]["enabled"] and params["format"] == "Smallest Lossless":
            self.notifyUser("Downscaling Disabled", "Downscaling was set to disabled,\nbecause it's not available for Smallest Lossless")
            params["downscaling"]["enabled"] = False
            self.modify_tab.disableDownscaling()

        # Parse data
        self.data.clear()
        self.data.parseData(self.input_tab.file_view.invisibleRootItem(), ALLOWED_INPUT)
        if self.data.getItemCount() == 0:
            return
        
        # Set progress dialog
        self.progress_dialog = QProgressDialog("Converting Images...", "Cancel",0,self.data.getItemCount(), self)
        self.progress_dialog.setWindowTitle("XL Converter")
        self.progress_dialog.setMinimumWidth(350)
        self.progress_dialog.show()
        self.progress_dialog.canceled.connect(TaskStatus.cancel)

        # Configure Multithreading
        threads_per_worker = 1

        match params["format"]:
            case "AVIF":    # Use encoder-based multithreading 
                threads_per_worker = self.output_tab.getUsedThreadCount()
                self.threadpool.setMaxThreadCount(1)
            case _:
                self.threadpool.setMaxThreadCount(self.output_tab.getUsedThreadCount())

        # Start workers
        TaskStatus.reset()
        self.setUIEnabled(False)

        for i in range(0,self.data.getItemCount()):
            worker = Worker(i, self.data.getItem(i), params, threads_per_worker)
            worker.signals.started.connect(self.start)
            worker.signals.completed.connect(self.complete)
            worker.signals.canceled.connect(self.cancel)
            self.threadpool.start(worker)

    def setUIEnabled(self, n):
        self.tab.setEnabled(n)
    
    def notifyUser(self, title, msg):
        self.notify_dlg.setWindowTitle(title)
        self.notify_dlg.setText(msg)
        return self.notify_dlg.exec()
    
    def closeEvent(self, e):
        self.settings_tab.wm.saveState()
        self.output_tab.saveState()
        self.modify_tab.wm.saveState()
        self.about_tab.beforeExit()
    
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
    setTheme("dark")
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec())