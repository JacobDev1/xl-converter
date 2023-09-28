from VARIABLES import ALLOWED_RESAMPLING
from WidgetManager import WidgetManager

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
        self.wm.addWidget("downscale_cb", QCheckBox("Downscale"))
        self.wm.getWidget("downscale_cb").stateChanged.connect(self.toggleDownscaleUI)

        self.downscaling_lt.addWidget(self.wm.getWidget("downscale_cb"))

        # Scale by
        self.mode_hb = QHBoxLayout()

        self.wm.addWidget("mode_cmb", QComboBox())
        self.wm.getWidget("mode_cmb").addItems(("Max File Size", "Percent", "Max Resolution", "Shortest Side", "Longest Side"))
        self.wm.getWidget("mode_cmb").currentIndexChanged.connect(self.onModeChanged)

        self.mode_hb.addWidget(QLabel("Scale to"))
        self.mode_hb.addWidget(self.wm.getWidget("mode_cmb"))
        self.downscaling_lt.addLayout(self.mode_hb)

        # Percent
        percent_hb = QHBoxLayout()
        self.wm.addWidget("percent_l", QLabel("Percent"))
        self.wm.addWidget("percent_sb", QSpinBox())
        
        self.wm.getWidget("percent_sb").setRange(1, 99)
        self.wm.getWidget("percent_sb").setSuffix(" %")
        
        percent_hb.addWidget(self.wm.getWidget("percent_l"))
        percent_hb.addWidget(self.wm.getWidget("percent_sb"))
        self.downscaling_lt.addLayout(percent_hb)

        # Max Resolution - Width
        pixel_w_hb = QHBoxLayout()
        self.wm.addWidget("pixel_w_l", QLabel("Max Width"))
        self.wm.addWidget("pixel_w_sb", QSpinBox())

        self.wm.getWidget("pixel_w_sb").setRange(1, MAX_RES_PX)
        self.wm.getWidget("pixel_w_sb").setSuffix(" px")
        
        pixel_w_hb.addWidget(self.wm.getWidget("pixel_w_l"))
        pixel_w_hb.addWidget(self.wm.getWidget("pixel_w_sb"))
        self.downscaling_lt.addLayout(pixel_w_hb)
        
        # Max Resolution - Height
        pixel_h_hb = QHBoxLayout()
        self.wm.addWidget("pixel_h_l", QLabel("Max Height"))
        self.wm.addWidget("pixel_h_sb", QSpinBox())

        self.wm.getWidget("pixel_h_sb").setRange(1, MAX_RES_PX)
        self.wm.getWidget("pixel_h_sb").setSuffix(" px")
        
        pixel_h_hb.addWidget(self.wm.getWidget("pixel_h_l"))
        pixel_h_hb.addWidget(self.wm.getWidget("pixel_h_sb"))
        self.downscaling_lt.addLayout(pixel_h_hb)

        # File Size
        file_size_hb = QHBoxLayout()
        self.wm.addWidget("file_size_l", QLabel("Max File Size"))
        self.wm.addWidget("file_size_sb", QSpinBox())

        self.wm.getWidget("file_size_sb").setRange(1, MAX_FILE_SIZE)
        self.wm.getWidget("file_size_sb").setSuffix(" KiB")
        
        file_size_hb.addWidget(self.wm.getWidget("file_size_l"))
        file_size_hb.addWidget(self.wm.getWidget("file_size_sb"))
        self.downscaling_lt.addLayout(file_size_hb)

        # File Size - Step
        file_size_hb = QHBoxLayout()
        self.wm.addWidget("file_size_step_l", QLabel("Step"))
        self.wm.addWidget("file_size_step_sb", QSpinBox())

        self.wm.getWidget("file_size_step_sb").setRange(1, 99)
        self.wm.getWidget("file_size_step_sb").setSuffix(" %")
        
        file_size_hb.addWidget(self.wm.getWidget("file_size_step_l"))
        file_size_hb.addWidget(self.wm.getWidget("file_size_step_sb"))
        self.downscaling_lt.addLayout(file_size_hb)

        # Longest Side
        longest_hb = QHBoxLayout()
        self.wm.addWidget("longest_l", QLabel("Max Size"))
        self.wm.addWidget("longest_sb", QSpinBox())
       
        self.wm.getWidget("longest_sb").setRange(1, MAX_RES_PX)
        self.wm.getWidget("longest_sb").setSuffix(" px")
        
        longest_hb.addWidget(self.wm.getWidget("longest_l"))
        longest_hb.addWidget(self.wm.getWidget("longest_sb"))
        self.downscaling_lt.addLayout(longest_hb)

        # Shortest Side
        shortest_hb = QHBoxLayout()
        self.wm.addWidget("shortest_l", QLabel("Max Size"))
        self.wm.addWidget("shortest_sb", QSpinBox())

        self.wm.getWidget("shortest_sb").setRange(1, MAX_RES_PX)
        self.wm.getWidget("shortest_sb").setSuffix(" px")
        
        shortest_hb.addWidget(self.wm.getWidget("shortest_l"))
        shortest_hb.addWidget(self.wm.getWidget("shortest_sb"))
        self.downscaling_lt.addLayout(shortest_hb)

        # Resample
        resample_hb = QHBoxLayout()
        resample_hb.addWidget(QLabel("Resample"))
        self.wm.addWidget("resample_cmb", QComboBox())

        self.addResampling(settings["settings"]["all_resampling"])

        resample_hb.addWidget(self.wm.getWidget("resample_cmb"))
        self.downscaling_lt.addLayout(resample_hb)

        # Misc
        misc_grp = QGroupBox("Misc.")
        misc_grp_lt = QVBoxLayout()
        misc_grp.setLayout(misc_grp_lt)

        # Metadata
        # self.metadata_cb = QCheckBox("Preserve Metadata")
        # misc_grp_lt.addWidget(self.metadata_cb)

        # Date / Time
        self.wm.addWidget("date_time_cb", QCheckBox("Preserve Date && Time"))
        misc_grp_lt.addWidget(self.wm.getWidget("date_time_cb"))

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

        # WidgetManager Tags
        self.wm.addTags("mode_cmb", "downscale_ui")
        self.wm.addTags("resample_cmb", "downscale_ui")

        self.wm.addTags("percent_l", "percent")
        self.wm.addTags("percent_sb", "downscale_ui", "percent")
        
        self.wm.addTags("pixel_h_l", "pixel")
        self.wm.addTags("pixel_h_sb", "downscale_ui", "pixel")
        self.wm.addTags("pixel_w_l", "pixel")
        self.wm.addTags("pixel_w_sb", "downscale_ui", "pixel")

        self.wm.addTags("file_size_l", "file_size")
        self.wm.addTags("file_size_sb", "downscale_ui", "file_size")
        self.wm.addTags("file_size_step_l", "file_size")
        self.wm.addTags("file_size_step_sb", "downscale_ui", "file_size")
        
        self.wm.addTags("shortest_l", "shortest")
        self.wm.addTags("shortest_sb", "downscale_ui", "shortest")

        self.wm.addTags("longest_l", "longest")
        self.wm.addTags("longest_sb", "downscale_ui", "longest")

        # Set Default
        self.resetToDefault()
        self.toggleDownscaleUI(False)
        self.wm.loadState()
        self.onModeChanged()

        # Add to main layout
        tab_lt.addWidget(downscale_grp,0,0)
        tab_lt.addWidget(misc_grp,0,1)
    
    def toggleDownscaleUI(self, n):
        self.wm.setEnabledByTag("downscale_ui", n)

    def resetToDefault(self):
        self.wm.getWidget("mode_cmb").setCurrentIndex(0)
        self.wm.getWidget("resample_cmb").setCurrentIndex(0)
        self.wm.getWidget("file_size_sb").setValue(300)
        self.wm.getWidget("file_size_step_sb").setValue(10)
        self.wm.getWidget("percent_sb").setValue(80)
        self.wm.getWidget("pixel_w_sb").setValue(2000)
        self.wm.getWidget("pixel_h_sb").setValue(2000)
        self.wm.getWidget("shortest_sb").setValue(1080)
        self.wm.getWidget("longest_sb").setValue(1920)
    
    def onModeChanged(self):
        index = self.wm.getWidget("mode_cmb").currentText()
        self.wm.setVisibleByTag("percent", index == "Percent")
        self.wm.setVisibleByTag("pixel", index == "Max Resolution")
        self.wm.setVisibleByTag("file_size", index == "Max File Size")
        self.wm.setVisibleByTag("shortest", index == "Shortest Side")
        self.wm.setVisibleByTag("longest", index == "Longest Side")
    
    def getSettings(self):
        return {
            "downscaling": {
                "enabled": self.wm.getWidget("downscale_cb").isChecked(),
                "mode": self.wm.getWidget("mode_cmb").currentText(),
                "percent": self.wm.getWidget("percent_sb").value(),
                "file_size_step": self.wm.getWidget("file_size_step_sb").value(),
                "width": self.wm.getWidget("pixel_w_sb").value(),
                "height": self.wm.getWidget("pixel_w_sb").value(),
                "file_size": self.wm.getWidget("file_size_sb").value(),
                "shortest_side": self.wm.getWidget("shortest_sb").value(),
                "longest_side": self.wm.getWidget("longest_sb").value(),
                "resample": self.wm.getWidget("resample_cmb").currentText(),
            },
            "misc": {
                # "metadata": self.metadata_cb.isChecked(),
                "attributes": self.wm.getWidget("date_time_cb").isChecked(),
            }
        }
    
    def addResampling(self, _all=False):
        self.wm.getWidget("resample_cmb").clear()
        if _all:
            self.wm.getWidget("resample_cmb").addItem(("Default"))
            self.wm.getWidget("resample_cmb").addItems(ALLOWED_RESAMPLING)
        else:
            self.wm.getWidget("resample_cmb").addItems(("Default", "Lanczos", "Point", "Box"))