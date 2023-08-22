import os

from PySide6.QtWidgets import(
    QTreeWidget,
    QAbstractItemView,
    QTreeWidgetItem,
    QWidget
)

from PySide6.QtCore import(
    Qt
)

from HelperFunctions import stripPathToFilename, scanDir
from VARIABLES import ALLOWED_INPUT, ALLOWED_INPUT_CJXL, ALLOWED_INPUT_DJXL

# Before adding files disable sorting

class FileView(QTreeWidget):
    def __init__(self, parent):
        super(FileView, self).__init__(parent)
        self.setAcceptDrops(True)
        self.setDragDropMode(QAbstractItemView.InternalMove)    # Required for dropEvent to fire
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.sortByColumn(1, Qt.SortOrder.DescendingOrder)
    
    def addItem(self, *fields):
        is_duplicate = False
        item_count = self.invisibleRootItem().childCount()

        if item_count > 0:
            for i in range(item_count):
                item = self.invisibleRootItem().child(i)
                if item.text(2) == fields[2]:
                    is_duplicate = True
        if is_duplicate:
           print(f"[FileView] Duplicate entry ({fields[2]})")
        else:
            self.addTopLevelItem(QTreeWidgetItem(None, (fields[0],fields[1],fields[2])))
            self.scrollToItem(self.invisibleRootItem().child(item_count))   # Not -1, because we just added one

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()
    
    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
            
            self.setSortingEnabled(False)
            for i in event.mimeData().urls():
                path = ""
                if i.isLocalFile():
                    path = str(i.toLocalFile())
                    if os.path.isdir(path):
                        print(f"[FileView] Dropped directory: {path}")
                        files = scanDir(path)
                        for i in files:
                            file_data = stripPathToFilename(i)
                            if file_data[1].lower() in ALLOWED_INPUT:
                                self.addItem(file_data[0],file_data[1],file_data[3])
                    elif os.path.isfile(path):
                        print(f"[FileView] Dropped file: {path}")
                        file_data = stripPathToFilename(path)
                        if file_data[1].lower() in ALLOWED_INPUT:
                            self.addItem(file_data[0],file_data[1],file_data[3])
                else:
                    path = str(i.toString())
            self.setSortingEnabled(True)
            self.resizeToContent()

    def keyPressEvent(self, event):
        if event.key() == 16777223: # Delete
            print(f"[FileView] Pressed \"Delete\"")
            indexes = self.selectionModel().selectedIndexes()
            deleted_indexes = []
            if len(indexes) > 0:
                for i in range(len(indexes)-1,0,-1): # Descending, not to shift order
                    row = indexes[i].row()
                    if row not in deleted_indexes:
                        deleted_indexes.append(row)
                        self.takeTopLevelItem(row)
                        print(f"[FileView] Removed item from list (index {row})")
        # elif event.key() == Qt.Key_Up:        # For future implementation
        #     print(f"[FileView] Pressed \"Key_Up\"")
        # elif event.key() == Qt.Key_Down:
        #     print(f"[FileView] Pressed \"Key_Down\"")
    
    def selectAllItems(self):
        item_count = self.invisibleRootItem().childCount()

        if item_count > 0:
            for i in range(item_count):
                item = self.invisibleRootItem().child(i).setSelected(True)

    def resizeToContent(self):
        for i in range(0, self.columnCount() - 1):  # The last one resizes with the window
            self.resizeColumnToContents(i)