from unittest.mock import patch, MagicMock, mock_open
import platform
import csv

from PySide6.QtWidgets import (
    QTreeWidgetItem,
    QFileDialog,
)
from PySide6.QtCore import (
    Qt,
)
import pytest

from ui.dialogs.exception_view import ExceptionView

@pytest.fixture
def exception_view(app):
    ev = ExceptionView()
    yield ev
    ev.deleteLater()

def test_ExceptionView_init_no_exceptions(app):
    ev = ExceptionView()

def test_addItem(exception_view):
    id_str, exception, source = "ID0", "Sample exception", "/tmp/path/to/file.jpg"

    mock_item = MagicMock(spec=QTreeWidgetItem)

    with (
        patch("ui.dialogs.exception_view.QTreeWidgetItem", return_value=mock_item),
        patch.object(exception_view.exceptions_t, "addTopLevelItem") as mock_addTopLevelItem,
    ):
        exception_view.addItem(id_str, exception, source)
        assert mock_item.setText.call_args_list[0][0] == (0, id_str)
        assert mock_item.setTextAlignment.call_args_list[0][0] == (0, Qt.AlignCenter)
        assert mock_item.setText.call_args_list[1][0] == (1, exception)
        assert mock_item.setText.call_args_list[2][0] == (2, source)
        mock_addTopLevelItem.assert_called_once_with(mock_item)

def test_clear(exception_view):
    with patch.object(exception_view.exceptions_t, "clear") as mock_clear:
        exception_view.clear()
        mock_clear.assert_called_once()

def test_saveToFile_happy_path(exception_view):
    mock_dlg = MagicMock()
    mock_dlg.isValid.return_value = True
    mock_dlg.toLocalFile.return_value = "/tmp/output.csv"

    item_data = [
        ("A", "Sample exception", "/tmp/path/to/file.jpg"),
        ("B", "Sample exception 2", "/tmp/path/to/file_1.jpg"),
        ("C", "Sample exception 3", "/tmp/path/to/file_2.jpg"),
    ]
    mock_items = []
    for data in item_data:
        item = MagicMock()
        item.text.side_effect = lambda col, data=data: data[col]
        mock_items.append(item)

    exception_view.exceptions_t = MagicMock()
    exception_view.exceptions_t.topLevelItemCount.return_value = len(mock_items)
    exception_view.exceptions_t.topLevelItem.side_effect = lambda i: mock_items[i]

    with (
        patch.object(exception_view, "isEmpty", return_value=False) as mock_isEmpty,
        patch("ui.dialogs.exception_view.QFileDialog.getSaveFileUrl", return_value=(mock_dlg, None)) as mock_getSaveFileUrl,
        patch.object(exception_view, "_writeCsv") as mock__writeCsv,
        patch("ui.dialogs.exception_view.VERSION", "version") as version,
    ):
        exception_view.saveToFile()

        expected_rows = [
            ("Version", "version"),
            ("OS", platform.system()),
            ("Exceptions",),
            ("Err Location", "Exception", "Filename"),
            *item_data
        ]
        mock__writeCsv.assert_called_once_with(mock_dlg.toLocalFile.return_value, expected_rows)
        

@pytest.mark.parametrize("system, native_dlg", (
    ["Darwin", False],
    ["Linux", True],
    ["Windows", True],
))
def test_saveToFile_darwin_dlg(system, native_dlg, exception_view):
    mock_dlg = MagicMock()
    mock_dlg.isValid.return_value = False
    with (
        patch.object(exception_view, "isEmpty", return_value=False),
        patch.object(exception_view, "_writeCsv") as mock__writeCsv,
        patch("ui.dialogs.exception_view.platform.system", return_value=system),
        patch("ui.dialogs.exception_view.QFileDialog.getSaveFileUrl", return_value=(mock_dlg, None)) as mock_getSaveFileUrl,
    ):
        exception_view.saveToFile()

        mock__writeCsv.assert_not_called()
        assert bool(mock_getSaveFileUrl.call_args[1]["options"] & QFileDialog.DontUseNativeDialog) != native_dlg

def test_saveToFile_empty(exception_view):
    with (
        patch.object(exception_view, "isEmpty", return_value=True),
        patch("ui.dialogs.exception_view.message_box.info") as mock_message_box_info,
        patch.object(exception_view, "_writeCsv") as mock__writeCsv,
    ):
        exception_view.saveToFile()

        mock_message_box_info.assert_called_once()
        mock__writeCsv.assert_not_called()

def test_saveToFile_dlg_invalid(exception_view):
    mock_dlg = MagicMock()
    mock_dlg.isValid.return_value = False

    with (
        patch.object(exception_view, "isEmpty", return_value=False),
        patch("ui.dialogs.exception_view.QFileDialog.getSaveFileUrl", return_value=(mock_dlg, None)),
        patch.object(exception_view, "_writeCsv") as mock__writeCsv,
    ):
        exception_view.saveToFile()

        mock_dlg.isValid.assert_called_once()
        mock__writeCsv.assert_not_called()

def test__writeCsv_happy_path(exception_view):
    file_path = "/tmp/path/to/file.csv"
    rows = [
        ("Col 1", "Col 2"),
        ("Val 1", "Val 2"),
    ]

    with (
        patch("builtins.open", mock_open()) as mock_csv_file,
        patch("ui.dialogs.exception_view.csv.writer") as mock_csv_writer,
        patch("ui.dialogs.exception_view.message_box.info") as mock_message_box_info,
    ):
        exception_view._writeCsv(file_path, rows)

        mock_csv_file.assert_called_once_with(file_path, "w", newline="", encoding="utf-8")
        file_handle = mock_csv_file()
        mock_csv_writer.assert_called_once_with(file_handle, quoting=csv.QUOTE_MINIMAL)
        mock_csv_writer.return_value.writerows.assert_called_once_with(rows)
        mock_message_box_info.assert_not_called()

def test__writeCsv_sad_path(exception_view):
    file_path = "/tmp/path/to/file.csv"
    rows = [
        ("Col 1", "Col 2"),
        ("Val 1", "Val 2"),
    ]


    with (
        patch("builtins.open", side_effect=OSError()) as mock_csv_file,
        patch("ui.dialogs.exception_view.csv.writer") as mock_csv_writer,
        patch("ui.dialogs.exception_view.message_box.info") as mock_message_box_info,
    ):
        exception_view._writeCsv(file_path, rows)

        mock_csv_file.assert_called_once_with(file_path, "w", newline="", encoding="utf-8")
        mock_csv_writer.assert_not_called()
        mock_csv_writer.return_value.writerows.assert_not_called()
        mock_message_box_info.assert_called_once()

@pytest.mark.parametrize("item_count, expected", [
    (0, True),
    (1, False),
])
def test_resizeToContent(item_count, expected, exception_view):
    with patch.object(exception_view.exceptions_t, "topLevelItemCount", return_value=item_count):
        assert exception_view.isEmpty() == expected

def test_reset(exception_view):
    with (
        patch.object(exception_view, "close") as mock_close,
        patch.object(exception_view, "clear") as mock_clear,
    ):
        exception_view.reset()

        mock_close.assert_called_once()
        mock_clear.assert_called_once()
