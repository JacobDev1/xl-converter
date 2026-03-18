from unittest.mock import patch, MagicMock

import pytest
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from ui.tabs.modify_tab import ModifyTab

@pytest.fixture
def app(qtbot):
    with (
        patch("ui.tabs.modify_tab.WidgetManager.loadState"),
        patch("ui.tabs.modify_tab.WidgetManager.saveState"),
    ):
        tab = ModifyTab(
            {
                "disable_downscaling_startup": False,
                "custom_resampling": False,
            },
            {
                "format": "JPEG XL"
            }
        )
        qtbot.addWidget(tab)
        return tab

def test_init(app):
    assert app.resample_l.isVisibleTo(app) == False
    assert app.resample_cmb.isVisibleTo(app) == False

def test_getSettings_no_key_error(app):
    app.getSettings()

SAMPLE_STATES = {
    "downscale": True,
    "mode": "Resolution",
    "resample": "Default"
    # ...
}

@pytest.mark.parametrize("input_states, init_cache, expected_saveState_call_count, expected_cache", [
    # Fresh
    (SAMPLE_STATES, None, 1, SAMPLE_STATES),

    # Cached
    (SAMPLE_STATES, SAMPLE_STATES, 0, SAMPLE_STATES),

    # None
    (None, SAMPLE_STATES, 1, None),
])
def test_saveState(
    input_states,
    init_cache,
    expected_saveState_call_count,
    expected_cache,
    app
):
    app.cached_states = init_cache
    
    with patch.object(app.wm, "saveState"):
        app.saveState(input_states)
        
        assert app.wm.saveState.call_count == expected_saveState_call_count
        assert app.cached_states == expected_cache

def test_resetToDefault(app):
    app.downscale_cb.setChecked(True)
    app.metadata_cmb.setCurrentIndex(1)
    app.keep_timestamps_cb.setChecked(True)
    app.mode_cmb.setCurrentIndex(1)
    app.resample_cmb.setCurrentIndex(1)
    app.file_size_sb.setValue(400)
    app.percent_sb.setValue(81)
    app.pixel_w_sb.setValue(1000)
    app.pixel_h_sb.setValue(1000)
    app.shortest_sb.setValue(5000)
    app.longest_sb.setValue(5000)
    app.pixel_w_cb.setChecked(False)
    app.pixel_h_cb.setChecked(False)

    app.resetToDefault()

    assert app.downscale_cb.isChecked() == False
    assert app.resample_cmb.currentIndex() == 0
    assert app.metadata_cmb.currentIndex() == 0
    assert app.keep_timestamps_cb.isChecked() == False
    assert app.mode_cmb.currentIndex() == 0
    assert app.resample_cmb.currentIndex() == 0
    assert app.file_size_sb.value() == 300
    assert app.percent_sb.value() == 80
    assert app.pixel_w_sb.value() == 2000
    assert app.pixel_h_sb.value() == 2000
    assert app.shortest_sb.value() == 1080
    assert app.longest_sb.value() == 1920
    assert app.megapixels_sb.value() == 2.1
    assert app.pixel_w_cb.isChecked() == True
    assert app.pixel_h_cb.isChecked() == True
    assert app.downscale_cb.isChecked() == False

@pytest.mark.parametrize("enabled", [True, False])
def test_setDownscalingEnabled(enabled, app):
    app.setDownscalingEnabled(enabled)
    assert app.downscale_cb.isChecked() == enabled

@pytest.mark.parametrize("enabled", [
    False, True,
])
def test_setDownscalingEnabled(enabled, app):
    app.setDownscalingEnabled(enabled)
    assert app.percent_l.isEnabled() == enabled
    assert app.percent_sb.isEnabled() == enabled
    if not enabled:
        assert app.pixel_h_cb.isEnabled() == enabled
        assert app.pixel_w_cb.isEnabled() == enabled
        assert app.pixel_h_sb.isEnabled() == enabled
        assert app.pixel_w_sb.isEnabled() == enabled
    assert app.file_size_l.isEnabled() == enabled
    assert app.file_size_sb.isEnabled() == enabled
    assert app.shortest_l.isEnabled() == enabled
    assert app.shortest_sb.isEnabled() == enabled
    assert app.longest_l.isEnabled() == enabled
    assert app.longest_sb.isEnabled() == enabled
    assert app.megapixels_sb.isEnabled() == enabled
    assert app.megapixels_l.isEnabled() == enabled

@pytest.mark.parametrize("custom_resampling_enabled", [True, False])
def test_setCustomResamplingEnabled(custom_resampling_enabled, app):
    app.setCustomResamplingEnabled(custom_resampling_enabled)

    assert app.resample_visible == custom_resampling_enabled
    assert app.resample_cmb.isVisibleTo(app) == custom_resampling_enabled
    assert app.resample_l.isVisibleTo(app) == custom_resampling_enabled

def test_onFileFormatChanged(app):
    with patch.object(app, "_updateDownscalingWidgets") as mock__updateDownscalingWidgets:
        app.onFileFormatChanged("format")
        app._updateDownscalingWidgets.assert_called_once()

@pytest.mark.parametrize("downscale_enabled, setEnabled_call_count_expected", [
    (True, 1),
    (False, 0),
])
def test_onResWidgetToggle(
    downscale_enabled,
    setEnabled_call_count_expected,
    app
):
    widget = MagicMock()
    widget.setEnabled = MagicMock()
    app.downscale_cb.setEnabled(downscale_enabled)
    app._onResWidgetToggled(widget, True)
    assert widget.setEnabled.call_count == setEnabled_call_count_expected

@pytest.mark.parametrize("file_format, allowed", [
    ("Lossless JPEG Transcoding", False),
    ("JPEG Reconstruction", False),
    ("JPEG XL", True),
])
def test_updateDownscalingWidgets_metadata(
    file_format, allowed, app
):
    app.file_format = file_format
    app._updateDownscalingWidgets()
    assert app.metadata_cmb.isEnabled() == allowed

@pytest.mark.parametrize("file_format, downscaling_checked, expected_enabled", [
    ("Lossless JPEG Transcoding", True, False),
    ("JPEG Reconstruction", True, False),
    ("Smallest Lossless", True, False),
    ("JPEG XL", True, True),
    ("PNG Optimization", True, False),
])
def test_updateDownscalingWidgets_downscaling(
    file_format,
    downscaling_checked,
    expected_enabled,
    app
):
    app.file_format = file_format
    app.downscale_cb.setChecked(downscaling_checked)

    app._updateDownscalingWidgets()

    assert len(app.wm.getWidgetsByTag("downscale_ui")) > 1
    for w in app.wm.getWidgetsByTag("downscale_ui"):
        assert w.isEnabled() == expected_enabled
    assert app.downscale_cb.isEnabled() == expected_enabled

@pytest.mark.parametrize("downscaling_enabled, pixel_w_checked, pixel_h_checked, expected_w_enabled, expected_h_enabled", [
    (True, False, False, False, False),
    (True, True, False, True, False),
    (True, False, True, False, True),
    (True, True, True, True, True),
    (False, True, True, False, False),
])
def test_updateDownscalingWidgets_pixel_widgets(
    downscaling_enabled,
    pixel_w_checked,
    pixel_h_checked,
    expected_w_enabled,
    expected_h_enabled,
    app
):
    app.file_format = "JPEG XL" if downscaling_enabled else "Lossless JPEG Transcoding"
    app.downscale_cb.setChecked(downscaling_enabled)
    app.pixel_w_cb.setChecked(pixel_w_checked)
    app.pixel_h_cb.setChecked(pixel_h_checked)

    app._updateDownscalingWidgets()

    assert app.pixel_w_sb.isEnabled() == expected_w_enabled
    assert app.pixel_h_sb.isEnabled() == expected_h_enabled

# Testing for resolution widget edge cases.
@pytest.mark.parametrize("downscaling_cb, width_cb, height_cb, expected_width_sb_enabled, expected_height_sb_enabled", [
    (True, True, True, True, True),
    (False, False, False, False, False),
    (False, True, True, False, False),
    (True, True, False, True, False),
    (True, False, True, False, True),
    (True, False, False, False, False),
])
def test_resolution_checkboxes_interactions(downscaling_cb, width_cb, height_cb, expected_width_sb_enabled, expected_height_sb_enabled, app):
    app.file_format = "JPEG XL"
    app.downscale_cb.setChecked(downscaling_cb)
    app.pixel_w_cb.setChecked(width_cb)
    app.pixel_h_cb.setChecked(height_cb)
    assert app.pixel_w_sb.isEnabled() == expected_width_sb_enabled
    assert app.pixel_h_sb.isEnabled() == expected_height_sb_enabled

@pytest.mark.parametrize("downscale_checked, pixel_w_checked, pixel_h_checked", [
    (True, True, True),
    (True, False, False),
    (False, True, True),
    (False, False, False),
])
def test_resolution_checkboxes_resetToDefault(
    downscale_checked,
    pixel_w_checked,
    pixel_h_checked,
    app
):
    app.file_format = "JPEG XL"
    app.downscale_cb.setChecked(downscale_checked)
    app.pixel_w_cb.setChecked(pixel_w_checked)
    app.pixel_h_cb.setChecked(pixel_h_checked)
    app.resetToDefault()
    
    assert not app.pixel_w_sb.isEnabled()
    assert not app.pixel_h_sb.isEnabled()

@pytest.mark.parametrize("mode_title", [
    ("Percent"),
    ("Resolution"),
    ("File Size"),
    ("Shortest Side"),
    ("Longest Side"),
    ("Megapixels"),
])
def test_onModeChanged_visibility(mode_title, app):
    app.mode_cmb.setCurrentText(mode_title)
    assert app.pixel_h_cb.isVisibleTo(app) == (mode_title == "Resolution")
    assert app.pixel_h_sb.isVisibleTo(app) == (mode_title == "Resolution")
    assert app.pixel_w_cb.isVisibleTo(app) == (mode_title == "Resolution")
    assert app.pixel_w_sb.isVisibleTo(app) == (mode_title == "Resolution")
    assert app.percent_l.isVisibleTo(app) == (mode_title == "Percent")
    assert app.percent_sb.isVisibleTo(app) == (mode_title == "Percent")
    assert app.file_size_l.isVisibleTo(app) == (mode_title == "File Size")
    assert app.file_size_sb.isVisibleTo(app) == (mode_title == "File Size")
    assert app.shortest_l.isVisibleTo(app) == (mode_title == "Shortest Side")
    assert app.shortest_sb.isVisibleTo(app) == (mode_title == "Shortest Side")
    assert app.longest_l.isVisibleTo(app) == (mode_title == "Longest Side")
    assert app.longest_sb.isVisibleTo(app) == (mode_title == "Longest Side")
    assert app.megapixels_sb.isVisibleTo(app) == (mode_title == "Megapixels")
    assert app.megapixels_l.isVisibleTo(app) == (mode_title == "Megapixels")

def test_isDownscalingEnabled_disabled(app):
    app.downscale_cb.setChecked(False)
    assert not app._isDownscalingEnabled()

def test_isDownscalingEnabled_resolution_options_disabled(app):
    app.mode_cmb.setCurrentText("Resolution")
    app.pixel_w_cb.setChecked(False)
    app.pixel_h_cb.setChecked(False)

    assert not app._isDownscalingEnabled()

def test_isDownscalingEnabled_enabled(app):
    app.mode_cmb.setCurrentText("Resolution")
    app.pixel_w_cb.setChecked(True)
    app.downscale_cb.setChecked(True)

    assert app._isDownscalingEnabled()

def test_getResampling_disabled(app):
    app.setCustomResamplingEnabled(False)
    app.resample_cmb.setCurrentIndex(1)
    assert app._getResampling() == "Default"

def test_getResampling_enabled(app):
    app.setCustomResamplingEnabled(True)
    app.resample_cmb.setCurrentIndex(1)
    assert app._getResampling() != "Default"
