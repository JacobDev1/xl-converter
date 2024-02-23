import os

from PySide6.QtWidgets import(
    QTreeWidget,
    QAbstractItemView,
    QTreeWidgetItem,
)
from PySide6.QtCore import(
    Qt,
    QItemSelectionModel,
    QItemSelection,
)

from core.pathing import stripPathToFilename
from core.utils import scanDir
from data.constants import ALLOWED_INPUT

class FileView(QTreeWidget):
    def __init__(self, parent):
        super(FileView, self).__init__(parent)

        self.setting_sorting_disabled = False
        self.shift_start = None

        self.setColumnCount(3)
        self.setHeaderLabels(("File Name", "Ext.", "Location"))

        self.setAcceptDrops(True)
        self.setDragDropMode(QAbstractItemView.InternalMove)    # Required for dropEvent to fire
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setStyleSheet("""QTreeView::item:focus {
                border: none;
                outline: none;
            }""")   # Disables the dark outline after deselecting an item
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
                        files = scanDir(path)
                        for file in files:
                            file_data = stripPathToFilename(file)
                            if file_data[1].lower() in ALLOWED_INPUT:
                                items.append((file_data[0], file_data[1], file_data[3]))
                    elif os.path.isfile(path):
                        file_data = stripPathToFilename(path)
                        if file_data[1].lower() in ALLOWED_INPUT:
                            items.append((file_data[0], file_data[1], file_data[3]))
                else:
                    path = str(i.toString())

            self.startAddingItems()
            self.addItems(items)
            self.finishAddingItems()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Delete:
            self.deleteSelected()
        elif event.key() == Qt.Key_Up:
            if event.modifiers() == Qt.ShiftModifier:
                self.selectShiftUp()
            else:
                self.shift_start = None
                self.moveIndexUp()
        elif event.key() == Qt.Key_Down:
            if event.modifiers() == Qt.ShiftModifier:
                self.selectShiftDown()
            else:
                self.shift_start = None
                self.moveIndexDown()
        elif event.key() == Qt.Key_Home:
            if event.modifiers() == Qt.ShiftModifier:
                self.selectItemsAbove()
            else:
                self.moveIndexToTop()
        elif event.key() == Qt.Key_End:
            if event.modifiers() == Qt.ShiftModifier:
                self.selectItemsBelow()
            else:
                self.moveIndexToBottom()

    def mousePressEvent(self, event):
        self.shift_start = None
        super(FileView, self).mousePressEvent(event)

    # Navigation
    def selectAllItems(self):
        if self.invisibleRootItem().childCount() > 0:
            self.selectAll()
    
    def selectItemsBelow(self):
        current_item = self.currentItem()
        root = self.invisibleRootItem()
        if current_item:
            current_index = self.indexFromItem(current_item)
            last_item = root.child(root.childCount() - 1)
            last_index = self.indexFromItem(last_item)

            top_left = self.model().index(current_index.row(), 0)
            bottom_right = self.model().index(last_index.row(), self.columnCount() - 1)
            selection = QItemSelection(top_left, bottom_right)

            self.setCurrentIndex(last_index)
            self.moveIndexToBottom()
            self.selectionModel().select(selection, QItemSelectionModel.Select)

    def selectItemsAbove(self):
        current_item = self.currentItem()
        root = self.invisibleRootItem()
        if current_item:
            current_index = self.indexFromItem(current_item)
            first_item = root.child(0)
            first_index = self.indexFromItem(first_item)

            top_left = self.model().index(first_index.row(), 0)
            bottom_right = self.model().index(current_index.row(), self.columnCount() - 1)
            selection = QItemSelection(top_left, bottom_right)

            self.setCurrentIndex(first_index)
            self.moveIndexToTop()
            self.selectionModel().select(selection, QItemSelectionModel.Select)

    def selectShiftDown(self):
        self.selectShift(self.itemBelow)

    def selectShiftUp(self):
        self.selectShift(self.itemAbove)

    def selectShift(self, get_next_item):
        current_item = self.currentItem()
        if self.shift_start is None:
            self.shift_start = current_item

        next_item = get_next_item(current_item)
        if next_item:
            self.setCurrentItem(next_item)
            current_item = next_item

        self.setSelectionMode(QTreeWidget.MultiSelection)
        self.clearSelection()
        start_index = self.indexFromItem(self.shift_start)
        end_index = self.indexFromItem(self.currentItem())
        for i in range(min(start_index.row(), end_index.row()), max(start_index.row(), end_index.row()) + 1):
            item = self.topLevelItem(i)
            item.setSelected(True)
        self.setSelectionMode(QTreeWidget.ExtendedSelection)

    def moveIndexDown(self):
        cur_idx = self.currentIndex()

        if cur_idx.isValid() and cur_idx.row() < self.model().rowCount(cur_idx.parent()) - 1:
            new_idx = self.model().index(cur_idx.row() + 1, cur_idx.column())
            self.setCurrentIndex(new_idx)
    
    def moveIndexUp(self):
        cur_idx = self.currentIndex()

        if cur_idx.isValid() and cur_idx.row() > 0:
            new_idx = self.model().index(cur_idx.row() - 1, cur_idx.column())
            self.setCurrentIndex(new_idx)

    def moveIndexToTop(self):
        self.setCurrentIndex(self.model().index(0, 0))
    
    def moveIndexToBottom(self):
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

        self.setUpdatesEnabled(False)
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
        
        if root.childCount() > 0:
            self.setCurrentIndex(self.model().index(next_row, 0))
        
        self.setUpdatesEnabled(True)