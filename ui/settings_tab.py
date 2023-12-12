from core.utils import setTheme
from .widget_manager import WidgetManager

from PySide6.QtWidgets import(
    QWidget,
    QGridLayout,
    QVBoxLayout,
    QHBoxLayout,
    QCheckBox,
    QGroupBox,
    QPushButton,
    QLabel,
    QSizePolicy,
)

from PySide6.QtCore import(
    Signal,
    QObject,
    Qt,
)

class Signals(QObject):
    custom_resampling = Signal(bool)
    disable_sorting = Signal(bool)
    save_file_list = Signal()
    load_file_list = Signal()

class SettingsTab(QWidget):
    def __init__(self):
        super(SettingsTab, self).__init__()

        tab_lt = QGridLayout()
        self.setLayout(tab_lt)

        self.wm = WidgetManager("SettingsTab")
        self.signals = Signals()

        # General group
        gen_grp = QGroupBox("General")
        gen_grp_lt = QVBoxLayout()
        gen_grp.setLayout(gen_grp_lt)

        self.wm.addWidget("dark_theme_cb", QCheckBox("Dark Theme"))
        self.wm.getWidget("dark_theme_cb").toggled.connect(self.toggleTheme)
        gen_grp_lt.addWidget(self.wm.getWidget("dark_theme_cb"))

        self.wm.addWidget("disable_downscaling_startup_cb", QCheckBox("Disable Downscaling on Startup"))
        gen_grp_lt.addWidget(self.wm.getWidget("disable_downscaling_startup_cb"))
        
        self.wm.addWidget("disable_delete_startup_cb", QCheckBox("Disable Delete Original on Startup"))
        gen_grp_lt.addWidget(self.wm.getWidget("disable_delete_startup_cb"))

        self.wm.addWidget("no_exceptions_cb", QCheckBox("Disable Exception Popups"))
        gen_grp_lt.addWidget(self.wm.getWidget("no_exceptions_cb"))

        self.wm.addWidget("no_sorting_cb", QCheckBox("Input - Disable Sorting"))
        self.wm.getWidget("no_sorting_cb").toggled.connect(self.signals.disable_sorting)
        gen_grp_lt.addWidget(self.wm.getWidget("no_sorting_cb"))

        # Conversion group
        conv_grp = QGroupBox("Conversion")
        conv_grp_lt = QVBoxLayout()
        conv_grp.setLayout(conv_grp_lt)

        self.wm.addWidget("custom_resampling_cb", QCheckBox("Downscaling - Custom Resampling"))
        self.wm.getWidget("custom_resampling_cb").toggled.connect(self.signals.custom_resampling.emit)
        conv_grp_lt.addWidget(self.wm.getWidget("custom_resampling_cb"))

        # File List
        file_list_hbox = QHBoxLayout()
        self.wm.addWidget("file_list_l", QLabel("File List"))
        self.wm.addWidget("file_list_save_btn", QPushButton("Save"))
        self.wm.getWidget("file_list_save_btn").clicked.connect(self.signals.save_file_list)
        self.wm.addWidget("file_list_load_btn", QPushButton("Load"))
        self.wm.getWidget("file_list_load_btn").clicked.connect(self.signals.load_file_list)
        file_list_hbox.addWidget(self.wm.getWidget("file_list_l"))
        file_list_hbox.addWidget(self.wm.getWidget("file_list_save_btn"))
        file_list_hbox.addWidget(self.wm.getWidget("file_list_load_btn"))
        conv_grp_lt.addLayout(file_list_hbox)

        # logs_hbox = QHBoxLayout()
        # self.wm.addWidget("logs_cb", QCheckBox("Enable Logs"))
        # self.wm.addWidget("logs_open_btn", QPushButton("Open"))
        # self.wm.addWidget("logs_wipe_btn", QPushButton("Wipe"))
        # logs_hbox.addWidget(self.wm.getWidget("logs_cb"))
        # logs_hbox.addWidget(self.wm.getWidget("logs_open_btn"))
        # logs_hbox.addWidget(self.wm.getWidget("logs_wipe_btn"))
        # gen_grp_lt.addLayout(logs_hbox)

        # Bottom
        self.wm.addWidget("restore_defaults_btn", QPushButton("Reset to Default"))
        self.wm.getWidget("restore_defaults_btn").clicked.connect(self.resetToDefault)
        tab_lt.addWidget(self.wm.getWidget("restore_defaults_btn"),1,0,1,0)

        # Size Policy
        tab_lt.setAlignment(Qt.AlignTop)

        gen_grp.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        conv_grp.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        gen_grp.setMaximumSize(400, 232)
        conv_grp.setMaximumSize(400, 232)

        # Main Layout
        tab_lt.addWidget(gen_grp, 0, 0)
        tab_lt.addWidget(conv_grp, 0, 1)

        # Misc.
        self.resetToDefault()
        self.wm.loadState()
    
    def toggleTheme(self, enabled):
        if enabled:
            setTheme("dark")
        else:
            setTheme("light")        

    def getSettings(self):
        return {
            "custom_resampling": self.wm.getWidget("custom_resampling_cb").isChecked(),
            "sorting_disabled": self.wm.getWidget("no_sorting_cb").isChecked(),
            "disable_downscaling_startup": self.wm.getWidget("disable_downscaling_startup_cb").isChecked(),
            "disable_delete_startup": self.wm.getWidget("disable_delete_startup_cb").isChecked(),
            "no_exceptions": self.wm.getWidget("no_exceptions_cb").isChecked(),
        }
    
    def resetToDefault(self):
        self.wm.getWidget("dark_theme_cb").setChecked(True)
        # self.wm.getWidget("logs_cb").setChecked(False)
        self.wm.getWidget("no_sorting_cb").setChecked(False)
        
        self.wm.getWidget("custom_resampling_cb").setChecked(False)
        self.wm.getWidget("disable_downscaling_startup_cb").setChecked(True)
        self.wm.getWidget("disable_delete_startup_cb").setChecked(True)