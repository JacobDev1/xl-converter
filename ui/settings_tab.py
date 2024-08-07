import os
import logging

from PySide6.QtWidgets import(
    QWidget,
    QGridLayout,
    QVBoxLayout,
    QHBoxLayout,
    QCheckBox,
    QPushButton,
    QLabel,
    QSizePolicy,
    QFormLayout,
    QSpacerItem,
    QTextEdit,
    QComboBox,
)
from PySide6.QtCore import(
    Signal,
    QObject,
    Qt,
    QUrl,
)
from PySide6.QtGui import(
    QDesktopServices,
)

from ui.theme import setTheme
from ui.widget_manager import WidgetManager
from ui.scroll_area import ScrollArea
from ui.spinbox import SpinBox
from ui.combobox import ComboBox
from data.logging_manager import LoggingManager
from ui.notifications import Notifications
from ui.utils import setToolTip
from data.tooltips import TOOLTIPS

class Signals(QObject):
    custom_resampling = Signal(bool)
    disable_sorting = Signal(bool)
    enable_jxl_effort_10 = Signal(bool)
    enable_quality_prec_snap = Signal(bool)
    change_jpg_encoder = Signal(str)

class SettingsTab(QWidget):
    def __init__(self):
        super(SettingsTab, self).__init__()

        self.wm = WidgetManager("SettingsTab")
        self.signals = Signals()
        self.logging_manager = LoggingManager()
        self.notifications = Notifications(self)

        # Init UI
        self.setupUI()
        self.setupWidgets()
        self.setupLayouts()
        self.setupSignals()
        self.setSizes()

        # Init states
        self.changeCategory("General")
        self.resetToDefault()
        self.wm.loadState()
        self.setToolTips()

        # Refresh states
        self.onCustomArgsToggled()
        self.onPlaySoundOnFinishVolumeToggled()

        # Apply Settings
        self.setDarkModeEnabled(self.dark_theme_cb.isChecked())

    def setupUI(self):
        self.main_lt = QGridLayout()
        self.setLayout(self.main_lt)

        self.categories_lt = QVBoxLayout()
        self.settings_w = QWidget()
        self.settings_sa = ScrollArea(self)
        self.settings_lt = QVBoxLayout()
        self.settings_w.setLayout(self.settings_lt)
        self.settings_sa.setWidget(self.settings_w)
        self.categories_lt.setContentsMargins(0, 1, 0, 1)

        self.main_lt.addLayout(self.categories_lt, 0, 0)
        self.main_lt.addWidget(self.settings_sa, 0, 1)
        self.main_lt.setColumnStretch(0, 3)
        self.main_lt.setColumnStretch(1, 7)

    def setupWidgets(self):
        self.dark_theme_cb = self.wm.addWidget("dark_theme_cb", QCheckBox("Dark Theme", self))
        self.disable_on_startup_l = QLabel("Disable on Startup")
        self.disable_downscaling_startup_cb = self.wm.addWidget("disable_downscaling_startup_cb", QCheckBox("Downscaling", self))
        self.disable_delete_startup_cb = self.wm.addWidget("disable_delete_startup_cb", QCheckBox("Delete Original", self))
        self.no_exceptions_cb = self.wm.addWidget("no_exceptions_cb", QCheckBox("Disable Exception Popups", self))
        self.no_sorting_cb = self.wm.addWidget("no_sorting_cb", QCheckBox("Input - Disable Sorting", self))
        self.enable_jxl_effort_10 = self.wm.addWidget("enable_jxl_effort_10", QCheckBox("JPEG XL - Enable Effort 10", self))
        self.disable_progressive_jpegli_cb = self.wm.addWidget("disable_progressive_jpegli_cb", QCheckBox("JPEGLI - Disable Progressive Scan", self))
        self.custom_resampling_cb = self.wm.addWidget("custom_resampling_cb", QCheckBox("Downscaling - Custom Resampling", self))
        self.quality_prec_snap_cb = self.wm.addWidget("quality_prec_snap_cb", QCheckBox("Quality Slider - Snap to Individual Values"))
        self.jxl_lossless_jpeg_cb = self.wm.addWidget("jxl_lossless_jpeg_cb", QCheckBox("JPEG XL - Automatic JPEG Recompression"))
        self.play_sound_on_finish_cb = self.wm.addWidget("play_sound_on_finish_cb", QCheckBox("Play Sound When Conversion Finishes"))
        self.play_sound_on_finish_vol_l = self.wm.addWidget("play_sound_on_finish_vol_l", QLabel("Volume"))
        self.play_sound_on_finish_vol_sb = self.wm.addWidget("play_sound_on_finish_vol_sb", SpinBox())
        self.play_sound_on_finish_vol_sb.setRange(0, 100)
        self.play_sound_on_finish_vol_sb.setSuffix("%")

        self.jpg_encoder_l = self.wm.addWidget("jpg_encoder_l", QLabel("JPEG Encoder"))
        self.jpg_encoder_cmb = self.wm.addWidget("jpg_encoder_cmb", ComboBox())
        self.jpg_encoder_cmb.addItems((
            "JPEGLI",
            "libjpeg",
        ))
        self.keep_if_larger_cb = self.wm.addWidget("keep_if_larger_cb", QCheckBox("Do Not Delete Original When Result is Larger"))
        self.copy_if_larger_cb = self.wm.addWidget("copy_if_larger_cb", QCheckBox("Copy Original When Result is Larger"))
        self.multithreading_cmb = self.wm.addWidget("multithreading_cmb", QComboBox())
        self.multithreading_l = QLabel("Multithreading")
        self.multithreading_cmb.addItems(("Performance", "Low RAM"))

        self.exiftool_l = QLabel("ExifTool Arguments")
        self.exiftool_wipe_l = QLabel("Wipe")
        self.exiftool_wipe_te = self.wm.addWidget("exiftool_wipe_te", QTextEdit())
        self.exiftool_preserve_l = QLabel("Preserve")
        self.exiftool_preserve_te = self.wm.addWidget("exiftool_preserve_te", QTextEdit())
        self.exiftool_unsafe_wipe_l = QLabel("Unsafe Wipe")
        self.exiftool_unsafe_wipe_te = self.wm.addWidget("exiftool_unsafe_wipe_te", QTextEdit())
        self.exiftool_custom_l = QLabel("Custom")
        self.exiftool_custom_te = self.wm.addWidget("exiftool_custom_te", QTextEdit())
        self.exiftool_reset_btn = QPushButton("Reset")
        self.exiftool_wipe_te.setAcceptRichText(False)
        self.exiftool_preserve_te.setAcceptRichText(False)
        self.exiftool_unsafe_wipe_te.setAcceptRichText(False)
        self.exiftool_custom_te.setAcceptRichText(False)

        self.custom_args_cb = self.wm.addWidget("custom_args_cb", QCheckBox("Additional Encoder Arguments"))
        self.avifenc_args_l = QLabel("avifenc\nAVIF")
        self.avifenc_args_te = self.wm.addWidget("avifenc_args_te", QTextEdit())
        self.cjpegli_args_l = QLabel("cjpegli\nJPEG")
        self.cjpegli_args_te = self.wm.addWidget("cjpegli_args_te", QTextEdit())
        self.cjxl_args_l = QLabel("cjxl\nJPEG XL")
        self.cjxl_args_te = self.wm.addWidget("cjxl_args_te", QTextEdit())
        self.im_args_l = QLabel("ImageMagick\nWebP\nJPEG (libjpeg)")
        self.im_args_te = self.wm.addWidget("im_args_te", QTextEdit())
        self.avifenc_args_te.setAcceptRichText(False)
        self.cjpegli_args_te.setAcceptRichText(False)
        self.cjxl_args_te.setAcceptRichText(False)
        self.im_args_te.setAcceptRichText(False)

        self.start_logging_btn = self.wm.addWidget("start_logging_btn", QPushButton("Start Logging"))
        self.open_log_dir_btn = self.wm.addWidget("open_log_dir_btn", QPushButton("Open Logs Folder"))
        self.wipe_log_dir_btn = self.wm.addWidget("wipe_log_dir_btn", QPushButton("Wipe Logs Folder"))
        self.start_logging_btn.setCheckable(True)

        self.general_btn = QPushButton("General", self)
        self.conversion_btn = QPushButton("Conversion", self)
        self.advanced_btn = QPushButton("Advanced", self)
        self.general_btn.setCheckable(True)
        self.conversion_btn.setCheckable(True)
        self.advanced_btn.setCheckable(True)

        self.restore_defaults_btn = QPushButton("Reset to Default", self)

    def setupLayouts(self):
        ## Categories
        self.categories_lt.addWidget(self.general_btn)
        self.categories_lt.addWidget(self.conversion_btn)
        self.categories_lt.addWidget(self.advanced_btn)
        self.categories_lt.addItem(QSpacerItem(10, 10, QSizePolicy.Minimum, QSizePolicy.Expanding))
        self.categories_lt.addWidget(self.restore_defaults_btn)

        ## General
        self.settings_lt.addLayout(self.createQHboxLayout(self.disable_on_startup_l, self.disable_delete_startup_cb, self.disable_downscaling_startup_cb))
        self.settings_lt.addWidget(self.dark_theme_cb)
        self.settings_lt.addWidget(self.quality_prec_snap_cb)
        self.settings_lt.addWidget(self.no_sorting_cb)
        self.settings_lt.addWidget(self.play_sound_on_finish_cb)
        self.play_sound_on_finish_vol_hb = self.createQHboxLayout(self.play_sound_on_finish_vol_l, self.play_sound_on_finish_vol_sb)
        self.settings_lt.addLayout(self.play_sound_on_finish_vol_hb)

        ## Conversion
        self.settings_lt.addWidget(self.jxl_lossless_jpeg_cb)
        self.jpg_encoder_hb = self.createQHboxLayout(self.jpg_encoder_l, self.jpg_encoder_cmb)
        self.settings_lt.addLayout(self.jpg_encoder_hb)
        self.jpg_encoder_hb.addStretch()
        self.settings_lt.addWidget(self.disable_progressive_jpegli_cb)
        self.settings_lt.addWidget(self.keep_if_larger_cb)
        self.settings_lt.addWidget(self.copy_if_larger_cb)
        self.multithreading_hb = self.createQHboxLayout(self.multithreading_l, self.multithreading_cmb)
        self.settings_lt.addLayout(self.multithreading_hb)

        ## Advanced
        self.settings_lt.addWidget(self.enable_jxl_effort_10)
        self.settings_lt.addWidget(self.custom_resampling_cb)
        self.settings_lt.addWidget(self.no_exceptions_cb)
        self.settings_lt.addWidget(self.exiftool_l)
        self.settings_lt.addLayout(self.createQHboxLayout(self.exiftool_wipe_l, self.exiftool_wipe_te))
        self.settings_lt.addLayout(self.createQHboxLayout(self.exiftool_preserve_l, self.exiftool_preserve_te))
        self.settings_lt.addLayout(self.createQHboxLayout(self.exiftool_unsafe_wipe_l, self.exiftool_unsafe_wipe_te))
        self.settings_lt.addLayout(self.createQHboxLayout(self.exiftool_custom_l, self.exiftool_custom_te))
        self.settings_lt.addWidget(self.exiftool_reset_btn)
        self.settings_lt.addWidget(self.custom_args_cb)
        self.settings_lt.addLayout(self.createQHboxLayout(self.cjxl_args_l, self.cjxl_args_te))
        self.settings_lt.addLayout(self.createQHboxLayout(self.avifenc_args_l, self.avifenc_args_te))
        self.settings_lt.addLayout(self.createQHboxLayout(self.cjpegli_args_l, self.cjpegli_args_te))
        self.settings_lt.addLayout(self.createQHboxLayout(self.im_args_l, self.im_args_te))
        self.settings_lt.addLayout(self.createQHboxLayout(self.start_logging_btn, self.open_log_dir_btn, self.wipe_log_dir_btn))

        ## All
        self.settings_lt.addStretch()

    def setSizes(self):
        label_width = 90
        text_edit_height = 50

        self.play_sound_on_finish_vol_hb.setAlignment(Qt.AlignLeft)
        self.multithreading_hb.setAlignment(Qt.AlignLeft)
        self.play_sound_on_finish_vol_sb.setMinimumWidth(150)

        self.avifenc_args_l.setMinimumWidth(label_width)
        self.cjpegli_args_l.setMinimumWidth(label_width)
        self.cjxl_args_l.setMinimumWidth(label_width)
        self.im_args_l.setMinimumWidth(label_width)
        self.avifenc_args_te.setMaximumHeight(text_edit_height)
        self.cjpegli_args_te.setMaximumHeight(text_edit_height)
        self.cjxl_args_te.setMaximumHeight(text_edit_height)
        self.im_args_te.setMaximumHeight(text_edit_height)

        self.exiftool_wipe_l.setMinimumWidth(label_width)
        self.exiftool_preserve_l.setMinimumWidth(label_width)
        self.exiftool_unsafe_wipe_l.setMinimumWidth(label_width)
        self.exiftool_custom_l.setMinimumWidth(label_width)
        self.exiftool_wipe_te.setMaximumHeight(text_edit_height)
        self.exiftool_preserve_te.setMaximumHeight(text_edit_height)
        self.exiftool_unsafe_wipe_te.setMaximumHeight(text_edit_height)
        self.exiftool_custom_te.setMaximumHeight(text_edit_height)

        self.jpg_encoder_cmb.setMinimumWidth(150)
        self.multithreading_cmb.setMinimumWidth(150)

    def setupSignals(self):
        self.dark_theme_cb.toggled.connect(self.setDarkModeEnabled)
        self.custom_args_cb.toggled.connect(self.onCustomArgsToggled)
        self.play_sound_on_finish_cb.toggled.connect(self.onPlaySoundOnFinishVolumeToggled)

        self.no_sorting_cb.toggled.connect(self.signals.disable_sorting)
        self.enable_jxl_effort_10.clicked.connect(self.signals.enable_jxl_effort_10)
        self.custom_resampling_cb.toggled.connect(self.signals.custom_resampling.emit)
        self.quality_prec_snap_cb.toggled.connect(self.signals.enable_quality_prec_snap)
        self.jpg_encoder_cmb.currentTextChanged.connect(self.signals.change_jpg_encoder)

        self.exiftool_reset_btn.clicked.connect(self.resetExifTool)

        self.start_logging_btn.clicked.connect(self.toggleLogging)
        self.open_log_dir_btn.clicked.connect(self.openLogsDir)
        self.wipe_log_dir_btn.clicked.connect(self.wipeLogsDir)

        self.general_btn.clicked.connect(lambda: self.changeCategory("General"))
        self.conversion_btn.clicked.connect(lambda: self.changeCategory("Conversion"))
        self.advanced_btn.clicked.connect(lambda: self.changeCategory("Advanced"))
        self.restore_defaults_btn.clicked.connect(self.resetToDefault)

    def setToolTips(self):
        setToolTip(TOOLTIPS["disable_delete_startup"], self.disable_delete_startup_cb)
        setToolTip(TOOLTIPS["disable_downscaling_startup"], self.disable_downscaling_startup_cb)
        setToolTip(TOOLTIPS["dark_theme"], self.dark_theme_cb)
        setToolTip(TOOLTIPS["quality_prec_snap"], self.quality_prec_snap_cb)
        setToolTip(TOOLTIPS["sorting"], self.no_sorting_cb)
        setToolTip(TOOLTIPS["play_sound_on_finish"], self.play_sound_on_finish_cb)
        setToolTip(TOOLTIPS["jxl_lossless_jpeg"], self.jxl_lossless_jpeg_cb)
        setToolTip(TOOLTIPS["jpeg_encoder"], self.jpg_encoder_cmb)
        setToolTip(TOOLTIPS["progressive_jpegli"], self.disable_progressive_jpegli_cb)
        setToolTip(TOOLTIPS["copy_if_larger"], self.copy_if_larger_cb)
        setToolTip(TOOLTIPS["keep_if_larger"], self.keep_if_larger_cb)
        setToolTip(TOOLTIPS["enable_jxl_effort_10"], self.enable_jxl_effort_10)
        setToolTip(TOOLTIPS["resample"], self.custom_resampling_cb)
        setToolTip(TOOLTIPS["no_exceptions"], self.no_exceptions_cb)
        setToolTip(TOOLTIPS["exiftool_args"], self.exiftool_wipe_te, self.exiftool_custom_te, self.exiftool_preserve_te, self.exiftool_unsafe_wipe_te)
        setToolTip(TOOLTIPS["encoder_args"], self.avifenc_args_te, self.cjpegli_args_te, self.cjxl_args_te, self.im_args_te)
        setToolTip(TOOLTIPS["multithreading"], self.multithreading_cmb)

    def changeCategory(self, category):
        # Category buttons
        self.general_btn.setChecked(category == "General")
        self.conversion_btn.setChecked(category == "Conversion")
        self.advanced_btn.setChecked(category == "Advanced")

        # Settings
        visibility = {
            "General": [
                "dark_theme_cb",
                "disable_on_startup_l", "disable_downscaling_startup_cb", "disable_delete_startup_cb",
                "no_sorting_cb",
                "quality_prec_snap_cb",
                "play_sound_on_finish_cb", "play_sound_on_finish_vol_l", "play_sound_on_finish_vol_sb",
            ],
            "Conversion": [
                "jxl_lossless_jpeg_cb",
                "jpg_encoder_l", "jpg_encoder_cmb",
                "disable_progressive_jpegli_cb",
                "keep_if_larger_cb",
                "copy_if_larger_cb",
                "multithreading_l", "multithreading_cmb",
            ],
            "Advanced": [
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

        for ct in visibility:
            visible = category == ct
            for widget_str in visibility[ct]:
                try:
                    getattr(self, widget_str).setVisible(visible)
                except AttributeError as e:
                    logging.error(f"[SettingsTab - changeCategory] {e}")

    def onCustomArgsToggled(self):
        enabled = self.custom_args_cb.isChecked()

        self.cjxl_args_l.setEnabled(enabled)
        self.cjxl_args_te.setEnabled(enabled)
        self.avifenc_args_l.setEnabled(enabled)
        self.avifenc_args_te.setEnabled(enabled)
        self.cjpegli_args_l.setEnabled(enabled)
        self.cjpegli_args_te.setEnabled(enabled)
        self.im_args_l.setEnabled(enabled)
        self.im_args_te.setEnabled(enabled)

    def onPlaySoundOnFinishVolumeToggled(self):
        enabled = self.play_sound_on_finish_cb.isChecked()
        self.play_sound_on_finish_vol_l.setEnabled(enabled)
        self.play_sound_on_finish_vol_sb.setEnabled(enabled)

    def setDarkModeEnabled(self, enabled):
        setTheme("dark" if enabled else "light")

    def toggleLogging(self):
        if self.logging_manager.isLoggingToFile():
            self.logging_manager.stopLoggingToFile()
            self.start_logging_btn.setText("Start Logging")
        else:
            self.logging_manager.startLoggingToFile("DEBUG")
            self.start_logging_btn.setText("Stop Logging")

    def openLogsDir(self):
        logs_dir = self.logging_manager.getLogsDir()
        if not os.path.isdir(logs_dir):
            self.notifications.notify("No logs", "No logs have been found.")
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(logs_dir))
    
    def wipeLogsDir(self):
        logging_to_file = self.logging_manager.isLoggingToFile()
        if logging_to_file:
            self.logging_manager.stopLoggingToFile()

        self.notifications.notify("File Message", self.logging_manager.wipeLogsDir())

        if logging_to_file:
            self.logging_manager.startLoggingToFile()

    def createQHboxLayout(self, *widgets) -> QHBoxLayout:
        """Creates and returns a QHBoxLayout containing the specified widgets."""
        layout = QHBoxLayout()
        for w in widgets:
            layout.addWidget(w)
        return layout

    def getSettings(self):
        return {
            "custom_resampling": self.custom_resampling_cb.isChecked(),
            "sorting_disabled": self.no_sorting_cb.isChecked(),
            "disable_downscaling_startup": self.disable_downscaling_startup_cb.isChecked(),
            "disable_delete_startup": self.disable_delete_startup_cb.isChecked(),
            "no_exceptions": self.no_exceptions_cb.isChecked(),
            "enable_jxl_effort_10": self.enable_jxl_effort_10.isChecked(),
            "disable_progressive_jpegli": self.disable_progressive_jpegli_cb.isChecked(),
            "enable_custom_args": self.custom_args_cb.isChecked(),
            "cjxl_args": self.cjxl_args_te.toPlainText(),
            "avifenc_args": self.avifenc_args_te.toPlainText(),
            "cjpegli_args": self.cjpegli_args_te.toPlainText(),
            "im_args": self.im_args_te.toPlainText(),
            "enable_quality_precision_snapping": self.quality_prec_snap_cb.isChecked(),
            "jpg_encoder": self.jpg_encoder_cmb.currentText(),
            "jxl_lossless_jpeg": self.jxl_lossless_jpeg_cb.isChecked(),
            "play_sound_on_finish": self.play_sound_on_finish_cb.isChecked(),
            "play_sound_on_finish_vol": round(self.play_sound_on_finish_vol_sb.value() / 100, 2),
            "keep_if_larger": self.keep_if_larger_cb.isChecked(),
            "copy_if_larger": self.copy_if_larger_cb.isChecked(),
            "multithreading_mode": self.multithreading_cmb.currentText(),
            "exiftool_args": {      # Mapped to values from modify_tab.metadata_cmb
                "ExifTool - Wipe": self.exiftool_wipe_te.toPlainText(),
                "ExifTool - Preserve": self.exiftool_preserve_te.toPlainText(),
                "ExifTool - Unsafe Wipe": self.exiftool_unsafe_wipe_te.toPlainText(),
                "ExifTool - Custom": self.exiftool_custom_te.toPlainText(),
            },
        }
    
    def resetExifTool(self):
        self.exiftool_wipe_te.setText("-all= -tagsFromFile @ -icc_profile:all -ColorSpace:all -Orientation $dst -overwrite_original")
        self.exiftool_preserve_te.setText("-tagsFromFile $src $dst -overwrite_original")
        self.exiftool_unsafe_wipe_te.setText("-all= $dst -overwrite_original")
        self.exiftool_custom_te.setText("")

    def resetToDefault(self):
        self.dark_theme_cb.setChecked(True)
        self.no_sorting_cb.setChecked(False)
        self.disable_downscaling_startup_cb.setChecked(True)
        self.disable_delete_startup_cb.setChecked(True)
        self.no_exceptions_cb.setChecked(False)
        self.quality_prec_snap_cb.setChecked(False)
        self.jxl_lossless_jpeg_cb.setChecked(False)
        self.play_sound_on_finish_cb.setChecked(False)
        self.play_sound_on_finish_vol_sb.setValue(60)

        self.enable_jxl_effort_10.setChecked(False)
        self.custom_resampling_cb.setChecked(False)
        self.disable_progressive_jpegli_cb.setChecked(False)
        self.jpg_encoder_cmb.setCurrentIndex(0)
        self.keep_if_larger_cb.setChecked(False)
        self.copy_if_larger_cb.setChecked(False)
        self.multithreading_cmb.setCurrentIndex(0)

        self.resetExifTool()

        self.custom_args_cb.setChecked(False)
        self.cjxl_args_te.clear()
        self.cjpegli_args_te.clear()
        self.im_args_te.clear()
        self.avifenc_args_te.clear()