from PySide6.QtWidgets import(
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QWidget,
)
from PySide6.QtCore import(
    Qt,
    QUrl,
)

import data.constants as constants
from ui.dialogs import UpdateChecker
from ui.lib.utils import openRemoteUrl, openUrl
from ui.widgets import StyledLabel

class AboutTab(QWidget):
    def __init__(self):
        super(AboutTab, self).__init__()
        self.update_checker = UpdateChecker(self)

        self.setupWidgets()
        self.setupLayouts()
        self.setupStyles()
    
    def setupWidgets(self):
        # Labels
        self.title_l = QLabel(f"XL Converter")
        self.version_l = QLabel(f"Version beta-26-01-12")
        self.credits_l = StyledLabel(f"""
            <div style='line-height: 120%;'>
                <a href=\"https://codepoems.eu\" >website</a>
                <br>
                <a href=\"mailto:contact@codepoems.eu\">contact@codepoems.eu</a>
                <br>
                <a href=\"{QUrl.fromLocalFile(constants.LICENSE_PATH).toString()}\">license</a> / 
                <a href=\"{QUrl.fromLocalFile(constants.LICENSE_3RD_PARTY_PATH).toString()}\">3rd party</a>
            </div>
        """)
        self.credits_l.linkActivated.connect(lambda qurl: openUrl(qurl))

        self.title_l.setOpenExternalLinks(True)
        self.credits_l.setOpenExternalLinks(False)

        # Buttons
        self.update_btn = QPushButton("Check for Updates", clicked=self.checkForUpdate)
        self.update_checker.finished.connect(lambda: self.update_btn.setEnabled(True))
        self.manual_btn = QPushButton("Manual", clicked=lambda: openRemoteUrl("https://xl-docs.codepoems.eu/"))
        self.report_bug_btn = QPushButton("Report Bug", clicked=lambda: openRemoteUrl("https://github.com/JacobDev1/xl-converter-beta/issues"))

    def setupLayouts(self):
        # Labels
        labels_vb = QVBoxLayout()
        labels_vb.addWidget(self.title_l)
        labels_vb.addWidget(self.version_l)
        labels_vb.addWidget(self.credits_l)
        self.title_l.setObjectName("title_l")
        self.version_l.setObjectName("version_l")

        # Buttons
        buttons_vb = QVBoxLayout()
        buttons_vb.addWidget(self.update_btn)
        buttons_vb.addWidget(self.manual_btn)
        buttons_vb.addWidget(self.report_bug_btn)
        self.update_btn.setEnabled(constants.UPDATE_CHECKER_ENABLED)
        
        # Main
        self.content_w = QWidget()
        self.content_lt = QHBoxLayout(self.content_w)
        self.content_lt.addLayout(labels_vb)
        self.content_lt.addLayout(buttons_vb)

        self.main_lt = QHBoxLayout(self)
        self.main_lt.addWidget(self.content_w)

        # Size policy
        self.content_w.setMaximumWidth(1000)
        labels_vb.setAlignment(Qt.AlignVCenter)
        buttons_vb.setAlignment(Qt.AlignVCenter)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def setupStyles(self):
        ## Labels
        self.title_l.setStyleSheet("padding-bottom: 3px;")
        self.version_l.setStyleSheet("padding-bottom: 5px;")

        self.title_l.setAlignment(Qt.AlignCenter)
        self.version_l.setAlignment(Qt.AlignCenter)
        self.credits_l.setAlignment(Qt.AlignCenter)

    def checkForUpdate(self):
        self.update_btn.setEnabled(False)
        self.update_checker.run()
