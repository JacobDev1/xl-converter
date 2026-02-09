from unittest.mock import patch, call
from contextlib import ExitStack
import logging

import pytest
from PySide6.QtWidgets import QApplication, QCheckBox, QComboBox
from PySide6.QtCore import Qt

from ui.tabs.settings_tab import SettingsTab, STOCK_PRESETS
import data.process_manager as process_manager

@pytest.fixture
def app(qtbot):
    with (
        patch("ui.tabs.settings_tab.WidgetManager.loadState"),
        patch("ui.tabs.settings_tab.WidgetManager.saveState"),
        patch("ui.tabs.settings_tab.setTheme"),
        patch.object(SettingsTab, "runMigrations", autospec=True),
    ):
        tab = SettingsTab()
        qtbot.addWidget(tab)
        return tab

@pytest.fixture
def app_migrations(qtbot):
    """Version of app with unpatched runMigrations."""
    with (
        patch("ui.tabs.settings_tab.WidgetManager.loadState"),
        patch("ui.tabs.settings_tab.WidgetManager.saveState"),
        patch("ui.tabs.settings_tab.setTheme"),
    ):
        with patch.object(SettingsTab, "runMigrations", autospec=True):    # Prevents running in __init__
            tab = SettingsTab()
            qtbot.addWidget(tab)
        return tab

@pytest.mark.parametrize("category, button", [
    ("General", "general_btn"),
    ("Conversion", "conversion_btn"),
    ("ExifTool", "exiftool_btn"),
    ("Advanced", "advanced_btn"),
])
def test_changeCategory_visibility(category, button, app):
    visibility = {
        "General": [
            "disable_on_startup_l", "disable_downscaling_startup_cb", "disable_delete_startup_cb",
            "theme_l", "theme_cmb",
            "no_sorting_cb",
            "quality_prec_snap_cb",
            "play_sound_on_finish_cb", "play_sound_on_finish_vol_l", "play_sound_on_finish_vol_sb",
        ],
        "Conversion": [
            "jxl_auto_lossless_jpeg_cb",
            "jxl_lossy_modular_cb",
            "jpg_encoder_l", "jpg_encoder_cmb",
            "disable_progressive_jpegli_cb",
            "avif_encoder_l", "avif_encoder_cmb",
            "avif_bit_depth_l", "avif_bit_depth_cmb",
            "avif_aom_iq_tune_cb",
            "keep_if_larger_cb",
            "copy_if_larger_cb",
        ],
        "ExifTool": [
            "exiftool_reset_btn",
            "exiftool_wipe_l", "exiftool_wipe_te",
            "exiftool_preserve_l", "exiftool_preserve_te",
            "exiftool_unsafe_wipe_l", "exiftool_unsafe_wipe_te",
            "exiftool_custom_l", "exiftool_custom_te",
        ],
        "Advanced": [
            "ram_optimizer_l", "ram_optimizer_cmb",
            "ram_optimizer_rules_l", "ram_optimizer_rules_te",
            "ram_optimizer_rules_reset_btn",
            "jxl_int_effort_cb",
            "jxl_effort_10_cb",
            "custom_resampling_cb",
            "custom_args_cb",
            "avifenc_args_l", "avifenc_args_te",
            "cjxl_args_l", "cjxl_args_te",
            "cjpegli_args_l", "cjpegli_args_te",
            "im_args_l", "im_args_te",
            "processing_order_l", "processing_order_cmb",
            "process_priority_l", "process_priority_cmb",
            "start_logging_btn", "open_log_dir_btn", "wipe_log_dir_btn",
        ],
    }
    tracked_widgets = [widget for widgets in visibility.values() for widget in widgets]

    if (btn_ref := getattr(app, button, None)) is None:
        assert False, f"Button \"{button}\" not found"

    btn_ref.click()

    for widget_str in tracked_widgets:
        widget_p = getattr(app, widget_str, None)
        if widget_p is None:
            assert False, f"Widget not found ({widget_str})"
        assert widget_p.isVisibleTo(app) == ( widget_str in visibility[category] ), \
            f"Expected {widget_str in visibility[category]} got {widget_p.isVisibleTo(app)} ({widget_str})"

@pytest.mark.parametrize("signal_attr, widget_attr", [
    ("custom_resampling_toggled", "custom_resampling_cb"),
    ("sorting_toggled", "no_sorting_cb"),
    ("jxl_effort_10_toggled", "jxl_effort_10_cb"),
    ("avif_encoder_changed", "avif_encoder_cmb"),
])
def test_signals(signal_attr, widget_attr, qtbot, app):
    with qtbot.waitSignal(getattr(app.signals, signal_attr), timeout=1000) as blocker:
        widget = getattr(app, widget_attr, None)
        if widget is None:
            pytest.fail(f"Widget does not exist ({widget_attr})")
        if isinstance(widget, QCheckBox):
            widget.setChecked(not widget.isChecked())
        elif isinstance(widget, QComboBox):
            widget.setCurrentIndex((widget.currentIndex() - 1) % widget.count())
    assert blocker.signal_triggered

@pytest.fixture
def onAVIFBitDepthChanged_patches(app):
    patches = {
        "avif_encoder_cmb.currentText": patch.object(app.avif_encoder_cmb, "currentText"),
        "avif_bit_depth_cmb.currentText": patch.object(app.avif_bit_depth_cmb, "currentText"),
        "wm.getVar": patch.object(app.wm, "getVar", return_value="8"),
        "avif_bit_depth_cmb.setCurrentText": patch.object(app.avif_bit_depth_cmb, "setCurrentText"),
        "avif_bit_depth_cmb.clear": patch.object(app.avif_bit_depth_cmb, "clear"),
        "blockSignals": patch("ui.tabs.settings_tab.blockSignals"),
        "avif_aom_iq_tune_cb.setEnabled": patch.object(app.avif_aom_iq_tune_cb, "setEnabled"),
    }

    with ExitStack() as stack:
        _mocks = {name: stack.enter_context(patcher) for name, patcher in patches.items()}
        yield app, _mocks

@pytest.mark.parametrize("encoder, var_name", [
    ("AOM AV1", "aom_av1_bit_depth"),
    ("SVT-AV1-PSY", "svt_av1_psy_bit_depth"),
])
def test_onAVIFBitDepthChanged_happy_path(encoder, var_name, onAVIFBitDepthChanged_patches):
    app, mocks = onAVIFBitDepthChanged_patches
    mocks["avif_encoder_cmb.currentText"].return_value = encoder
    mocks["avif_bit_depth_cmb.currentText"].return_value = var_name

    app.onAVIFEncoderChanged()

    mocks["blockSignals"].assert_called_once_with(app.avif_bit_depth_cmb)
    mocks["avif_bit_depth_cmb.clear"].assert_called_once()
    mocks["wm.getVar"].assert_called_once_with(var_name)
    mocks["avif_bit_depth_cmb.setCurrentText"].assert_called_once_with(mocks["wm.getVar"].return_value)
    mocks["avif_aom_iq_tune_cb.setEnabled"].assert_called_once_with(encoder == "AOM AV1")

def test_onAVIFBitDepthChanged_unknown_encoder(caplog, onAVIFBitDepthChanged_patches):
    app, mocks = onAVIFBitDepthChanged_patches
    mocks["avif_encoder_cmb.currentText"].return_value = "new_enc"
    caplog.set_level(logging.ERROR)

    app.onAVIFEncoderChanged()

    assert "Unknown encoder" in caplog.records[0].message
    mocks["wm.getVar"].assert_not_called()

def test_onAVIFBitDepthChanged_var_not_found(onAVIFBitDepthChanged_patches):
    app, mocks = onAVIFBitDepthChanged_patches
    mocks["wm.getVar"].return_value = None
    mocks["avif_encoder_cmb.currentText"].return_value = "AOM AV1"

    app.onAVIFEncoderChanged()

    mocks["avif_bit_depth_cmb.setCurrentText"].assert_called_once_with("Auto")

def test_onThemeChanged(app):
    with (
        patch.object(app.theme_cmb, "currentText", return_value="theme") as mock_currentText,
        patch("ui.tabs.settings_tab.setTheme") as mock_setTheme,
    ):
        app.onThemeChanged()
        mock_setTheme.assert_called_once_with(mock_currentText.return_value)

@pytest.mark.parametrize(
    "priority_str, expected_enum",
    [
        ("Normal", process_manager.ProcessPriority.NORMAL),
        ("Below Normal", process_manager.ProcessPriority.BELOW_NORMAL),
        ("Idle", process_manager.ProcessPriority.IDLE),
    ]
)
def test_onProcessPriorityChanged_valid_values(priority_str, expected_enum, app):
    with (
        patch.object(app.process_priority_cmb, "currentText", return_value=priority_str),
        patch("ui.tabs.settings_tab.process_manager.ProcessPriorityManager.setPriority") as mock_setPriority,
    ):
        app.onProcessPriorityChanged()
        mock_setPriority.assert_called_once_with(expected_enum)

def test_onProcessPriorityChanged_invalid_value(app, caplog):
    with (
        patch.object(app.process_priority_cmb, "currentText", return_value="Unsupported"),
        patch("ui.tabs.settings_tab.process_manager.ProcessPriorityManager.setPriority") as mock_setPriority,
        caplog.at_level(logging.ERROR),
    ):
        app.onProcessPriorityChanged()
        assert "Unmapped priority" in caplog.text
        mock_setPriority.assert_not_called()

@pytest.mark.parametrize("currently_logging", [True, False])
def test_enableLogging(currently_logging, app):
    with (
        patch.object(app.logging_manager, "isLoggingToFile", return_value=currently_logging) as mock_isLoggingToFile,
        patch.object(app.logging_manager, "startLoggingToFile") as mock_startLoggingToFile,
        patch.object(app.start_logging_btn, "setText") as mock_setText,
        patch.object(app.start_logging_btn, "setChecked") as mock_setChecked,
    ):
        app.enableLogging()
        mock_isLoggingToFile.assert_called_once()
        if currently_logging:
            mock_startLoggingToFile.assert_not_called()
        else:
            mock_startLoggingToFile.assert_called_once_with("INFO")
        mock_setText.assert_called_once_with("Stop Logging")
        mock_setChecked.assert_called_once_with(True)

@pytest.mark.parametrize("currently_logging", [True, False])
def test_disableLogging(currently_logging, app):
    with (
        patch.object(app.logging_manager, "isLoggingToFile", return_value=currently_logging) as mock_isLoggingToFile,
        patch.object(app.logging_manager, "stopLoggingToFile") as mock_stopLoggingToFile,
        patch.object(app.start_logging_btn, "setText") as mock_setText,
        patch.object(app.start_logging_btn, "setChecked") as mock_setChecked,
    ):
        app.disableLogging()
        mock_isLoggingToFile.assert_called_once()
        assert mock_stopLoggingToFile.call_count == int(currently_logging)
        mock_setText.assert_called_once_with("Start Logging")
        mock_setChecked.assert_called_once_with(False)

@pytest.mark.parametrize("currently_logging", [True, False])
def test_toggleLogging(currently_logging, app):
    with (
        patch.object(app.logging_manager, "isLoggingToFile", return_value=currently_logging) as mock_isLoggingToFile,
        patch.object(app, "disableLogging") as mock_disableLogging,
        patch.object(app, "enableLogging") as mock_enableLogging,
    ):
        app.toggleLogging()
        mock_isLoggingToFile.assert_called_once()
        assert mock_enableLogging.call_count == int(not currently_logging)
        assert mock_disableLogging.call_count == int(currently_logging)

def test_openLogsDir_dir_exists(app):
    sample_logs_dir = "/tmp/logs_dir"
    with (
        patch.object(app.logging_manager, "getLogsDir", return_value=sample_logs_dir) as mock_getLogsDir,
        patch("ui.tabs.settings_tab.os.path.isdir", return_value=True) as mock_isdir,
        patch("ui.tabs.settings_tab.message_box.info") as mock_message_box_info,
        patch("ui.tabs.settings_tab.openLocalUrl") as mock_openLocalUrl,
    ):
        app.openLogsDir()
        mock_getLogsDir.assert_called_once()
        mock_isdir.assert_called_once()
        mock_message_box_info.assert_not_called()
        mock_openLocalUrl.assert_called_once_with(sample_logs_dir)

def test_openLogsDir_no_dir(app):
    sample_logs_dir = "/tmp/logs_dir"
    with (
        patch.object(app.logging_manager, "getLogsDir", return_value=sample_logs_dir) as mock_getLogsDir,
        patch("ui.tabs.settings_tab.os.path.isdir", return_value=False) as mock_isdir,
        patch("ui.tabs.settings_tab.message_box.info") as mock_message_box_info,
        patch("ui.tabs.settings_tab.openLocalUrl") as mock_openLocalUrl,
    ):
        app.openLogsDir()
        mock_getLogsDir.assert_called_once()
        mock_isdir.assert_called_once()
        mock_message_box_info.assert_called_once_with(app, "No logs", "No logs have been found.")
        # mock_message_box_info.assert_called_once()
        # args, _ = mock_message_box_info.call_args
        # assert args[0] == app
        # assert isinstance(args[1], str)
        # assert isinstance(args[2], str)
        mock_openLocalUrl.assert_not_called()

def test_wipeLogsDir(app):
    with (
        patch.object(app, "disableLogging") as mock_disableLogging,
        patch.object(app.logging_manager, "wipeLogsDir", return_value="Wiped successfully") as mock_wipeLogsDir,
        patch("ui.tabs.settings_tab.message_box.info") as mock_message_box_info,
    ):
        app.wipeLogsDir()
        mock_disableLogging.assert_called_once()
        mock_wipeLogsDir.assert_called_once()
        mock_message_box_info.assert_called_once_with(app, "File Message", "Wiped successfully")

def test_resetExifTool(app):
    with (
        patch.object(app.exiftool_wipe_te, "setText") as mock_setText_wipe,
        patch.object(app.exiftool_preserve_te, "setText") as mock_setText_preserve,
        patch.object(app.exiftool_unsafe_wipe_te, "setText") as mock_setText_unsafe_wipe,
    ):
        app.resetExifTool()

        mock_setText_wipe.assert_called_once_with(STOCK_PRESETS.exiftool_wipe)
        mock_setText_preserve.assert_called_once_with(STOCK_PRESETS.exiftool_preserve)
        mock_setText_unsafe_wipe.assert_called_once_with(STOCK_PRESETS.exiftool_unsafe_wipe)

@pytest.mark.parametrize("reset_custom", [True, False])
def test_resetExifTool_reset_custom(reset_custom, app):
    with (
        patch.object(app.exiftool_wipe_te, "setText") as mock_setText_wipe,
        patch.object(app.exiftool_preserve_te, "setText") as mock_setText_preserve,
        patch.object(app.exiftool_unsafe_wipe_te, "setText") as mock_setText_unsafe_wipe,
        patch.object(app.exiftool_custom_te, "setText") as mock_setText_custom,
    ):
        app.resetExifTool(reset_custom=reset_custom)

        mock_setText_wipe.assert_called_once_with(STOCK_PRESETS.exiftool_wipe)
        mock_setText_preserve.assert_called_once_with(STOCK_PRESETS.exiftool_preserve)
        mock_setText_unsafe_wipe.assert_called_once_with(STOCK_PRESETS.exiftool_unsafe_wipe)
        assert bool(mock_setText_custom.call_count) == reset_custom

def test_getSettings_no_key_error(app):
    app.getSettings()

def test_resetOptimizationRules(app):
    with patch.object(app.ram_optimizer_rules_te, "setText") as mock_setText:
        app.resetOptimizationRules() 
        mock_setText.assert_called_once()

def test_resetToDefault(app):
    app.resetToDefault()

    assert app.no_sorting_cb.isChecked() == False
    assert app.disable_downscaling_startup_cb.isChecked() == True
    assert app.disable_delete_startup_cb.isChecked() == True
    
    assert app.jxl_effort_10_cb.isChecked() == False
    assert app.jxl_lossy_modular_cb.isChecked() == False
    assert app.custom_resampling_cb.isChecked() == False
    assert app.disable_progressive_jpegli_cb.isChecked() == False

    assert app.jxl_int_effort_cb.isChecked() == False
    assert app.custom_args_cb.isChecked() == False
    assert app.cjxl_args_te.toPlainText() == ""
    assert app.cjpegli_args_te.toPlainText() == ""
    assert app.im_args_te.toPlainText() == ""
    assert app.avifenc_args_te.toPlainText() == ""
    assert app.process_priority_cmb.currentIndex() == 0

def test_runMigrations_no_loaded_ver(app_migrations):
    with (
        patch.object(app_migrations.wm, "getLoadedVersion", return_value=None) as mock_getLoadedVersion,
        patch.object(app_migrations, "resetExifTool") as mock_resetExifTool,
        patch.object(app_migrations.exiftool_preserve_te, "toPlainText", return_value="custom"),
        patch("ui.tabs.settings_tab.message_box.info") as mock_message_box_info,
        patch("ui.tabs.settings_tab.message_box.confirm") as mock_message_box_confirm,
    ):
        app_migrations.runMigrations()
        mock_getLoadedVersion.assert_called_once()
        mock_resetExifTool.assert_not_called()
        mock_message_box_info.assert_not_called()
        mock_message_box_confirm.assert_not_called()

def test_runMigrations_skip_if_already_set_to_stock(app_migrations):
    with (
        patch.object(app_migrations.wm, "getLoadedVersion", return_value="v1.2.2") as mock_getLoadedVersion,
        patch.object(app_migrations, "resetExifTool") as mock_resetExifTool,
        patch.object(app_migrations.exiftool_wipe_te, "toPlainText", return_value=STOCK_PRESETS.exiftool_wipe),
        patch.object(app_migrations.exiftool_preserve_te, "toPlainText", return_value=STOCK_PRESETS.exiftool_preserve),
        patch.object(app_migrations.exiftool_unsafe_wipe_te, "toPlainText", return_value=STOCK_PRESETS.exiftool_unsafe_wipe),
        patch("ui.tabs.settings_tab.message_box.info") as mock_message_box_info,
        patch("ui.tabs.settings_tab.message_box.confirm") as mock_message_box_confirm,
    ):
        app_migrations.runMigrations()
        mock_resetExifTool.assert_not_called()
        mock_message_box_info.assert_not_called()
        mock_message_box_confirm.assert_not_called()

@pytest.mark.parametrize("version, expect_run", [
    ("1.0.0", True),
    ("1.2.2", True),
    ("1.2.3", False),
    ("1.2.4", False),
    ("dev-build", True),
])
def test_runMigrations_version_check(version, expect_run, app_migrations):
    with (
        patch.object(app_migrations.wm, "getLoadedVersion", return_value=version),
        patch.object(app_migrations, "resetExifTool") as mock_resetExifTool,
        patch.object(app_migrations.exiftool_preserve_te, "toPlainText", return_value="custom"),
        patch("ui.tabs.settings_tab.message_box.info") as mock_message_box_info,
        patch("ui.tabs.settings_tab.message_box.confirm") as mock_message_box_confirm,
    ):
        app_migrations.runMigrations()
        assert bool(mock_resetExifTool.call_count) == expect_run

def test_runMigrations_automatic(app_migrations):
    with (
        patch.object(app_migrations.wm, "getLoadedVersion", return_value="1.2.2"),
        patch.object(app_migrations, "resetExifTool") as mock_resetExifTool,
        patch.object(app_migrations.exiftool_wipe_te, "toPlainText", return_value="-all= -tagsFromFile @ -icc_profile:all -ColorSpace:all -Orientation $dst -overwrite_original"),
        patch.object(app_migrations.exiftool_preserve_te, "toPlainText", return_value="-tagsFromFile $src $dst -overwrite_original"),
        patch.object(app_migrations.exiftool_unsafe_wipe_te, "toPlainText", return_value="-all= $dst -overwrite_original"),
        patch("ui.tabs.settings_tab.message_box.info") as mock_message_box_info,
        patch("ui.tabs.settings_tab.message_box.confirm") as mock_message_box_confirm,
    ):
        app_migrations.runMigrations()

        mock_resetExifTool.assert_called_once_with(reset_custom=False)
        mock_message_box_info.assert_not_called()
        mock_message_box_confirm.assert_not_called()

def test_runMigrations_manual_accept(app_migrations):
    with (
        patch.object(app_migrations.wm, "getLoadedVersion", return_value="1.2.2"),
        patch.object(app_migrations, "resetExifTool") as mock_resetExifTool,
        patch.object(app_migrations.exiftool_wipe_te, "toPlainText", return_value="custom"),
        patch("ui.tabs.settings_tab.message_box.info") as mock_message_box_info,
        patch("ui.tabs.settings_tab.message_box.confirm", return_value=True) as mock_message_box_confirm,
    ):
        app_migrations.runMigrations()

        mock_resetExifTool.assert_called_once_with(reset_custom=False)
        mock_message_box_confirm.assert_called_once_with(app_migrations, "Settings Migration", "Recommended ExifTool presets changed. Apply them?")
        mock_message_box_info.assert_not_called()

def test_runMigrations_manual_reject(app_migrations):
    with (
        patch.object(app_migrations.wm, "getLoadedVersion", return_value="1.2.2"),
        patch.object(app_migrations, "resetExifTool") as mock_resetExifTool,
        patch.object(app_migrations.exiftool_wipe_te, "toPlainText", return_value="custom"),
        patch("ui.tabs.settings_tab.message_box.info") as mock_message_box_info,
        patch("ui.tabs.settings_tab.message_box.confirm", return_value=False) as mock_message_box_confirm,
    ):
        app_migrations.runMigrations()

        mock_resetExifTool.assert_not_called()
        mock_message_box_confirm.assert_called_once_with(app_migrations, "Settings Migration", "Recommended ExifTool presets changed. Apply them?")
        mock_message_box_info.assert_called_once_with(app_migrations, "Settings Migration", "This change is highly recommended. To apply changes later, press \"Reset\" in Settings -> ExifTool.")
