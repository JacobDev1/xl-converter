from PySide6.QtWidgets import(
    QWidget,
    QGridLayout,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QComboBox,
    QSlider,
    QLabel,
    QCheckBox,
    QLineEdit,
    QRadioButton,
    QPushButton,
    QFileDialog,
    QSpinBox,
    QSizePolicy,
)
from PySide6.QtCore import(
    Qt,
    Signal
)

from .widget_manager import WidgetManager
from core.utils import dictToList

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
        self.threads_sl = self.wm.addWidget("threads_sl", QSlider(Qt.Horizontal))
        self.threads_sb = self.wm.addWidget("threads_sb", QSpinBox())

        self.threads_sl.setRange(1, self.MAX_THREAD_COUNT)
        self.threads_sb.setRange(1, self.MAX_THREAD_COUNT)
        self.threads_sl.setTickInterval(1)
        self.threads_sl.valueChanged.connect(self.onThreadSlChange)
        self.threads_sb.valueChanged.connect(self.onThreadSbChange)
        
        self.duplicates_cmb = self.wm.addWidget("duplicates_cmb", QComboBox())
        self.duplicates_cmb.addItems(("Replace", "Rename", "Skip"))

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
        self.delete_original_cmb = self.wm.addWidget("delete_original_cmb", QComboBox())

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

        # Format - widgets
        self.format_cmb = self.wm.addWidget("format_cmb", QComboBox())
        self.format_cmb.addItems(("JPEG XL","AVIF", "WEBP", "JPG", "PNG", "Smallest Lossless"))
        self.format_cmb.currentIndexChanged.connect(self.onFormatChange)

        self.effort_l = self.wm.addWidget("effort_l", QLabel("Effort"))
        self.effort_sb = self.wm.addWidget("effort_sb", QSpinBox())
        self.int_effort_cb = self.wm.addWidget("int_effort_cb", QCheckBox("Intelligent"))
        self.int_effort_cb.toggled.connect(self.onEffortToggled)

        self.wm.addTag("effort", "effort_l")
        self.wm.addTag("effort", "int_effort_cb")
        self.wm.addTag("effort", "effort_sb")

        self.quality_l = self.wm.addWidget("quality_l", QLabel("Quality"), "quality_all")
        self.quality_sb = self.wm.addWidget("quality_sb", QSpinBox(), "quality", "quality_all")
        self.quality_sl = self.wm.addWidget("quality_sl", QSlider(Qt.Horizontal), "quality", "quality_all")
        self.quality_sl.setTickInterval(5)
        self.quality_sl.valueChanged.connect(self.onQualitySlChanged)
        self.quality_sb.valueChanged.connect(self.onQualitySbChanged)

        self.lossless_cb = self.wm.addWidget("lossless_cb", QCheckBox("Lossless"), "lossless")
        self.lossless_if_cb = self.wm.addWidget("lossless_if_cb", QCheckBox("Lossless (only if smaller)"), "lossless")
        self.lossless_if_cb.toggled.connect(self.onLosslessToggled)
        self.lossless_cb.toggled.connect(self.onLosslessToggled)

        self.max_compression_cb = self.wm.addWidget("max_compression_cb", QCheckBox("Max Compression"))
        
        self.jxl_mode_l = self.wm.addWidget("jxl_mode_l", QLabel("Lossy Mode"), "jxl_mode")
        self.jxl_mode_cmb = self.wm.addWidget("jxl_mode_cmb", QComboBox(), "jxl_mode")
        self.jxl_mode_cmb.addItems((
            "Default",
            "VarDCT",
            "Modular",
        ))
        
        self.smallest_lossless_png_cb = self.wm.addWidget("smallest_lossless_png_cb", QCheckBox("PNG"), "format_pool")
        self.smallest_lossless_webp_cb = self.wm.addWidget("smallest_lossless_webp_cb", QCheckBox("WEBP"), "format_pool")
        self.smallest_lossless_jxl_cb = self.wm.addWidget("smallest_lossless_jxl_cb", QCheckBox("JPEG XL"), "format_pool")
        
        self.reconstruct_jpg_cb = self.wm.addWidget("reconstruct_jpg_cb", QCheckBox("Reconstruct JPG from JPEG XL"))
        
        # Format - layout
        format_cmb_hb = QHBoxLayout()                       # Format ComboBox
        format_cmb_hb.addWidget(QLabel("Format"))
        format_cmb_hb.addWidget(self.format_cmb)
        
        effort_hb = QHBoxLayout()                           # Effort
        for i in self.wm.getWidgetsByTag("effort"):
            effort_hb.addWidget(i)

        lossless_hb = QHBoxLayout()                         # Lossless
        lossless_hb.addWidget(self.lossless_cb)
        lossless_hb.addWidget(self.lossless_if_cb)

        self.jxl_mode_hb = QHBoxLayout()                    # JPEG XL Mode
        self.jxl_mode_hb.addWidget(self.jxl_mode_l)
        self.jxl_mode_hb.addWidget(self.jxl_mode_cmb)

        quality_hb = QHBoxLayout()                          # Quality
        quality_hb.addWidget(self.quality_l)
        quality_hb.addWidget(self.quality_sl)
        quality_hb.addWidget(self.quality_sb)
        
        format_sm_l_hb = QHBoxLayout()                      # Smallest Lossless
        for i in self.wm.getWidgetsByTag("format_pool"):
            format_sm_l_hb.addWidget(i)

        format_grp = QGroupBox("Format")                    # Layout
        format_grp_lt = QVBoxLayout()
        format_grp.setLayout(format_grp_lt)
        format_grp_lt.addLayout(format_cmb_hb)
        format_grp_lt.addLayout(effort_hb)
        format_grp_lt.addLayout(quality_hb)
        format_grp_lt.addLayout(lossless_hb)
        format_grp_lt.addLayout(format_sm_l_hb)
        format_grp_lt.addWidget(self.max_compression_cb)
        format_grp_lt.addLayout(self.jxl_mode_hb)
        format_grp_lt.addWidget(self.reconstruct_jpg_cb)

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
        
        output_page_lt.setAlignment(Qt.AlignTop)

        format_grp.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        conv_grp.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        after_conv_grp.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        output_grp.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Misc
        self.resetToDefault()
        self.wm.loadState()

        # Apply Settings
        if settings["disable_delete_startup"]:
            self.delete_original_cb.setChecked(False)

        # Setup widgets' states
        self.onFormatChange()
        self.onDeleteOriginalChanged()
        self.onOutputToggled()
    
    def isClearAfterConvChecked(self):
        return self.clear_after_conv_cb.isChecked()

    def getSettings(self):
        return {
            "format": self.format_cmb.currentText(),
            "quality": self.quality_sb.value(),
            "lossless": self.lossless_cb.isChecked(),
            "lossless_if_smaller": self.lossless_if_cb.isChecked(),
            "max_compression": self.max_compression_cb.isChecked(),
            "effort": self.effort_sb.value(),
            "intelligent_effort": self.int_effort_cb.isChecked(),
            "reconstruct_jpg": self.reconstruct_jpg_cb.isChecked(),
            "jxl_mode": self.jxl_mode_cmb.currentText(),
            "if_file_exists": self.duplicates_cmb.currentText(),
            "custom_output_dir": self.choose_output_ct_rb.isChecked(),
            "custom_output_dir_path": self.choose_output_ct_le.text(),
            "delete_original": self.delete_original_cb.isChecked(),
            "delete_original_mode": self.delete_original_cmb.currentText(),
            "smallest_format_pool": {
                "png": self.smallest_lossless_png_cb.isChecked(),
                "webp": self.smallest_lossless_webp_cb.isChecked(),
                "jxl": self.smallest_lossless_jxl_cb.isChecked()
                },
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
        
    def onFormatChange(self):
        self.saveFormatState()
        
        cur_format = self.format_cmb.currentText()
        self.prev_format = cur_format
        
        self.wm.setCheckedByTag("lossless", False)  # Widgets re-enable themselves when you use setChecked() on a disabled widget, so this needs to stay in the beginning

        # Enable Lossless Mode
        self.wm.setEnabledByTag("lossless", cur_format in ("JPEG XL", "WEBP"))

        # Effort
        self.int_effort_cb.setEnabled(cur_format == "JPEG XL")
        self.effort_sb.setEnabled(cur_format in ("JPEG XL", "AVIF"))
        self.effort_l.setEnabled(cur_format in ("JPEG XL", "AVIF"))

        if cur_format == "JPEG XL":
            self.onEffortToggled()  # It's very important to update int_effort_cb to avoid issues when changing formats while it's enabled

        # Special Modes
        self.wm.setVisibleByTag("jxl_mode", cur_format == "JPEG XL")

        # Disable Quality Slider
        self.wm.setEnabledByTag("quality_all", not cur_format in ("PNG", "Smallest Lossless"))

        # Quality slider
        if cur_format in ("JPEG XL", "AVIF"):
            self.setQualityRange(0, 99)
        else:
            self.setQualityRange(1, 100)

        # Quality Slider Range and label
        if cur_format == "AVIF":
            self.effort_sb.setRange(0, 10)
            self.effort_l.setText("Speed")
        else:
            if cur_format == "JPEG XL":
                self.setQualityRange(0, 99)
            else:
                self.setQualityRange(1, 100)
            self.effort_sb.setRange(1, 9)
            self.quality_l.setText("Quality")
            self.effort_l.setText("Effort")
        
        # Smallest Lossless mode
        is_sm_l = cur_format == "Smallest Lossless"
        self.wm.setVisibleByTag("lossless", not is_sm_l)
        self.wm.setVisibleByTag("effort", not is_sm_l)
        self.wm.setVisibleByTag("format_pool", is_sm_l)
        self.max_compression_cb.setVisible(is_sm_l)
        
        # Decoding (PNG)
        if cur_format == "PNG":
            self.reconstruct_jpg_cb.setVisible(True)
            self.wm.setVisibleByTag("lossless", False)
        else:
            self.reconstruct_jpg_cb.setVisible(False)

        self.loadFormatState()
        
    def onQualitySlChanged(self):
        self.quality_sb.setValue(abs(self.quality_sl.value()))

    def onQualitySbChanged(self):
        self.quality_sl.setValue(self.quality_sb.value())
    
    def onDeleteOriginalChanged(self):
        self.delete_original_cmb.setEnabled(self.delete_original_cb.isChecked())

    def onEffortToggled(self):
        self.effort_sb.setEnabled(not self.int_effort_cb.isChecked())

    def onLosslessToggled(self):
        lossless_checked = self.lossless_cb.isChecked()
        lossless_if_checked = self.lossless_if_cb.isChecked()

        self.wm.setEnabledByTag("quality_all", not (lossless_checked or lossless_if_checked))
        self.lossless_cb.setEnabled(not lossless_if_checked)
        self.lossless_if_cb.setEnabled(not lossless_checked)
        
        self.wm.setEnabledByTag("jxl_mode", not (lossless_checked or lossless_if_checked))        

    def resetToDefault(self):
        self.wm.cleanVars()

        if self.format_cmb.currentText() == "AVIF":
            self.quality_sl.setValue(70)
            self.effort_sb.setValue(6)
        else:
            self.quality_sl.setValue(80)
            self.effort_sb.setValue(7)
        
        self.int_effort_cb.setChecked(False)
        self.jxl_mode_cmb.setCurrentIndex(0)

        self.choose_output_src_rb.setChecked(True)

        self.delete_original_cb.setChecked(False)
        self.delete_original_cmb.setCurrentIndex(0)
        self.clear_after_conv_cb.setChecked(False)
        
        self.threads_sl.setValue(self.MAX_THREAD_COUNT - 1 if self.MAX_THREAD_COUNT > 0 else 1)  # -1 because the OS needs some CPU time as well
        self.duplicates_cmb.setCurrentIndex(1)

        # Lossless
        self.wm.setCheckedByTag("lossless", False)
        self.max_compression_cb.setChecked(False)

        # Smallest Lossless
        for i in self.wm.getWidgetsByTag("format_pool"):
            i.setChecked(True)
        
        self.reconstruct_jpg_cb.setChecked(True)
    
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
                self.wm.setVar("jxl_lossless_if", self.lossless_if_cb.isChecked())
                self.wm.setVar("jxl_mode", self.jxl_mode_cmb.currentText())
            case "AVIF":
                self.wm.setVar("avif_quality", self.quality_sl.value())
                self.wm.setVar("avif_speed", self.effort_sb.value())
            case "WEBP":
                self.wm.setVar("webp_quality", self.quality_sl.value())
                self.wm.setVar("webp_lossless", self.lossless_cb.isChecked())
                self.wm.setVar("webp_lossless_if", self.lossless_if_cb.isChecked())
            case "JPG":
                self.wm.setVar("jpg_quality", self.quality_sl.value())

    def loadFormatState(self):
        match self.prev_format:
            case "JPEG XL":
                self.wm.applyVar("jxl_quality", "quality_sl", 80)
                self.wm.applyVar("jxl_effort", "effort_sb", 7)
                self.wm.applyVar("jxl_lossless", "lossless_cb", False)
                self.wm.applyVar("jxl_lossless_if", "lossless_if_cb", False)
                self.wm.applyVar("jxl_mode", "jxl_mode_cmb", "Default")
            case "AVIF":
                self.wm.applyVar("avif_quality", "quality_sl", 70)
                self.wm.applyVar("avif_speed", "effort_sb", 6)
            case "WEBP":
                self.wm.applyVar("webp_quality", "quality_sl", 80)
                self.wm.applyVar("webp_lossless", "lossless_cb", False)
                self.wm.applyVar("webp_lossless_if", "lossless_if_cb", False)
            case "JPG":
                self.wm.applyVar("jpg_quality", "quality_sl", 80)

    def saveState(self):
        self.wm.disableAutoSaving([
            "quality_sb",
            "quality_sl",
            "effort_sb",
            "lossless_cb",
            "lossless_if_cb",
            "jxl_mode_cmb",
        ])

        self.saveFormatState()
        self.wm.saveState()