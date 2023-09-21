#!/usr/bin/python3

import sys, os

from VARIABLES import PROGRAM_FOLDER, ALLOWED_INPUT
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

        self.threadpool = QThreadPool.globalInstance()
        self.data = Data()
        self.progress_dialog = None

        self.settings_tab = SettingsTab()   # Needs to be declared before other tabs

        self.input_tab = InputTab()
        self.input_tab.signals.convert.connect(self.convert)

        self.output_tab = OutputTab()
        self.output_tab.signals.convert.connect(self.convert)

        self.modify_tab = ModifyTab(self.settings_tab.getSettings())
        self.modify_tab.signals.convert.connect(self.convert)
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
        self.progress_dialog.setValue(self.data.getCompletedItemsCount())

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
                    dlg = QMessageBox()
                    dlg.setWindowTitle("Access Error")
                    dlg.setText(f"{err}\nMake sure the path is accessible\nand that you have write permissions.")
                    dlg.exec()
                    return

        # Parse data
        self.data.clear()
        self.data.parseData(self.input_tab.file_view.invisibleRootItem(), ALLOWED_INPUT)
        if self.data.getItemCount() == 0:
            return
        
        # Set progress dialog
        self.progress_dialog = QProgressDialog("Converting Items...", "Cancel",0,self.data.getItemCount(), self)
        self.progress_dialog.setWindowTitle("XL Converter")
        self.progress_dialog.setMinimumWidth(300)
        self.progress_dialog.show()
        self.progress_dialog.canceled.connect(TaskStatus.cancel)

        # Start workers
        TaskStatus.reset()
        self.setUIEnabled(False)

        for i in range(0,self.data.getItemCount()):
            worker = Worker(i, self.data.getItem(i), params, burstThreadPool(self.data.getItemCount(), self.output_tab.getUsedThreadCount()))
            worker.signals.started.connect(self.start)
            worker.signals.completed.connect(self.complete)
            worker.signals.canceled.connect(self.cancel)
            self.threadpool.start(worker)

    def setUIEnabled(self, n):
        self.tab.setEnabled(n)
    
    def closeEvent(self, e):
        self.settings_tab.wm.saveState()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    setTheme("dark")
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec())