from unittest.mock import patch

import pytest
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from ui.about_tab import AboutTab

@pytest.fixture
def app(qtbot):
    app = QApplication.instance()
    if not app:
        app = QApplication([])
    tab = AboutTab()
    qtbot.addWidget(tab)
    return tab

def test_checkForUpdates(app, qtbot):
    with patch("ui.about_tab.UpdateChecker.run") as mock_run:
        qtbot.mouseClick(app.update_btn, Qt.LeftButton)
        mock_run.assert_called_once()
        assert not app.update_btn.isEnabled()

def test_update_btn_reenabled(app, qtbot):
    with patch("ui.about_tab.UpdateChecker.run") as mock_run:
        qtbot.mouseClick(app.update_btn, Qt.LeftButton)
        assert not app.update_btn.isEnabled()
        app.update_checker.finished.emit()
        assert app.update_btn.isEnabled()

def test_openExternalLinks(app, qtbot):
    with patch("PySide6.QtGui.QDesktopServices.openUrl") as mock_openUrl:
        qtbot.mouseClick(app.manual_btn, Qt.LeftButton)
        assert mock_openUrl.call_count == 1

        qtbot.mouseClick(app.report_bug_btn, Qt.LeftButton)
        assert mock_openUrl.call_count == 2

        qtbot.mouseClick(app.website_btn, Qt.LeftButton)
        assert mock_openUrl.call_count == 3

        qtbot.mouseClick(app.donate_btn, Qt.LeftButton)
        assert mock_openUrl.call_count == 4
