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
    QSpinBox
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
    def __init__(self):
        super(OutputTab, self).__init__()

        self.signals = Signals()

        self.threadpool = QThreadPool.globalInstance()
        self.MAX_THREAD_COUNT = self.threadpool.maxThreadCount()

        output_page_lt = QGridLayout()
        self.setLayout(output_page_lt)

        # Conversion Group
        conv_grp = QGroupBox("Conversion")
        conv_grp_layout = QVBoxLayout()
        conv_grp.setLayout(conv_grp_layout)
        
        self.if_file_exists_cmb = QComboBox()
        self.if_file_exists_cmb.addItems(("Replace", "Rename", "Skip"))
        self.conv_cores_sl = QSlider(Qt.Horizontal)
        self.conv_cores_sl.setTickPosition(QSlider.TicksBelow)
        self.conv_cores_sl.setRange(1,self.MAX_THREAD_COUNT)
        self.conv_cores_sl.setTickInterval(1)
        self.conv_cores_sl.valueChanged.connect(lambda: self.onThreadCountChange())

        if_file_exists_hbox = QHBoxLayout()
        if_file_exists_hbox.addWidget(QLabel("If File Already Exists"))
        if_file_exists_hbox.addWidget(self.if_file_exists_cmb)

        self.conv_cores_l = QLabel("1")
        conv_cores_hbox = QHBoxLayout()
        conv_cores_hbox.addWidget(QLabel("Threads Used"))
        conv_cores_hbox.addWidget(self.conv_cores_sl)
        conv_cores_hbox.addWidget(self.conv_cores_l)

        conv_grp_layout.addLayout(if_file_exists_hbox)
        conv_grp_layout.addLayout(conv_cores_hbox)
        output_page_lt.addWidget(conv_grp,1,0)

        # After Conversion Group
        after_conv_grp = QGroupBox("After Conversion")
        after_conv_grp_layout = QVBoxLayout()
        after_conv_grp.setLayout(after_conv_grp_layout)

        self.clear_after_conv_cb = QCheckBox()
        self.clear_after_conv_cb.setText("Clear File List")

        self.delete_original_cb = QCheckBox("Delete Original")
        self.delete_original_cmb = QComboBox()
        self.delete_original_cmb.addItems(("To Trash", "Permanently"))

        if self.delete_original_cb.isChecked() == False:
            self.delete_original_cmb.setEnabled(False)
        self.delete_original_cb.stateChanged.connect(lambda: self.delete_original_cmb.setEnabled(True) if self.delete_original_cb.isChecked() else self.delete_original_cmb.setEnabled(False))

        after_conv_grp_layout.addWidget(self.clear_after_conv_cb)
        delete_original_hbox = QHBoxLayout()
        delete_original_hbox.addWidget(self.delete_original_cb)
        delete_original_hbox.addWidget(self.delete_original_cmb)
        after_conv_grp_layout.addLayout(delete_original_hbox)
        output_page_lt.addWidget(after_conv_grp,1,1)

        # Output Group
        output_grp = QGroupBox("Where to Save Files")
        output_grp_layout = QVBoxLayout()
        output_grp.setLayout(output_grp_layout)

        self.choose_output_src = QRadioButton("Source Folder")
        self.choose_output_src.setChecked(True)

        self.choose_output_ct_rb = QRadioButton("Custom")
        self.choose_output_ct_rb.toggled.connect(self.toggleOutput)
        self.choose_output_ct_le = QLineEdit()
        self.choose_output_ct_le.setText(os.path.normpath(os.path.expanduser('~/Desktop/converted')))    # Placeholder
        self.choose_output_ct_btn = QPushButton("...",clicked=self.chooseOutput)
        self.choose_output_ct_btn.setMaximumWidth(25)

        if self.choose_output_src.isChecked():
            self.choose_output_ct_btn.setEnabled(False)
            self.choose_output_ct_le.setEnabled(False)

        output_grp_layout.addWidget(self.choose_output_src)
        choose_output_ct_hbox = QHBoxLayout()
        choose_output_ct_hbox.addWidget(self.choose_output_ct_rb)
        choose_output_ct_hbox.addWidget(self.choose_output_ct_le)
        choose_output_ct_hbox.addWidget(self.choose_output_ct_btn)
        output_grp_layout.addLayout(choose_output_ct_hbox)
        output_page_lt.addWidget(output_grp, 0, 0)

        # Format Group
        format_grp = QGroupBox("Format")
        format_grp_layout = QVBoxLayout()
        format_grp.setLayout(format_grp_layout)

        self.format_cmb = QComboBox()
        self.format_q_l = QLabel("Quality")
        self.format_cmb.addItems(("JPEG XL","AVIF", "WEBP", "JPG", "PNG"))
        self.format_cmb.currentIndexChanged.connect(self.onFormatChange)

        self.format_jxl_e_sb = QSpinBox()
        self.format_jxl_e_sb.setRange(1,9)
        self.format_e_l = QLabel("Effort")
        self.format_jxl_e_int_cb = QCheckBox("Intelligent")
        self.format_jxl_e_int_cb.toggled.connect(self.toggleEffort)

        self.format_jxl_q_sb = QSpinBox()
        self.format_jxl_q_sb.setRange(1,100)
        
        self.format_jxl_q_sl = QSlider(Qt.Horizontal)
        self.format_jxl_q_sl.setRange(1, 100)
        self.format_jxl_q_sl.setTickPosition(QSlider.TicksBelow)
        self.format_jxl_q_sl.setTickInterval(5)
        self.format_jxl_q_sl.valueChanged.connect(self.onQualitySlChange)
        self.format_jxl_q_sb.valueChanged.connect(self.onQualitySbChange)

        self.format_lossless_if_cb = QCheckBox("Lossless (only if smaller)")
        self.format_lossless_if_cb.toggled.connect(self.toggleLossless)
        self.format_jxl_q_lossless_cb = QCheckBox("Lossless")
        self.format_jxl_q_lossless_cb.toggled.connect(self.toggleLossless)
        format_lossless_hbox = QHBoxLayout()
        format_lossless_hbox.addWidget(self.format_jxl_q_lossless_cb)
        format_lossless_hbox.addWidget(self.format_lossless_if_cb)

        format_cmb_hbox = QHBoxLayout()
        format_cmb_hbox.addWidget(QLabel("Format"))
        format_cmb_hbox.addWidget(self.format_cmb)
        format_grp_layout.addLayout(format_cmb_hbox)

        format_jxl_e_hbox = QHBoxLayout()
        format_jxl_e_hbox.addWidget(self.format_e_l)
        format_jxl_e_hbox.addWidget(self.format_jxl_e_int_cb)
        format_jxl_e_hbox.addWidget(self.format_jxl_e_sb)
        format_grp_layout.addLayout(format_jxl_e_hbox)

        format_jxl_q_hbox = QHBoxLayout()
        format_jxl_q_hbox.addWidget(self.format_q_l)
        format_jxl_q_hbox.addWidget(self.format_jxl_q_sl)
        format_jxl_q_hbox.addWidget(self.format_jxl_q_sb)
        format_grp_layout.addLayout(format_jxl_q_hbox)
        format_grp_layout.addLayout(format_lossless_hbox)
        output_page_lt.addWidget(format_grp,0,1)

        # Buttons
        reset_to_default_btn = QPushButton("Reset to Default")
        reset_to_default_btn.clicked.connect(self.resetToDefault)
        self.convert_btn_2 = QPushButton("Convert")
        self.convert_btn_2.clicked.connect(lambda: self.signals.convert.emit())
        output_page_lt.addWidget(reset_to_default_btn,2,0)
        output_page_lt.addWidget(self.convert_btn_2,2,1)

        # Misc
        self.resetToDefault()
    
    def isClearAfterConvChecked(self):
        return self.clear_after_conv_cb.isChecked()

    def getSettings(self):
        parameters = {
            "format": self.format_cmb.currentText(),
            "quality": self.format_jxl_q_sb.value(),
            "lossless": self.format_jxl_q_lossless_cb.isChecked(),
            "lossless_if_smaller": self.format_lossless_if_cb.isChecked(),
            "effort": self.format_jxl_e_sb.value(),
            "intelligent_effort": self.format_jxl_e_int_cb.isChecked(),
            "if_file_exists": self.if_file_exists_cmb.currentText(),
            "custom_output_dir": self.choose_output_ct_rb.isChecked(),
            "custom_output_dir_path": self.choose_output_ct_le.text(),
            "delete_original": self.delete_original_cb.isChecked(),
            "delete_original_mode": self.delete_original_cmb.currentText()
        }
        return parameters
    
    def onThreadCountChange(self):
        self.conv_cores_l.setText(str(self.conv_cores_sl.value()))
        self.threadpool.setMaxThreadCount(self.conv_cores_sl.value())
    
    def chooseOutput(self):
        dlg = QFileDialog()
        dlg.setFileMode(QFileDialog.Directory)

        if dlg.exec():
            self.choose_output_ct_le.setText(dlg.selectedFiles()[0])

    def toggleOutput(self):
        if self.choose_output_ct_rb.isChecked():
            self.choose_output_ct_le.setEnabled(True)
            self.choose_output_ct_btn.setEnabled(True)
        else:
            self.choose_output_ct_le.setEnabled(False)
            self.choose_output_ct_btn.setEnabled(False)
        
    def onFormatChange(self):
        cur_format = self.format_cmb.currentText()
        
        self.format_jxl_q_lossless_cb.setChecked(False)     # It needs to in the beginning
        self.format_lossless_if_cb.setChecked(False)        # Widgets reenable themselves when you use setChecked() on a disabled widget

        # Enable Lossless Mode
        if cur_format in ("JPEG XL", "WEBP"):
            self.format_jxl_q_lossless_cb.setEnabled(True)
            self.format_lossless_if_cb.setEnabled(True)
        else:
            self.format_jxl_q_lossless_cb.setEnabled(False)
            self.format_lossless_if_cb.setEnabled(False)

        # Enable Effort Settings
        if cur_format == "JPEG XL":
            self.format_jxl_e_int_cb.setEnabled(True)
        else:
            self.format_jxl_e_int_cb.setEnabled(False)
        
        # Effort / Speed
        if cur_format in ("JPEG XL", "AVIF"):
            self.format_jxl_e_sb.setEnabled(True)
        else:
            self.format_jxl_e_sb.setEnabled(False)

        # Disable Quality Slider
        if cur_format == "PNG":
            self.format_jxl_q_sb.setEnabled(False)
            self.format_jxl_q_sl.setEnabled(False)
        else:
            self.format_jxl_q_sb.setEnabled(True)
            self.format_jxl_q_sl.setEnabled(True)
        
        # Quality Slider Range and label
        if cur_format == "AVIF":
            self.format_jxl_q_sl.setRange(-63, 0)
            self.format_jxl_q_sb.setRange(0, 63)
            self.format_jxl_e_sb.setRange(0, 10)
            self.format_jxl_e_sb.setValue(6)
            self.format_jxl_q_sl.setValue(-20)
            self.format_q_l.setText("Constant Quality")
            self.format_e_l.setText("Speed")
        else:
            self.format_jxl_q_sl.setRange(1, 100)
            self.format_jxl_q_sb.setRange(1, 100)
            self.format_jxl_e_sb.setRange(1, 9)
            self.format_jxl_e_sb.setValue(7)
            self.format_jxl_q_sl.setValue(80)
            self.format_q_l.setText("Quality")
            self.format_e_l.setText("Effort")

    def onQualitySlChange(self):
        self.format_jxl_q_sb.setValue(abs(self.format_jxl_q_sl.value()))

    def onQualitySbChange(self):
        if self.format_cmb.currentText() == "AVIF":
            self.format_jxl_q_sl.setValue(-self.format_jxl_q_sb.value())
        else:
            self.format_jxl_q_sl.setValue(self.format_jxl_q_sb.value())

    def toggleEffort(self):
        if self.format_jxl_e_sb.isEnabled():
            self.format_jxl_e_sb.setEnabled(False)
        else:
            self.format_jxl_e_sb.setEnabled(True)

    def toggleLossless(self):
        lossless = self.format_jxl_q_lossless_cb.isChecked()
        lossless_if = self.format_lossless_if_cb.isChecked()

        if lossless or lossless_if:
            self.format_jxl_q_sl.setEnabled(False)
            self.format_jxl_q_sb.setEnabled(False)
            if lossless:
                self.format_lossless_if_cb.setEnabled(False)
            elif lossless_if:
                self.format_jxl_q_lossless_cb.setEnabled(False)
        else:
            self.format_jxl_q_sl.setEnabled(True)
            self.format_jxl_q_sb.setEnabled(True)
            self.format_lossless_if_cb.setEnabled(True)
            self.format_jxl_q_lossless_cb.setEnabled(True)

    def resetToDefault(self):
        if self.format_cmb.currentText() == "AVIF":
            self.format_jxl_e_sb.setValue(6)
            self.format_jxl_q_sl.setValue(-20)
        else:
            self.format_jxl_e_sb.setValue(7)
            self.format_jxl_q_sl.setValue(80)

        self.choose_output_src.setChecked(True)
        self.delete_original_cb.setChecked(False)
        self.clear_after_conv_cb.setChecked(False)
        self.if_file_exists_cmb.setCurrentIndex(1)
        self.delete_original_cmb.setCurrentIndex(0)
        self.format_jxl_q_lossless_cb.setChecked(False)
        self.format_lossless_if_cb.setChecked(False)
        self.conv_cores_sl.setValue(self.MAX_THREAD_COUNT - 1 if self.MAX_THREAD_COUNT > 0 else 1)  # -1 because the OS needs some CPU time as well