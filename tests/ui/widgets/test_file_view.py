from unittest.mock import patch, MagicMock
from pathlib import Path

import pytest
from PySide6.QtWidgets import QApplication, QStyle, QStyleOptionViewItem
from PySide6.QtCore import Qt, QMimeData, QUrl, QModelIndex, QItemSelectionModel
from PySide6.QtGui import QPainter

import ui.widgets.file_view as file_view_module

@pytest.fixture
def file_view(qtbot):
    file_view = QApplication.instance()
    if not file_view:
        file_view = QApplication([])
    tab = file_view_module.FileView()
    qtbot.addWidget(tab)
    return tab

def normalizePath(path: str) -> str:
    """Returns normalized path."""
    return str(Path(path))

def get_sample_items(count):
    items = []
    for i in range(count):
        items.append(
            (
                f"image_{count}",
                "png",
                normalizePath(f"/path/images/image_{count}.png"),
                Path("/path/images/")
            )
        )

    return items

def get_sample_img_paths(count):
    return [normalizePath(f"/path/images/image_{i}.png") for i in range(count)]

def get_sample_folder_paths(count):
    return [normalizePath(f"/path/images_{i}/") for i in range(count)]

def get_sample_img_paths_qurls(count):
    return [QUrl.fromLocalFile(normalizePath(f"/path/images/image_{i}.png")) for i in range(count)]

def test_init(file_view):
    assert file_view.columnCount() == 3
    header_item = file_view.headerItem()
    assert header_item.text(0) == "File Name"
    assert header_item.text(1) == "Ext."
    assert header_item.text(2) == "Location"

def test_addItems(file_view):
    sample_items = get_sample_items(2)
    file_view.addItems(sample_items)

    assert file_view.topLevelItemCount() == 2
    assert file_view.topLevelItem(0).text(0) == sample_items[0][0]
    assert file_view.topLevelItem(0).text(1) == sample_items[0][1]
    assert file_view.topLevelItem(0).text(2) == sample_items[0][2]
    assert file_view.topLevelItem(0).data(0, Qt.UserRole) == sample_items[0][3]

def test_addItems_remove_duplicates(file_view):
    sample_items = get_sample_items(1)
    sample_items.append(sample_items[0])

    file_view.startAddingItems()
    file_view.addItems(sample_items)
    file_view.finishAddingItems()

    assert file_view.topLevelItemCount() == 1

def test_getItems(file_view):
    sample_items = get_sample_items(2)
    file_view.addItems(sample_items)

    assert file_view.getItems() == [
        (sample_items[0][2], sample_items[0][3]),
        (sample_items[1][2], sample_items[1][3]),
    ]

def test_disableSorting(file_view):
    file_view.disableSorting(True)
    assert file_view.isSortingEnabled() == False
    file_view.disableSorting(False)
    assert file_view.isSortingEnabled() == True

def test_deleteSelected_one(file_view):
    file_view.addItems(get_sample_items(1))
    file_view.setCurrentItem(file_view.topLevelItem(0))
    file_view.deleteSelected()

    assert file_view.topLevelItemCount() == 0

def test_deleteSelected_multiple_middle(file_view):
    sample_items = get_sample_items(3)
    file_view.addItems(sample_items)

    file_view.topLevelItem(0).setSelected(True)
    file_view.topLevelItem(2).setSelected(True)
    file_view.deleteSelected()

    assert file_view.topLevelItemCount() == 1
    assert file_view.topLevelItem(0).text(2) == sample_items[1][2]

def test_deleteSelected_all(file_view):
    file_view.addItems(get_sample_items(2))

    file_view.topLevelItem(0).setSelected(True)
    file_view.topLevelItem(1).setSelected(True)
    file_view.deleteSelected()

    assert file_view.topLevelItemCount() == 0

def test_deleteSelected_first(file_view):
    file_view.addItems(get_sample_items(3))

    file_view.topLevelItem(0).setSelected(True)
    file_view.deleteSelected()

    assert file_view.topLevelItemCount() == 2
    assert file_view.currentItem() == file_view.topLevelItem(0)

def test_deleteSelected_last(file_view):
    file_view.addItems(get_sample_items(3))

    file_view.topLevelItem(2).setSelected(True)
    file_view.deleteSelected()

    assert file_view.topLevelItemCount() == 2
    assert file_view.currentItem() == file_view.topLevelItem(1)

@patch("ui.widgets.file_view.os.path.isdir", return_value=False)
@patch("ui.widgets.file_view.os.path.isfile", return_value=True)
def test_drop_event_files(mock_isfile, mock_isdir, file_view):
    sample_imgs = get_sample_img_paths_qurls(2)
    mime_data = QMimeData()
    mime_data.setUrls(sample_imgs)
    mock_event = MagicMock()
    mock_event.mimeData.return_value = mime_data

    file_view.dropEvent(mock_event)

    assert file_view.topLevelItemCount() == 2
    assert file_view.topLevelItem(0).text(2) == normalizePath(sample_imgs[0].path())

@patch("ui.widgets.file_view.os.path.isdir", return_value=True)
@patch("ui.widgets.file_view.os.path.isfile", return_value=False)
@patch("ui.widgets.file_view.scanDir")
def test_drop_event_folders(mock_scanDir, mock_isfile, mock_isdir, file_view):
    sample_imgs = get_sample_img_paths(2)
    mock_scanDir.return_value = sample_imgs
    mime_data = QMimeData()
    mime_data.setUrls([QUrl.fromLocalFile(get_sample_folder_paths(1)[0])])
    mock_event = MagicMock()
    mock_event.mimeData.return_value = mime_data

    file_view.dropEvent(mock_event)

    assert file_view.topLevelItemCount() == 2
    assert file_view.topLevelItem(0).text(2) == sample_imgs[0]
    assert file_view.topLevelItem(1).text(2) == sample_imgs[1]

@patch("ui.widgets.file_view.os.path.isdir", side_effect=[False, True])
@patch("ui.widgets.file_view.os.path.isfile", side_effect=[True, False])
@patch("ui.widgets.file_view.scanDir")
def test_drop_event_files_and_folders(mock_scanDir, mock_isfile, mock_isdir, file_view):
    sample_imgs = get_sample_img_paths(3)
    mock_scanDir.return_value = [sample_imgs[1], sample_imgs[2]]
    mime_data = QMimeData()
    mime_data.setUrls([
        QUrl.fromLocalFile(sample_imgs[0]),
        QUrl.fromLocalFile(get_sample_folder_paths(1)[0]),
    ])
    mock_event = MagicMock()
    mock_event.mimeData.return_value = mime_data

    file_view.dropEvent(mock_event)

    assert file_view.topLevelItemCount() == 3
    assert file_view.topLevelItem(0).text(2) == sample_imgs[0]
    assert file_view.topLevelItem(2).text(2) == sample_imgs[2]

def test_drop_event_flatpak_no_permissions(file_view):
    sample_imgs = get_sample_img_paths(3)
    mime_data = QMimeData()
    mime_data.setUrls([
        QUrl.fromLocalFile(sample_imgs[0]),
        QUrl.fromLocalFile(get_sample_folder_paths(1)[0]),
    ])
    mock_event = MagicMock()
    mock_event.mimeData.return_value = mime_data
    with (
        patch("ui.widgets.file_view.os.path.exists", return_value=False),
        patch("ui.widgets.file_view.scanDir") as mock_scanDir,
        patch("ui.widgets.file_view.FLATPAK", True),
        patch("ui.widgets.file_view.message_box.info") as mock_message_box_info,
    ):
        mock_scanDir.return_value = [sample_imgs[1], sample_imgs[2]]
        
        file_view.dropEvent(mock_event)

        mock_message_box_info.assert_called_once()

def test_drop_event_flatpak_has_permissions(file_view):
    sample_imgs = get_sample_img_paths(3)
    mime_data = QMimeData()
    mime_data.setUrls([
        QUrl.fromLocalFile(sample_imgs[0]),
        QUrl.fromLocalFile(get_sample_folder_paths(1)[0]),
    ])
    mock_event = MagicMock()
    mock_event.mimeData.return_value = mime_data
    with (
        patch("ui.widgets.file_view.os.path.exists", return_value=True),
        patch("ui.widgets.file_view.os.path.isdir", side_effect=[False, True]),
        patch("ui.widgets.file_view.os.path.isfile", side_effect=[True, False]),
        patch("ui.widgets.file_view.scanDir") as mock_scanDir,
        patch("ui.widgets.file_view.FLATPAK", True),
        patch("ui.widgets.file_view.message_box.info") as mock_message_box_info,
    ):
        mock_scanDir.return_value = [sample_imgs[1], sample_imgs[2]]
        
        file_view.dropEvent(mock_event)

        mock_message_box_info.assert_not_called()
        assert file_view.topLevelItemCount() == 3
        assert file_view.topLevelItem(0).text(2) == sample_imgs[0]
        assert file_view.topLevelItem(2).text(2) == sample_imgs[2]

def test_move_down(file_view):
    file_view.addItems(get_sample_items(3))

    file_view.moveIndexDown()         # Nothing is selected at first
    assert file_view.currentItem() == file_view.topLevelItem(0)
    file_view.moveIndexDown()
    assert file_view.currentItem() == file_view.topLevelItem(1)
    file_view.moveIndexDown()
    assert file_view.currentItem() == file_view.topLevelItem(2)
    file_view.moveIndexDown()
    assert file_view.currentItem() == file_view.topLevelItem(2)

def test_move_down(file_view):
    file_view.addItems(get_sample_items(3))

    file_view.moveIndexUp()
    assert file_view.currentItem() == file_view.topLevelItem(0)
    file_view.setCurrentItem(file_view.topLevelItem(2))
    file_view.moveIndexUp()
    assert file_view.currentItem() == file_view.topLevelItem(1)
    file_view.moveIndexUp()
    assert file_view.currentItem() == file_view.topLevelItem(0)
    file_view.moveIndexUp()
    assert file_view.currentItem() == file_view.topLevelItem(0)

def test_move_top_top(file_view):
    file_view.addItems(get_sample_items(4))

    file_view.setCurrentItem(file_view.topLevelItem(3))
    file_view.moveIndexToTop()
    assert file_view.currentItem() == file_view.topLevelItem(0)

def test_move_top_bottom(file_view):
    file_view.addItems(get_sample_items(4))

    file_view.setCurrentItem(file_view.topLevelItem(0))
    file_view.moveIndexToBottom()
    assert file_view.currentItem() == file_view.topLevelItem(3)

def test_select_all(file_view):
    file_view.addItems(get_sample_items(4))

    file_view.selectAllItems()
    for i in range(file_view.invisibleRootItem().childCount()):
        assert file_view.topLevelItem(i).isSelected() == True

def test_selectItemsBelow(file_view):
    file_view.addItems(get_sample_items(4))

    file_view.setCurrentItem(file_view.topLevelItem(1))
    file_view.selectItemsBelow()
    assert file_view.topLevelItem(0).isSelected() == False
    for i in range(1, 3):
        assert file_view.topLevelItem(i).isSelected() == True

def test_selectItemsAbove(file_view):
    file_view.addItems(get_sample_items(4))

    file_view.setCurrentItem(file_view.topLevelItem(2))
    file_view.selectItemsAbove()
    assert file_view.topLevelItem(3).isSelected() == False
    for i in range(2, 0, -1):
        assert file_view.topLevelItem(i).isSelected() == True

def test_shift_up(file_view):
    def assert_selected():
        assert file_view.topLevelItem(0).isSelected() == True
        assert file_view.topLevelItem(1).isSelected() == True
        assert file_view.topLevelItem(2).isSelected() == False

    file_view.addItems(get_sample_items(3))

    file_view.setCurrentItem(file_view.topLevelItem(1))
    file_view.selectShiftUp()
    assert_selected()
    file_view.selectShiftUp()
    assert_selected()

def test_shift_down(file_view):
    def assert_selected():
        assert file_view.topLevelItem(0).isSelected() == False
        assert file_view.topLevelItem(1).isSelected() == True
        assert file_view.topLevelItem(2).isSelected() == True
    file_view.addItems(get_sample_items(3))

    file_view.setCurrentItem(file_view.topLevelItem(1))
    file_view.selectShiftDown()
    assert_selected()
    file_view.selectShiftDown()
    assert_selected()

def test_shift_intersect(file_view):
    def assert_selected(item_0: bool, item_1: bool, item_2: bool):
        assert file_view.topLevelItem(0).isSelected() == item_0
        assert file_view.topLevelItem(1).isSelected() == item_1
        assert file_view.topLevelItem(2).isSelected() == item_2
    file_view.addItems(get_sample_items(3))
    file_view.setCurrentItem(file_view.topLevelItem(1))
    file_view.selectShiftDown()
    file_view.selectShiftUp()
    assert_selected(False, True, False)
    file_view.selectShiftUp()
    assert_selected(True, True, False)
    file_view.selectShiftDown()
    assert_selected(False, True, False)
    file_view.selectShiftDown()
    assert_selected(False, True, True)

def test_paint_remove_focus_rectangle(file_view):
    option = QStyleOptionViewItem()
    option.state = option.state | QStyle.State_HasFocus | QStyle.State_Enabled | QStyle.State_Selected
    original_state = option.state

    delegate = file_view_module.ItemDelegate()
    delegate.paint(QPainter(), option, QModelIndex())

    assert option.state == (original_state & ~QStyle.State_HasFocus)

def test_paint_default(file_view):
    option = QStyleOptionViewItem()
    option.state = QStyle.State_Enabled

    delegate = file_view_module.ItemDelegate()
    delegate.paint(QPainter(), option, QModelIndex())

    assert option.state == QStyle.State_Enabled

def test_movePage_invalid_direction(file_view):
    file_view.currentItem = MagicMock(return_value=MagicMock())

    file_view.movePage("invalid")

    file_view.currentItem.assert_not_called()

@pytest.mark.parametrize("direction", ["up", "down"])
def test_movePage_valid_directions(direction, file_view):
    file_view.currentItem = MagicMock(return_value=None)
    file_view.moveIndexToBottom = MagicMock()

    file_view.movePage(direction)

    file_view.moveIndexToBottom.assert_called_once()

@pytest.mark.parametrize("direction", ["up", "down"])
def test_movePage_no_current_item(direction, file_view):
    file_view.currentItem = MagicMock(return_value=None)
    file_view.moveIndexToBottom = MagicMock()
    file_view.indexFromItem = MagicMock()

    file_view.movePage(direction)

    file_view.moveIndexToBottom.assert_called_once()
    file_view.indexFromItem.assert_not_called()

@pytest.fixture
def file_view_movePage_patched(file_view):
    SCROLL_AMOUNT = 0.95
    VIEWPORT_HEIGHT = 500
    ITEM_RECT_HEIGHT = 50

    file_view.addItems(get_sample_items(32))

    viewport = MagicMock()
    viewport.height.return_value = VIEWPORT_HEIGHT
    file_view.viewport = MagicMock(return_value=viewport)

    item_rect = MagicMock()
    item_rect.height.return_value = ITEM_RECT_HEIGHT
    file_view.visualRect = MagicMock(return_value=item_rect)

    cur_item = file_view.topLevelItem(16)
    file_view.currentItem = MagicMock(return_value=cur_item)
    file_view.setCurrentItem = MagicMock()
    file_view.scrollToItem = MagicMock()

    return file_view

def test_movePage_move_up(file_view_movePage_patched):
    file_view = file_view_movePage_patched
    cur_item = file_view.topLevelItem(16)
    file_view.currentItem = MagicMock(return_value=cur_item)

    file_view.movePage("up")
    
    file_view.setCurrentItem.assert_called_once_with(file_view.topLevelItem(16 - 9))
    file_view.scrollToItem.assert_called_once_with(file_view.topLevelItem(16 - 10))

def test_movePage_move_up_boundary(file_view_movePage_patched):
    file_view = file_view_movePage_patched
    cur_item = file_view.topLevelItem(1)
    file_view.currentItem = MagicMock(return_value=cur_item)

    file_view.movePage("up")
    
    file_view.setCurrentItem.assert_called_once_with(file_view.topLevelItem(0))
    file_view.scrollToItem.assert_called_once_with(file_view.topLevelItem(0))

def test_movePage_move_down(file_view_movePage_patched):
    file_view = file_view_movePage_patched
    cur_item = file_view.topLevelItem(16)
    file_view.currentItem = MagicMock(return_value=cur_item)

    file_view.movePage("down")
    
    file_view.setCurrentItem.assert_called_once_with(file_view.topLevelItem(16 + 9))
    file_view.scrollToItem.assert_called_once_with(file_view.topLevelItem(16 + 10))

def test_movePage_move_down_boundary(file_view_movePage_patched):
    file_view = file_view_movePage_patched
    cur_item = file_view.topLevelItem(31)
    file_view.currentItem = MagicMock(return_value=cur_item)

    file_view.movePage("down")
    
    file_view.setCurrentItem.assert_called_once_with(file_view.topLevelItem(31))
    file_view.scrollToItem.assert_called_once_with(file_view.topLevelItem(31))

def test_movePage_zero_height(file_view_movePage_patched):
    file_view = file_view_movePage_patched
    cur_item = file_view.topLevelItem(5)
    file_view.currentItem = MagicMock(return_value=cur_item)
    item_rect = MagicMock()
    item_rect.height.return_value = 0
    file_view.visualRect = MagicMock(return_value=item_rect)

    file_view.movePage("down")
    
    file_view.setCurrentItem.assert_called_once_with(file_view.topLevelItem(6))
    file_view.scrollToItem.assert_called_once_with(file_view.topLevelItem(6))

def test_movePage_select(file_view_movePage_patched):
    file_view = file_view_movePage_patched
    cur_item = file_view.topLevelItem(16)
    file_view.currentItem = MagicMock(return_value=cur_item)
    selection_model = MagicMock()
    file_view.selectionModel = MagicMock(return_value=selection_model)
    file_view.shift_start = None

    file_view.movePage("down", True)
    
    selection_model.select.assert_called_once()
    selection = selection_model.select.call_args[0][0]
    assert selection.indexes() == [file_view.indexFromItem(cur_item)]
    assert selection_model.select.call_args[0][1] == QItemSelectionModel.ClearAndSelect | QItemSelectionModel.Rows
