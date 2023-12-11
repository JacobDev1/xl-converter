import os

from PySide6.QtWidgets import(
    QTreeWidget,
    QAbstractItemView,
    QTreeWidgetItem,
)

from PySide6.QtCore import(
    Qt
)

from pathing import stripPathToFilename
from utils import scanDir
from variables import ALLOWED_INPUT, ALLOWED_INPUT_CJXL, ALLOWED_INPUT_DJXL, FILEVIEW_LOGS

class FileView(QTreeWidget):
    def __init__(self, parent):
        super(FileView, self).__init__(parent)

        self.setting_sorting_disabled = False

        self.setColumnCount(3)
        self.setHeaderLabels(("File Name", "Ext.", "Location"))

        self.setAcceptDrops(True)
        self.setDragDropMode(QAbstractItemView.InternalMove)    # Required for dropEvent to fire
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.sortByColumn(1, Qt.SortOrder.DescendingOrder)

    # Adding items
    def addItems(self, items):
        self.invisibleRootItem().addChildren([QTreeWidgetItem(None, (fields[0],fields[1],fields[2])) for fields in items])

    def startAddingItems(self):
        """Run before adding items"""
        self.setSortingEnabled(False)

    def finishAddingItems(self):
        """Run after all items have been added."""
        self.resizeToContent()
        self.removeDuplicates()
        self.scrollToLastItem()
        if not self.setting_sorting_disabled:
            self.setSortingEnabled(True)

    def removeDuplicates(self):
        unique_items = set()

        for n in range(self.invisibleRootItem().childCount() - 1, -1, -1):
            item = self.invisibleRootItem().child(n)
            path = item.text(2)
            if path in unique_items:
                self.log(f"Duplicate found: {path}")
                self.takeTopLevelItem(n)
            else:
                unique_items.add(path)

    def disableSorting(self, disabled):
        self.setting_sorting_disabled = disabled
        self.setSortingEnabled(not disabled)

    # Events
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
            
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

            self.startAddingItems()
            self.addItems(items)
            # QApplication.processEvents()
            self.finishAddingItems()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Delete:
            self.deleteSelected()
        elif event.key() == Qt.Key_Up:
            self.moveSelectionUp()
        elif event.key() == Qt.Key_Down:
            self.moveSelectionDown()
        elif event.key() == Qt.Key_Home:
            self.moveSelectionToTop()
        elif event.key() == Qt.Key_End:
            self.moveSelectionToBottom()

    # Navigation
    def selectAllItems(self):
        if self.invisibleRootItem().childCount() > 0:
            self.selectAll()
    
    def moveSelectionDown(self):
        cur_idx = self.currentIndex()

        if cur_idx.isValid() and cur_idx.row() < self.model().rowCount(cur_idx.parent()) - 1:
            new_idx = self.model().index(cur_idx.row() + 1, cur_idx.column())
            self.setCurrentIndex(new_idx)
    
    def moveSelectionUp(self):
        cur_idx = self.currentIndex()

        if cur_idx.isValid() and cur_idx.row() > 0:
            new_idx = self.model().index(cur_idx.row() - 1, cur_idx.column())
            self.setCurrentIndex(new_idx)

    def moveSelectionToTop(self):
        self.setCurrentIndex(self.model().index(0, 0))
    
    def moveSelectionToBottom(self):
        self.setCurrentIndex(self.model().index(self.model().rowCount() - 1, 0))

    def scrollToLastItem(self):
        item_count = self.invisibleRootItem().childCount()
        self.scrollToItem(self.invisibleRootItem().child(item_count - 1))
    
    def resizeToContent(self):
        for i in range(0, self.columnCount() - 1):  # The last one resizes with the window
            self.resizeColumnToContents(i)
    
    # Operations
    def deleteSelected(self):
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
    
    # Misc.
    def log(self, msg):
        if FILEVIEW_LOGS:
            print(f"[FileView] {msg}")