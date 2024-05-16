from unittest.mock import patch, call

import pytest
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from ui.settings_tab import SettingsTab

@pytest.fixture
def app(qtbot):
    with patch("ui.settings_tab.WidgetManager.loadState"), \
        patch("ui.settings_tab.WidgetManager.saveState"), \
        patch("ui.settings_tab.setTheme"):
        app = QApplication.instance()
        if not app:
            app = QApplication([])

        tab = SettingsTab()
        qtbot.addWidget(tab)
        return tab

@pytest.mark.parametrize("category", ["general", "conversion", "advanced"])
def test_changeCategory_visibility(category, app, qtbot):
    general = conversion = advanced = False
    match category:
        case "general":
            qtbot.mouseClick(app.general_btn, Qt.LeftButton)
            general = True
        case "conversion":
            qtbot.mouseClick(app.conversion_btn, Qt.LeftButton)
            conversion = True
        case "advanced":
            qtbot.mouseClick(app.advanced_btn, Qt.LeftButton)
            advanced = True
    
    assert app.dark_theme_cb.isVisibleTo(app) == general
    assert app.disable_on_startup_l.isVisibleTo(app) == general
    assert app.disable_downscaling_startup_cb.isVisibleTo(app) == general
    assert app.disable_delete_startup_cb.isVisibleTo(app) == general
    assert app.no_exceptions_cb.isVisibleTo(app) == general
    assert app.no_sorting_cb.isVisibleTo(app) == general

    assert app.disable_progressive_jpegli_cb.isVisibleTo(app) == conversion
    assert app.webp_method_l.isVisibleTo(app) == conversion
    assert app.webp_method_sb.isVisibleTo(app) == conversion

    assert app.enable_jxl_effort_10.isVisibleTo(app) == advanced
    assert app.custom_resampling_cb.isVisibleTo(app) == advanced
    assert app.custom_args_cb.isVisibleTo(app) == advanced
    assert app.avifenc_args_l.isVisibleTo(app) == advanced
    assert app.avifenc_args_te.isVisibleTo(app) == advanced
    assert app.cjxl_args_l.isVisibleTo(app) == advanced
    assert app.cjxl_args_te.isVisibleTo(app) == advanced
    assert app.cjpegli_args_l.isVisibleTo(app) == advanced
    assert app.cjpegli_args_te.isVisibleTo(app) == advanced
    assert app.im_args_l.isVisibleTo(app) == advanced
    assert app.im_args_te.isVisibleTo(app) == advanced
    assert app.empty_l.isVisibleTo(app) == advanced

def test_changeCategory_category_buttons(app, qtbot):
    qtbot.mouseClick(app.general_btn, Qt.LeftButton)
    assert app.general_btn.isChecked()
    assert app.conversion_btn.isChecked() == False
    assert app.advanced_btn.isChecked() == False
    qtbot.mouseClick(app.conversion_btn, Qt.LeftButton)
    assert app.conversion_btn.isChecked()
    qtbot.mouseClick(app.advanced_btn, Qt.LeftButton)
    assert app.advanced_btn.isChecked()

@patch("ui.settings_tab.setTheme")
def test_setDarkModeEnabled(mock_setTheme, app):
    app.dark_theme_cb.setChecked(True)
    assert mock_setTheme.called_once_with("dark")
    mock_setTheme.reset_mock()
    app.dark_theme_cb.setChecked(False)
    assert mock_setTheme.called_once_with("light")

@patch("ui.settings_tab.SettingsTab.blockSignals")
def test_setExceptionsEnabled(mock_blockSignals, app):
    app.setExceptionsEnabled(False)
    mock_blockSignals.assert_has_calls([call(True), call(False)])

@pytest.mark.parametrize("signal_attr, widget_attr", [
    ("custom_resampling", "custom_resampling_cb"),
    ("disable_sorting", "no_sorting_cb"),
    ("no_exceptions", "no_exceptions_cb"),
    ("enable_jxl_effort_10", "enable_jxl_effort_10"),
])
def test_signals(app, qtbot, signal_attr, widget_attr):
    with qtbot.waitSignal(getattr(app.signals, signal_attr)) as blocker:
        qtbot.mouseClick(getattr(app, widget_attr), Qt.LeftButton)
    assert blocker.signal_triggered

def test_getSettings_no_key_error(app):
    app.getSettings()

def test_resetToDefault(app):
    app.resetToDefault()

    assert app.dark_theme_cb.isChecked() == True
    assert app.no_sorting_cb.isChecked() == False
    assert app.disable_downscaling_startup_cb.isChecked() == True
    assert app.disable_delete_startup_cb.isChecked() == True
    assert app.no_exceptions_cb.isChecked() == False
    
    assert app.enable_jxl_effort_10.isChecked() == False
    assert app.custom_resampling_cb.isChecked() == False
    assert app.disable_progressive_jpegli_cb.isChecked() == False
    assert app.webp_method_sb.value() == 6

    assert app.custom_args_cb.isChecked() == False
    assert app.cjxl_args_te.toPlainText() == ""
    assert app.cjpegli_args_te.toPlainText() == ""
    assert app.im_args_te.toPlainText() == ""
    assert app.avifenc_args_te.toPlainText() == ""