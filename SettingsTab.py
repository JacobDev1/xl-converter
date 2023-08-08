import qdarktheme

from PySide6.QtWidgets import(
    QWidget,
    QGridLayout,
    QCheckBox
)

class SettingsTab(QWidget):
    def __init__(self):
        super(SettingsTab, self).__init__()

        settings_l = QGridLayout()
        self.setLayout(settings_l)

        dark_theme_cb = QCheckBox("Dark Theme")
        dark_theme_cb.setChecked(True)
        dark_theme_cb.clicked.connect(lambda: qdarktheme.setup_theme("dark", corner_shape="sharp", custom_colors={"primary":"#F18000"}) if dark_theme_cb.isChecked() else qdarktheme.setup_theme("light", corner_shape="sharp", custom_colors={"primary":"#EF7202"}))

        settings_l.addWidget(dark_theme_cb, 0, 0)