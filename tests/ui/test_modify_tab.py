from unittest.mock import patch

import pytest
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from ui.modify_tab import ModifyTab

@pytest.fixture
def app(qtbot):
    with patch("ui.modify_tab.WidgetManager.loadState"), \
        patch("ui.modify_tab.WidgetManager.saveState"):
        app = QApplication.instance()
        if not app:
            app = QApplication([])
        tab = ModifyTab({
            "disable_downscaling_startup": False,
            "custom_resampling": False,
        })
        qtbot.addWidget(tab)
        return tab

def test_init(app):
    assert app.resample_l.isVisibleTo(app) == False
    assert app.resample_cmb.isVisibleTo(app) == False

@pytest.mark.parametrize("enabled", [
    False, True,
])
def test_toggleDownscaleUI(enabled, app):
    app.toggleDownscaleUI(enabled)
    assert app.percent_l.isEnabled() == enabled
    assert app.percent_sb.isEnabled() == enabled
    assert app.pixel_h_l.isEnabled() == enabled
    assert app.pixel_h_sb.isEnabled() == enabled
    assert app.pixel_w_l.isEnabled() == enabled
    assert app.pixel_w_sb.isEnabled() == enabled
    assert app.file_size_l.isEnabled() == enabled
    assert app.file_size_sb.isEnabled() == enabled
    assert app.shortest_l.isEnabled() == enabled
    assert app.shortest_sb.isEnabled() == enabled
    assert app.longest_l.isEnabled() == enabled
    assert app.longest_sb.isEnabled() == enabled

def test_resetToDefault(app):
    app.downscale_cb.setChecked(True)
    app.metadata_cmb.setCurrentIndex(1)
    app.date_time_cb.setChecked(True)
    app.mode_cmb.setCurrentIndex(1)
    app.resample_cmb.setCurrentIndex(1)
    app.file_size_sb.setValue(400)
    app.percent_sb.setValue(81)
    app.pixel_w_sb.setValue(1000)
    app.pixel_h_sb.setValue(1000)
    app.shortest_sb.setValue(5000)
    app.longest_sb.setValue(5000)

    app.resetToDefault()

    assert app.downscale_cb.isChecked() == False
    assert app.resample_cmb.currentIndex() == 0
    assert app.metadata_cmb.currentIndex() == 0
    assert app.date_time_cb.isChecked() == False
    assert app.mode_cmb.currentIndex() == 0
    assert app.resample_cmb.currentIndex() == 0
    assert app.file_size_sb.value() == 300
    assert app.percent_sb.value() == 80
    assert app.pixel_w_sb.value() == 2000
    assert app.pixel_h_sb.value() == 2000
    assert app.shortest_sb.value() == 1080
    assert app.longest_sb.value() == 1920

def test_getSettings_key_error(app):
    app.getSettings()

def test_getReportData_key_error(app):
    app.getReportData()

@pytest.mark.parametrize("mode, percent, resolution, file_size, shortest, longest", [
    ("Percent", True, False, False, False, False),
    ("Resolution", False, True, False, False, False),
    ("File Size", False, False, True, False, False),
    ("Shortest Side", False, False, False, True, False),
    ("Longest Side", False, False, False, False, True),
])
def test_onModeChanged_visibility(mode, percent, resolution, file_size, shortest, longest, app):
    app.mode_cmb.setCurrentIndex(app.mode_cmb.findText(mode))
    assert app.percent_l.isVisibleTo(app) == percent
    assert app.percent_sb.isVisibleTo(app) == percent
    assert app.pixel_h_l.isVisibleTo(app) == resolution
    assert app.pixel_h_sb.isVisibleTo(app) == resolution
    assert app.pixel_w_l.isVisibleTo(app) == resolution
    assert app.pixel_w_sb.isVisibleTo(app) == resolution
    assert app.file_size_l.isVisibleTo(app) == file_size
    assert app.file_size_sb.isVisibleTo(app) == file_size
    assert app.shortest_l.isVisibleTo(app) == shortest
    assert app.shortest_sb.isVisibleTo(app) == shortest
    assert app.longest_l.isVisibleTo(app) == longest
    assert app.longest_sb.isVisibleTo(app) == longest

@pytest.mark.parametrize("downscaling_on", [
    False, True,
])
def test_customResampling_visibility(downscaling_on, app):
    app.downscale_cb.setChecked(downscaling_on)
    assert app.percent_l.isEnabled() == downscaling_on
    assert app.percent_sb.isEnabled() == downscaling_on
    assert app.pixel_h_l.isEnabled() == downscaling_on
    assert app.pixel_h_sb.isEnabled() == downscaling_on
    assert app.pixel_w_l.isEnabled() == downscaling_on
    assert app.pixel_w_sb.isEnabled() == downscaling_on
    assert app.file_size_l.isEnabled() == downscaling_on
    assert app.file_size_sb.isEnabled() == downscaling_on
    assert app.shortest_l.isEnabled() == downscaling_on
    assert app.shortest_sb.isEnabled() == downscaling_on
    assert app.longest_l.isEnabled() == downscaling_on
    assert app.longest_sb.isEnabled() == downscaling_on

def test_getResampling_disabled(app):
    app.toggleCustomResampling(False)
    app.resample_cmb.setCurrentIndex(1)
    assert app.getResampling() == "Default"

def test_getResampling_enabled(app):
    app.toggleCustomResampling(True)
    app.resample_cmb.setCurrentIndex(1)
    assert app.getResampling() != "Default"

@pytest.mark.parametrize("custom_resampling_enabled", [True, False])
def test_toggleCustomResampling(custom_resampling_enabled, app):
    app.toggleCustomResampling(custom_resampling_enabled)

    assert app.resample_visible == custom_resampling_enabled
    assert app.resample_cmb.isVisibleTo(app) == custom_resampling_enabled
    assert app.resample_l.isVisibleTo(app) == custom_resampling_enabled