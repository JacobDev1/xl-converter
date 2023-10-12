from HelperFunctions import setTheme
from WidgetManager import WidgetManager

from PySide6.QtWidgets import(
    QWidget,
    QGridLayout,
    QVBoxLayout,
    QHBoxLayout,
    QCheckBox,
    QGroupBox,
    QPushButton,
    QLineEdit,
    QComboBox,
    QLabel,
    QSizePolicy,
)

from PySide6.QtCore import(
    Signal,
    QObject,
    Qt,
)

class Signals(QObject):
    all_resampling = Signal(bool)
    disable_sorting = Signal(bool)

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

        self.wm.addWidget("no_exceptions_cb", QCheckBox("Disable Exception Popups"))
        gen_grp_lt.addWidget(self.wm.getWidget("no_exceptions_cb"))

        self.wm.addWidget("sorting_cb", QCheckBox("Input - Disable Sorting"))
        self.wm.getWidget("sorting_cb").toggled.connect(self.signals.disable_sorting)
        gen_grp_lt.addWidget(self.wm.getWidget("sorting_cb"))

        # Conversion group
        conv_grp = QGroupBox("Downscaling")
        conv_grp_lt = QVBoxLayout()
        conv_grp.setLayout(conv_grp_lt)

        self.wm.addWidget("all_resampling_cb", QCheckBox("All Resampling Methods"))
        self.wm.getWidget("all_resampling_cb").toggled.connect(self.signals.all_resampling.emit)
        conv_grp_lt.addWidget(self.wm.getWidget("all_resampling_cb"))

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
            "settings": {
                "all_resampling": self.wm.getWidget("all_resampling_cb").isChecked(),
                "sorting_disabled": self.wm.getWidget("sorting_cb").isChecked(),
                "disable_downscaling_startup": self.wm.getWidget("disable_downscaling_startup_cb").isChecked(),
                "no_exceptions": self.wm.getWidget("no_exceptions_cb").isChecked()
            }
        }
    
    def resetToDefault(self):
        self.wm.getWidget("dark_theme_cb").setChecked(True)
        # self.wm.getWidget("logs_cb").setChecked(False)
        self.wm.getWidget("sorting_cb").setChecked(False)
        self.wm.getWidget("all_resampling_cb").setChecked(False)
        self.wm.getWidget("disable_downscaling_startup_cb").setChecked(True)