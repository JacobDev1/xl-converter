from pathlib import Path
import logging
from typing import List, Tuple

from PySide6.QtWidgets import(
    QWidget,
    QGridLayout,
    QPushButton,
    QFileDialog
)
from PySide6.QtCore import(
    Signal,
    QUrl
)
from PySide6.QtGui import(
    QShortcut,
    QKeySequence,
)

from .file_view import FileView
from data.constants import ALLOWED_INPUT
from core.utils import scanDir, listToFilter
from .notifications import Notifications

class InputTab(QWidget):
    convert = Signal()

    def __init__(self, settings):
        super(InputTab, self).__init__()
        self.file_view = FileView(self)
        self.notify = Notifications()

        # Apply Settings
        self.disableSorting(settings["sorting_disabled"])

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
        self.convert_btn.clicked.connect(self.convert.emit)

        # Positions
        input_l.addWidget(add_files_btn,1,0)
        input_l.addWidget(add_folder_btn,1,1)
        input_l.addWidget(clear_list_btn,1,2)
        input_l.addWidget(self.convert_btn,1,3,1,2)
        input_l.addWidget(self.file_view,0,0,1,0)

    # Items
    def getItems(self):
        return self.file_view.getItems()
    
    def _addItems(self, items: List[Tuple[Path, Path]]) -> None:
        """
        Adds items to the file list.
        
        Params:
            items - a list of tuples containing the following fields
                - absolute path
                - anchor path
        """ 
        if not items:
            return
        
        tmp = []
        for abs_path, anchor_path in items:
            ext = abs_path.suffix[1:]

            if ext.lower() in ALLOWED_INPUT:
                tmp.append(
                    (
                        abs_path.stem,
                        ext,
                        str(abs_path),
                        anchor_path,
                    )
                )
        
        self.file_view.startAddingItems()
        self.file_view.addItems(tmp)
        self.file_view.finishAddingItems()

    def addFiles(self):
        dlg = QFileDialog()
        dlg.setWindowTitle("Add Images")
        dlg.setFileMode(QFileDialog.ExistingFiles)
        dlg.setNameFilter(listToFilter("Images", ALLOWED_INPUT))

        if dlg.exec():
            # Add items
            file_paths = []
            for i in dlg.selectedFiles():
                file_paths.append(
                    (
                        Path(i),
                        Path(i).parent,
                    )
                )
            self._addItems(file_paths)

    def addFolder(self):
        dlg = QFileDialog()
        dlg.setWindowTitle("Add Images from a Folder")
        dlg.setFileMode(QFileDialog.Directory)

        if dlg.exec():
            selected_dir = dlg.selectedFiles()[0]
            file_paths = scanDir(selected_dir)
            
            # Add items
            tmp = []
            for i in file_paths:
                tmp.append(
                    (
                        Path(i),
                        Path(selected_dir),
                    )
                )
            self._addItems(tmp)
    
    # Misc.
    def clearInput(self):
        self.file_view.clear()
    
    def disableSorting(self, disabled):
        self.file_view.disableSorting(disabled)