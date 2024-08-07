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
    Signal
)

from .widget_manager import WidgetManager
from core.utils import dictToList
from ui.slider import Slider
from ui.combobox import ComboBox
from ui.spinbox import SpinBox
from ui.utils import setToolTip
from data.tooltips import TOOLTIPS

class OutputTab(QWidget):
    convert = Signal()
    
    def __init__(self, max_threads, settings):
        super(OutputTab, self).__init__()

        self.wm = WidgetManager("OutputTab")
        self.prev_format = None

        self.MAX_THREAD_COUNT = max_threads

        # Main layout
        output_page_lt = QGridLayout()
        self.setLayout(output_page_lt)

        # Conversion - widgets
        self.threads_sl = self.wm.addWidget("threads_sl", Slider())
        self.threads_sb = self.wm.addWidget("threads_sb", SpinBox())

        self.threads_sl.setRange(1, self.MAX_THREAD_COUNT)
        self.threads_sb.setRange(1, self.MAX_THREAD_COUNT)
        self.threads_sl.setTickInterval(1)
        self.threads_sl.valueChanged.connect(self.onThreadSlChange)
        self.threads_sb.valueChanged.connect(self.onThreadSbChange)
        
        self.duplicates_cmb = self.wm.addWidget("duplicates_cmb", ComboBox())
        self.duplicates_cmb.addItems(("Rename", "Replace", "Skip"))

        # Conversion - layout
        conv_grp = QGroupBox("Conversion")
        conv_grp_lt = QVBoxLayout()
        conv_grp.setLayout(conv_grp_lt)
        
        threads_hb = QHBoxLayout()
        threads_hb.addWidget(QLabel("Threads"))
        threads_hb.addWidget(self.threads_sl)
        threads_hb.addWidget(self.threads_sb)

        duplicates_hb = QHBoxLayout()
        duplicates_hb.addWidget(QLabel("Duplicates"))
        duplicates_hb.addWidget(self.duplicates_cmb)

        conv_grp_lt.addLayout(duplicates_hb)
        conv_grp_lt.addLayout(threads_hb)
        
        # After Conversion - widgets
        self.clear_after_conv_cb = self.wm.addWidget("clear_after_conv_cb", QCheckBox("Clear File List"))
        self.delete_original_cb = self.wm.addWidget("delete_original_cb", QCheckBox("Delete Original"))
        self.delete_original_cmb = self.wm.addWidget("delete_original_cmb", ComboBox())

        self.delete_original_cmb.addItems(("To Trash", "Permanently"))
        self.delete_original_cb.stateChanged.connect(self.onDeleteOriginalChanged)

        # After conversion - layout
        after_conv_grp = QGroupBox("After Conversion")
        after_conv_grp_lt = QVBoxLayout()
        after_conv_grp.setLayout(after_conv_grp_lt)

        after_conv_grp_lt.addWidget(self.clear_after_conv_cb)
        delete_original_hb = QHBoxLayout()
        delete_original_hb.addWidget(self.delete_original_cb)
        delete_original_hb.addWidget(self.delete_original_cmb)
        after_conv_grp_lt.addLayout(delete_original_hb)

        # Output - widgets
        self.choose_output_src_rb = self.wm.addWidget("choose_output_src_rb", QRadioButton("Source Folder"))
        self.choose_output_ct_rb = self.wm.addWidget("choose_output_ct_rb", QRadioButton("Custom"))
        self.choose_output_ct_le = self.wm.addWidget("choose_output_ct_le", QLineEdit(), "output_ct")
        self.choose_output_ct_btn = self.wm.addWidget("choose_output_ct_btn", QPushButton("..."), "output_ct")
        self.keep_dir_struct_cb = self.wm.addWidget("keep_dir_struct_cb", QCheckBox("Keep Folder Structure"))

        self.choose_output_ct_btn.clicked.connect(self.chooseOutput)        
        self.choose_output_ct_rb.toggled.connect(self.onOutputToggled)
        self.choose_output_ct_btn.setMaximumWidth(25)

        # Output - layout
        output_grp = QGroupBox("Save To")
        output_grp_lt = QVBoxLayout()
        output_grp.setLayout(output_grp_lt)

        output_hb = QHBoxLayout()
        output_hb.addWidget(self.choose_output_ct_rb)
        for i in self.wm.getWidgetsByTag("output_ct"):
            output_hb.addWidget(i)

        output_grp_lt.addWidget(self.choose_output_src_rb)
        output_grp_lt.addLayout(output_hb)
        output_grp_lt.addWidget(self.keep_dir_struct_cb)

        # Format - widgets
        self.format_cmb = self.wm.addWidget("format_cmb", ComboBox())
        self.format_cmb.addItems((
            "JPEG XL",
            "AVIF",
            "WebP",
            "JPEG",
            "PNG",
            "Lossless JPEG Recompression",
            "JPEG Reconstruction",
            "Smallest Lossless",
        ))
        self.format_cmb.currentIndexChanged.connect(self.onFormatChange)

        self.effort_l = self.wm.addWidget("effort_l", QLabel("Effort"))
        self.effort_sb = self.wm.addWidget("effort_sb", SpinBox())
        self.int_effort_cb = self.wm.addWidget("int_effort_cb", QCheckBox("Intelligent"))
        self.int_effort_cb.toggled.connect(self.onEffortToggled)

        self.wm.addTag("effort", "effort_l")
        self.wm.addTag("effort", "int_effort_cb")
        self.wm.addTag("effort", "effort_sb")

        self.quality_l = self.wm.addWidget("quality_l", QLabel("Quality"), "quality_all")
        self.quality_sb = self.wm.addWidget("quality_sb", SpinBox(), "quality", "quality_all")
        self.quality_sl = self.wm.addWidget("quality_sl", Slider(), "quality", "quality_all")
        self.quality_sl.valueChanged.connect(self.onQualitySlChanged)
        self.quality_sb.valueChanged.connect(self.onQualitySbChanged)

        self.lossless_cb = self.wm.addWidget("lossless_cb", QCheckBox("Lossless"), "lossless")
        self.lossless_spacer_l = self.wm.addWidget("lossless_spacer_l", QLabel(""), "lossless")
        self.lossless_cb.toggled.connect(self.onLosslessToggled)

        self.max_compression_cb = self.wm.addWidget("max_compression_cb", QCheckBox("Max Compression"))
        
        self.jxl_modular_l = self.wm.addWidget("jxl_modular_l", QLabel("Lossy Mode"), "jxl_advanced")
        self.jxl_modular_cb = self.wm.addWidget("jxl_modular_cb", QCheckBox("Modular"), "jxl_advanced")

        self.smallest_lossless_png_cb = self.wm.addWidget("smallest_lossless_png_cb", QCheckBox("PNG"), "format_pool")
        self.smallest_lossless_webp_cb = self.wm.addWidget("smallest_lossless_webp_cb", QCheckBox("WebP"), "format_pool")
        self.smallest_lossless_jxl_cb = self.wm.addWidget("smallest_lossless_jxl_cb", QCheckBox("JPEG XL"), "format_pool")
        
        self.chroma_subsampling_l = self.wm.addWidget("chroma_subsampling_l", QLabel("Chroma Subsampling", self), "chroma_subsampling")
        self.chroma_subsampling_jpegli_cmb = self.wm.addWidget("chroma_subsampling_jpegli_cmb", ComboBox(self), "chroma_subsampling")
        self.chroma_subsampling_jpegli_cmb.addItems(("Default", "4:4:4", "4:2:2", "4:2:0",))
        self.chroma_subsampling_avif_cmb = self.wm.addWidget("chroma_subsampling_avif_cmb", ComboBox(self), "chroma_subsampling")
        self.chroma_subsampling_avif_cmb.addItems(("Default", "4:4:4", "4:2:2", "4:2:0", "4:0:0",))
        self.chroma_subsampling_jpg_cmb = self.wm.addWidget("chroma_subsampling_jpg_cmb", ComboBox(self), "chroma_subsampling")
        self.chroma_subsampling_jpg_cmb.addItems(("Default", "4:4:4", "4:2:2", "4:2:0",))

        self.jxl_png_fallback_cb = self.wm.addWidget("jxl_png_fallback_cb", QCheckBox("PNG Fallback"))

        # Format - layout
        format_cmb_hb = QHBoxLayout()                       # Format ComboBox
        format_cmb_hb.addWidget(QLabel("Format"))
        format_cmb_hb.addWidget(self.format_cmb)
        
        effort_hb = QHBoxLayout()                           # Effort
        for i in self.wm.getWidgetsByTag("effort"):
            effort_hb.addWidget(i)

        lossless_hb = QHBoxLayout()                         # Lossless
        lossless_hb.addWidget(self.lossless_spacer_l)
        lossless_hb.addWidget(self.lossless_cb)

        quality_hb = QHBoxLayout()                          # Quality
        quality_hb.addWidget(self.quality_l)
        quality_hb.addWidget(self.quality_sl)
        quality_hb.addWidget(self.quality_sb)

        jxl_advanced_hb = QHBoxLayout()                     # JPEG XL Mode
        jxl_advanced_hb.addWidget(self.jxl_modular_l)
        jxl_advanced_hb.addWidget(self.jxl_modular_cb)

        format_sm_l_hb = QHBoxLayout()                      # Smallest Lossless
        for i in self.wm.getWidgetsByTag("format_pool"):
            format_sm_l_hb.addWidget(i)

        self.chroma_subsampling_hb = QHBoxLayout()      # Chroma subsampling
        self.chroma_subsampling_hb.addWidget(self.chroma_subsampling_l)
        self.chroma_subsampling_hb.addWidget(self.chroma_subsampling_jpegli_cmb)
        self.chroma_subsampling_hb.addWidget(self.chroma_subsampling_avif_cmb)
        self.chroma_subsampling_hb.addWidget(self.chroma_subsampling_jpg_cmb)

        # Layout
        format_grp = QGroupBox("Format")
        format_grp_lt = QVBoxLayout()
        format_grp.setLayout(format_grp_lt)
        format_grp_lt.addLayout(format_cmb_hb)
        format_grp_lt.addLayout(effort_hb)
        format_grp_lt.addLayout(quality_hb)
        format_grp_lt.addLayout(jxl_advanced_hb)
        format_grp_lt.addLayout(lossless_hb)
        format_grp_lt.addLayout(format_sm_l_hb)
        format_grp_lt.addWidget(self.max_compression_cb)
        format_grp_lt.addLayout(self.chroma_subsampling_hb)
        format_grp_lt.addWidget(self.jxl_png_fallback_cb)
        self.format_cmb.setMinimumWidth(220)

        # Buttons
        reset_to_default_btn = QPushButton("Reset to Default")
        reset_to_default_btn.clicked.connect(self.resetToDefault)
        self.convert_btn_2 = QPushButton("Convert")
        self.convert_btn_2.clicked.connect(self.convert.emit)
        
        # Main layout
        output_page_lt.addWidget(reset_to_default_btn,2,0)
        output_page_lt.addWidget(self.convert_btn_2,2,1)
        
        output_page_lt.addWidget(format_grp,0,1)
        output_page_lt.addWidget(output_grp, 0, 0)
        output_page_lt.addWidget(conv_grp,1,0)
        output_page_lt.addWidget(after_conv_grp,1,1)
        
        # Size policy
        output_page_lt.setAlignment(Qt.AlignTop)
        output_page_lt.setRowMinimumHeight(0, 150)

        format_grp.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        conv_grp.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        after_conv_grp.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        output_grp.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Load Settings
        self.enable_jxl_effort_10 = settings["enable_jxl_effort_10"]
        self.jpg_encoder = settings["jpg_encoder"]
        
        # Misc
        self.resetToDefault()
        self.wm.loadState()
        self.setToolTipsStatic()
        
        # Apply Settings
        if settings["disable_delete_startup"]:
            self.delete_original_cb.setChecked(False)

        self.enableQualityPrecisionSnapping(settings["enable_quality_precision_snapping"])

        # Setup widgets' states
        self.onFormatChange()
        self.onDeleteOriginalChanged()
        self.onOutputToggled()
    
    def setToolTipsStatic(self):
        """Sets tooltips at once at startup."""
        setToolTip(TOOLTIPS["duplicates"], self.duplicates_cmb)
        setToolTip(TOOLTIPS["threads"], self.threads_sl, self.threads_sb)
        setToolTip(TOOLTIPS["output_src"], self.choose_output_src_rb)
        setToolTip(TOOLTIPS["output_ct"], self.choose_output_ct_le, self.choose_output_ct_rb, self.choose_output_ct_btn)
        setToolTip(TOOLTIPS["keep_dir_struct"], self.keep_dir_struct_cb)
        setToolTip(TOOLTIPS["delete_original"], self.delete_original_cb, self.delete_original_cmb)
        setToolTip(TOOLTIPS["clear_after_conv"], self.clear_after_conv_cb)
        setToolTip(TOOLTIPS["format"], self.format_cmb)
        setToolTip(TOOLTIPS["jxl_modular"], self.jxl_modular_cb)
        setToolTip(TOOLTIPS["jxl_png_fallback"], self.jxl_png_fallback_cb)
        setToolTip(TOOLTIPS["int_effort"], self.int_effort_cb)
        setToolTip(TOOLTIPS["chroma_subsampling_jpeg"], self.chroma_subsampling_jpegli_cmb, self.chroma_subsampling_jpg_cmb)
        setToolTip(TOOLTIPS["chroma_subsampling_avif"], self.chroma_subsampling_avif_cmb)
        setToolTip(TOOLTIPS["smallest_lossless_png"], self.smallest_lossless_png_cb)
        setToolTip(TOOLTIPS["smallest_lossless_webp"], self.smallest_lossless_webp_cb)
        setToolTip(TOOLTIPS["smallest_lossless_jpeg_xl"], self.smallest_lossless_jxl_cb)
        setToolTip(TOOLTIPS["smallest_lossless_max_comp"], self.max_compression_cb)

    def setToolTipsDynamic(self):
        """Sets tooltips. Their content can change."""
        match self.format_cmb.currentText():
            case "JPEG XL":
                setToolTip(TOOLTIPS["lossless_jpeg_xl"], self.lossless_cb)
                setToolTip(TOOLTIPS["effort"], self.effort_sb)
                setToolTip(TOOLTIPS["quality_jpeg_xl"], self.quality_sl, self.quality_sb)
            case "AVIF":
                setToolTip(TOOLTIPS["speed"], self.effort_sb)
                setToolTip(TOOLTIPS["quality_avif"], self.quality_sl, self.quality_sb)
            case "WebP":
                setToolTip(TOOLTIPS["method"], self.effort_sb)
                setToolTip(TOOLTIPS["quality_webp"], self.quality_sl, self.quality_sb)
                setToolTip(TOOLTIPS["lossless"], self.lossless_cb)
            case "JPEG":
                setToolTip(TOOLTIPS["quality_jpeg"], self.quality_sl, self.quality_sb)
            case "Lossless JPEG Recompression":
                setToolTip(TOOLTIPS["effort_jpeg_recomp"], self.effort_sb)

    def isClearAfterConvChecked(self):
        return self.clear_after_conv_cb.isChecked()

    def getSettings(self):
        return {
            "format": self.format_cmb.currentText(),
            "quality": self.quality_sb.value(),
            "lossless": self.lossless_cb.isChecked(),
            "max_compression": self.max_compression_cb.isChecked(),
            "effort": self.effort_sb.value(),
            "intelligent_effort": self.int_effort_cb.isChecked(),
            "jxl_modular": self.jxl_modular_cb.isChecked(),
            "avif_chroma_subsampling": self.chroma_subsampling_avif_cmb.currentText(),
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
    
    def getReportData(self):
        """Used by ExceptionView"""
        report = self.getSettings()
        report.pop("custom_output_dir_path")

        return {
            "Output": dictToList(report)
        }

    def onThreadSlChange(self):
        self.threads_sb.setValue(self.threads_sl.value())

    def onThreadSbChange(self):
        self.threads_sl.setValue(self.threads_sb.value())

    def getUsedThreadCount(self):
        return self.threads_sl.value()

    def smIsFormatPoolEmpty(self):
        empty = True
        for w in self.wm.getWidgetsByTag("format_pool"):
            if w.isChecked():
                empty = False
        return empty
        
    def chooseOutput(self):
        dlg = QFileDialog()
        dlg.setWindowTitle("Choose Output Folder")
        dlg.setFileMode(QFileDialog.Directory)

        if dlg.exec():
            self.choose_output_ct_le.setText(dlg.selectedFiles()[0])

    def onOutputToggled(self):
        src_checked = self.choose_output_src_rb.isChecked()
        self.wm.setEnabledByTag("output_ct", not src_checked)
        self.keep_dir_struct_cb.setEnabled(not src_checked)
        
    def onFormatChange(self):
        self.saveFormatState()
        
        cur_format = self.format_cmb.currentText()
        self.prev_format = cur_format

        # Visible
        self.wm.setVisibleByTag("quality_all", cur_format in ("JPEG XL", "AVIF", "WebP", "JPEG"))
        self.int_effort_cb.setVisible(cur_format == "JPEG XL")
        self.effort_sb.setVisible(cur_format in ("JPEG XL", "AVIF", "WebP", "Lossless JPEG Recompression"))
        self.effort_l.setVisible(cur_format in ("JPEG XL", "AVIF", "WebP", "Lossless JPEG Recompression"))
        self.wm.setVisibleByTag("jxl_advanced", cur_format == "JPEG XL")
        self.wm.setVisibleByTag("lossless", cur_format in ("JPEG XL", "WebP"))
        self.wm.setVisibleByTag("format_pool", cur_format == "Smallest Lossless")
        self.max_compression_cb.setVisible(cur_format == "Smallest Lossless")
        self.chroma_subsampling_l.setVisible(cur_format in ("JPEG", "AVIF"))
        self.chroma_subsampling_jpg_cmb.setVisible(cur_format == "JPEG" and self.jpg_encoder == "libjpeg")
        self.chroma_subsampling_jpegli_cmb.setVisible(cur_format == "JPEG" and self.jpg_encoder == "JPEGLI")
        self.chroma_subsampling_avif_cmb.setVisible(cur_format == "AVIF")
        self.jxl_png_fallback_cb.setVisible(cur_format == "JPEG Reconstruction")

        # Params
        if cur_format == "AVIF":
            self.effort_sb.setRange(0, 10)
            self.effort_l.setText("Speed")
        elif cur_format in ("JPEG XL", "Lossless JPEG Recompression"):
            self.effort_sb.setRange(1, 10 if self.enable_jxl_effort_10 else 9)
            self.effort_l.setText("Effort")
        elif cur_format == "WebP":
            self.effort_sb.setRange(0, 6)
            self.effort_l.setText("Method")

        if cur_format in ("JPEG XL", "AVIF"):
            self.setQualityRange(0, 99)
        elif cur_format == "WebP":
            self.setQualityRange(1, 99)
        else:
            self.setQualityRange(1, 100)
        
        # Update states
        self.wm.setCheckedByTag("lossless", False)
        self.effort_sb.setEnabled(cur_format in ("JPEG XL", "AVIF", "WebP", "Lossless JPEG Recompression"))
        
        if cur_format == "JPEG XL":
            self.onEffortToggled()  # It's very important to update int_effort_cb to avoid issues when changing formats while it's enabled

        self.loadFormatState()
        self.setToolTipsDynamic()
        
    def onQualitySlChanged(self):
        self.quality_sb.setValue(self.quality_sl.value())

    def onQualitySbChanged(self):
        self.quality_sl.setValue(self.quality_sb.value())
    
    def onDeleteOriginalChanged(self):
        self.delete_original_cmb.setEnabled(self.delete_original_cb.isChecked())

    def onEffortToggled(self):
        self.effort_sb.setEnabled(not self.int_effort_cb.isChecked())

    def onLosslessToggled(self):
        lossless_checked = self.lossless_cb.isChecked()

        self.wm.setEnabledByTag("quality_all", not lossless_checked)
        self.wm.setEnabledByTag("jxl_advanced", not lossless_checked)        

    def onJPGEncoderChanged(self, encoder):
        if self.format_cmb.currentText() == "JPEG":
            self.chroma_subsampling_jpg_cmb.setVisible(encoder == "libjpeg")
            self.chroma_subsampling_jpegli_cmb.setVisible(encoder == "JPEGLI")

    def setJxlEffort10Enabled(self, enabled):
        self.enable_jxl_effort_10 = enabled
        if self.format_cmb.currentText() == "JPEG XL":
            self.effort_sb.setRange(1, 10 if self.enable_jxl_effort_10 else 9)

    def enableQualityPrecisionSnapping(self, enabled):
        if enabled:
            self.quality_sl.setTickInterval(0)
        else:
            self.quality_sl.setTickInterval(5)

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
            case "Lossless JPEG Recompression":
                self.effort_sb.setValue(9)
        
        self.int_effort_cb.setChecked(False)
        self.jxl_modular_cb.setChecked(False)

        self.choose_output_src_rb.setChecked(True)
        self.keep_dir_struct_cb.setChecked(False)

        self.delete_original_cb.setChecked(False)
        self.delete_original_cmb.setCurrentIndex(0)
        self.clear_after_conv_cb.setChecked(False)
        
        self.threads_sl.setValue(self.MAX_THREAD_COUNT - 1 if self.MAX_THREAD_COUNT > 0 else 1)  # -1 because the OS needs some CPU time as well
        self.duplicates_cmb.setCurrentIndex(0)
        
        self.chroma_subsampling_jpegli_cmb.setCurrentIndex(0)
        self.chroma_subsampling_avif_cmb.setCurrentIndex(0)
        self.chroma_subsampling_jpg_cmb.setCurrentIndex(0)

        # Lossless
        self.wm.setCheckedByTag("lossless", False)
        self.max_compression_cb.setChecked(False)

        # Smallest Lossless
        for i in self.wm.getWidgetsByTag("format_pool"):
            i.setChecked(True)
        
        self.jxl_png_fallback_cb.setChecked(True)
    
    def setQualityRange(self, _min, _max):
        for i in self.wm.getWidgetsByTag("quality"):
            i.setRange(_min, _max)

    def saveFormatState(self):
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
            case "Lossless JPEG Recompression":
                self.wm.setVar("jxl_lossless_jpeg_effort", self.effort_sb.value())

    def loadFormatState(self):
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
            case "Lossless JPEG Recompression":
                self.wm.applyVar("jxl_lossless_jpeg_effort", "effort_sb", 9)

    def saveState(self):
        self.wm.disableAutoSaving(
            "quality_sb",
            "quality_sl",
            "effort_sb",
            "lossless_cb",
        )

        self.saveFormatState()
        self.wm.saveState()