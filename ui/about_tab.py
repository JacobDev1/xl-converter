from variables import VERSION, LICENSE_PATH, LICENSE_3RD_PARTY_PATH
from .update_checker import UpdateChecker

from PySide6.QtWidgets import(
    QWidget,
    QGridLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
)

from PySide6.QtCore import(
    Qt,
    QUrl,
)

from PySide6.QtGui import (
    QDesktopServices
)

class AboutTab(QWidget):
    def __init__(self):
        super(AboutTab, self).__init__()

        tab_lt = QGridLayout()
        self.setLayout(tab_lt)
        self.update_checker = UpdateChecker()

        # Label
        credits_l = QLabel(f"<h3>XL Converter</h3>Version {VERSION}<br>contact@codepoems.eu<br>XL Converter is licensed under <a href=\"{QUrl.fromLocalFile(LICENSE_PATH).toString()}\">GPL v3</a><br><a href=\"{QUrl.fromLocalFile(LICENSE_3RD_PARTY_PATH).toString()}\">3rd party licenses")
        credits_l.setAlignment(Qt.AlignCenter)
        credits_l.setOpenExternalLinks(True)

        # Buttons
        donate_btn = QPushButton("Donate", clicked=lambda: QDesktopServices.openUrl(QUrl("https://codepoems.eu/donate")))
        website_btn = QPushButton("Website", clicked=lambda: QDesktopServices.openUrl(QUrl("https://codepoems.eu")))
        self.update_btn = QPushButton("Check for an Update", clicked=self.checkForUpdate)
        self.update_checker.finished.connect(lambda: self.update_btn.setEnabled(True))

        # Positions
        tab_lt.addWidget(credits_l,0,0,1,0)
        tab_lt.addWidget(donate_btn,1,0)
        tab_lt.addWidget(website_btn,1,1)
        tab_lt.addWidget(self.update_btn, 2, 0, 1, 0)

        # Size Policy
        tab_lt.setVerticalSpacing(10)
        tab_lt.setAlignment(Qt.AlignCenter)

        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.setMaximumSize(900, 300)
    
    def checkForUpdate(self):
        self.update_checker.run()
        self.update_btn.setEnabled(False)
    
    def beforeExit(self):
        """Clean-up before exiting the application."""
        self.update_checker.beforeExit()