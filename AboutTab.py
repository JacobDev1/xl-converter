from VARIABLES import VERSION

from PySide6.QtWidgets import(
    QWidget,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy
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

        tab_lt = QGridLayout()
        self.setLayout(tab_lt)

        # Label
        credits_l = QLabel(f"<h3>XL Converter</h3>Version {VERSION}<br>contact@codepoems.eu<br>XL Converter is licensed under <a href=\"LICENSE.txt\">GPL v3</a><br><a href=\"LICENSE_3RD_PARTY.txt\">3rd party licenses")
        credits_l.setAlignment(Qt.AlignCenter)
        credits_l.setOpenExternalLinks(True)

        # Buttons
        donate_btn = QPushButton("Donate", clicked=lambda: QDesktopServices.openUrl(QUrl("https://codepoems.eu/donate")))
        website_btn = QPushButton("Website", clicked=lambda: QDesktopServices.openUrl(QUrl("https://codepoems.eu")))

        # Positions
        tab_lt.addWidget(credits_l,0,0,1,0)
        tab_lt.addWidget(donate_btn,1,0)
        tab_lt.addWidget(website_btn,1,1)

        # Size Policy
        tab_lt.setVerticalSpacing(20)
        tab_lt.setAlignment(Qt.AlignCenter)

        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.setMaximumSize(900, 300)