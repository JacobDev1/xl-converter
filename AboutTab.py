from PySide6.QtWidgets import(
    QWidget,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton
)

from PySide6.QtCore import(
    Qt,
    QUrl
)

from PySide6.QtGui import (
    QDesktopServices
)

class AboutTab(QWidget):
    def __init__(self):
        super(AboutTab, self).__init__()

        about_tab_lt = QGridLayout()
        self.setLayout(about_tab_lt)

        # Left Side
        credits_l = QLabel("<h3><a href=\"https://codepoems.eu\">CodePoems.eu</a></h3>Version 0.6<br>contact@codepoems.eu<br>XL Converter is licensed under <a href=\"LICENSE.txt\">GPL v3</a><br><a href=\"LICENSE_3RD_PARTY.txt\">3rd party licenses")
        credits_l.setAlignment(Qt.AlignCenter)
        credits_l.setOpenExternalLinks(True)
        about_tab_lt.addWidget(credits_l,0,0)

        # Right Side
        about_tab_btn_lt = QHBoxLayout()
        about_tab_btn_lt.addWidget(QPushButton("Donate", clicked=lambda: QDesktopServices.openUrl(QUrl("https://liberapay.com/CodePoems/donate"))))
        about_tab_btn_lt.addWidget(QPushButton("My Website", clicked=lambda: QDesktopServices.openUrl(QUrl("https://codepoems.eu"))))

        about_tab_lt.addLayout(about_tab_btn_lt,0,1)