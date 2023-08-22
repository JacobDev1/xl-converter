from FileView import *
from VARIABLES import ALLOWED_INPUT
from HelperFunctions import stripPathToFilename, scanDir

from PySide6.QtWidgets import(
    QWidget,
    QGridLayout,
    QPushButton,
    QFileDialog
)

from PySide6.QtCore import(
    QObject,
    Signal
)

from PySide6.QtGui import(
    QShortcut,
    QKeySequence
)

class Signals(QObject):
    convert = Signal()

class InputTab(QWidget):
    def __init__(self):
        super(InputTab, self).__init__()
        self.signals = Signals()

        self.file_view = FileView(self)
        self.file_view.setColumnCount(3)
        self.file_view.setHeaderLabels(("File Name", "Extension", "Location"))

        # Shortcuts
        self.select_all_sc = QShortcut(QKeySequence('Ctrl+A'), self)
        self.select_all_sc.activated.connect(self.file_view.selectAllItems)
        self.delete_all_sc = QShortcut(QKeySequence("Ctrl+Shift+X"), self)
        self.delete_all_sc.activated.connect(self.file_view.clear)

        # UI
        input_l = QGridLayout()
        self.setLayout(input_l)
        
        add_files_btn = QPushButton(self)
        add_files_btn.setText("Add Files")
        add_files_btn.clicked.connect(self.addFiles)

        add_folder_btn = QPushButton(self)
        add_folder_btn.setText("Add Folder")
        add_folder_btn.clicked.connect(self.addFolder)

        clear_list_btn = QPushButton(self)
        clear_list_btn.setText("Clear List")
        clear_list_btn.clicked.connect(self.clearInput)

        self.convert_btn = QPushButton(self)
        self.convert_btn.setText("Convert")
        self.convert_btn.clicked.connect(lambda: self.signals.convert.emit())

        input_l.addWidget(add_files_btn,1,0)
        input_l.addWidget(add_folder_btn,1,1)
        input_l.addWidget(clear_list_btn,1,2)
        input_l.addWidget(self.convert_btn,1,4)
        input_l.addWidget(self.file_view,0,0,1,0)

    def addFiles(self):
        dlg = QFileDialog()
        dlg.setFileMode(QFileDialog.ExistingFiles)
        name_filter = "Images ("
        for i in ALLOWED_INPUT:
            name_filter += f"*.{i}"
            if i != ALLOWED_INPUT[len(ALLOWED_INPUT)-1]:
                name_filter += " "
        name_filter += ")"
        dlg.setNameFilter(name_filter)

        self.file_view.setSortingEnabled(False)
        filepaths = ""
        if dlg.exec():
            filepaths = dlg.selectedFiles()
            for i in filepaths:
                file_data = stripPathToFilename(i)
                print(file_data)
                self.file_view.addItem(file_data[0], file_data[1], file_data[3])
        
        self.file_view.setSortingEnabled(True)
        self.file_view.resizeToContent()

    def addFolder(self):
        dlg = QFileDialog()
        dlg.setFileMode(QFileDialog.Directory)
        
        self.file_view.setSortingEnabled(False)
        if dlg.exec():
            files = scanDir(dlg.selectedFiles()[0])
            for i in files:
                file_data = stripPathToFilename(i)
                if file_data[1] in ALLOWED_INPUT:
                    self.file_view.addItem(file_data[0], file_data[1], file_data[3])
        
        self.file_view.setSortingEnabled(True)
        self.file_view.resizeToContent()

    def clearInput(self):
        self.file_view.clear()