from unittest.mock import patch, ANY, MagicMock

import pytest
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QDir

from ui.tabs.output_tab import OutputTab

@pytest.fixture
def app(qtbot):
    with (
        patch("ui.tabs.output_tab.WidgetManager.loadState"),
        patch("ui.tabs.output_tab.WidgetManager.saveState"),
    ):
        tab = OutputTab(
            {
                "disable_delete_startup": False,
                "enable_jxl_effort_10": False,
                "enable_quality_precision_snapping": False,
                "jpg_encoder": "JPEGLI",
                "jxl_lossy_modular": False,
                "jxl_int_effort": False,
                "avif_encoder": "AOM AV1",
            }
        )
        qtbot.addWidget(tab)
        return tab

def test_initial_state(app):
    # Format
    settings = app.getSettings()
    assert settings["format"] == "JPEG XL"
    assert settings["quality"] == 80
    assert settings["lossless"] == False
    assert settings["max_compression"] == False
    assert settings["effort"] == 7
    assert settings["intelligent_effort"] == False
    assert settings["jxl_modular"] == False
    assert settings["jxl_png_fallback"] == False
    assert settings["delete_original"] == False
    assert settings["jxl_verify"] == False
    assert settings["jxl_normalize_enable"] == False
    assert settings["jxl_normalize_when"] == "On Fail"
    assert not app.smIsFormatPoolEmpty()

    # Conv.
    assert settings["if_file_exists"] == "Rename"
    
    # After conv.
    assert not app.isClearAfterConvChecked()
    assert settings["delete_original_mode"] == "To Trash"

    # Save To
    assert settings["custom_output_dir"] == False
    assert settings["custom_output_dir_path"] == ""
    assert settings["keep_dir_struct"] == False

def test_thread_slider_change(app, qtbot):
    qtbot.mouseClick(app.threads_sl, Qt.LeftButton, pos=app.threads_sl.rect().center())
    assert app.threads_sb.value() == app.threads_sl.value()

def test_thread_spinbox_change(app):
    app.threads_sb.setValue(2)
    assert app.threads_sb.value() == 2
    assert app.threads_sb.value() == app.threads_sl.value()

def test_thread_slider_change(app):
    app.quality_sl.setValue(50)
    assert app.quality_sl.value() == 50
    assert app.quality_sl.value() == app.quality_sb.value()

def test_thread_spinbox_change(app):
    app.quality_sb.setValue(50)
    assert app.quality_sb.value() == 50
    assert app.quality_sl.value() == app.quality_sb.value()

def test_deleteOriginal_change(app):
    app.delete_original_cb.setChecked(True)
    assert app.delete_original_cmb.isEnabled()

def test_output_toggled(app):
    app.choose_output_ct_rb.setChecked(True)
    assert app.choose_output_ct_le.isEnabled()
    assert app.choose_output_ct_btn.isEnabled()
    
    app.choose_output_src_rb.setChecked(True)
    assert not app.choose_output_ct_le.isEnabled()
    assert not app.choose_output_ct_btn.isEnabled()

def test__onEffortToggled_jpeg_xl(app):
    app.jxl_int_effort_visible = True
    with (
        patch.object(app.format_cmb, "currentText", return_value="JPEG XL"),
        patch.object(app.int_effort_cb, "isChecked", return_value=True),
        patch.object(app.effort_sb, "setEnabled") as mock_setEnabled,
    ):
        app._onEffortToggled()
        mock_setEnabled.assert_called_once_with(False)

def test__onEffortToggled_other(app):
    app.jxl_int_effort_visible = True
    with (
        patch.object(app.format_cmb, "currentText", return_value="PNG"),
        patch.object(app.effort_sb, "setEnabled") as mock_setEnabled,
    ):
        app._onEffortToggled()
        mock_setEnabled.assert_called_once_with(True)

@pytest.mark.parametrize("visible", [True, False])
def test_onJXLLossyModularVisibleToggled(visible, app):
    with (
        patch.object(app.format_cmb, "currentText", return_value="JPEG XL"),
        patch("ui.tabs.output_tab.WidgetManager.setVisibleByTag") as mock_setVisibleByTag,
    ):
        app.onJXLLossyModularVisibleToggled(visible)

        assert app.jxl_lossy_modular_visible == visible
        mock_setVisibleByTag.assert_called_once_with("jxl_losssy_modular", visible)

@pytest.mark.parametrize("visible", [True, False])
def test_onJXLIntEffortVisibleToggled(visible, app):
    with (
        patch.object(app.format_cmb, "currentText", return_value="JPEG XL"),
        patch.object(app.int_effort_cb, "setVisible") as mock_setVisible,
        patch.object(app, "_onEffortToggled") as mock__onEffortToggled,
    ):
        app.onJXLIntEffortVisibleToggled(visible)

        assert app.jxl_int_effort_visible == visible
        mock_setVisible.assert_called_once_with(visible)
        mock__onEffortToggled.assert_called_once()

def test_onFormatChange_int_e_toggle(app):
    app.format_cmb.setCurrentText("JPEG XL")
    app.onJXLIntEffortVisibleToggled(True)
    app.int_effort_cb.setChecked(True)

    assert not app.effort_sb.isEnabled()

def test_onFormatChange_lossless_toggled(app):
    app.lossless_cb.setChecked(True)
    
    assert app.lossless_cb.isEnabled()
    assert not app.quality_sl.isEnabled()
    assert not app.quality_sb.isEnabled()
    
    app.lossless_cb.setChecked(False)
    
    assert app.lossless_cb.isEnabled()
    assert app.quality_sl.isEnabled()
    assert app.quality_sb.isEnabled()

@pytest.mark.parametrize("file_format, visible_widgets", [
    ("JPEG XL", ["quality", "effort", "lossless"]),
    ("AVIF", ["quality", "effort", "chroma_subsampling"]),
    ("WebP", ["quality", "effort", "lossless"]),
    ("JPEG", ["quality", "chroma_subsampling"]),
    ("PNG", []),
    ("Lossless JPEG Transcoding", ["effort", "jxl_verify", "jxl_normalize"]),
    ("JPEG Reconstruction", ["png_fallback"]),
    ("Smallest Lossless", ["smallest_lossless"]),
])
def test_onFormatChange_visibility(app, file_format, visible_widgets):
    app.format_cmb.setCurrentText(file_format)
    assert app.format_cmb.currentText() == file_format
    
    # Effort
    effort = "effort" in visible_widgets
    assert app.int_effort_cb.isVisibleTo(app) == ("int_effort" in visible_widgets)
    assert app.effort_sb.isVisibleTo(app) == effort
    assert app.effort_l.isVisibleTo(app) == effort
    
    # Quality
    quality = "quality" in visible_widgets
    assert app.quality_l.isVisibleTo(app) == quality
    assert app.quality_sl.isVisibleTo(app) == quality
    assert app.quality_sb.isVisibleTo(app) == quality
    
    # Lossless
    assert app.lossless_cb.isVisibleTo(app) == ("lossless" in visible_widgets)
    
    # Misc.
    jxl_modular = "jxl_modular" in visible_widgets
    assert app.jxl_modular_cb.isVisibleTo(app) == jxl_modular

    chroma_subsampling = "chroma_subsampling" in visible_widgets
    assert app.chroma_subsampling_l.isVisibleTo(app) == chroma_subsampling
    assert (
        app.chroma_subsampling_jpegli_cmb.isVisibleTo(app) == chroma_subsampling or
        app.chroma_subsampling_jpg_cmb.isVisibleTo(app) == chroma_subsampling or
        file_format == "AVIF"   # Tested in test_AVIF_chroma_subsampling_visibility
    )

    smallest_lossless = "smallest_lossless" in visible_widgets
    assert app.smallest_lossless_png_cb.isVisibleTo(app) == smallest_lossless
    assert app.smallest_lossless_webp_cb.isVisibleTo(app) == smallest_lossless
    assert app.smallest_lossless_jxl_cb.isVisibleTo(app) == smallest_lossless
    assert app.max_compression_cb.isVisibleTo(app) == smallest_lossless
    assert app.jxl_png_fallback_cb.isVisibleTo(app) == ("png_fallback" in visible_widgets)

    assert app.jxl_verify_cb.isVisibleTo(app) == ("jxl_verify" in visible_widgets)
    assert app.jxl_normalize_enable_cb.isVisibleTo(app) == ("jxl_normalize" in visible_widgets)
    assert app.jxl_normalize_when_cmb.isVisibleTo(app) == ("jxl_normalize" in visible_widgets)

@pytest.mark.parametrize("encoder", [
    ("AOM AV1"),
    ("SVT-AV1-PSY"),
])
def test_AVIF_chroma_subsampling_visibility(encoder, app):
    app.format_cmb.setCurrentText("AVIF")
    app.onAVIFEncoderChanged(encoder)
    assert app.chroma_subsampling_svt_av1_psy_cmb.isVisibleTo(app) == (encoder == "SVT-AV1-PSY")
    assert app.chroma_subsampling_aom_av1_cmb.isVisibleTo(app) == (encoder == "AOM AV1")

@pytest.mark.parametrize("widget_name, variable_name", [
    ("int_effort_cb", "jxl_int_effort_visible"),
    ("jxl_modular_cb", "jxl_lossy_modular_visible"),
])
def test_onFormatChange_visibility_controled_by_vars(widget_name, variable_name, app):
    if not hasattr(app, variable_name):
        raise AssertionError(f"Variable \"{variable_name}\" does not exist")
    setattr(app, variable_name, False)
    app._onFormatChange()
    assert not getattr(app, widget_name).isVisibleTo(app), f"Widget \"{widget_name}\" does not exist"
    setattr(app, variable_name, True)
    app._onFormatChange()
    assert getattr(app, widget_name).isVisibleTo(app), f"Widget \"{widget_name}\" does not exist"

def test_onFormatChange_lossless_glitch(app):
    """Tests if an option set in one format affects others."""
    app.lossless_cb.setChecked(True)
    app.onJXLIntEffortVisibleToggled(True)
    assert not app.quality_sl.isEnabled()

    app.format_cmb.setCurrentText("WebP")
    assert app.quality_sl.isEnabled()

    app.format_cmb.setCurrentText("JPEG XL")
    
def test_onFormatChange_int_e_glitch(app):
    app.int_effort_cb.setChecked(True)
    app.onJXLIntEffortVisibleToggled(True)
    assert not app.effort_sb.isEnabled()

    app.format_cmb.setCurrentText("AVIF")
    assert app.effort_sb.isEnabled()

    app.format_cmb.setCurrentText("JPEG XL")
    assert not app.effort_sb.isEnabled()

def test_jpeg_xl_effort_10(app):
    app.format_cmb.setCurrentText("JPEG XL")
    
    assert app.effort_sb.maximum() == 9
    app.onJXLEffort10Enabled(True)
    assert app.effort_sb.maximum() == 10

@pytest.mark.parametrize("file_format, min_val, max_val", [
    ("JPEG XL", 1, 9),
    ("AVIF", 0, 10),
])
def test_effort_ranges(app, file_format, min_val, max_val):
    app.format_cmb.setCurrentText(file_format)
    
    assert app.effort_sb.minimum() == min_val
    assert app.effort_sb.maximum() == max_val

def test__chooseOutput_var_default(app):
    with (
        patch("ui.tabs.output_tab.QFileDialog") as mock_qfiledialog,
        patch("ui.lib.widget_manager.WidgetManager.getVar", return_value=None),
        patch("ui.lib.utils.isPathValidStr", return_value=False),
    ):
        mock_qfiledialog.return_value.exec.return_value = False

        app._chooseOutput()

        mock_qfiledialog.assert_called_once_with(app, ANY, QDir.homePath())

def test__chooseOutput_var_load(app):
    last_used = "/home/user/Pictures"
    with (
        patch("ui.tabs.output_tab.QFileDialog") as mock_qfiledialog,
        patch("ui.lib.widget_manager.WidgetManager.getVar", return_value=last_used),
        patch("ui.lib.widget_manager.WidgetManager.setVar") as mock_setVar,
        patch("ui.tabs.output_tab.isPathValidStr", return_value=True),
    ):
        mock_qfiledialog.return_value.exec.return_value = False

        app._chooseOutput()

        mock_qfiledialog.assert_called_once_with(app, ANY, last_used)

def test__chooseOutput_var_save(app):
    last_used = "/home/user/Pictures"
    with (
        patch("ui.tabs.output_tab.QFileDialog") as mock_qfiledialog,
        patch("ui.lib.widget_manager.WidgetManager.getVar", return_value=last_used),
        patch("ui.lib.widget_manager.WidgetManager.setVar") as mock_setVar,
        patch("ui.tabs.output_tab.isPathValidStr", return_value=False),
    ):
        mock_qfiledialog.return_value.exec.return_value = True
        mock_qfiledialog.return_value.directory.return_value.absolutePath.return_value = last_used
        app.choose_output_ct_le = MagicMock()

        app._chooseOutput()

        mock_setVar.assert_called_once_with("choose_output_last_dir", last_used)

@pytest.mark.parametrize("widget_name, variable_name, associated_key", [
    ("int_effort_cb", "jxl_int_effort_visible", "intelligent_effort"),
    ("jxl_modular_cb", "jxl_lossy_modular_visible", "jxl_modular"),
    ("int_effort_cb", "jxl_int_effort_visible", "intelligent_effort"),
])
def test_getSettings_widget_visibility(widget_name, variable_name, associated_key, app):
    getattr(app, widget_name).setChecked(True)
    setattr(app, variable_name, False)
    assert not app.getSettings()[associated_key]
    setattr(app, variable_name, True)
    assert app.getSettings()[associated_key]

def test_getSettings_no_png_opt(app):
    app.duplicates_cmb.setCurrentText("Rename")
    app.choose_output_src_rb.setChecked(True)
    app.delete_original_cb.setChecked(True)
    app.format_cmb.setCurrentText("JPEG")
    app.png_opt_inplace_cb.setChecked(True)

    settings = app.getSettings()

    assert settings["if_file_exists"] == "Rename"
    assert settings["custom_output_dir"] == False
    assert settings["delete_original"] == True

def test_getSettings_png_opt(app):
    app.duplicates_cmb.setCurrentText("Rename")
    app.choose_output_ct_rb.setChecked(False)
    app.delete_original_cb.setChecked(True)
    app.format_cmb.setCurrentText("PNG Optimization")
    app.png_opt_inplace_cb.setChecked(True)

    settings = app.getSettings()

    assert settings["if_file_exists"] == "Replace"
    assert settings["custom_output_dir"] == False
    assert settings["delete_original"] == False

@pytest.mark.parametrize(
    "jxl_modular_visible, jxl_lossless_checked, jxl_modular_checked, expected_return", [
        (False, False, True, False),
        (True, True, True, False),
        (False, True, True, False),
        (True, False, True, True),
    ]
)
def test_getSettings_jxl_lossy_modular(
    jxl_modular_visible,
    jxl_lossless_checked,
    jxl_modular_checked,
    expected_return,
    app,
):
    app.jxl_modular_cb.setChecked(True)
    setattr(app, "jxl_lossy_modular_visible", jxl_modular_visible)
    app.lossless_cb.setChecked(jxl_lossless_checked)
    app.jxl_modular_cb.setChecked(jxl_modular_checked)

    assert app.getSettings()["jxl_modular"] == expected_return

def test__onJXLNormalizeClicked_no_var(app):
    with (
        patch.object(app.wm, "getVar", return_value=None) as mock_getVar,
        patch.object(app.wm, "setVar") as mock_setVar,
        patch("ui.tabs.output_tab.message_box.info") as mock_message_box_info,
    ):
        app._onJXLNormalizeClicked()
    
    mock_getVar.assert_called_once_with("jxl_normalize_checksum_msg_seen")
    mock_message_box_info.assert_called_once()
    mock_setVar.assert_called_once_with("jxl_normalize_checksum_msg_seen", True)

def test__onJXLNormalizeClicked_var_present(app):
    with (
        patch.object(app.wm, "getVar", return_value=True) as mock_getVar,
        patch.object(app.wm, "setVar") as mock_setVar,
        patch("ui.tabs.output_tab.message_box.info") as mock_message_box_info,
    ):
        app._onJXLNormalizeClicked()
    
    mock_getVar.assert_called_once_with("jxl_normalize_checksum_msg_seen")
    mock_message_box_info.assert_not_called()
    mock_setVar.assert_not_called()

@pytest.mark.parametrize("encoder", ("AOM AV1", "SVT-AV1-PSY"))
def test_onAVIFEncoderChanged_happy_path(encoder, app):
    app.format_cmb.setCurrentText("AVIF")

    app.onAVIFEncoderChanged(encoder)

    assert app.chroma_subsampling_svt_av1_psy_cmb.isVisibleTo(app) == (encoder == "SVT-AV1-PSY")
    assert app.chroma_subsampling_aom_av1_cmb.isVisibleTo(app) == (encoder == "AOM AV1")

def test_onAVIFEncoderChanged_other_format(app):
    app.format_cmb.setCurrentText("JPEG XL")

    app.onAVIFEncoderChanged("AOM AV1")

    assert not app.chroma_subsampling_svt_av1_psy_cmb.isVisibleTo(app)
    assert not app.chroma_subsampling_aom_av1_cmb.isVisibleTo(app)

def test_png_opt_inplace_happy_path(app):
    # PNG Optimization / inplace on
    app.format_cmb.setCurrentText("PNG Optimization")
    app.delete_original_cb.setChecked(False)
    app.png_opt_inplace_cb.setChecked(True)
    assert not app.output_grp.isEnabled()
    assert not app.duplicates_l.isEnabled()
    assert not app.duplicates_cmb.isEnabled()
    assert not app.delete_original_cb.isEnabled()
    assert not app.delete_original_cmb.isEnabled()

    # PNG Optimization / inplace off
    app.png_opt_inplace_cb.setChecked(False)
    assert app.output_grp.isEnabled()
    assert app.duplicates_l.isEnabled()
    assert app.duplicates_cmb.isEnabled()
    assert app.delete_original_cb.isEnabled()
    assert not app.delete_original_cmb.isEnabled()

    # JPEG / reference
    app.png_opt_inplace_cb.setChecked(True)
    app.format_cmb.setCurrentText("JPEG")
    assert app.output_grp.isEnabled()
    assert app.duplicates_l.isEnabled()
    assert app.duplicates_cmb.isEnabled()
    assert app.delete_original_cb.isEnabled()
    assert not app.delete_original_cmb.isEnabled()

def test_delete_original_happy_path(app):
    # Default behavior
    app.format_cmb.setCurrentText("JPEG")
    app.delete_original_cb.setChecked(True)
    assert app.delete_original_cmb.isEnabled()
    app.delete_original_cb.setChecked(False)
    assert not app.delete_original_cmb.isEnabled()

    # PNG Optimization
    app.format_cmb.setCurrentText("PNG Optimization")
    app.png_opt_inplace_cb.setChecked(True)
    assert not app.delete_original_cb.isEnabled()
    assert not app.delete_original_cmb.isEnabled()
    app.png_opt_inplace_cb.setChecked(False)
    app.delete_original_cb.setChecked(False)
    assert app.delete_original_cb.isEnabled()
    assert not app.delete_original_cmb.isEnabled()

    # Verify default behavior
    app.format_cmb.setCurrentText("JPEG")
    assert app.delete_original_cb.isEnabled()
    assert not app.delete_original_cmb.isEnabled()
    app.delete_original_cb.setChecked(True)
    assert app.delete_original_cb.isEnabled()
    assert app.delete_original_cmb.isEnabled()
