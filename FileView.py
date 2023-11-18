import os

from PySide6.QtWidgets import(
    QTreeWidget,
    QAbstractItemView,
    QTreeWidgetItem,
    QWidget,
)

from PySide6.QtCore import(
    Qt
)

from utils import stripPathToFilename, scanDir
from VARIABLES import ALLOWED_INPUT, ALLOWED_INPUT_CJXL, ALLOWED_INPUT_DJXL, FILEVIEW_LOGS

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

    def addItems(self, items):
        self.invisibleRootItem().addChildren([QTreeWidgetItem(None, (fields[0],fields[1],fields[2])) for fields in items])

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

            items = []
            for i in event.mimeData().urls():
                path = ""
                if i.isLocalFile():
                    path = str(i.toLocalFile())
                    if os.path.isdir(path):
                        self.log(f"Dropped directory: {path}")
                        files = scanDir(path)
                        for file in files:
                            file_data = stripPathToFilename(file)
                            if file_data[1].lower() in ALLOWED_INPUT:
                                items.append((file_data[0], file_data[1], file_data[3]))
                    elif os.path.isfile(path):
                        self.log(f"Dropped file: {path}")
                        file_data = stripPathToFilename(path)
                        if file_data[1].lower() in ALLOWED_INPUT:
                            items.append((file_data[0], file_data[1], file_data[3]))
                else:
                    path = str(i.toString())

            self.addItems(items)
            # QApplication.processEvents()
            self.finishAddingItems()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Delete:
            self.log("Pressed \"Delete\"")
            root = self.invisibleRootItem()

            selected_indexes = self.selectionModel().selectedIndexes()
            if not selected_indexes:
                return

            selected_rows = sorted(set(idx.row() for idx in selected_indexes), reverse=True)
            next_row = -1

            if root.childCount() == 0:
                next_row = -1
            elif selected_rows[0] == root.childCount() - 1:
                next_row = max(0, selected_rows[0] - 1)
            else:
                next_row = selected_rows[0]

            for row in selected_rows:
                self.takeTopLevelItem(row)
                self.log(f"Removed item from list (index {row})")
            
            if root.childCount() > 0:
                self.setCurrentIndex(self.model().index(next_row, 0))
        elif event.key() == Qt.Key_Up:
            cur_idx = self.currentIndex()

            if cur_idx.isValid() and cur_idx.row() > 0:
                new_idx = self.model().index(cur_idx.row() - 1, cur_idx.column())
                self.setCurrentIndex(new_idx)
        elif event.key() == Qt.Key_Down:
            cur_idx = self.currentIndex()

            if cur_idx.isValid() and cur_idx.row() < self.model().rowCount(cur_idx.parent()) - 1:
                new_idx = self.model().index(cur_idx.row() + 1, cur_idx.column())
                self.setCurrentIndex(new_idx)
        elif event.key() == Qt.Key_Home:
            self.setCurrentIndex(self.model().index(0, 0))
        elif event.key() == Qt.Key_End:
            self.setCurrentIndex(self.model().index(self.model().rowCount() - 1, 0))

    def selectAllItems(self):
        if self.invisibleRootItem().childCount() > 0:
            self.selectAll()

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
                self.log(f"Duplicate found: {item.text(2)}")
                self.takeTopLevelItem(n)
                item_count -= 1
    
    def disableSorting(self, disabled):
        self.setting_sorting_disabled = disabled
        self.setSortingEnabled(not disabled)
    
    def log(self, msg):
        if FILEVIEW_LOGS:
            print(f"[FileView] {msg}")