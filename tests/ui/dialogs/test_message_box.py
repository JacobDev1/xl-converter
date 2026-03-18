from unittest.mock import patch, MagicMock
from contextlib import ExitStack

import pytest
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QWidget, QMessageBox

import ui.dialogs.message_box as message_box

@pytest.fixture
def _displayMessageBox_patched(app):
    mock_QMessageBox = MagicMock(spec=QMessageBox)
    mock_QMessageBox.exec.return_value = QMessageBox.StandardButton.Ok

    mocks = {
        "QMessageBox": patch("ui.dialogs.message_box.QMessageBox", return_value=mock_QMessageBox),
        "QIcon": patch("ui.dialogs.message_box.QIcon", return_value=MagicMock(spec=QIcon)),
    }

    with ExitStack() as stack:
        _mocks = {name: stack.enter_context(patcher) for name, patcher in mocks.items()}
        _mock_QWidget_parent = MagicMock(spec=QWidget)
        yield _mocks, _mock_QWidget_parent

def assert__displayMessageBox(
    mocks: dict,
    mock_parent: QWidget,
    title: str,
    text: str,
    detailed_text: str | None = None,
    buttons: QMessageBox.StandardButton = QMessageBox.StandardButton.Ok,
) -> None:
    mocks["QMessageBox"].assert_called_once_with(mock_parent)
    mocks["QMessageBox"].return_value.setWindowIcon.assert_called_once_with(mocks["QIcon"].return_value)
    mocks["QMessageBox"].return_value.setWindowTitle.assert_called_once_with(title)
    mocks["QMessageBox"].return_value.setText.assert_called_once_with(text)
    mocks["QMessageBox"].return_value.setDetailedText.assert_called_once_with(detailed_text)
    mocks["QMessageBox"].return_value.setStandardButtons.assert_called_once_with(buttons)
    mocks["QMessageBox"].return_value.deleteLater.assert_called_once()

def test__displayMessageBox_ok_no_detailed_text(_displayMessageBox_patched):
    mocks, mock_parent = _displayMessageBox_patched

    assert message_box._displayMessageBox(
        mock_parent, "title", "text", None, QMessageBox.StandardButton.Ok
    ) == QMessageBox.StandardButton.Ok
    
    assert__displayMessageBox(
        mocks, mock_parent, "title", "text", None, QMessageBox.StandardButton.Ok
    )
def test__displayMessageBox_ok_detailed_text(_displayMessageBox_patched):
    mocks, mock_parent = _displayMessageBox_patched

    assert message_box._displayMessageBox(
        mock_parent, "title", "text", "detailed text", QMessageBox.StandardButton.Ok
    ) == QMessageBox.StandardButton.Ok
    
    assert__displayMessageBox(
        mocks, mock_parent, "title", "text", "detailed text", QMessageBox.StandardButton.Ok
    )

def test_info_default():
    mock_parent = MagicMock(spec=QWidget)
    with patch("ui.dialogs.message_box._displayMessageBox") as mock__displayMessageBox:
        message_box.info(mock_parent, "title", "text")
        mock__displayMessageBox.assert_called_once_with(
            mock_parent, "title", "text", None, QMessageBox.StandardButton.Ok
        )

def test_info_all_args_specified():
    mock_parent = MagicMock(spec=QWidget)
    with patch("ui.dialogs.message_box._displayMessageBox") as mock__displayMessageBox:
        message_box.info(mock_parent, "title", "text", "detailed text")
        mock__displayMessageBox.assert_called_once_with(
            mock_parent, "title", "text", "detailed text", QMessageBox.StandardButton.Ok
        )

@pytest.mark.parametrize("button_pressed, expect_returned", [
    (QMessageBox.StandardButton.Yes, True),
    (QMessageBox.StandardButton.No, False),
])
def test_confirm_choices(button_pressed, expect_returned):
    mock_parent = MagicMock(spec=QWidget)
    with patch("ui.dialogs.message_box._displayMessageBox", return_value=button_pressed) as mock__displayMessageBox:
        assert message_box.confirm(mock_parent, "title", "text", "detailed text") == expect_returned
        mock__displayMessageBox.assert_called_once_with(
            mock_parent, "title", "text", "detailed text", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
