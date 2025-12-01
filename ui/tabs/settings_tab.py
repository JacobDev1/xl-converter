import os
import logging
from typing import Optional, Dict
from copy import deepcopy
from dataclasses import dataclass

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

from data.logging_manager import LoggingManager
from data.utils import compareVersions, VersionParseErrorPolicy
from ui.lib import WidgetManager
from ui.lib.utils import setToolTip, openLocalUrl, createQHBoxLayout, blockSignals
from ui.theme import setTheme
from ui.widgets import ScrollArea, SpinBox, ComboBox
from ui.dialogs import message_box
import data.process_manager as process_manager

@dataclass(frozen=True)
class StockPresets:
    exiftool_wipe: str = "-m -all= -tagsFromFile @ -icc_profile:all -ColorSpace:all -Orientation $dst -overwrite_original"
    exiftool_preserve: str = "-m -tagsFromFile $src $dst -overwrite_original"
    exiftool_unsafe_wipe: str = "-m -all= $dst -overwrite_original"

STOCK_PRESETS = StockPresets()

class Signals(QObject):
    custom_resampling_toggled = Signal(bool)
    sorting_toggled = Signal(bool)
    jxl_effort_10_toggled = Signal(bool)
    quality_prec_snap_toggled = Signal(bool)
    jpeg_encoder_changed = Signal(str)
    jxl_lossy_modular_toggled = Signal(bool)
    jxl_int_effort_toggled = Signal(bool)
    avif_encoder_changed = Signal(str)

class SettingsTab(QWidget):
    def __init__(self):
        super(SettingsTab, self).__init__()

        self.wm = WidgetManager("SettingsTab")
        self.signals = Signals()
        self.logging_manager = LoggingManager()

        # Init UI
        self.setupUI()
        self.setupWidgets()
        self.setupLayouts()
        self.setupSignals()
        self.setStyles()
        self.setToolTips()

        # Init states
        self.changeCategory("General")
        with blockSignals(  # States refreshed below.
            self.custom_args_cb,
            self.play_sound_on_finish_cb,
            self.avif_encoder_cmb,
            self.theme_cmb,
        ):
            self.resetToDefault()
            self.wm.loadState()

        # Refresh states
        self.onCustomArgsToggled()
        self.onPlaySoundOnFinishVolumeToggled()
        self.onAVIFEncoderChanged()
        self.onThemeChanged()
        self.onRamOptimizerChanged()

        # Misc.
        self.runMigrations()

        # Vars
        self.cached_states = {}

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
        self.settings_sa.setObjectName("settingsScrollArea")

        self.main_lt.addLayout(self.categories_lt, 0, 0)
        self.main_lt.addWidget(self.settings_sa, 0, 1)
        self.main_lt.setColumnStretch(0, 3)
        self.main_lt.setColumnStretch(1, 7)

    def setupWidgets(self):
        # General
        self.disable_on_startup_l = QLabel("Disable on Startup")
        self.disable_downscaling_startup_cb = self.wm.addWidget("disable_downscaling_startup_cb", QCheckBox("Downscaling"))
        self.disable_delete_startup_cb = self.wm.addWidget("disable_delete_startup_cb", QCheckBox("Delete Original"))
        self.theme_l = self.wm.addWidget("theme_l", QLabel("Theme"))
        self.theme_cmb = self.wm.addWidget("theme_cmb", ComboBox(("Ralsei", "Dark Amber", "Light Amber")))
        self.no_sorting_cb = self.wm.addWidget("no_sorting_cb", QCheckBox("Input - Disable Sorting"))
        self.quality_prec_snap_cb = self.wm.addWidget("quality_prec_snap_cb", QCheckBox("Quality Slider - Snap to Individual Values"))
        self.play_sound_on_finish_cb = self.wm.addWidget("play_sound_on_finish_cb", QCheckBox("Play Sound When Conversion Finishes"))
        self.play_sound_on_finish_vol_l = self.wm.addWidget("play_sound_on_finish_vol_l", QLabel("Volume"))
        self.play_sound_on_finish_vol_sb = self.wm.addWidget("play_sound_on_finish_vol_sb", SpinBox())
        self.play_sound_on_finish_vol_sb.setRange(0, 100)
        self.play_sound_on_finish_vol_sb.setSuffix("%")

        # Conversion
        self.jxl_lossy_modular_cb = self.wm.addWidget("jxl_lossy_modular_cb", QCheckBox("JPEG XL - Allow Lossy Modular"))
        self.jxl_auto_lossless_jpeg_cb = self.wm.addWidget("jxl_auto_lossless_jpeg_cb", QCheckBox("JPEG XL - Automatic Lossless JPEG Transcoding"))
        self.jpg_encoder_l = self.wm.addWidget("jpg_encoder_l", QLabel("JPEG Encoder"))
        self.jpg_encoder_cmb = self.wm.addWidget("jpg_encoder_cmb", ComboBox(("JPEGLI", "libjpeg")))
        self.disable_progressive_jpegli_cb = self.wm.addWidget("disable_progressive_jpegli_cb", QCheckBox("JPEGLI - Disable Progressive Scan", self))
        self.avif_bit_depth_l = self.wm.addWidget("avif_bit_depth_l", QLabel("AVIF - Bit Depth"))
        self.avif_bit_depth_cmb = self.wm.addWidget("avif_bit_depth_cmb", ComboBox(("Auto", "12", "10", "8")))
        self.avif_encoder_l = self.wm.addWidget("avif_encoder_l", QLabel("AVIF Encoder"))
        self.avif_encoder_cmb = self.wm.addWidget("avif_encoder_cmb", ComboBox(("AOM AV1", "SVT-AV1-PSY")))
        # self.avif_aom_tune_l = self.wm.addWidget("avif_aom_tune_l", QLabel("AOM AV1 Tune"))
        # self.avif_aom_tune_cmb = self.wm.addWidget("avif_aom_tune_cmb", ComboBox(("SSIM", "IQ", "PSNR")))
        self.avif_aom_iq_tune_cb = self.wm.addWidget("avif_aom_iq_tune_cb", QCheckBox("AOM AV1 - Use IQ Tune"))
        self.keep_if_larger_cb = self.wm.addWidget("keep_if_larger_cb", QCheckBox("Do Not Delete Original When Result is Larger"))
        self.copy_if_larger_cb = self.wm.addWidget("copy_if_larger_cb", QCheckBox("Copy Original When Result is Larger"))

        # ExifTool
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

        # Advanced
        self.ram_optimizer_l = self.wm.addWidget("ram_optimizer_l", QLabel("RAM Optimizer"))
        self.ram_optimizer_cmb = self.wm.addWidget("ram_optimizer_cmb", ComboBox(("Dynamic", "Static", "Disabled")))
        self.ram_optimizer_rules_l = self.wm.addWidget("ram_optimizer_rules_l", QLabel("Optimization Rules"))
        self.ram_optimizer_rules_te = self.wm.addWidget("ram_optimizer_rules_te", QTextEdit())
        self.ram_optimizer_rules_reset_btn = self.wm.addWidget("ram_optimizer_rules_reset_btn", QPushButton("Reset"))
        self.jxl_effort_10_cb = self.wm.addWidget("jxl_effort_10_cb", QCheckBox("JPEG XL - Enable Effort 10", self))
        self.jxl_int_effort_cb = self.wm.addWidget("jxl_int_effort_cb", QCheckBox("JPEG XL - Allow Intelligent Effort (Deprecated)"))
        self.custom_resampling_cb = self.wm.addWidget("custom_resampling_cb", QCheckBox("Downscaling - Custom Resampling", self))
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
        self.processing_order_l = self.wm.addWidget("processing_order_l", QLabel("Processing Order"))
        self.processing_order_cmb = self.wm.addWidget("processing_order_cmb", ComboBox(("Random", "Sequential")))
        self.start_logging_btn = self.wm.addWidget("start_logging_btn", QPushButton("Start Logging"))
        self.open_log_dir_btn = self.wm.addWidget("open_log_dir_btn", QPushButton("Open Logs Folder"))
        self.wipe_log_dir_btn = self.wm.addWidget("wipe_log_dir_btn", QPushButton("Wipe Logs Folder"))
        self.start_logging_btn.setCheckable(True)
        self.process_priority_l = self.wm.addWidget("process_priority_l", QLabel("Process Priority"))
        self.process_priority_cmb = self.wm.addWidget("process_priority_cmb", ComboBox(("Normal", "Below Normal", "Idle")))

        # Categories
        self.general_btn = QPushButton("General")
        self.conversion_btn = QPushButton("Conversion")
        self.exiftool_btn = QPushButton("ExifTool")
        self.advanced_btn = QPushButton("Advanced")
        self.restore_defaults_btn = QPushButton("Reset to Defaults")
        
        self.general_btn.setCheckable(True)
        self.conversion_btn.setCheckable(True)
        self.exiftool_btn.setCheckable(True)
        self.advanced_btn.setCheckable(True)

    def setupLayouts(self):
        # Categories
        self.categories_lt.addWidget(self.general_btn)
        self.categories_lt.addWidget(self.conversion_btn)
        self.categories_lt.addWidget(self.exiftool_btn)
        self.categories_lt.addWidget(self.advanced_btn)
        self.categories_lt.addItem(QSpacerItem(10, 10, QSizePolicy.Minimum, QSizePolicy.Expanding))
        self.categories_lt.addWidget(self.restore_defaults_btn)

        # General
        self.settings_lt.addLayout(createQHBoxLayout(self.disable_on_startup_l, self.disable_delete_startup_cb, self.disable_downscaling_startup_cb))
        self.settings_lt.addWidget(self.quality_prec_snap_cb)
        self.theme_hb = createQHBoxLayout(self.theme_l, self.theme_cmb)
        self.settings_lt.addLayout(self.theme_hb)
        self.settings_lt.addWidget(self.no_sorting_cb)
        self.settings_lt.addWidget(self.play_sound_on_finish_cb)
        self.play_sound_on_finish_vol_hb = createQHBoxLayout(self.play_sound_on_finish_vol_l, self.play_sound_on_finish_vol_sb)
        self.settings_lt.addLayout(self.play_sound_on_finish_vol_hb)

        # Conversion
        self.settings_lt.addWidget(self.jxl_lossy_modular_cb)
        self.settings_lt.addWidget(self.jxl_auto_lossless_jpeg_cb)
        self.jpg_encoder_hb = createQHBoxLayout(self.jpg_encoder_l, self.jpg_encoder_cmb)
        self.settings_lt.addLayout(self.jpg_encoder_hb)
        self.settings_lt.addWidget(self.disable_progressive_jpegli_cb)
        self.avif_bit_depth_hb = createQHBoxLayout(self.avif_bit_depth_l, self.avif_bit_depth_cmb)
        self.settings_lt.addLayout(self.avif_bit_depth_hb)
        self.avif_encoder_hb = createQHBoxLayout(self.avif_encoder_l, self.avif_encoder_cmb)
        self.settings_lt.addLayout(self.avif_encoder_hb)
        # self.avif_aom_tune_hb = createQHBoxLayout(self.avif_aom_tune_l, self.avif_aom_tune_cmb)
        # self.settings_lt.addLayout(self.avif_aom_tune_hb)
        self.settings_lt.addWidget(self.avif_aom_iq_tune_cb)
        self.settings_lt.addWidget(self.keep_if_larger_cb)
        self.settings_lt.addWidget(self.copy_if_larger_cb)

        # ExifTool
        self.settings_lt.addLayout(createQHBoxLayout(self.exiftool_wipe_l, self.exiftool_wipe_te))
        self.settings_lt.addLayout(createQHBoxLayout(self.exiftool_preserve_l, self.exiftool_preserve_te))
        self.settings_lt.addLayout(createQHBoxLayout(self.exiftool_unsafe_wipe_l, self.exiftool_unsafe_wipe_te))
        self.settings_lt.addLayout(createQHBoxLayout(self.exiftool_custom_l, self.exiftool_custom_te))
        self.settings_lt.addWidget(self.exiftool_reset_btn)

        # Advanced
        self.ram_optimizer_hb = createQHBoxLayout(self.ram_optimizer_l, self.ram_optimizer_cmb)
        self.settings_lt.addLayout(self.ram_optimizer_hb)
        self.settings_lt.addWidget(self.ram_optimizer_rules_l)
        self.settings_lt.addWidget(self.ram_optimizer_rules_te)
        self.settings_lt.addWidget(self.ram_optimizer_rules_reset_btn)
        self.settings_lt.addWidget(self.jxl_effort_10_cb)
        self.settings_lt.addWidget(self.jxl_int_effort_cb)
        self.settings_lt.addWidget(self.custom_resampling_cb)
        self.settings_lt.addWidget(self.custom_args_cb)
        self.settings_lt.addLayout(createQHBoxLayout(self.cjxl_args_l, self.cjxl_args_te))
        self.settings_lt.addLayout(createQHBoxLayout(self.avifenc_args_l, self.avifenc_args_te))
        self.settings_lt.addLayout(createQHBoxLayout(self.cjpegli_args_l, self.cjpegli_args_te))
        self.settings_lt.addLayout(createQHBoxLayout(self.im_args_l, self.im_args_te))
        self.processing_order_hb = createQHBoxLayout(self.processing_order_l, self.processing_order_cmb)
        self.settings_lt.addLayout(self.processing_order_hb)
        self.process_priority_hb = createQHBoxLayout(self.process_priority_l, self.process_priority_cmb)
        self.settings_lt.addLayout(self.process_priority_hb)
        self.settings_lt.addLayout(createQHBoxLayout(self.start_logging_btn, self.open_log_dir_btn, self.wipe_log_dir_btn))

        # All
        self.settings_lt.addStretch()

    def setStyles(self):
        self.play_sound_on_finish_vol_sb.setProperty("class", "min_width_sb")

        for hbox in (
            self.jpg_encoder_hb,
            self.avif_encoder_hb,
            self.avif_bit_depth_hb,
            self.play_sound_on_finish_vol_hb,
            self.theme_hb,
            self.ram_optimizer_hb,
            self.processing_order_hb,
            self.process_priority_hb,
            # self.avif_aom_tune_hb,
        ):
            hbox.setAlignment(Qt.AlignLeft)

        self.exiftool_wipe_l.setProperty("class", "min_width_l")
        self.exiftool_preserve_l.setProperty("class", "min_width_l")
        self.exiftool_unsafe_wipe_l.setProperty("class", "min_width_l")
        self.exiftool_custom_l.setProperty("class", "min_width_l")

        self.avifenc_args_l.setProperty("class", "min_width_l")
        self.cjpegli_args_l.setProperty("class", "min_width_l")
        self.cjxl_args_l.setProperty("class", "min_width_l")
        self.im_args_l.setProperty("class", "min_width_l")
        
        self.jpg_encoder_cmb.setProperty("class", "min_width_cmb")
        self.avif_encoder_cmb.setProperty("class", "min_width_cmb")
        self.avif_bit_depth_cmb.setProperty("class", "min_width_cmb")
        self.theme_cmb.setProperty("class", "min_width_cmb")
        self.ram_optimizer_cmb.setProperty("class", "min_width_cmb")
        self.processing_order_cmb.setProperty("class", "min_width_cmb")
        self.process_priority_cmb.setProperty("class", "min_width_cmb")
        # self.avif_aom_tune_cmb.setProperty("class", "min_width_cmb")

    def setupSignals(self):
        self.custom_args_cb.toggled.connect(self.onCustomArgsToggled)
        self.play_sound_on_finish_cb.toggled.connect(self.onPlaySoundOnFinishVolumeToggled)
        self.no_sorting_cb.toggled.connect(self.signals.sorting_toggled)
        self.jxl_effort_10_cb.toggled.connect(self.signals.jxl_effort_10_toggled)
        self.custom_resampling_cb.toggled.connect(self.signals.custom_resampling_toggled.emit)
        self.quality_prec_snap_cb.toggled.connect(self.signals.quality_prec_snap_toggled)
        self.jpg_encoder_cmb.currentTextChanged.connect(self.signals.jpeg_encoder_changed)
        self.exiftool_reset_btn.clicked.connect(lambda checked=False: self.resetExifTool(reset_custom=False))
        self.start_logging_btn.clicked.connect(self.toggleLogging)
        self.open_log_dir_btn.clicked.connect(self.openLogsDir)
        self.wipe_log_dir_btn.clicked.connect(self.wipeLogsDir)
        self.jxl_lossy_modular_cb.toggled.connect(self.signals.jxl_lossy_modular_toggled)
        self.jxl_int_effort_cb.toggled.connect(self.signals.jxl_int_effort_toggled)
        self.avif_encoder_cmb.currentTextChanged.connect(self.signals.avif_encoder_changed)
        self.avif_encoder_cmb.currentTextChanged.connect(self.onAVIFEncoderChanged)
        self.avif_bit_depth_cmb.currentTextChanged.connect(self.onAVIFBitDepthChanged)
        self.theme_cmb.currentTextChanged.connect(self.onThemeChanged)
        self.ram_optimizer_rules_reset_btn.clicked.connect(self.resetOptimizationRules)
        self.ram_optimizer_cmb.currentTextChanged.connect(self.onRamOptimizerChanged)
        self.process_priority_cmb.currentTextChanged.connect(self.onProcessPriorityChanged)

        self.general_btn.clicked.connect(lambda: self.changeCategory("General"))
        self.exiftool_btn.clicked.connect(lambda: self.changeCategory("ExifTool"))
        self.conversion_btn.clicked.connect(lambda: self.changeCategory("Conversion"))
        self.advanced_btn.clicked.connect(lambda: self.changeCategory("Advanced"))
        self.restore_defaults_btn.clicked.connect(self.resetToDefault)

    def setToolTips(self):
        setToolTip("disable_delete_startup", self.disable_delete_startup_cb)
        setToolTip("disable_downscaling_startup", self.disable_downscaling_startup_cb)
        setToolTip("quality_prec_snap", self.quality_prec_snap_cb)
        setToolTip("sorting", self.no_sorting_cb)
        setToolTip("play_sound_on_finish", self.play_sound_on_finish_cb)
        setToolTip("jxl_auto_lossless_jpeg", self.jxl_auto_lossless_jpeg_cb)
        setToolTip("jpeg_encoder", self.jpg_encoder_cmb)
        setToolTip("progressive_jpegli", self.disable_progressive_jpegli_cb)
        setToolTip("copy_if_larger", self.copy_if_larger_cb)
        setToolTip("keep_if_larger", self.keep_if_larger_cb)
        setToolTip("jxl_effort_10", self.jxl_effort_10_cb)
        setToolTip("resample", self.custom_resampling_cb)
        setToolTip("exiftool_args", self.exiftool_wipe_te, self.exiftool_custom_te, self.exiftool_preserve_te, self.exiftool_unsafe_wipe_te)
        setToolTip("encoder_args", self.avifenc_args_te, self.cjpegli_args_te, self.cjxl_args_te, self.im_args_te)
        setToolTip("jxl_int_effort", self.jxl_int_effort_cb)
        setToolTip("jxl_lossy_modular", self.jxl_lossy_modular_cb)
        setToolTip("avif_encoder", self.avif_encoder_cmb)
        setToolTip("avif_bit_depth", self.avif_bit_depth_cmb)
        setToolTip("avif_aom_iq_tune", self.avif_aom_iq_tune_cb)
        setToolTip("ram_optimizer", self.ram_optimizer_cmb)
        setToolTip("ram_optimizer_rules", self.ram_optimizer_rules_te)
        setToolTip("processing_order", self.processing_order_cmb)
        setToolTip("process_priority", self.process_priority_cmb)

    def changeCategory(self, category):
        # Category buttons
        self.general_btn.setChecked(category == "General")
        self.conversion_btn.setChecked(category == "Conversion")
        self.exiftool_btn.setChecked(category == "ExifTool")
        self.advanced_btn.setChecked(category == "Advanced")

        # Settings
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
                # "avif_aom_tune_l", "avif_aom_tune_cmb",
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

        for v_category in visibility:
            visible = category == v_category
            for widget_str in visibility[v_category]:
                try:
                    getattr(self, widget_str).setVisible(visible)
                except AttributeError as e:
                    logging.error(f"[SettingsTab - changeCategory] {e}")
        
        self.settings_sa.verticalScrollBar().setValue(0)    # Move to top

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

    def onAVIFBitDepthChanged(self) -> None:
        match self.avif_encoder_cmb.currentText():
            case "AOM AV1":
                self.wm.setVar("aom_av1_bit_depth", self.avif_bit_depth_cmb.currentText())
            case "SVT-AV1-PSY":
                self.wm.setVar("svt_av1_psy_bit_depth", self.avif_bit_depth_cmb.currentText())

    def onAVIFEncoderChanged(self) -> None:
        """Adjusts encoder settings based on which one is selected."""
        avif_enc = self.avif_encoder_cmb.currentText()
        with blockSignals(self.avif_bit_depth_cmb):
            self.avif_bit_depth_cmb.clear()
            match avif_enc:
                case "AOM AV1":
                    self.avif_bit_depth_cmb.addItems(("Auto", "12", "10", "8"))
                    loaded_var = self.wm.getVar("aom_av1_bit_depth")
                case "SVT-AV1-PSY":
                    self.avif_bit_depth_cmb.addItems(("Auto", "10", "8"))
                    loaded_var = self.wm.getVar("svt_av1_psy_bit_depth")
                case _:
                    logging.error(f"[onAVIFEncoderChanged] Unknown encoder ({avif_enc})")
                    return
            self.avif_bit_depth_cmb.setCurrentText(loaded_var or "Auto")
            self.avif_aom_iq_tune_cb.setEnabled(avif_enc == "AOM AV1")

    def onThemeChanged(self) -> None:
        setTheme(self.theme_cmb.currentText())

    def onRamOptimizerChanged(self) -> None:
        dynamic_ram_optimizer = self.ram_optimizer_cmb.currentText() == "Dynamic"
        self.ram_optimizer_rules_te.setEnabled(dynamic_ram_optimizer)
        self.ram_optimizer_rules_l.setEnabled(dynamic_ram_optimizer)
        self.ram_optimizer_rules_reset_btn.setEnabled(dynamic_ram_optimizer)

    def onProcessPriorityChanged(self) -> None:
        priority = self.process_priority_cmb.currentText()
        match priority:
            case "Normal":
                process_manager.ProcessPriorityManager.setPriority(
                    process_manager.ProcessPriority.NORMAL
                )
            case "Below Normal":
                process_manager.ProcessPriorityManager.setPriority(
                    process_manager.ProcessPriority.BELOW_NORMAL
                )
            case "Idle":
                process_manager.ProcessPriorityManager.setPriority(
                    process_manager.ProcessPriority.IDLE
                )
            case _:
                logging.error(f"[onProcessPriorityChanged] Unmapped priority ({priority})")

    def enableLogging(self) -> None:
        if not self.logging_manager.isLoggingToFile():
            self.logging_manager.startLoggingToFile("INFO")
        self.start_logging_btn.setText("Stop Logging")
        self.start_logging_btn.setChecked(True)

    def disableLogging(self) -> None:
        if self.logging_manager.isLoggingToFile():
            self.logging_manager.stopLoggingToFile()
        self.start_logging_btn.setText("Start Logging")
        self.start_logging_btn.setChecked(False)

    def toggleLogging(self):
        if self.logging_manager.isLoggingToFile():
            self.disableLogging()
        else:
            self.enableLogging()

    def openLogsDir(self):
        logs_dir = self.logging_manager.getLogsDir()
        if not os.path.isdir(logs_dir):
            message_box.info(self, "No logs", "No logs have been found.")
            return
        openLocalUrl(logs_dir)
    
    def wipeLogsDir(self):
        self.disableLogging()
        message_box.info(self, "File Message", self.logging_manager.wipeLogsDir())

    def getSettings(self):
        return {
            "custom_resampling": self.custom_resampling_cb.isChecked(),
            "sorting_disabled": self.no_sorting_cb.isChecked(),
            "disable_downscaling_startup": self.disable_downscaling_startup_cb.isChecked(),
            "disable_delete_startup": self.disable_delete_startup_cb.isChecked(),
            "enable_jxl_effort_10": self.jxl_effort_10_cb.isChecked(),
            "disable_progressive_jpegli": self.disable_progressive_jpegli_cb.isChecked(),
            "enable_custom_args": self.custom_args_cb.isChecked(),
            "cjxl_args": self.cjxl_args_te.toPlainText(),
            "avifenc_args": self.avifenc_args_te.toPlainText(),
            "cjpegli_args": self.cjpegli_args_te.toPlainText(),
            "im_args": self.im_args_te.toPlainText(),
            "enable_quality_precision_snapping": self.quality_prec_snap_cb.isChecked(),
            "jpg_encoder": self.jpg_encoder_cmb.currentText(),
            "jxl_auto_lossless_jpeg": self.jxl_auto_lossless_jpeg_cb.isChecked(),
            "ram_optimizer": self.ram_optimizer_cmb.currentText(),
            "ram_optimizer_rules": self.ram_optimizer_rules_te.toPlainText(),
            "jxl_lossy_modular": self.jxl_lossy_modular_cb.isChecked(),
            "jxl_int_effort": self.jxl_int_effort_cb.isChecked(),
            "play_sound_on_finish": self.play_sound_on_finish_cb.isChecked(),
            "play_sound_on_finish_vol": round(self.play_sound_on_finish_vol_sb.value() / 100, 2),
            "keep_if_larger": self.keep_if_larger_cb.isChecked(),
            "copy_if_larger": self.copy_if_larger_cb.isChecked(),
            "exiftool_args": {      # Mapped to values from modify_tab.metadata_cmb
                "ExifTool - Wipe": self.exiftool_wipe_te.toPlainText(),
                "ExifTool - Preserve": self.exiftool_preserve_te.toPlainText(),
                "ExifTool - Unsafe Wipe": self.exiftool_unsafe_wipe_te.toPlainText(),
                "ExifTool - Custom": self.exiftool_custom_te.toPlainText(),
            },
            "avif_encoder": self.avif_encoder_cmb.currentText(),
            "avif_bit_depth": self.avif_bit_depth_cmb.currentText(),
            "avif_aom_iq_tune": self.avif_aom_iq_tune_cb.isChecked(),
            "processing_order": self.processing_order_cmb.currentText(),
        }
    
    def resetExifTool(self, reset_custom=False):
        self.exiftool_wipe_te.setText(STOCK_PRESETS.exiftool_wipe)
        self.exiftool_preserve_te.setText(STOCK_PRESETS.exiftool_preserve)
        self.exiftool_unsafe_wipe_te.setText(STOCK_PRESETS.exiftool_unsafe_wipe)

        if reset_custom:
            self.exiftool_custom_te.setText("")

    def resetOptimizationRules(self):
        self.ram_optimizer_rules_te.setText("""("all", 3.5, "7/8"), ("all", 4.5, "6/8"), ("all", 5.5, "5/8"), ("all", 6.5, "4/8"), ("all", 7.5, "3/8"), ("all", 8.5, "2/8"), ("all", 9.5, "1/8"), ("all", 10.5, "1")""")

    def resetToDefault(self):
        self.no_sorting_cb.setChecked(False)
        self.disable_downscaling_startup_cb.setChecked(True)
        self.disable_delete_startup_cb.setChecked(True)
        self.theme_cmb.setCurrentIndex(0)
        self.quality_prec_snap_cb.setChecked(False)
        self.jxl_auto_lossless_jpeg_cb.setChecked(False)
        self.play_sound_on_finish_cb.setChecked(False)
        self.play_sound_on_finish_vol_sb.setValue(60)

        self.jxl_lossy_modular_cb.setChecked(False)
        self.jxl_effort_10_cb.setChecked(False)
        self.custom_resampling_cb.setChecked(False)
        self.disable_progressive_jpegli_cb.setChecked(False)
        self.jpg_encoder_cmb.setCurrentIndex(0)
        self.avif_encoder_cmb.setCurrentIndex(0)
        self.avif_bit_depth_cmb.setCurrentIndex(0)
        self.avif_aom_iq_tune_cb.setChecked(False)
        self.keep_if_larger_cb.setChecked(False)
        self.copy_if_larger_cb.setChecked(False)

        self.ram_optimizer_cmb.setCurrentIndex(0)
        self.resetOptimizationRules()
        self.jxl_int_effort_cb.setChecked(False)
        self.resetExifTool()
        self.processing_order_cmb.setCurrentIndex(0)
        self.custom_args_cb.setChecked(False)
        self.cjxl_args_te.clear()
        self.cjpegli_args_te.clear()
        self.im_args_te.clear()
        self.avifenc_args_te.clear()
        self.process_priority_cmb.setCurrentIndex(0)
    
    def saveState(self, new_states: Optional[Dict] = None) -> None:
        if new_states is None or new_states != self.cached_states:
            self.wm.disableAutoSaving(
                "avif_bit_depth_cmb",
            )
            self.wm.saveState()
            self.cached_states = deepcopy(new_states)

    def runMigrations(self) -> None:
        """Migrate old settings."""
        # Skip if no file is loaded (e.g. during the first launch).
        if self.wm.getLoadedVersion() is None:
            return

        # Skip if v1.2.3 or newer.
        if compareVersions("v1.2.3", self.wm.getLoadedVersion(), VersionParseErrorPolicy.ASSUME_OLDER) >= 0:
            return

        # Skip if current preset is detected (e.g. in case user changes versions).
        if (
            self.exiftool_wipe_te.toPlainText() == STOCK_PRESETS.exiftool_wipe and
            self.exiftool_preserve_te.toPlainText() == STOCK_PRESETS.exiftool_preserve and
            self.exiftool_unsafe_wipe_te.toPlainText() == STOCK_PRESETS.exiftool_unsafe_wipe
        ):
            return

        automatic_migration = False
        legacy_presets = [
            {
                "version": "v1.2.2",
                "wipe": "-all= -tagsFromFile @ -icc_profile:all -ColorSpace:all -Orientation $dst -overwrite_original",
                "preserve": "-tagsFromFile $src $dst -overwrite_original",
                "unsafe_wipe": "-all= $dst -overwrite_original",
            },
        ]

        if any(
            self.exiftool_wipe_te.toPlainText() == legacy_preset["wipe"] and
            self.exiftool_preserve_te.toPlainText() == legacy_preset["preserve"] and
            self.exiftool_unsafe_wipe_te.toPlainText() == legacy_preset["unsafe_wipe"]
            for legacy_preset in legacy_presets
        ):
            automatic_migration = True

        # Perform migration
        if automatic_migration == True:
            self.resetExifTool(reset_custom=False)
        elif message_box.confirm(self, "Settings Migration", "Recommended ExifTool presets changed. Apply them?"):
            self.resetExifTool(reset_custom=False)
        else:
            message_box.info(self, "Settings Migration", "This change is highly recommended. To apply changes later, press \"Reset\" in Settings -> ExifTool.")


