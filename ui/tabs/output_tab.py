from typing import Optional, Dict
from copy import deepcopy
import os

from PySide6.QtWidgets import(
    QWidget,
    QGridLayout,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QLabel,
    QCheckBox,
    QLineEdit,
    QRadioButton,
    QPushButton,
    QFileDialog,
    QSizePolicy,
)
from PySide6.QtCore import(
    Qt,
    Signal,
    QDir,
)

from core.utils import dictToList
from ui.lib import WidgetManager
from ui.lib.utils import setToolTip, isPathValidStr, createQHBoxLayout, blockSignals
from ui.widgets import Slider, ComboBox, SpinBox
from ui.dialogs import message_box

class OutputTab(QWidget):
    convert = Signal()
    file_format_changed = Signal(str)
    
    def __init__(self, settings):
        super(OutputTab, self).__init__()

        # Components
        self.wm = WidgetManager("OutputTab")

        # Variables
        self.prev_format = None
        self.MAX_THREAD_COUNT = os.cpu_count() or 1
        self.jpg_encoder = settings["jpg_encoder"]
        self.enable_jxl_effort_10 = settings["enable_jxl_effort_10"]
        self.jxl_lossy_modular_visible = settings["jxl_lossy_modular"]
        self.jxl_int_effort_visible = settings["jxl_int_effort"]
        self.avif_encoder = settings["avif_encoder"]

        # Setup
        self._setupWidgets()
        self._setupLayouts()
        self._setupSignals()
        self._setToolTipsStatic()

        # Load states
        with blockSignals(self.format_cmb):
            self.resetToDefault()
            self.wm.loadState()
        
        # Update states
        if settings["disable_delete_startup"]:
            self.delete_original_cb.setChecked(False)
        self.onQualityPrecisionSnappingEnabled(settings["enable_quality_precision_snapping"])

        self._onFormatChange()
        self._onJXLNormalizeToggled()
        self._onSmLBitDepthChanged()

        # Variables
        self.cached_states = self.getSettings()
    
    def _setupWidgets(self):
        # Conversion
        self.threads_sl = self.wm.addWidget("threads_sl", Slider())
        self.threads_sb = self.wm.addWidget("threads_sb", SpinBox())
        self.threads_sl.setRange(1, self.MAX_THREAD_COUNT)
        self.threads_sb.setRange(1, self.MAX_THREAD_COUNT)
        self.threads_sl.setTickInterval(1)
        self.duplicates_cmb = self.wm.addWidget("duplicates_cmb", ComboBox(("Rename", "Replace", "Skip")))

        # After Conversion
        self.clear_after_conv_cb = self.wm.addWidget("clear_after_conv_cb", QCheckBox("Clear File List"))
        self.delete_original_cb = self.wm.addWidget("delete_original_cb", QCheckBox("Delete Original"))
        self.delete_original_cmb = self.wm.addWidget("delete_original_cmb", ComboBox(("To Trash", "Permanently")))

        # Output
        self.choose_output_src_rb = self.wm.addWidget("choose_output_src_rb", QRadioButton("Source Folder"))
        self.choose_output_ct_rb = self.wm.addWidget("choose_output_ct_rb", QRadioButton("Custom"))
        self.choose_output_ct_le = self.wm.addWidget("choose_output_ct_le", QLineEdit(), "output_ct")
        self.choose_output_ct_btn = self.wm.addWidget("choose_output_ct_btn", QPushButton("..."), "output_ct")
        self.keep_dir_struct_cb = self.wm.addWidget("keep_dir_struct_cb", QCheckBox("Keep Folder Structure"))
        self.choose_output_ct_btn.setMaximumWidth(25)

        # Format
        self.format_cmb = self.wm.addWidget("format_cmb", ComboBox((
            "JPEG XL",
            "AVIF",
            "WebP",
            "JPEG",
            "PNG",
            "Lossless JPEG Transcoding",
            "JPEG Reconstruction",
            "Smallest Lossless",
            "PNG Optimization",
        )))
        self.effort_l = self.wm.addWidget("effort_l", QLabel("Effort"), "effort")
        self.effort_sb = self.wm.addWidget("effort_sb", SpinBox(), "effort")
        self.int_effort_cb = self.wm.addWidget("int_effort_cb", QCheckBox("Intelligent"))
        self.quality_l = self.wm.addWidget("quality_l", QLabel("Quality"), "quality_all")
        self.quality_sb = self.wm.addWidget("quality_sb", SpinBox(), "quality", "quality_all")
        self.quality_sl = self.wm.addWidget("quality_sl", Slider(), "quality", "quality_all")
        self.lossless_cb = self.wm.addWidget("lossless_cb", QCheckBox("Lossless"), "lossless")
        self.jxl_modular_cb = self.wm.addWidget("jxl_modular_cb", QCheckBox("Lossy Modular"), "jxl_losssy_modular")
        self.smallest_lossless_png_cb = self.wm.addWidget("smallest_lossless_png_cb", QCheckBox("PNG (Oxipng)"), "format_pool", "smallest_lossless")
        self.smallest_lossless_webp_cb = self.wm.addWidget("smallest_lossless_webp_cb", QCheckBox("WebP"), "format_pool", "smallest_lossless")
        self.smallest_lossless_jxl_cb = self.wm.addWidget("smallest_lossless_jxl_cb", QCheckBox("JPEG XL"), "format_pool", "smallest_lossless")
        self.max_compression_cb = self.wm.addWidget("max_compression_cb", QCheckBox("Max Compression"), "smallest_lossless")
        self.smallest_lossless_bit_depth_l = self.wm.addWidget("smallest_lossless_bit_depth_l", QLabel("Max Bit Depth:"), "smallest_lossless")
        self.chroma_subsampling_l = self.wm.addWidget("chroma_subsampling_l", QLabel("Chroma Subsampling", ), "chroma_subsampling")
        self.chroma_subsampling_jpegli_cmb = self.wm.addWidget("chroma_subsampling_jpegli_cmb", ComboBox(("Default", "4:4:4", "4:2:2", "4:2:0",)), "chroma_subsampling")
        self.chroma_subsampling_aom_av1_cmb = self.wm.addWidget("chroma_subsampling_aom_av1_cmb", ComboBox(("Default", "4:4:4", "4:2:2", "4:2:0", "4:0:0",)), "chroma_subsampling")
        self.chroma_subsampling_svt_av1_psy_cmb = self.wm.addWidget("chroma_subsampling_svt_av1_psy_cmb", ComboBox(("4:2:0",)))
        self.chroma_subsampling_jpg_cmb = self.wm.addWidget("chroma_subsampling_jpg_cmb", ComboBox(("Default", "4:4:4", "4:2:2", "4:2:0",)), "chroma_subsampling")
        self.jxl_png_fallback_cb = self.wm.addWidget("jxl_png_fallback_cb", QCheckBox("PNG Fallback"))
        self.jxl_verify_cb = self.wm.addWidget("jxl_verify_cb", QCheckBox("Verify"))
        self.jxl_normalize_enable_cb = self.wm.addWidget("jxl_normalize_enable_cb", QCheckBox("Normalize"))
        self.jxl_normalize_when_cmb = self.wm.addWidget("jxl_normalize_when_cmb", ComboBox(("On Fail", "Always")))  # There is a quirk / bug in Qt which causes the popup opened by this specific widget in this particular layout combination on Windows to shrink. Overriding `showPopup` fixed it in Qt 6.6 but Qt 6.8 broke it.
        self.oxipng_inplace_cb = self.wm.addWidget("oxipng_inplace_cb", QCheckBox("In-place"))

        # Buttons
        self.reset_to_default_btn = QPushButton("Reset to Defaults")
        self.convert_btn = QPushButton("Convert")
    
    def _setupLayouts(self):
        # Conversion
        self.conv_grp = QGroupBox("Conversion")
        self.conv_grp_lt = QVBoxLayout(self.conv_grp)
        self.duplicates_l = QLabel("If Output Exists")
        self.conv_grp_lt.addLayout(createQHBoxLayout(self.duplicates_l, self.duplicates_cmb))
        self.conv_grp_lt.addLayout(createQHBoxLayout(QLabel("Threads"), self.threads_sl, self.threads_sb))

        # After conversion
        self.after_conv_grp = QGroupBox("After Conversion")
        after_conv_grp_lt = QVBoxLayout(self.after_conv_grp)
        after_conv_grp_lt.addWidget(self.clear_after_conv_cb)
        after_conv_grp_lt.addLayout(createQHBoxLayout(self.delete_original_cb, self.delete_original_cmb))

        # Output
        self.output_grp = QGroupBox("Save To")
        self.output_grp_lt = QVBoxLayout(self.output_grp)
        self.output_grp_lt.addWidget(self.choose_output_src_rb)
        self.output_grp_lt.addLayout(createQHBoxLayout(self.choose_output_ct_rb, self.choose_output_ct_le, self.choose_output_ct_btn))
        self.output_grp_lt.addWidget(self.keep_dir_struct_cb)

        # Format
        self.format_grp = QGroupBox("Format")
        self.format_grp_lt = QVBoxLayout(self.format_grp)
        self.format_grp_lt.addLayout(createQHBoxLayout(QLabel("Format / Mode"), self.format_cmb))
        self.format_grp_lt.addLayout(createQHBoxLayout(self.effort_l, self.int_effort_cb, self.effort_sb))
        self.format_grp_lt.addLayout(createQHBoxLayout(self.quality_l, self.quality_sl, self.quality_sb))
        self.format_grp_lt.addLayout(createQHBoxLayout(self.lossless_cb, self.jxl_modular_cb))
        self.format_grp_lt.addLayout(createQHBoxLayout(self.smallest_lossless_png_cb, self.smallest_lossless_webp_cb, self.smallest_lossless_jxl_cb))
        self.format_grp_lt.addWidget(self.max_compression_cb)
        self.format_grp_lt.addWidget(self.smallest_lossless_bit_depth_l)
        self.format_grp_lt.addLayout(createQHBoxLayout(self.chroma_subsampling_l, self.chroma_subsampling_jpegli_cmb, self.chroma_subsampling_aom_av1_cmb, self.chroma_subsampling_jpg_cmb, self.chroma_subsampling_svt_av1_psy_cmb))
        self.format_grp_lt.addWidget(self.jxl_png_fallback_cb)
        self.format_grp_lt.addLayout(createQHBoxLayout(self.jxl_normalize_enable_cb, self.jxl_normalize_when_cmb))
        self.format_grp_lt.addWidget(self.jxl_verify_cb)
        self.format_grp_lt.addWidget(self.oxipng_inplace_cb)

        self.smallest_lossless_bit_depth_l.setMaximumHeight(13)

        # Main
        self.main_lt = QGridLayout(self)
        self.main_lt.addWidget(self.reset_to_default_btn, 2, 0)
        self.main_lt.addWidget(self.convert_btn, 2, 1)
        self.main_lt.addWidget(self.format_grp, 0, 1)
        self.main_lt.addWidget(self.output_grp, 0, 0)
        self.main_lt.addWidget(self.conv_grp, 1, 0)
        self.main_lt.addWidget(self.after_conv_grp, 1, 1)
        
        # Size policies
        self.main_lt.setAlignment(Qt.AlignTop)
        self.main_lt.setRowMinimumHeight(0, 150)
        self.format_grp.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.conv_grp.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.after_conv_grp.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.output_grp.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.format_cmb.setMinimumWidth(220)
        self.threads_sb.setFixedWidth(55)
        self.quality_sb.setFixedWidth(55)

    def _setupSignals(self):
        self.threads_sl.valueChanged.connect(lambda n: self.threads_sb.setValue(n))
        self.threads_sb.valueChanged.connect(lambda n: self.threads_sl.setValue(n))
        self.delete_original_cb.stateChanged.connect(self._updateOutputStates)
        self.choose_output_ct_btn.clicked.connect(self._chooseOutput)
        self.choose_output_ct_rb.toggled.connect(self._updateOutputStates)
        self.format_cmb.currentIndexChanged.connect(self._onFormatChange)
        self.format_cmb.currentTextChanged.connect(self.file_format_changed)
        self.int_effort_cb.toggled.connect(self._onEffortToggled)
        self.quality_sl.valueChanged.connect(lambda n: self.quality_sb.setValue(n))
        self.quality_sb.valueChanged.connect(lambda n: self.quality_sl.setValue(n))
        self.lossless_cb.toggled.connect(self._onLosslessToggled)
        self.reset_to_default_btn.clicked.connect(self.resetToDefault)
        self.convert_btn.clicked.connect(self.convert.emit)
        self.jxl_normalize_enable_cb.toggled.connect(self._onJXLNormalizeToggled)
        self.jxl_normalize_enable_cb.clicked.connect(self._onJXLNormalizeClicked)
        self.smallest_lossless_webp_cb.toggled.connect(self._onSmLBitDepthChanged)
        self.oxipng_inplace_cb.toggled.connect(self._updateOutputStates)

    def _setToolTipsStatic(self):
        """Sets tooltips at once at startup."""
        setToolTip("duplicates", self.duplicates_cmb)
        setToolTip("threads", self.threads_sl, self.threads_sb)
        setToolTip("output_src", self.choose_output_src_rb)
        setToolTip("output_ct", self.choose_output_ct_le, self.choose_output_ct_rb, self.choose_output_ct_btn)
        setToolTip("keep_dir_struct", self.keep_dir_struct_cb)
        setToolTip("delete_original", self.delete_original_cb, self.delete_original_cmb)
        setToolTip("clear_after_conv", self.clear_after_conv_cb)
        setToolTip("format", self.format_cmb)
        setToolTip("jxl_modular", self.jxl_modular_cb)
        setToolTip("jxl_png_fallback", self.jxl_png_fallback_cb)
        setToolTip("jxl_verify", self.jxl_verify_cb)
        setToolTip("jxl_normalize_enable", self.jxl_normalize_enable_cb)
        setToolTip("jxl_normalize_when", self.jxl_normalize_when_cmb)
        setToolTip("int_effort", self.int_effort_cb)
        setToolTip("chroma_subsampling_jpeg", self.chroma_subsampling_jpegli_cmb, self.chroma_subsampling_jpg_cmb)
        setToolTip("chroma_subsampling_aom_av1", self.chroma_subsampling_aom_av1_cmb)
        setToolTip("chroma_subsampling_svt_av1_psy", self.chroma_subsampling_svt_av1_psy_cmb)
        setToolTip("smallest_lossless_png", self.smallest_lossless_png_cb)
        setToolTip("smallest_lossless_webp", self.smallest_lossless_webp_cb)
        setToolTip("smallest_lossless_jpeg_xl", self.smallest_lossless_jxl_cb)
        setToolTip("smallest_lossless_max_comp", self.max_compression_cb)
        setToolTip("oxipng_inplace", self.oxipng_inplace_cb)

    def _setToolTipsDynamic(self):
        """Sets tooltips. Their content can change."""
        match self.format_cmb.currentText():
            case "JPEG XL":
                setToolTip("lossless_jpeg_xl", self.lossless_cb)
                setToolTip("effort", self.effort_sb)
                setToolTip("quality_jpeg_xl", self.quality_sl, self.quality_sb)
            case "AVIF":
                setToolTip("speed", self.effort_sb)
                setToolTip("quality_avif", self.quality_sl, self.quality_sb)
            case "WebP":
                setToolTip("method", self.effort_sb)
                setToolTip("quality_webp", self.quality_sl, self.quality_sb)
                setToolTip("lossless", self.lossless_cb)
            case "JPEG":
                setToolTip("quality_jpeg", self.quality_sl, self.quality_sb)
            case "Lossless JPEG Transcoding":
                setToolTip("effort_jpeg_recomp", self.effort_sb)
            case "PNG Optimization":
                setToolTip("oxipng_level", self.effort_sb)

    # //////////////////////////////////////////////////////////
    # /                      Getters
    # //////////////////////////////////////////////////////////

    def isClearAfterConvChecked(self):
        return self.clear_after_conv_cb.isChecked()

    def getUsedThreadCount(self) -> int:
        return self.threads_sl.value()

    def smIsFormatPoolEmpty(self) -> bool:
        empty = True
        for w in self.wm.getWidgetsByTag("format_pool"):
            if w.isChecked():
                empty = False
        return empty

    def getSettings(self):
        settings = {
            "format": self.format_cmb.currentText(),
            "quality": self.quality_sb.value(),
            "lossless": self.lossless_cb.isChecked(),
            "max_compression": self.max_compression_cb.isChecked(),
            "effort": self.effort_sb.value(),
            "intelligent_effort": self.int_effort_cb.isChecked() if self.jxl_int_effort_visible else False,
            "jxl_modular": self.jxl_modular_cb.isChecked() if self.jxl_lossy_modular_visible and not self.lossless_cb.isChecked() else False,
            "jxl_verify": self.jxl_verify_cb.isChecked(),
            "jxl_normalize_enable": self.jxl_normalize_enable_cb.isChecked(),
            "jxl_normalize_when": self.jxl_normalize_when_cmb.currentText(),
            "aom_av1_chroma_subsampling": self.chroma_subsampling_aom_av1_cmb.currentText(),
            "jpegli_chroma_subsampling": self.chroma_subsampling_jpegli_cmb.currentText(),
            "jpg_chroma_subsampling": self.chroma_subsampling_jpg_cmb.currentText(),
            "if_file_exists": self.duplicates_cmb.currentText(),
            "custom_output_dir": self.choose_output_ct_rb.isChecked(),
            "custom_output_dir_path": self.choose_output_ct_le.text(),
            "keep_dir_struct": self.keep_dir_struct_cb.isChecked(),
            "delete_original": self.delete_original_cb.isChecked(),
            "delete_original_mode": self.delete_original_cmb.currentText(),
            "smallest_format_pool": {
                "png": self.smallest_lossless_png_cb.isChecked(),
                "webp": self.smallest_lossless_webp_cb.isChecked(),
                "jxl": self.smallest_lossless_jxl_cb.isChecked()
                },
            "jxl_png_fallback": self.jxl_png_fallback_cb.isChecked(),
        }

        if (
            self.format_cmb.currentText() == "PNG Optimization" and
            self.oxipng_inplace_cb.isChecked()
        ):
            settings["if_file_exists"] = "Replace"
            settings["custom_output_dir"] = False
            settings["delete_original"] = False

        return settings

    # //////////////////////////////////////////////////////////
    # /                      Handlers
    # //////////////////////////////////////////////////////////

    def _chooseOutput(self):
        dir_to_load = self.wm.getVar("choose_output_last_dir")
        if dir_to_load is None or not isPathValidStr(dir_to_load):
            dir_to_load = QDir.homePath()

        dlg = QFileDialog(
            self,
            "Choose Output Folder",
            dir_to_load
        )
        dlg.setFileMode(QFileDialog.Directory)

        if dlg.exec():
            self.wm.setVar("choose_output_last_dir", dlg.directory().absolutePath())
            self.choose_output_ct_le.setText(dlg.selectedFiles()[0])

    def _onFormatChange(self):
        self._saveFormatVars()
        
        cur_format = self.format_cmb.currentText()
        self.prev_format = cur_format

        # Visible
        self.wm.setVisibleByTag("quality_all", cur_format in ("JPEG XL", "AVIF", "WebP", "JPEG"))
        self.int_effort_cb.setVisible(cur_format == "JPEG XL" and self.jxl_int_effort_visible)
        self.wm.setVisibleByTag("effort", cur_format in ("JPEG XL", "AVIF", "WebP", "Lossless JPEG Transcoding", "PNG Optimization"))
        self.wm.setVisibleByTag("jxl_losssy_modular", cur_format == "JPEG XL" and self.jxl_lossy_modular_visible)
        self.wm.setVisibleByTag("lossless", cur_format in ("JPEG XL", "WebP"))
        self.wm.setVisibleByTag("smallest_lossless", cur_format == "Smallest Lossless")
        self.chroma_subsampling_l.setVisible(cur_format in ("JPEG", "AVIF"))
        self.chroma_subsampling_jpg_cmb.setVisible(cur_format == "JPEG" and self.jpg_encoder == "libjpeg")
        self.chroma_subsampling_jpegli_cmb.setVisible(cur_format == "JPEG" and self.jpg_encoder == "JPEGLI")
        self.chroma_subsampling_aom_av1_cmb.setVisible(cur_format == "AVIF" and self.avif_encoder == "AOM AV1")
        self.chroma_subsampling_svt_av1_psy_cmb.setVisible(cur_format == "AVIF" and self.avif_encoder == "SVT-AV1-PSY")
        self.jxl_png_fallback_cb.setVisible(cur_format == "JPEG Reconstruction")
        self.jxl_verify_cb.setVisible(cur_format == "Lossless JPEG Transcoding")
        self.jxl_normalize_enable_cb.setVisible(cur_format == "Lossless JPEG Transcoding")
        self.jxl_normalize_when_cmb.setVisible(cur_format == "Lossless JPEG Transcoding")
        self.oxipng_inplace_cb.setVisible(cur_format == "PNG Optimization")

        # Params
        if cur_format == "AVIF":
            self.effort_sb.setRange(0, 10)
            self.effort_l.setText("Speed")
        elif cur_format in ("JPEG XL", "Lossless JPEG Transcoding"):
            self.effort_sb.setRange(1, 10 if self.enable_jxl_effort_10 else 9)
            self.effort_l.setText("Effort")
        elif cur_format == "WebP":
            self.effort_sb.setRange(0, 6)
            self.effort_l.setText("Method")
        elif cur_format == "PNG Optimization":
            self.effort_sb.setRange(0, 9)
            self.effort_l.setText("Level")

        if cur_format in ("JPEG XL", "AVIF"):
            self._setQualityRange(0, 99)
        elif cur_format == "WebP":
            self._setQualityRange(1, 99)
        else:
            self._setQualityRange(1, 100)
        
        # Update states
        self.wm.setCheckedByTag("lossless", False)
        self.effort_sb.setEnabled(cur_format in ("JPEG XL", "AVIF", "WebP", "Lossless JPEG Transcoding"))
        self._onEffortToggled()  # It's very important to update int_effort_cb to avoid issues when changing formats while it's enabled
        self._updateOutputStates()
        self._loadFormatVars()
        self._setToolTipsDynamic()

    def _onEffortToggled(self):
        if self.format_cmb.currentText() == "JPEG XL" and self.jxl_int_effort_visible:
            self.effort_sb.setEnabled(not self.int_effort_cb.isChecked())
        else:
            self.effort_sb.setEnabled(True)

    def _onLosslessToggled(self):
        lossless_checked = self.lossless_cb.isChecked()
        self.wm.setEnabledByTag("quality_all", not lossless_checked)
        self.wm.setEnabledByTag("jxl_losssy_modular", not lossless_checked)        

    def onJPEGEncoderChanged(self, encoder: str) -> None:
        if self.format_cmb.currentText() == "JPEG":
            self.chroma_subsampling_jpg_cmb.setVisible(encoder == "libjpeg")
            self.chroma_subsampling_jpegli_cmb.setVisible(encoder == "JPEGLI")

    def _onJXLNormalizeToggled(self) -> None:
        self.jxl_normalize_when_cmb.setEnabled(self.jxl_normalize_enable_cb.isChecked())

    def _onJXLNormalizeClicked(self) -> None:
        """On user's action."""
        if self.wm.getVar("jxl_normalize_checksum_msg_seen") is None:
            message_box.info(self, "Usage Info", "After \"Normalize\" is applied, JPEG images will have a different checksum, and get slightly larger once reconstructed. Learn more in the manual.")
            self.wm.setVar("jxl_normalize_checksum_msg_seen", True)

    def _onSmLBitDepthChanged(self) -> None:
        if self.smallest_lossless_webp_cb.isChecked():
            self.smallest_lossless_bit_depth_l.setText("Max Bit Depth: 8-bit")
        else:
            self.smallest_lossless_bit_depth_l.setText("Max Bit Depth: 16-bit")

    def onJXLEffort10Enabled(self, enabled: bool) -> None:
        self.enable_jxl_effort_10 = enabled
        cur_format = self.format_cmb.currentText()
        if cur_format in ("JPEG XL", "Lossless JPEG Transcoding"):
            self.effort_sb.setRange(1, 10 if self.enable_jxl_effort_10 else 9)

    def onQualityPrecisionSnappingEnabled(self, enabled: bool) -> None:
        self.quality_sl.setTickInterval(0 if enabled else 5)

    def onJXLLossyModularVisibleToggled(self, visible: bool) -> None:
        self.jxl_lossy_modular_visible = visible
        if self.format_cmb.currentText() == "JPEG XL":
            self.wm.setVisibleByTag("jxl_losssy_modular", visible)
    
    def onJXLIntEffortVisibleToggled(self, visible: bool) -> None:
        self.jxl_int_effort_visible = visible
        if self.format_cmb.currentText() == "JPEG XL":
            self.int_effort_cb.setVisible(visible)
        self._onEffortToggled()

    def onAVIFEncoderChanged(self, encoder: str) -> None:
        self.avif_encoder = encoder
        if self.format_cmb.currentText() == "AVIF":
            self.chroma_subsampling_svt_av1_psy_cmb.setVisible(encoder == "SVT-AV1-PSY")
            self.chroma_subsampling_aom_av1_cmb.setVisible(encoder == "AOM AV1")

    def _updateOutputStates(self) -> None:
        inplace = self.format_cmb.currentText() == "PNG Optimization" and self.oxipng_inplace_cb.isChecked()

        self.output_grp.setDisabled(inplace)
        if not inplace:
            src_checked = self.choose_output_src_rb.isChecked()
            self.wm.setEnabledByTag("output_ct", not src_checked)
            self.keep_dir_struct_cb.setEnabled(not src_checked)

        self.duplicates_l.setDisabled(inplace)
        self.duplicates_cmb.setDisabled(inplace)

        self.delete_original_cb.setDisabled(inplace)
        self.delete_original_cmb.setEnabled(
            self.delete_original_cb.isChecked() and not inplace
        )

    # //////////////////////////////////////////////////////////
    # /                   Actions / Utils
    # //////////////////////////////////////////////////////////
    
    def resetToDefault(self):
        self.wm.cleanVars()
        cur_format = self.format_cmb.currentText()

        match cur_format:
            case "AVIF":
                self.quality_sl.setValue(70)
                self.effort_sb.setValue(6)
            case "JPEG XL":
                self.quality_sl.setValue(80)
                self.effort_sb.setValue(7)
            case "JPEG":
                self.quality_sl.setValue(90)
            case "WebP":
                self.quality_sl.setValue(90)
                self.effort_sb.setValue(6)
            case "Lossless JPEG Transcoding":
                self.effort_sb.setValue(7)
            case "PNG Optimization":
                self.effort_sb.setValue(2)
        
        self.int_effort_cb.setChecked(False)
        self.jxl_modular_cb.setChecked(False)
        self.jxl_verify_cb.setChecked(False)
        self.jxl_normalize_enable_cb.setChecked(False)
        self.jxl_normalize_when_cmb.setCurrentIndex(0)

        self.choose_output_src_rb.setChecked(True)
        self.keep_dir_struct_cb.setChecked(False)

        self.delete_original_cb.setChecked(False)
        self.delete_original_cmb.setCurrentIndex(0)
        self.clear_after_conv_cb.setChecked(False)
        
        self.threads_sl.setValue(max(self.MAX_THREAD_COUNT - 1, 1))
        self.duplicates_cmb.setCurrentIndex(0)
        
        self.chroma_subsampling_jpegli_cmb.setCurrentIndex(0)
        self.chroma_subsampling_aom_av1_cmb.setCurrentIndex(0)
        self.chroma_subsampling_svt_av1_psy_cmb.setCurrentIndex(0)
        self.chroma_subsampling_jpg_cmb.setCurrentIndex(0)

        # Lossless
        self.wm.setCheckedByTag("lossless", False)
        self.max_compression_cb.setChecked(False)

        # Smallest Lossless
        for i in self.wm.getWidgetsByTag("format_pool"):
            i.setChecked(True)
        
        self.jxl_png_fallback_cb.setChecked(False)
        self.oxipng_inplace_cb.setChecked(False)

    def _setQualityRange(self, _min: int, _max: int) -> None:
        for i in self.wm.getWidgetsByTag("quality"):
            i.setRange(_min, _max)

    def _saveFormatVars(self):
        if self.prev_format == None:
            return

        match self.prev_format:
            case "JPEG XL":
                self.wm.setVar("jxl_quality", self.quality_sl.value())
                self.wm.setVar("jxl_effort", self.effort_sb.value())
                self.wm.setVar("jxl_int_effort", self.int_effort_cb.isChecked())
                self.wm.setVar("jxl_lossless", self.lossless_cb.isChecked())
            case "AVIF":
                self.wm.setVar("avif_quality", self.quality_sl.value())
                self.wm.setVar("avif_speed", self.effort_sb.value())
            case "WebP":
                self.wm.setVar("webp_quality", self.quality_sl.value())
                self.wm.setVar("webp_effort", self.effort_sb.value())
                self.wm.setVar("webp_lossless", self.lossless_cb.isChecked())
            case "JPEG":
                self.wm.setVar("jpg_quality", self.quality_sl.value())
            case "Lossless JPEG Transcoding":
                self.wm.setVar("jxl_lossless_jpeg_effort", self.effort_sb.value())
            case "PNG Optimization":
                self.wm.setVar("oxipng_level", self.effort_sb.value())

    def _loadFormatVars(self):
        match self.prev_format:
            case "JPEG XL":
                self.wm.applyVar("jxl_quality", "quality_sl", 80)
                self.wm.applyVar("jxl_effort", "effort_sb", 7)
                self.wm.applyVar("jxl_lossless", "lossless_cb", False)
            case "AVIF":
                self.wm.applyVar("avif_quality", "quality_sl", 70)
                self.wm.applyVar("avif_speed", "effort_sb", 6)
            case "WebP":
                self.wm.applyVar("webp_quality", "quality_sl", 90)
                self.wm.applyVar("webp_effort", "effort_sb", 6)
                self.wm.applyVar("webp_lossless", "lossless_cb", False)
            case "JPEG":
                self.wm.applyVar("jpg_quality", "quality_sl", 90)
            case "Lossless JPEG Transcoding":
                self.wm.applyVar("jxl_lossless_jpeg_effort", "effort_sb", 7)
            case "PNG Optimization":
                self.wm.applyVar("oxipng_level", "effort_sb", 2)

    def saveState(self, new_states: Optional[Dict] = None) -> None:
        if new_states is None or new_states != self.cached_states:
            self.cached_states = deepcopy(new_states)
            self.wm.disableAutoSaving(
                "quality_sb",
                "quality_sl",
                "effort_sb",
                "lossless_cb",
            )
            self._saveFormatVars()
            self.wm.saveState()
