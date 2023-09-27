from WidgetManager import WidgetManager
import os

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
    QThreadPool,
    QObject,
    Signal
)

class Signals(QObject):
    convert = Signal()

class OutputTab(QWidget):
    def __init__(self, max_threads):
        super(OutputTab, self).__init__()

        self.signals = Signals()
        self.wm = WidgetManager("OutputTab")
        self.prev_format = None

        self.MAX_THREAD_COUNT = max_threads

        output_page_lt = QGridLayout()
        self.setLayout(output_page_lt)

        # Conversion Group
        conv_grp = QGroupBox("Conversion")
        conv_grp_lt = QVBoxLayout()
        conv_grp.setLayout(conv_grp_lt)

        threads_hb = QHBoxLayout()
        self.wm.addWidget("threads_sl", QSlider(Qt.Horizontal))
        self.wm.getWidget("threads_sl").setRange(1, self.MAX_THREAD_COUNT)
        self.wm.getWidget("threads_sl").setTickInterval(1)
        self.wm.getWidget("threads_sl").valueChanged.connect(self.onThreadCountChange)
        self.wm.addWidget("threads_l", QLabel("1"))
        threads_hb.addWidget(QLabel("Threads Used"))
        threads_hb.addWidget(self.wm.getWidget("threads_sl"))
        threads_hb.addWidget(self.wm.getWidget("threads_l"))

        duplicates_hb = QHBoxLayout()
        self.wm.addWidget("duplicates_cmb", QComboBox())
        self.wm.getWidget("duplicates_cmb").addItems(("Replace", "Rename", "Skip"))
        duplicates_hb.addWidget(QLabel("Duplicates"))
        duplicates_hb.addWidget(self.wm.getWidget("duplicates_cmb"))

        conv_grp_lt.addLayout(duplicates_hb)
        conv_grp_lt.addLayout(threads_hb)

        # After Conversion Group
        after_conv_grp = QGroupBox("After Conversion")
        after_conv_grp_lt = QVBoxLayout()
        after_conv_grp.setLayout(after_conv_grp_lt)

        self.wm.addWidget("clear_after_conv_cb", QCheckBox("Clear File List"))
        self.wm.addWidget("delete_original_cb", QCheckBox("Delete Original"))
        self.wm.addWidget("delete_original_cmb", QComboBox())

        self.wm.getWidget("delete_original_cmb").addItems(("To Trash", "Permanently"))
        self.wm.getWidget("delete_original_cb").stateChanged.connect(self.onDeleteOriginalChanged)

        after_conv_grp_lt.addWidget(self.wm.getWidget("clear_after_conv_cb"))
        delete_original_hb = QHBoxLayout()
        delete_original_hb.addWidget(self.wm.getWidget("delete_original_cb"))
        delete_original_hb.addWidget(self.wm.getWidget("delete_original_cmb"))
        after_conv_grp_lt.addLayout(delete_original_hb)

        # Output Group
        output_grp = QGroupBox("Save To")
        output_grp_lt = QVBoxLayout()
        output_grp.setLayout(output_grp_lt)

        self.wm.addWidget("choose_output_src_rb", QRadioButton("Source Folder"))
        self.wm.addWidget("choose_output_ct_rb", QRadioButton("Custom"))
        self.wm.addWidget("choose_output_ct_le", QLineEdit(), "output_ct")
        self.wm.addWidget("choose_output_ct_btn", QPushButton("...",clicked=self.chooseOutput), "output_ct")
        
        self.wm.getWidget("choose_output_ct_rb").toggled.connect(self.onOutputToggled)
        self.wm.getWidget("choose_output_ct_btn").setMaximumWidth(25)

        output_hb = QHBoxLayout()
        output_hb.addWidget(self.wm.getWidget("choose_output_ct_rb"))
        for i in self.wm.getWidgetsByTag("output_ct"):
            output_hb.addWidget(i)

        output_grp_lt.addWidget(self.wm.getWidget("choose_output_src_rb"))
        output_grp_lt.addLayout(output_hb)

        # Format Group
        format_grp = QGroupBox("Format")
        format_grp_lt = QVBoxLayout()
        format_grp.setLayout(format_grp_lt)

        self.wm.addWidget("quality_l", QLabel("Quality"))
        self.wm.addWidget("format_cmb", QComboBox())
        self.wm.getWidget("format_cmb").addItems(("JPEG XL","AVIF", "WEBP", "JPG", "PNG", "Smallest Lossless"))
        self.wm.getWidget("format_cmb").currentIndexChanged.connect(self.onFormatChange)

        self.wm.addWidget("effort_l", QLabel("Effort"), "effort")
        self.wm.addWidget("int_effort_cb", QCheckBox("Intelligent"), "effort")
        self.wm.addWidget("effort_sb", QSpinBox(), "effort")
        self.wm.getWidget("int_effort_cb").toggled.connect(self.onEffortToggled)

        self.wm.addWidget("quality_sb", QSpinBox(), "quality")
        self.wm.addWidget("quality_sl", QSlider(Qt.Horizontal), "quality")
        self.wm.getWidget("quality_sl").setTickInterval(5)

        self.wm.getWidget("quality_sl").valueChanged.connect(self.onQualitySlChanged)
        self.wm.getWidget("quality_sb").valueChanged.connect(self.onQualitySbChanged)

        # Lossless
        self.wm.addWidget("lossless_cb", QCheckBox("Lossless"), "lossless")
        self.wm.addWidget("lossless_if_cb", QCheckBox("Lossless (only if smaller)"), "lossless")
        self.wm.addWidget("max_compression_cb", QCheckBox("Max Compression"))

        self.wm.getWidget("lossless_if_cb").toggled.connect(self.onLosslessToggled)
        self.wm.getWidget("lossless_cb").toggled.connect(self.onLosslessToggled)

        lossless_hb = QHBoxLayout()
        lossless_hb.addWidget(self.wm.getWidget("lossless_cb"))
        lossless_hb.addWidget(self.wm.getWidget("lossless_if_cb"))
        lossless_hb.addWidget(self.wm.getWidget("max_compression_cb"))

        # Assemble Format UI
        format_cmb_hb = QHBoxLayout()
        format_cmb_hb.addWidget(QLabel("Format"))
        format_cmb_hb.addWidget(self.wm.getWidget("format_cmb"))
        format_grp_lt.addLayout(format_cmb_hb)

        effort_hb = QHBoxLayout()
        for i in self.wm.getWidgetsByTag("effort"):
            effort_hb.addWidget(i)
        format_grp_lt.addLayout(effort_hb)

        quality_hb = QHBoxLayout()
        quality_hb.addWidget(self.wm.getWidget("quality_l"))
        quality_hb.addWidget(self.wm.getWidget("quality_sl"))
        quality_hb.addWidget(self.wm.getWidget("quality_sb"))
        format_grp_lt.addLayout(quality_hb)
        
        # Smallest Lossless - Format Pool
        format_sm_l_hb = QHBoxLayout()

        self.wm.addWidget("smallest_lossless_png_cb", QCheckBox("PNG"), "format_pool")
        self.wm.addWidget("smallest_lossless_webp_cb", QCheckBox("WEBP"), "format_pool")
        self.wm.addWidget("smallest_lossless_jxl_cb", QCheckBox("JPEG XL"), "format_pool")
        
        for i in self.wm.getWidgetsByTag("format_pool"):
            format_sm_l_hb.addWidget(i)
        format_grp_lt.addLayout(format_sm_l_hb)

        # Lossless
        format_grp_lt.addLayout(lossless_hb)

        # Buttons
        reset_to_default_btn = QPushButton("Reset to Default")
        self.convert_btn_2 = QPushButton("Convert")
        
        reset_to_default_btn.clicked.connect(self.resetToDefault)
        self.convert_btn_2.clicked.connect(self.signals.convert.emit)

        output_page_lt.addWidget(reset_to_default_btn,2,0)
        output_page_lt.addWidget(self.convert_btn_2,2,1)

        # Group Positions
        output_page_lt.addWidget(format_grp,0,1)
        output_page_lt.addWidget(output_grp, 0, 0)
        output_page_lt.addWidget(conv_grp,1,0)
        output_page_lt.addWidget(after_conv_grp,1,1)

        # Size Policy
        output_page_lt.setAlignment(Qt.AlignTop)

        format_grp.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        conv_grp.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        after_conv_grp.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        output_grp.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)    # Minimum so it can spread vertically

        output_grp.setMaximumWidth(400)
        format_grp.setMaximumWidth(400)
        conv_grp.setMaximumWidth(400)
        after_conv_grp.setMaximumWidth(400)

        # Misc
        self.resetToDefault()
        self.wm.loadState()
        self.onFormatChange()
        self.onDeleteOriginalChanged()
        self.onOutputToggled()
        self.onQualitySbChanged()
        self.onQualitySlChanged()
    
    def isClearAfterConvChecked(self):
        return self.wm.getWidget("clear_after_conv_cb").isChecked()

    def getSettings(self):
        return {
            "format": self.wm.getWidget("format_cmb").currentText(),
            "quality": self.wm.getWidget("quality_sb").value(),
            "lossless": self.wm.getWidget("lossless_cb").isChecked(),
            "lossless_if_smaller": self.wm.getWidget("lossless_if_cb").isChecked(),
            "max_compression": self.wm.getWidget("max_compression_cb").isChecked(),
            "effort": self.wm.getWidget("effort_sb").value(),
            "intelligent_effort": self.wm.getWidget("int_effort_cb").isChecked(),
            "if_file_exists": self.wm.getWidget("duplicates_cmb").currentText(),
            "custom_output_dir": self.wm.getWidget("choose_output_ct_rb").isChecked(),
            "custom_output_dir_path": self.wm.getWidget("choose_output_ct_le").text(),
            "delete_original": self.wm.getWidget("delete_original_cb").isChecked(),
            "delete_original_mode": self.wm.getWidget("delete_original_cmb").currentText(),
            "smallest_format_pool": {
                "png": self.wm.getWidget("smallest_lossless_png_cb").isChecked(),
                "webp": self.wm.getWidget("smallest_lossless_webp_cb").isChecked(),
                "jxl": self.wm.getWidget("smallest_lossless_jxl_cb").isChecked()
                },
        }
    
    def onThreadCountChange(self):
        self.wm.getWidget("threads_l").setText(str(self.wm.getWidget("threads_sl").value()))

    def getUsedThreadCount(self):
        return self.wm.getWidget("threads_sl").value()
    
    def chooseOutput(self):
        dlg = QFileDialog()
        dlg.setWindowTitle("Choose Output Folder")
        dlg.setFileMode(QFileDialog.Directory)

        if dlg.exec():
            self.wm.getWidget("choose_output_ct_le").setText(dlg.selectedFiles()[0])

    def onOutputToggled(self):
        src_checked = self.wm.getWidget("choose_output_src_rb").isChecked()
        self.wm.setEnabledByTag("output_ct", not src_checked)
        
    def onFormatChange(self):
        self.saveFormatState()
        
        cur_format = self.wm.getWidget("format_cmb").currentText()
        self.prev_format = cur_format
        
        self.wm.setCheckedByTag("lossless", False)  # Widgets reenable themselves when you use setChecked() on a disabled widget, so this needs to stay in the beginning

        # Enable Lossless Mode
        self.wm.setEnabledByTag("lossless", cur_format in ("JPEG XL", "WEBP"))

        # Effort
        if cur_format in ("JPEG XL", "AVIF"):
            self.wm.getWidget("int_effort_cb").setEnabled(True)
            self.onEffortToggled()  # This is important to avoid issues with the effort_sb enabled state
        else:
            self.wm.getWidget("int_effort_cb").setEnabled(False)
            self.wm.getWidget("effort_sb").setEnabled(False)

        # Disable Quality Slider
        self.wm.setEnabledByTag("quality", not cur_format in ("PNG", "Smallest Lossless"))

        # Quality Slider Range and label
        if cur_format == "AVIF":
            self.wm.getWidget("quality_sl").setRange(-63, 0)
            self.wm.getWidget("quality_sb").setRange(0, 63)
            self.wm.getWidget("effort_sb").setRange(0, 10)
            self.wm.getWidget("quality_l").setText("Constant Quality")
            self.wm.getWidget("effort_l").setText("Speed")
            self.wm.getWidget("int_effort_cb").setText("Best Quality")
        else:
            if cur_format == "JPEG XL":
                self.setQualityRange(0, 99)
            else:
                self.setQualityRange(1, 100)
            self.wm.getWidget("effort_sb").setRange(1, 9)
            self.wm.getWidget("quality_l").setText("Quality")
            self.wm.getWidget("effort_l").setText("Effort")
            self.wm.getWidget("int_effort_cb").setText("Intelligent")
        
        # Smallest Lossless mode
        if cur_format == "Smallest Lossless":
            self.wm.setVisibleByTag("lossless", False)
            self.wm.setVisibleByTag("effort", False)
            self.wm.setVisibleByTag("format_pool", True)
            self.wm.getWidget("max_compression_cb").setVisible(True)
        else:
            self.wm.setVisibleByTag("lossless", True)
            self.wm.setVisibleByTag("effort", True)
            self.wm.setVisibleByTag("format_pool", False)
            self.wm.getWidget("max_compression_cb").setVisible(False)
        
        self.loadFormatState()
        

    def onQualitySlChanged(self):
        self.wm.getWidget("quality_sb").setValue(abs(self.wm.getWidget("quality_sl").value()))

    def onQualitySbChanged(self):
        if self.wm.getWidget("format_cmb").currentText() == "AVIF":
            self.wm.getWidget("quality_sl").setValue(-self.wm.getWidget("quality_sb").value())
        else:
            self.wm.getWidget("quality_sl").setValue(self.wm.getWidget("quality_sb").value())
    
    def onDeleteOriginalChanged(self):
        self.wm.getWidget("delete_original_cmb").setEnabled(self.wm.getWidget("delete_original_cb").isChecked())

    def onEffortToggled(self):
        self.wm.getWidget("effort_sb").setEnabled(not self.wm.getWidget("int_effort_cb").isChecked())

    def onLosslessToggled(self):
        if self.wm.getWidget("lossless_cb").isChecked():
            self.wm.setEnabledByTag("quality", False)
            self.wm.getWidget("lossless_if_cb").setEnabled(False)
        elif self.wm.getWidget("lossless_if_cb").isChecked():
            self.wm.getWidget("lossless_cb").setEnabled(False)
        else:
            self.wm.setEnabledByTag("quality", True)
            self.wm.setEnabledByTag("lossless", True)

    def resetToDefault(self):
        self.wm.cleanVars()

        if self.wm.getWidget("format_cmb").currentText() == "AVIF":
            self.wm.getWidget("quality_sl").setValue(-20)
            self.wm.getWidget("effort_sb").setValue(6)
        else:
            self.wm.getWidget("quality_sl").setValue(80)
            self.wm.getWidget("effort_sb").setValue(7)
        
        self.wm.getWidget("int_effort_cb").setChecked(False)

        self.wm.getWidget("choose_output_src_rb").setChecked(True)

        self.wm.getWidget("delete_original_cb").setChecked(False)
        self.wm.getWidget("delete_original_cmb").setCurrentIndex(0)
        self.wm.getWidget("clear_after_conv_cb").setChecked(False)
        
        self.wm.getWidget("threads_sl").setValue(self.MAX_THREAD_COUNT - 1 if self.MAX_THREAD_COUNT > 0 else 1)  # -1 because the OS needs some CPU time as well
        self.wm.getWidget("duplicates_cmb").setCurrentIndex(1)

        # Lossless
        self.wm.setCheckedByTag("lossless", False)
        self.wm.getWidget("max_compression_cb").setChecked(False)

        # Smallest Lossless
        for i in self.wm.getWidgetsByTag("format_pool"):
            i.setChecked(True)
    
    def setQualityRange(self, _min, _max):
        for i in self.wm.getWidgetsByTag("quality"):
            i.setRange(_min, _max)

    def saveFormatState(self):
        if self.prev_format == None:
            return

        match self.prev_format:
            case "JPEG XL":
                self.wm.setVar("jxl_quality", self.wm.getWidget("quality_sl").value())
                self.wm.setVar("jxl_effort", self.wm.getWidget("effort_sb").value())
                self.wm.setVar("jxl_int_effort", self.wm.getWidget("int_effort_cb").isChecked())
                self.wm.setVar("jxl_lossless", self.wm.getWidget("lossless_cb").isChecked())
                self.wm.setVar("jxl_lossless_if", self.wm.getWidget("lossless_if_cb").isChecked())
            case "AVIF":
                self.wm.setVar("avif_quality", self.wm.getWidget("quality_sl").value())
                self.wm.setVar("avif_speed", self.wm.getWidget("effort_sb").value())
                self.wm.setVar("avif_best_quality", self.wm.getWidget("int_effort_cb").isChecked())
            case "WEBP":
                self.wm.setVar("webp_quality", self.wm.getWidget("quality_sl").value())
                self.wm.setVar("webp_lossless", self.wm.getWidget("lossless_cb").isChecked())
                self.wm.setVar("webp_lossless_if", self.wm.getWidget("lossless_if_cb").isChecked())
            case "JPG":
                self.wm.setVar("jpg_quality", self.wm.getWidget("quality_sl").value())

    def loadFormatState(self):
        match self.prev_format:
            case "JPEG XL":
                self.wm.applyVar("jxl_quality", "quality_sl", 80)
                self.wm.applyVar("jxl_effort", "effort_sb", 7)
                self.wm.applyVar("jxl_int_effort", "int_effort_cb", False)
                self.wm.applyVar("jxl_lossless", "lossless_cb", False)
                self.wm.applyVar("jxl_lossless_if", "lossless_if_cb", False)
            case "AVIF":
                self.wm.applyVar("avif_quality", "quality_sl", -20)
                self.wm.applyVar("avif_speed", "effort_sb", 6)
                self.wm.applyVar("avif_best_quality", "int_effort_cb", False)
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
            "int_effort_cb",
            "lossless_cb",
            "lossless_if_cb",
        ])

        self.saveFormatState()
        self.wm.saveState()