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
    visibility = {
        "general": [
            "dark_theme_cb",
            "disable_on_startup_l", "disable_downscaling_startup_cb", "disable_delete_startup_cb",
            "no_sorting_cb",
            "quality_prec_snap_cb",
            "play_sound_on_finish_cb", "play_sound_on_finish_vol_l", "play_sound_on_finish_vol_sb",
        ],
        "conversion": [
            "jxl_lossless_jpeg_cb",
            "jpg_encoder_l", "jpg_encoder_cmb",
            "disable_progressive_jpegli_cb",
            "keep_if_larger_cb",
            "copy_if_larger_cb",
            "multithreading_l", "multithreading_cmb",
        ],
        "advanced": [
            "no_exceptions_cb",
            "enable_jxl_effort_10",
            "custom_resampling_cb",
            "exiftool_l",
            "exiftool_reset_btn",
            "exiftool_wipe_l", "exiftool_wipe_te",
            "exiftool_preserve_l", "exiftool_preserve_te",
            "exiftool_unsafe_wipe_l", "exiftool_unsafe_wipe_te",
            "exiftool_custom_l", "exiftool_custom_te",
            "custom_args_cb",
            "avifenc_args_l", "avifenc_args_te",
            "cjxl_args_l", "cjxl_args_te",
            "cjpegli_args_l", "cjpegli_args_te",
            "im_args_l", "im_args_te",
            "start_logging_btn", "open_log_dir_btn", "wipe_log_dir_btn",
        ],
    }

    tracked_widgets = [widget for widgets in visibility.values() for widget in widgets]

    qtbot.mouseClick(getattr(app, category + "_btn"), Qt.LeftButton)
    for widget_str in tracked_widgets:
        widget_p = getattr(app, widget_str, None)
        if widget_p is None:
            assert False, f"Widget not found ({widget_str})"
        assert widget_p.isVisibleTo(app) == ( widget_str in visibility[category] ), \
            f"Expected {widget_str in visibility[category]} got {widget_p.isVisibleTo(app)} ({widget_str})"

@patch("ui.settings_tab.setTheme")
def test_setDarkModeEnabled(mock_setTheme, app):
    app.dark_theme_cb.setChecked(True)
    assert mock_setTheme.called_once_with("dark")
    mock_setTheme.reset_mock()
    app.dark_theme_cb.setChecked(False)
    assert mock_setTheme.called_once_with("light")

@pytest.mark.parametrize("signal_attr, widget_attr", [
    ("custom_resampling", "custom_resampling_cb"),
    ("disable_sorting", "no_sorting_cb"),
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

    assert app.custom_args_cb.isChecked() == False
    assert app.cjxl_args_te.toPlainText() == ""
    assert app.cjpegli_args_te.toPlainText() == ""
    assert app.im_args_te.toPlainText() == ""
    assert app.avifenc_args_te.toPlainText() == ""