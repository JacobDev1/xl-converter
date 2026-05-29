import os
from pathlib import Path
import logging
from typing import List, Tuple, Literal

from PySide6.QtWidgets import(
    QTreeWidget,
    QAbstractItemView,
    QTreeWidgetItem,
    QStyledItemDelegate,
    QStyle,
)
from PySide6.QtCore import(
    Qt,
    QItemSelectionModel,
    QItemSelection,
)

from core.utils import scanDir
from data.constants import ALLOWED_INPUT, FLATPAK
from ui.dialogs import message_box

class ItemDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        option.state &= ~QStyle.State_HasFocus      # Removes the focus rectangle. It is not possible in QSS.
        super().paint(painter, option, index)

class FileView(QTreeWidget):
    def __init__(self, parent=None):
        super(FileView, self).__init__(parent)

        self.setColumnCount(3)
        self.setHeaderLabels(("File Name", "Ext.", "Location"))

        self.setAcceptDrops(True)
        self.setDragDropMode(QAbstractItemView.InternalMove)    # Required for dropEvent to fire
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.sortByColumn(1, Qt.SortOrder.DescendingOrder)
        self.setItemDelegate(ItemDelegate())
        
        # Flags
        self.setting_sorting_disabled = False
        self.shift_start = None

    # Adding items
    def addItems(self, items):
        """Fast way of adding items.
        Params:
            items - array of
                item[0]: str - file name
                item[1]: str - file extensions
                item[2]: str - absolute path
                item[3]: Path - directory the file was added from
        """
        new_items = []
        for name, ext, abs_path, anchor_path in items:
            item = QTreeWidgetItem(
                None,
                (
                    name,
                    ext,
                    abs_path,
                )
            )
            item.setData(0, Qt.UserRole, anchor_path)
            new_items.append(item)
        self.invisibleRootItem().addChildren(new_items)

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

    def getItems(self):
        items = []
        for i in range(self.invisibleRootItem().childCount()):
            items.append(
                (
                    self.invisibleRootItem().child(i).text(2),
                    self.invisibleRootItem().child(i).data(0, Qt.UserRole),
                )
            )
        return items

    # Events
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        if not event.mimeData().hasUrls():
            event.ignore()
            return

        event.accept()

        items = []
        preserve_parent = len(event.mimeData().urls()) > 1
        flatpak_permisssion_err = False

        for url in event.mimeData().urls():
            if FLATPAK and url.isLocalFile() and not os.path.exists(url.toLocalFile()):
                flatpak_permisssion_err = True
                continue

            if url.isLocalFile():
                path = str(url.toLocalFile())
                if os.path.isdir(path):     # Directory
                    try:
                        files = scanDir(path)
                    except FileNotFoundError as e:
                        logging.error(f"[FileView - scanDir()] Directory not found. {e}")
                        continue

                    for file in files:
                        file_path = Path(file)
                        ext = file_path.suffix[1:]

                        if ext.lower() in ALLOWED_INPUT:
                            items.append(
                                (
                                    file_path.stem,
                                    ext,
                                    str(file_path),
                                    Path(path).parent if preserve_parent else Path(path),
                                )
                            )

                elif os.path.isfile(path):  # Single file
                    file_path = Path(path)
                    ext = file_path.suffix[1:]

                    if ext.lower() in ALLOWED_INPUT:
                        items.append(
                            (
                                file_path.stem,
                                ext,
                                str(file_path),
                                Path(file_path).parent,
                            )
                        )

        if flatpak_permisssion_err:
            message_box.info(self, "Permission Error", "Insufficient Flatpak permissions.\nAdd filesystem permissions to the source directory or the mounted volume.")

        if not items:
            return

        self.startAddingItems()
        self.addItems(items)
        self.finishAddingItems()

    def keyPressEvent(self, event):
        key = event.key()
        shift_pressed = event.modifiers() == Qt.ShiftModifier

        match key:
            case Qt.Key_Delete:
                self.shift_start = None
                self.deleteSelected()
            case Qt.Key_Up:
                if shift_pressed:
                    self.selectShiftUp()
                else:
                    self.shift_start = None
                    self.moveIndexUp()
            case Qt.Key_Down:
                if shift_pressed:
                    self.selectShiftDown()
                else:
                    self.shift_start = None
                    self.moveIndexDown()
            case Qt.Key_Home:
                if shift_pressed:
                    self.selectItemsAbove()
                else:
                    self.moveIndexToTop()
            case Qt.Key_End:
                if shift_pressed:
                    self.selectItemsBelow()
                else:
                    self.moveIndexToBottom()
            case Qt.Key_PageUp:
                self.movePage("up", shift_pressed)
            case Qt.Key_PageDown:
                self.movePage("down", shift_pressed)

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
            if item:
                item.setSelected(True)
        self.setSelectionMode(QTreeWidget.ExtendedSelection)

    def moveIndexDown(self):
        cur_idx = self.currentIndex()

        if cur_idx.isValid() and cur_idx.row() < self.model().rowCount(cur_idx.parent()) - 1:
            new_idx = self.model().index(cur_idx.row() + 1, cur_idx.column())
            self.setCurrentIndex(new_idx)
        elif not cur_idx.isValid():
            self.setCurrentIndex(self.indexFromItem(self.topLevelItem(0)))
    
    def moveIndexUp(self):
        cur_idx = self.currentIndex()

        if cur_idx.isValid() and cur_idx.row() > 0:
            new_idx = self.model().index(cur_idx.row() - 1, cur_idx.column())
            self.setCurrentIndex(new_idx)
        elif not cur_idx.isValid():
            self.setCurrentIndex(self.indexFromItem(self.topLevelItem(0)))

    def movePage(self, direction: Literal["up", "down"], shift_modifier=False):
        # Config
        SCROLL_AMOUNT = 0.95     # Fraction of the visible items that will change.
        
        # Checks
        if direction not in ("up", "down"):
            return
        
        cur_item = self.currentItem()
        if not cur_item:
            self.moveIndexToBottom()
            return
    
        if not shift_modifier:
            self.shift_start = None
        
        # Compute visible items
        cur_index = self.indexFromItem(cur_item)
        item_rect = self.visualRect(cur_index)
        
        if item_rect.height() <= 0:
            visible_items = 1
        else:
            visible_items = max(1, int(self.viewport().height() / item_rect.height()))

        # Compute scroll amount
        scroll_count = max(1 , int(visible_items * SCROLL_AMOUNT))
        overlap_count = visible_items - scroll_count

        total_items = self.invisibleRootItem().childCount()
        cur_row = cur_index.row()

        # Compute target items
        if direction == "down":
            target_row = min(total_items - 1, cur_row + scroll_count)
            last_visible_row = min(total_items - 1, target_row + overlap_count)
        elif direction == "up":
            target_row = max(0, cur_row - scroll_count)
            last_visible_row = max(0, target_row - overlap_count)

        # Apply
        if target_item := self.topLevelItem(target_row):
            # Set cur. item
            self.setCurrentItem(target_item)
            
            # Scroll
            if last_item := self.topLevelItem(last_visible_row):
                self.scrollToItem(last_item)

            # Select
            if shift_modifier:
                if self.shift_start is None:
                    self.shift_start = cur_item

                start_index = self.indexFromItem(self.shift_start)
                end_index = self.indexFromItem(self.currentItem())
                selection = QItemSelection(start_index, end_index)
                self.selectionModel().select(
                    selection, QItemSelectionModel.ClearAndSelect | QItemSelectionModel.Rows
                )

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

        # Get selected indexes
        selected_indexes = self.selectionModel().selectedIndexes()
        if not selected_indexes:
            return

        self.setUpdatesEnabled(False)
        selected_rows = sorted(set(idx.row() for idx in selected_indexes), reverse=True)
        
        # Determine next row to select
        next_row = -1
        if root.childCount() > 0:
            if selected_rows[-1] < root.childCount() - 1:
                next_row = selected_rows[-1]
            elif selected_rows[0] > 0:
                next_row = selected_rows[0] - 1

        # Remove selected items
        for row in selected_rows:
            self.takeTopLevelItem(row)
        
        # Select next item
        if root.childCount() > 0:
            self.setCurrentIndex(self.model().index(next_row, 0))
        
        self.setUpdatesEnabled(True)
