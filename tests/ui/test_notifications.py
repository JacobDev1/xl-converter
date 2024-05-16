from unittest.mock import patch

import pytest
from PySide6.QtWidgets import QMessageBox

from ui.notifications import Notifications

@pytest.fixture
def notifications():
    return Notifications()

@pytest.fixture
def notifications_mock():
    with patch("ui.notifications.QMessageBox") as mock_msgbox:
        mock_dlg = mock_msgbox.return_value
        notifications_instance = Notifications()
        yield notifications_instance, mock_dlg

def test_init(notifications):
    assert isinstance(notifications.dlg, QMessageBox)

def test_notify(notifications_mock):
    notifications, mock_dlg = notifications_mock

    assert notifications.notify("title", "message") == mock_dlg.exec()
    
    mock_dlg.setWindowTitle.assert_called_once_with("title")
    mock_dlg.setText.assert_called_once_with("message")
    mock_dlg.setDetailedText.assert_called_once_with(None)

def test_notifyDetailed(notifications_mock):
    notifications, mock_dlg = notifications_mock

    assert notifications.notifyDetailed("title", "message", "details") == mock_dlg.exec()
    
    mock_dlg.setWindowTitle.assert_called_once_with("title")
    mock_dlg.setText.assert_called_once_with("message")
    mock_dlg.setDetailedText.assert_called_once_with("details")