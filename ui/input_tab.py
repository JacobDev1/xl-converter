from .file_view import FileView
from variables import ALLOWED_INPUT
from core.utils import scanDir, listToFilter
from core.pathing import stripPathToFilename
from .notifications import Notifications

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

    def _addItems(self, file_paths):
        """Internal method for adding items to the file list.""" 
        if not file_paths:
            return
        
        items = []
        for file in file_paths:
            file_data = stripPathToFilename(file)
            if file_data[1].lower() in ALLOWED_INPUT:
                items.append((file_data[0], file_data[1], file_data[3]))
        
        self.file_view.startAddingItems()
        self.file_view.addItems(items)
        self.file_view.finishAddingItems()

    def addFiles(self):
        dlg = QFileDialog()
        dlg.setWindowTitle("Add Images")
        dlg.setFileMode(QFileDialog.ExistingFiles)
        dlg.setNameFilter(listToFilter("Images", ALLOWED_INPUT))

        if dlg.exec():
            file_paths = dlg.selectedFiles()
            self._addItems(file_paths)

    def addFolder(self):
        dlg = QFileDialog()
        dlg.setWindowTitle("Add Images from a Folder")
        dlg.setFileMode(QFileDialog.Directory)

        if dlg.exec():
            file_paths = scanDir(dlg.selectedFiles()[0])
            self._addItems(file_paths)

    def saveFileList(self):
        item_count = self.file_view.topLevelItemCount()
        
        if item_count == 0:
            self.notify.notify("Empty List", "File list is empty, there is nothing to save.")
            return

        dlg, _ = QFileDialog.getSaveFileUrl(
            self,
            "Save File List",
            QUrl.fromLocalFile("File List.txt"),
            "Text File (*.txt);;All Files (*)"
        )   # Options can be added

        if not dlg.isValid():
            return

        try:
            with open(dlg.toLocalFile(), "w") as file:
                for row in range(item_count):
                    path = self.file_view.topLevelItem(row).text(2)
                    if path is not None:
                        file.write(f"{path}\n")
        except Exception as err:
            self.notify.notifyDetailed("File Error", "Saving file list failed", str(err))


    def loadFileList(self):
        dlg, _ = QFileDialog.getOpenFileUrl(self, "Load File List")

        if not dlg.isValid():
            return
            
        try:
            paths = []
            with open(dlg.toLocalFile(), "r") as file:
                paths = [line.replace('\n', '') for line in file.readlines()]
            self._addItems(paths)
        except Exception as err:
            self.notify.notifyDetailed("File Error", "Loading file list failed", str(err))
    
    def clearInput(self):
        self.file_view.clear()
    
    def disableSorting(self, disabled):
        self.file_view.disableSorting(disabled)