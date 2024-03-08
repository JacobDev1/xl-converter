import os

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

from core.utils import setTheme
from .widget_manager import WidgetManager

class Signals(QObject):
    custom_resampling = Signal(bool)
    disable_sorting = Signal(bool)
    save_file_list = Signal()
    load_file_list = Signal()
    no_exceptions = Signal(bool)
    enable_jxl_effort_10 = Signal(bool)

class SettingsTab(QWidget):
    def __init__(self):
        super(SettingsTab, self).__init__()

        tab_lt = QGridLayout()
        self.setLayout(tab_lt)

        self.wm = WidgetManager("SettingsTab")
        self.signals = Signals()

        # General group - widgets
        self.dark_theme_cb = self.wm.addWidget("dark_theme_cb", QCheckBox("Dark Theme"))
        self.dark_theme_cb.toggled.connect(self.setDarkModeEnabled)

        self.disable_downscaling_startup_cb = self.wm.addWidget("disable_downscaling_startup_cb", QCheckBox("Disable Downscaling on Startup"))
        self.disable_delete_startup_cb = self.wm.addWidget("disable_delete_startup_cb", QCheckBox("Disable Delete Original on Startup"))

        self.no_exceptions_cb = self.wm.addWidget("no_exceptions_cb", QCheckBox("Disable Exception Popups"))
        self.no_exceptions_cb.toggled.connect(self.signals.no_exceptions)

        self.no_sorting_cb = self.wm.addWidget("no_sorting_cb", QCheckBox("Input - Disable Sorting"))
        self.no_sorting_cb.toggled.connect(self.signals.disable_sorting)

        # General group - layout
        gen_grp = QGroupBox("General")
        gen_grp_lt = QVBoxLayout()
        gen_grp.setLayout(gen_grp_lt)

        gen_grp_lt.addWidget(self.dark_theme_cb)
        gen_grp_lt.addWidget(self.disable_downscaling_startup_cb)
        gen_grp_lt.addWidget(self.disable_delete_startup_cb)
        gen_grp_lt.addWidget(self.no_exceptions_cb)
        gen_grp_lt.addWidget(self.no_sorting_cb)

        # Advanced group - widgets
        self.enable_jxl_effort_10 = self.wm.addWidget("enable_jxl_effort_10", QCheckBox("JPEG XL - Enable Effort 10 (slow)"))
        self.enable_jxl_effort_10.clicked.connect(self.signals.enable_jxl_effort_10)

        self.disable_jxl_utf8_check_cb = self.wm.addWidget("disable_jxl_utf8_check_cb", QCheckBox("JPEG XL - Disable UTF-8 Check"))

        self.custom_resampling_cb = self.wm.addWidget("custom_resampling_cb", QCheckBox("Downscaling - Custom Resampling"))
        self.custom_resampling_cb.toggled.connect(self.signals.custom_resampling.emit)

        self.file_list_save_btn = QPushButton("Save")
        self.file_list_load_btn = QPushButton("Load")
        self.file_list_save_btn.clicked.connect(self.signals.save_file_list)
        self.file_list_load_btn.clicked.connect(self.signals.load_file_list)

        # Advanced group - layout
        conv_grp = QGroupBox("Advanced")
        conv_grp_lt = QVBoxLayout()
        conv_grp.setLayout(conv_grp_lt)

        if os.name == "nt":
            conv_grp_lt.addWidget(self.disable_jxl_utf8_check_cb)
        
        conv_grp_lt.addWidget(self.enable_jxl_effort_10)
        conv_grp_lt.addWidget(self.custom_resampling_cb)
        
        file_list_hbox = QHBoxLayout()
        self.file_list_l = QLabel("File List")
        file_list_hbox.addWidget(self.file_list_l)
        file_list_hbox.addWidget(self.file_list_save_btn)
        file_list_hbox.addWidget(self.file_list_load_btn)
        
        conv_grp_lt.addLayout(file_list_hbox)

        # Bottom
        self.restore_defaults_btn = QPushButton("Reset to Default")
        self.restore_defaults_btn.clicked.connect(self.resetToDefault)
        tab_lt.addWidget(self.restore_defaults_btn,1,0,1,0)

        # Size Policy
        tab_lt.setAlignment(Qt.AlignTop)

        gen_grp.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        conv_grp.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Main Layout
        tab_lt.addWidget(gen_grp, 0, 0)
        tab_lt.addWidget(conv_grp, 0, 1)

        # Misc.
        self.resetToDefault()
        self.wm.loadState()

        # Apply Settings
        self.setDarkModeEnabled(self.dark_theme_cb.isChecked())
    
    def setDarkModeEnabled(self, enabled):
        if enabled:
            setTheme("dark")
        else:
            setTheme("light")        

    def setExceptionsEnabled(self, enabled):
        self.blockSignals(True)
        self.no_exceptions_cb.setChecked(enabled)
        self.blockSignals(False)

    def getSettings(self):
        return {
            "custom_resampling": self.custom_resampling_cb.isChecked(),
            "sorting_disabled": self.no_sorting_cb.isChecked(),
            "disable_downscaling_startup": self.disable_downscaling_startup_cb.isChecked(),
            "disable_delete_startup": self.disable_delete_startup_cb.isChecked(),
            "no_exceptions": self.no_exceptions_cb.isChecked(),
            "disable_jxl_utf8_check": self.disable_jxl_utf8_check_cb.isChecked(),
            "enable_jxl_effort_10": self.enable_jxl_effort_10.isChecked(),
        }
    
    def resetToDefault(self):
        self.dark_theme_cb.setChecked(True)
        self.no_sorting_cb.setChecked(False)
        
        self.enable_jxl_effort_10.setChecked(False)
        self.custom_resampling_cb.setChecked(False)
        self.disable_downscaling_startup_cb.setChecked(True)
        self.disable_delete_startup_cb.setChecked(True)
        self.no_exceptions_cb.setChecked(False)
        self.disable_jxl_utf8_check_cb.setChecked(False)