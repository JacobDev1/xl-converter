from PySide6.QtWidgets import(
    QWidget,
    QGridLayout,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
)
from PySide6.QtCore import(
    Qt,
    QUrl,
)
from PySide6.QtGui import(
    QDesktopServices,
)

from data.constants import VERSION, LICENSE_PATH, LICENSE_3RD_PARTY_PATH
from ui.update_checker import UpdateChecker

class AboutTab(QWidget):
    def __init__(self):
        super(AboutTab, self).__init__()

        tab_lt = QHBoxLayout()
        self.setLayout(tab_lt)
        self.update_checker = UpdateChecker()

        # Label
        text_vb = QVBoxLayout()
        headers_l = QLabel(f"""
            <h3><a href=\"https://codepoems.eu/xl-converter\">XL Converter</a></h3>
            <h4>Version {VERSION}</h4>
        """)
        credits_l = QLabel(f"""
            <a href=\"mailto:contact@codepoems.eu\">contact@codepoems.eu</a><br>
            XL Converter is licensed under <a href=\"{QUrl.fromLocalFile(LICENSE_PATH).toString()}\">GPL v3</a><br>
            <a href=\"{QUrl.fromLocalFile(LICENSE_3RD_PARTY_PATH).toString()}\">3rd party licenses</a>
        """)

        headers_l.setOpenExternalLinks(True)
        credits_l.setOpenExternalLinks(True)
        headers_l.setAlignment(Qt.AlignCenter)
        credits_l.setAlignment(Qt.AlignCenter)
        text_vb.addWidget(headers_l)
        text_vb.addWidget(credits_l)
        tab_lt.addLayout(text_vb)

        # Buttons
        buttons_vb = QVBoxLayout()

        self.update_btn = QPushButton("Check for Updates", clicked=self.checkForUpdate)
        self.update_checker.finished.connect(lambda: self.update_btn.setEnabled(True))
        self.manual_btn = QPushButton("Manual", clicked=lambda: QDesktopServices.openUrl(QUrl("https://xl-docs.codepoems.eu/")))
        self.report_bug_btn = QPushButton("Report Bug", clicked=lambda: QDesktopServices.openUrl(QUrl("https://github.com/JacobDev1/xl-converter/issues")))
        self.website_btn = QPushButton("Website", clicked=lambda: QDesktopServices.openUrl(QUrl("https://codepoems.eu/xl-converter")))

        buttons_vb.addWidget(self.update_btn)
        buttons_vb.addWidget(self.manual_btn)
        buttons_vb.addWidget(self.report_bug_btn)
        buttons_vb.addWidget(self.website_btn)
        tab_lt.addLayout(buttons_vb)

        # Layout

        text_vb.setAlignment(Qt.AlignVCenter)
        buttons_vb.setAlignment(Qt.AlignVCenter)

        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.setMaximumSize(700, 300)
    
    def checkForUpdate(self):
        self.update_checker.run()
        self.update_btn.setEnabled(False)