from unittest.mock import patch, MagicMock
from pathlib import Path

import pytest
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtTest import QSignalSpy

from ui.input_tab import InputTab
from ui.file_view import FileView

@pytest.fixture
def app():
    app = QApplication.instance()
    if not app:
        app = QApplication([])
    return app

@pytest.fixture
def input_tab(app, settings):
    return InputTab(settings)

@pytest.fixture
def settings():
    return {"sorting_disabled": False}

def normalizePath(path: str) -> str:
    """Returns normalized path."""
    return str(Path(path))

@patch("ui.input_tab.InputTab.disableSorting")
def test_init(mock_disableSorting, input_tab):
    assert input_tab.file_view is not None
    assert input_tab.notify is not None

@patch("ui.input_tab.QFileDialog.exec", return_value=True)
@patch("ui.input_tab.QFileDialog.selectedFiles", return_value=[normalizePath("/path/to/img.jpg")])
def test_addFiles(mock_selectedFiles, mock_exec, input_tab):
    input_tab.file_view = MagicMock(spec=FileView)
    input_tab.addFiles()
    input_tab.file_view.addItems.assert_called_once()

@patch("ui.input_tab.QFileDialog.exec", return_value=True)
@patch("ui.input_tab.QFileDialog.selectedFiles", return_value=[normalizePath("/path/to/folder")])
@patch("ui.input_tab.scanDir", return_value=[normalizePath("/path/to/folder")])
def test_addFolder(mock_scanDir, mock_selectedFiles, mock_exec, input_tab):
    input_tab.file_view = MagicMock(spec=FileView)
    input_tab.addFolder()
    input_tab.file_view.addItems.assert_called_once()

def test_clearInput(input_tab):
    input_tab.file_view = MagicMock(spec=FileView)
    input_tab.clearInput()
    input_tab.file_view.clear.assert_called_once()

def test_disableSorting(input_tab):
    input_tab.file_view = MagicMock(spec=FileView)
    input_tab.disableSorting(True)
    input_tab.file_view.disableSorting.assert_called_once_with(True)

def test__addItems(input_tab):
    mock_src_abs = Path("/path/to/folder/img.jPg")
    mock_src_anchor = Path("/path/to/folder")

    input_tab.file_view = MagicMock(spec=FileView)
    input_tab._addItems(
        [
            (
                mock_src_abs,
                mock_src_anchor
            ),
        ]
    )

    input_tab.file_view.addItems.assert_called_once_with(
        [
            (
                mock_src_abs.stem,
                mock_src_abs.suffix[1:],
                str(mock_src_abs),
                mock_src_anchor
            )
        ]
    )

def test_getItems(input_tab):
    input_tab.file_view = MagicMock(spec=FileView)
    input_tab.file_view.getItems()
    input_tab.file_view.getItems.assert_called_once()

def test_convert_button(input_tab, qtbot):
    spy = QSignalSpy(input_tab.convert)
    qtbot.mouseClick(input_tab.convert_btn, Qt.LeftButton)
    assert spy.count() == 1