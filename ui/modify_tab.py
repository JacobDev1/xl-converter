from data.constants import ALLOWED_RESAMPLING
from .widget_manager import WidgetManager

from PySide6.QtWidgets import(
    QWidget,
    QGridLayout,
    QHBoxLayout,
    QVBoxLayout,
    QPushButton,
    QComboBox,
    QVBoxLayout,
    QCheckBox,
    QLabel,
    QSpinBox,
    QGroupBox,
    QSizePolicy,
)

from PySide6.QtCore import(
    Qt,
    Signal
)

MAX_RES_PX = 999999999
MAX_FILE_SIZE = 1024**2   # KiB

class ModifyTab(QWidget):
    convert = Signal()

    def __init__(self, settings):
        super(ModifyTab, self).__init__()
        self.wm = WidgetManager("ModifyTab")

        # Set Main Layout
        tab_lt = QGridLayout()
        self.setLayout(tab_lt)
        
        self.downscaling_lt = QVBoxLayout()
        downscale_grp = QGroupBox("Downscaling")
        downscale_grp.setLayout(self.downscaling_lt)

        # Enable Downscaling
        self.downscale_cb = self.wm.addWidget("downscale_cb", QCheckBox("Downscale"))
        self.downscale_cb.stateChanged.connect(self.toggleDownscaleUI)

        self.downscaling_lt.addWidget(self.downscale_cb)

        # Scale by
        self.mode_hb = QHBoxLayout()

        self.mode_cmb = self.wm.addWidget("mode_cmb", QComboBox())
        self.mode_cmb.addItems((
            "Resolution",
            "Percent",
            "Shortest Side",
            "Longest Side",
            "File Size",
            ))
        self.mode_cmb.currentIndexChanged.connect(self.onModeChanged)

        self.mode_l = self.wm.addWidget("mode_l", QLabel("Scale to"))
        self.mode_hb.addWidget(self.mode_l)
        self.mode_hb.addWidget(self.mode_cmb)
        self.downscaling_lt.addLayout(self.mode_hb)

        # Percent
        percent_hb = QHBoxLayout()
        self.percent_l = self.wm.addWidget("percent_l", QLabel("Percent"))
        self.percent_sb = self.wm.addWidget("percent_sb", QSpinBox())
        
        self.percent_sb.setRange(1, 99)
        self.percent_sb.setSuffix(" %")
        
        percent_hb.addWidget(self.percent_l)
        percent_hb.addWidget(self.percent_sb)
        self.downscaling_lt.addLayout(percent_hb)

        # Resolution - Width
        pixel_w_hb = QHBoxLayout()
        self.pixel_w_l = self.wm.addWidget("pixel_w_l", QLabel("Max Width"))
        self.pixel_w_sb = self.wm.addWidget("pixel_w_sb", QSpinBox())

        self.pixel_w_sb.setRange(1, MAX_RES_PX)
        self.pixel_w_sb.setSuffix(" px")
        
        pixel_w_hb.addWidget(self.pixel_w_l)
        pixel_w_hb.addWidget(self.pixel_w_sb)
        self.downscaling_lt.addLayout(pixel_w_hb)
        
        # Resolution - Height
        pixel_h_hb = QHBoxLayout()
        self.pixel_h_l = self.wm.addWidget("pixel_h_l", QLabel("Max Height"))
        self.pixel_h_sb = self.wm.addWidget("pixel_h_sb", QSpinBox())

        self.pixel_h_sb.setRange(1, MAX_RES_PX)
        self.pixel_h_sb.setSuffix(" px")
        
        pixel_h_hb.addWidget(self.pixel_h_l)
        pixel_h_hb.addWidget(self.pixel_h_sb)
        self.downscaling_lt.addLayout(pixel_h_hb)

        # File Size
        file_size_hb = QHBoxLayout()
        self.file_size_l = self.wm.addWidget("file_size_l", QLabel("File Size"))
        self.file_size_sb = self.wm.addWidget("file_size_sb", QSpinBox())

        self.file_size_sb.setRange(1, MAX_FILE_SIZE)
        self.file_size_sb.setSuffix(" KiB")
        
        file_size_hb.addWidget(self.file_size_l)
        file_size_hb.addWidget(self.file_size_sb)
        self.downscaling_lt.addLayout(file_size_hb)

        # File Size - Step
        file_size_hb = QHBoxLayout()
        self.file_size_step_l = self.wm.addWidget("file_size_step_l", QLabel("Step"))
        self.file_size_step_sb = self.wm.addWidget("file_size_step_sb", QSpinBox())

        self.file_size_step_sb.setRange(1, 99)
        self.file_size_step_sb.setSuffix(" %")

        self.file_size_step_fast_cb = self.wm.addWidget("file_size_step_fast_cb", QCheckBox("Auto (Linear Regression)"))
        self.file_size_step_fast_cb.toggled.connect(self.toggleFastMode)

        file_size_hb.addWidget(self.file_size_step_l)
        file_size_hb.addWidget(self.file_size_step_fast_cb)
        file_size_hb.addWidget(self.file_size_step_sb)
        self.downscaling_lt.addLayout(file_size_hb)

        # Longest Side
        longest_hb = QHBoxLayout()
        self.longest_l = self.wm.addWidget("longest_l", QLabel("Max Size"))
        self.longest_sb = self.wm.addWidget("longest_sb", QSpinBox())
       
        self.longest_sb.setRange(1, MAX_RES_PX)
        self.longest_sb.setSuffix(" px")
        
        longest_hb.addWidget(self.longest_l)
        longest_hb.addWidget(self.longest_sb)
        self.downscaling_lt.addLayout(longest_hb)

        # Shortest Side
        shortest_hb = QHBoxLayout()
        self.shortest_l = self.wm.addWidget("shortest_l", QLabel("Max Size"))
        self.shortest_sb = self.wm.addWidget("shortest_sb", QSpinBox())

        self.shortest_sb.setRange(1, MAX_RES_PX)
        self.shortest_sb.setSuffix(" px")
        
        shortest_hb.addWidget(self.shortest_l)
        shortest_hb.addWidget(self.shortest_sb)
        self.downscaling_lt.addLayout(shortest_hb)

        # Resample
        resample_hb = QHBoxLayout()

        self.resample_l = self.wm.addWidget("resample_l", QLabel("Resample"))
        resample_hb.addWidget(self.resample_l)
        self.resample_cmb = self.wm.addWidget("resample_cmb", QComboBox())
        self.resample_cmb.addItem(("Default"))
        self.resample_cmb.addItems(ALLOWED_RESAMPLING)
        self.resample_visible = False

        resample_hb.addWidget(self.resample_cmb)
        self.downscaling_lt.addLayout(resample_hb)

        # Misc
        misc_grp = QGroupBox("Misc.")
        misc_grp_lt = QVBoxLayout()
        misc_grp.setLayout(misc_grp_lt)

        # Date / Time
        self.date_time_cb = self.wm.addWidget("date_time_cb", QCheckBox("Preserve Date && Time"))
        misc_grp_lt.addWidget(self.date_time_cb)

        # Metadata
        metadata_hb = QHBoxLayout()
        self.metadata_l = self.wm.addWidget("metadata_l", QLabel("Metadata"))
        self.metadata_cmb = self.wm.addWidget("metadata_cmb", QComboBox())
        self.metadata_cmb.addItems((
                "Up to Encoder - Wipe",
                "Up to Encoder - Preserve",
                "ExifTool - Safe Wipe",
                "ExifTool - Preserve",
                "ExifTool - Unsafe Wipe"
            ))

        metadata_hb.addWidget(self.metadata_l)
        metadata_hb.addWidget(self.metadata_cmb)
        misc_grp_lt.addLayout(metadata_hb)

        # Bottom
        default_btn = QPushButton("Reset to Default")
        default_btn.clicked.connect(self.resetToDefault)
        convert_btn = QPushButton("Convert")
        convert_btn.clicked.connect(self.convert.emit)

        tab_lt.addWidget(default_btn,2,0)
        tab_lt.addWidget(convert_btn,2,1)

        # Size Policy
        tab_lt.setAlignment(Qt.AlignTop)

        downscale_grp.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        misc_grp.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        misc_grp.setMaximumSize(400, 232)
        downscale_grp.setMaximumSize(400, 232)

        # Alignment
        metadata_hb.setAlignment(Qt.AlignLeft)

        # WidgetManager Tags
        self.wm.addTags("mode_cmb", "downscale_ui")
        self.wm.addTags("mode_l", "downscale_ui")

        self.wm.addTags("percent_l", "downscale_ui", "percent")
        self.wm.addTags("percent_sb", "downscale_ui", "percent")
        
        self.wm.addTags("pixel_h_l", "downscale_ui", "pixel")
        self.wm.addTags("pixel_h_sb", "downscale_ui", "pixel")
        self.wm.addTags("pixel_w_l", "downscale_ui", "pixel")
        self.wm.addTags("pixel_w_sb", "downscale_ui", "pixel")

        self.wm.addTags("file_size_l", "downscale_ui", "file_size")
        self.wm.addTags("file_size_sb", "downscale_ui", "file_size")
        self.wm.addTags("file_size_step_l", "downscale_ui", "file_size")
        self.wm.addTags("file_size_step_fast_cb", "downscale_ui", "file_size")
        self.wm.addTags("file_size_step_sb", "downscale_ui", "file_size")
        
        self.wm.addTags("shortest_l", "downscale_ui", "shortest")
        self.wm.addTags("shortest_sb", "downscale_ui", "shortest")

        self.wm.addTags("longest_l", "downscale_ui", "longest")
        self.wm.addTags("longest_sb", "downscale_ui", "longest")

        self.wm.addTags("resample_l", "downscale_ui", "resample")
        self.wm.addTags("resample_cmb", "downscale_ui", "resample")

        # Set Default
        self.resetToDefault()
        self.toggleDownscaleUI(False)
        self.wm.loadState()
        self.onModeChanged()
        self.toggleFastMode()

        # Apply Settings
        if settings["disable_downscaling_startup"]:
            self.disableDownscaling()
        self.toggleCustomResampling(settings["custom_resampling"])

        # Add to main layout
        tab_lt.addWidget(downscale_grp,0,0)
        tab_lt.addWidget(misc_grp,0,1)
    
    def toggleDownscaleUI(self, n):
        self.wm.setEnabledByTag("downscale_ui", n)
        self.toggleFastMode()
    
    def disableDownscaling(self):
        self.downscale_cb.setChecked(False)
    
    def toggleFastMode(self):
        if self.downscale_cb.isChecked():
            self.file_size_step_sb.setEnabled(not self.file_size_step_fast_cb.isChecked())

    def resetToDefault(self):
        self.disableDownscaling()
        self.metadata_cmb.setCurrentIndex(0)
        self.date_time_cb.setChecked(False)
        self.mode_cmb.setCurrentIndex(0)
        self.resample_cmb.setCurrentIndex(0)
        self.file_size_sb.setValue(300)
        self.file_size_step_sb.setValue(10)
        self.file_size_step_fast_cb.setChecked(True)
        self.percent_sb.setValue(80)
        self.pixel_w_sb.setValue(2000)
        self.pixel_h_sb.setValue(2000)
        self.shortest_sb.setValue(1080)
        self.longest_sb.setValue(1920)
    
    def onModeChanged(self):
        index = self.mode_cmb.currentText()
        self.wm.setVisibleByTag("percent", index == "Percent")
        self.wm.setVisibleByTag("pixel", index == "Resolution")
        self.wm.setVisibleByTag("file_size", index == "File Size")
        self.wm.setVisibleByTag("shortest", index == "Shortest Side")
        self.wm.setVisibleByTag("longest", index == "Longest Side")
    
    def getSettings(self):
        return {
            "downscaling": {
                "enabled": self.downscale_cb.isChecked(),
                "mode": self.mode_cmb.currentText(),
                "percent": self.percent_sb.value(),
                "file_size_step": self.file_size_step_sb.value(),
                "file_size_step_fast": self.file_size_step_fast_cb.isChecked(),
                "width": self.pixel_w_sb.value(),
                "height": self.pixel_h_sb.value(),
                "file_size": self.file_size_sb.value(),
                "shortest_side": self.shortest_sb.value(),
                "longest_side": self.longest_sb.value(),
                "resample": self.getResampling(),
            },
            "misc": {
                "keep_metadata": self.metadata_cmb.currentText(),
                "attributes": self.date_time_cb.isChecked(),
            }
        }
    
    def getResampling(self):
        if self.resample_visible:
            return self.resample_cmb.currentText()
        else:
            return "Default"

    def toggleCustomResampling(self, enabled=False):
        self.resample_visible = enabled
        if enabled:
            self.wm.setVisibleByTag("resample", True)
        else:
            self.wm.setVisibleByTag("resample", False)