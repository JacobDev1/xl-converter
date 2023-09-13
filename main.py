#!/usr/bin/python3

import sys, os
import qdarktheme

from VARIABLES import PROGRAM_FOLDER, ALLOWED_INPUT
from InputTab import InputTab
from AboutTab import AboutTab
from OutputTab import OutputTab
# from SettingsTab import SettingsTab    # For future implementation
from ModifyTab import ModifyTab
from Worker import Worker
from Data import Data
from HelperFunctions import stripPathToFilename, scanDir, burstThreadPool
import TaskStatus

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QGridLayout,
    QTabWidget,
    QProgressDialog
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

        # Input Tab
        self.input_tab = InputTab()
        self.input_tab.signals.convert.connect(self.convert)
        self.tab.addTab(self.input_tab, "Input")

        # Output Tab
        self.output_tab = OutputTab()
        self.output_tab.signals.convert.connect(self.convert)
        self.tab.addTab(self.output_tab, "Output")

        # Modify Tab
        self.modify_tab = ModifyTab()
        self.modify_tab.signals.convert.connect(self.convert)
        self.tab.addTab(self.modify_tab, "Modify")

        # Settings Tab
        # self.settings_tab = SettingsTab()
        # self.tab.addTab(self.settings_tab, "Settings")

        # About Tab
        self.about_tab = AboutTab()
        self.tab.addTab(self.about_tab, "About")

        # Main
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

if __name__ == "__main__":
    app = QApplication(sys.argv)
    qdarktheme.setup_theme(corner_shape="sharp", custom_colors={"primary":"#F18000"})
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec())