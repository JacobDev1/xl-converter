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
)

from PySide6.QtCore import(
    Signal,
    QObject,
)

class Signals(QObject):
    all_resampling = Signal(bool)

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

        ui_lt_hbox = QHBoxLayout()
        self.wm.addWidget("ui_layout_l", QLabel("Layout"))
        self.wm.addWidget("ui_layout_cmb", QComboBox())
        self.wm.getWidget("ui_layout_cmb").addItems(("Horizontal", "Vertical"))
        ui_lt_hbox.addWidget(self.wm.getWidget("ui_layout_l"))
        ui_lt_hbox.addWidget(self.wm.getWidget("ui_layout_cmb"))
        gen_grp_lt.addLayout(ui_lt_hbox)

        self.wm.addWidget("sorting_cb", QCheckBox("Input - Disable Sorting"))
        gen_grp_lt.addWidget(self.wm.getWidget("sorting_cb"))

        # Conversion group
        conv_grp = QGroupBox("Conversion")
        conv_grp_lt = QVBoxLayout()
        conv_grp.setLayout(conv_grp_lt)

        self.wm.addWidget("all_resampling_cb", QCheckBox("Downscaling - More Resampling Methods"))
        self.wm.getWidget("all_resampling_cb").toggled.connect(self.signals.all_resampling.emit)
        conv_grp_lt.addWidget(self.wm.getWidget("all_resampling_cb"))

        logs__hbox = QHBoxLayout()
        self.wm.addWidget("logs_cb", QCheckBox("Enable Logs"))
        self.wm.addWidget("logs_open_btn", QPushButton("Open"))
        self.wm.addWidget("logs_wipe_btn", QPushButton("Wipe"))
        logs__hbox.addWidget(self.wm.getWidget("logs_cb"))
        logs__hbox.addWidget(self.wm.getWidget("logs_open_btn"))
        logs__hbox.addWidget(self.wm.getWidget("logs_wipe_btn"))
        gen_grp_lt.addLayout(logs__hbox)

        self.wm.addWidget("restore_defaults_btn", QPushButton("Reset to Default"))
        self.wm.getWidget("restore_defaults_btn").clicked.connect(self.resetToDefault)
        gen_grp_lt.addWidget(self.wm.getWidget("restore_defaults_btn"))

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
            }
        }
    
    def resetToDefault(self):
        self.wm.getWidget("ui_layout_cmb").setCurrentIndex(0)
        self.wm.getWidget("dark_theme_cb").setChecked(True)
        self.wm.getWidget("logs_cb").setChecked(False)
        self.wm.getWidget("sorting_cb").setChecked(False)
        self.wm.getWidget("all_resampling_cb").setChecked(False)