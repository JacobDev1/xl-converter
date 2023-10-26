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

from utils import stripPathToFilename, scanDir
from VARIABLES import ALLOWED_INPUT, ALLOWED_INPUT_CJXL, ALLOWED_INPUT_DJXL

class FileView(QTreeWidget):
    def __init__(self, parent):
        super(FileView, self).__init__(parent)

        self.setting_sorting_disabled = False

        self.setColumnCount(3)
        self.setHeaderLabels(("File Name", "Ext.", "Location"))

        self.setAcceptDrops(True)
        self.setDragDropMode(QAbstractItemView.InternalMove)    # Required for dropEvent to fire
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.sortByColumn(1, Qt.SortOrder.DescendingOrder)
    
    def addItem(self, *fields):
        self.addTopLevelItem(QTreeWidgetItem(None, (fields[0],fields[1],fields[2])))

    def beforeAddingItems(self):
        """Run before adding items"""
        self.setSortingEnabled(False)

    def finishAddingItems(self):
        """Run after all items have been added."""
        self.resizeToContent()
        self.removeDuplicates()
        self.scrollToLastItem()
        if not self.setting_sorting_disabled:
            self.setSortingEnabled(True)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()
    
    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
            
            self.beforeAddingItems()
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
            
            self.finishAddingItems()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Delete:
            print(f"[FileView] Pressed \"Delete\"")
            selected_indexes = self.selectionModel().selectedIndexes()
            deleted_indexes = []
            if len(selected_indexes) > 0:
                for i in range(len(selected_indexes)-1,0,-1): # Descending, not to shift order
                    row = selected_indexes[i].row()
                    if row not in deleted_indexes:
                        deleted_indexes.append(row)
                        self.takeTopLevelItem(row)
                        print(f"[FileView] Removed item from list (index {row})")
                
                # Select next item
                item_count = self.invisibleRootItem().childCount()
                if item_count > 0:
                    row = selected_indexes[0].row()
                    next_row = row
                    if row == item_count:
                        next_row -= 1
                    self.invisibleRootItem().child(next_row).setSelected(True)
        # elif event.key() == Qt.Key_Up:
        #     pass
        # elif event.key() == Qt.Key_Down:
        #     pass
    
    def selectAllItems(self):
        item_count = self.invisibleRootItem().childCount()

        if item_count > 0:
            for i in range(item_count):
                item = self.invisibleRootItem().child(i).setSelected(True)

    def resizeToContent(self):
        for i in range(0, self.columnCount() - 1):  # The last one resizes with the window
            self.resizeColumnToContents(i)
    
    def scrollToLastItem(self):
        item_count = self.invisibleRootItem().childCount()
        self.scrollToItem(self.invisibleRootItem().child(item_count - 1))

    def removeDuplicates(self):
        """Remove all duplicates. Avoid calling often."""
        item_count = self.invisibleRootItem().childCount()
        unique_items = []
        
        n = 0
        while n < item_count:
            item = self.invisibleRootItem().child(n)
            if item.text(2) not in unique_items:
                unique_items.append(item.text(2))
                n += 1
            else:
                print(f"[FileView] Duplicate found: {item.text(2)}")
                self.takeTopLevelItem(n)
                item_count -= 1
    
    def disableSorting(self, disabled):
        self.setting_sorting_disabled = disabled
        self.setSortingEnabled(not disabled)