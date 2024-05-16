from unittest.mock import patch, MagicMock
from pathlib import Path

import pytest
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QMimeData, QUrl

from ui.file_view import FileView

@pytest.fixture
def app(qtbot):
    app = QApplication.instance()
    if not app:
        app = QApplication([])
    tab = FileView(None)
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

def test_init(app):
    assert app.columnCount() == 3
    header_item = app.headerItem()
    assert header_item.text(0) == "File Name"
    assert header_item.text(1) == "Ext."
    assert header_item.text(2) == "Location"

def test_addItems(app):
    sample_items = get_sample_items(2)
    app.addItems(sample_items)

    assert app.topLevelItemCount() == 2
    assert app.topLevelItem(0).text(0) == sample_items[0][0]
    assert app.topLevelItem(0).text(1) == sample_items[0][1]
    assert app.topLevelItem(0).text(2) == sample_items[0][2]
    assert app.topLevelItem(0).data(0, Qt.UserRole) == sample_items[0][3]

def test_addItems_remove_duplicates(app):
    sample_items = get_sample_items(1)
    sample_items.append(sample_items[0])

    app.startAddingItems()
    app.addItems(sample_items)
    app.finishAddingItems()

    assert app.topLevelItemCount() == 1

def test_getItems(app):
    sample_items = get_sample_items(2)
    app.addItems(sample_items)

    assert app.getItems() == [
        (sample_items[0][2], sample_items[0][3]),
        (sample_items[1][2], sample_items[1][3]),
    ]

def test_disableSorting(app):
    app.disableSorting(True)
    app.isSortingEnabled() == False
    app.disableSorting(False)
    app.isSortingEnabled() == True

def test_deleteSelected_one(app):
    app.addItems(get_sample_items(1))
    app.setCurrentItem(app.topLevelItem(0))
    app.deleteSelected()

    assert app.topLevelItemCount() == 0

def test_deleteSelected_multiple_middle(app):
    sample_items = get_sample_items(3)
    app.addItems(sample_items)

    app.topLevelItem(0).setSelected(True)
    app.topLevelItem(2).setSelected(True)
    app.deleteSelected()

    assert app.topLevelItemCount() == 1
    assert app.topLevelItem(0).text(2) == sample_items[1][2]

def test_deleteSelected_all(app):
    app.addItems(get_sample_items(2))

    app.topLevelItem(0).setSelected(True)
    app.topLevelItem(1).setSelected(True)
    app.deleteSelected()

    assert app.topLevelItemCount() == 0

def test_deleteSelected_first(app):
    app.addItems(get_sample_items(3))

    app.topLevelItem(0).setSelected(True)
    app.deleteSelected()

    assert app.topLevelItemCount() == 2
    assert app.currentItem() == app.topLevelItem(0)

def test_deleteSelected_last(app):
    app.addItems(get_sample_items(3))

    app.topLevelItem(2).setSelected(True)
    app.deleteSelected()

    assert app.topLevelItemCount() == 2
    assert app.currentItem() == app.topLevelItem(1)

@patch("ui.file_view.os.path.isdir", return_value=False)
@patch("ui.file_view.os.path.isfile", return_value=True)
def test_drop_event_files(mock_isfile, mock_isdir, app):
    sample_imgs = get_sample_img_paths_qurls(2)
    mime_data = QMimeData()
    mime_data.setUrls(sample_imgs)
    mock_event = MagicMock()
    mock_event.mimeData.return_value = mime_data

    app.dropEvent(mock_event)

    assert app.topLevelItemCount() == 2
    assert app.topLevelItem(0).text(2) == normalizePath(sample_imgs[0].path())

@patch("ui.file_view.os.path.isdir", return_value=True)
@patch("ui.file_view.os.path.isfile", return_value=False)
@patch("ui.file_view.scanDir")
def test_drop_event_folders(mock_scanDir, mock_isfile, mock_isdir, app):
    sample_imgs = get_sample_img_paths(2)
    mock_scanDir.return_value = sample_imgs
    mime_data = QMimeData()
    mime_data.setUrls([QUrl.fromLocalFile(get_sample_folder_paths(1)[0])])
    mock_event = MagicMock()
    mock_event.mimeData.return_value = mime_data

    app.dropEvent(mock_event)

    assert app.topLevelItemCount() == 2
    assert app.topLevelItem(0).text(2) == sample_imgs[0]
    assert app.topLevelItem(1).text(2) == sample_imgs[1]

@patch("ui.file_view.os.path.isdir", side_effect=[False, True])
@patch("ui.file_view.os.path.isfile", side_effect=[True, False])
@patch("ui.file_view.scanDir")
def test_drop_event_files_and_folders(mock_scanDir, mock_isfile, mock_isdir, app):
    sample_imgs = get_sample_img_paths(3)
    mock_scanDir.return_value = [sample_imgs[1], sample_imgs[2]]
    mime_data = QMimeData()
    mime_data.setUrls([
        QUrl.fromLocalFile(sample_imgs[0]),
        QUrl.fromLocalFile(get_sample_folder_paths(1)[0]),
    ])
    mock_event = MagicMock()
    mock_event.mimeData.return_value = mime_data

    app.dropEvent(mock_event)

    assert app.topLevelItemCount() == 3
    assert app.topLevelItem(0).text(2) == sample_imgs[0]
    assert app.topLevelItem(2).text(2) == sample_imgs[2]

def test_move_down(app):
    app.addItems(get_sample_items(3))

    app.moveIndexDown()         # Nothing is selected at first
    assert app.currentItem() == app.topLevelItem(0)
    app.moveIndexDown()
    assert app.currentItem() == app.topLevelItem(1)
    app.moveIndexDown()
    assert app.currentItem() == app.topLevelItem(2)
    app.moveIndexDown()
    assert app.currentItem() == app.topLevelItem(2)

def test_move_down(app):
    app.addItems(get_sample_items(3))

    app.moveIndexUp()
    assert app.currentItem() == app.topLevelItem(0)
    app.setCurrentItem(app.topLevelItem(2))
    app.moveIndexUp()
    assert app.currentItem() == app.topLevelItem(1)
    app.moveIndexUp()
    assert app.currentItem() == app.topLevelItem(0)
    app.moveIndexUp()
    assert app.currentItem() == app.topLevelItem(0)

def test_move_top_top(app):
    app.addItems(get_sample_items(4))

    app.setCurrentItem(app.topLevelItem(3))
    app.moveIndexToTop()
    assert app.currentItem() == app.topLevelItem(0)

def test_move_top_bottom(app):
    app.addItems(get_sample_items(4))

    app.setCurrentItem(app.topLevelItem(0))
    app.moveIndexToBottom()
    assert app.currentItem() == app.topLevelItem(3)

def test_select_all(app):
    app.addItems(get_sample_items(4))

    app.selectAllItems()
    for i in range(app.invisibleRootItem().childCount()):
        assert app.topLevelItem(i).isSelected() == True

def test_selectItemsBelow(app):
    app.addItems(get_sample_items(4))

    app.setCurrentItem(app.topLevelItem(1))
    app.selectItemsBelow()
    assert app.topLevelItem(0).isSelected() == False
    for i in range(1, 3):
        assert app.topLevelItem(i).isSelected() == True

def test_selectItemsAbove(app):
    app.addItems(get_sample_items(4))

    app.setCurrentItem(app.topLevelItem(2))
    app.selectItemsAbove()
    assert app.topLevelItem(3).isSelected() == False
    for i in range(2, 0, -1):
        assert app.topLevelItem(i).isSelected() == True

def test_shift_up(app):
    def assert_selected():
        assert app.topLevelItem(0).isSelected() == True
        assert app.topLevelItem(1).isSelected() == True
        assert app.topLevelItem(2).isSelected() == False

    app.addItems(get_sample_items(3))

    app.setCurrentItem(app.topLevelItem(1))
    app.selectShiftUp()
    assert_selected()
    app.selectShiftUp()
    assert_selected()

def test_shift_down(app):
    def assert_selected():
        assert app.topLevelItem(0).isSelected() == False
        assert app.topLevelItem(1).isSelected() == True
        assert app.topLevelItem(2).isSelected() == True
    app.addItems(get_sample_items(3))

    app.setCurrentItem(app.topLevelItem(1))
    app.selectShiftDown()
    assert_selected()
    app.selectShiftDown()
    assert_selected()

def test_shift_intersect(app):
    def assert_selected(item_0: bool, item_1: bool, item_2: bool):
        assert app.topLevelItem(0).isSelected() == item_0
        assert app.topLevelItem(1).isSelected() == item_1
        assert app.topLevelItem(2).isSelected() == item_2
    app.addItems(get_sample_items(3))
    app.setCurrentItem(app.topLevelItem(1))
    app.selectShiftDown()
    app.selectShiftUp()
    assert_selected(False, True, False)
    app.selectShiftUp()
    assert_selected(True, True, False)
    app.selectShiftDown()
    assert_selected(False, True, False)
    app.selectShiftDown()
    assert_selected(False, True, True)