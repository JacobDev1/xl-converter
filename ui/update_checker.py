from PySide6.QtWidgets import(
    QDialog,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
)
from PySide6.QtCore import(
    Qt,
    QUrl,
    QObject,
    Signal,
)
from PySide6.QtGui import(
    QDesktopServices,
    QGuiApplication,
    QIcon,
)

from data.constants import VERSION, ICON_SVG
from core.update_checker import Runner

class Dialog(QDialog):
    closed = Signal()

    def __init__(self, parent = None):
        super().__init__(parent)
        self.setWindowTitle("Update Checker")
        self.setWindowIcon(QIcon(ICON_SVG))
        self.setMinimumSize(280, 100)

        # Widgets
        self.text_l = QLabel("Placeholder", self)
        self.text_l.setAlignment(Qt.AlignCenter)
        self.text_l.setWordWrap(True)
        self.ok_btn = QPushButton("Ok", self)
        self.ok_btn.clicked.connect(self.close)
        self.link_btn = QPushButton("Open Link", self)

        # Layout
        self.main_lt = QVBoxLayout()
        self.setLayout(self.main_lt)

        self.main_lt.addWidget(self.text_l)

        buttons_hb = QHBoxLayout()
        buttons_hb.addWidget(self.link_btn)
        buttons_hb.addWidget(self.ok_btn)
        self.main_lt.addLayout(buttons_hb)

        buttons_hb.setAlignment(Qt.AlignRight)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.link_btn.setMinimumWidth(100)
        self.ok_btn.setMinimumWidth(100)

    def resizeToContent(self):
        """Resize to content and center."""
        self.setMinimumSize(self.main_lt.sizeHint())
        qr = self.frameGeometry()           
        cp = QGuiApplication.primaryScreen().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def show(self, message, url = None, url_text = None, resize_to_content = False):
        self.text_l.setText(message)
        if url:
            self.link_btn.setText(url_text if url_text else "Open Link")
            try:
                self.link_btn.clicked.disconnect()
            except:
                pass
            self.link_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(url)))

        self.link_btn.setVisible(url is not None)

        if resize_to_content:
            self.resizeToContent()
        
        super().show()

    def close(self):
        super().close()
        self.closed.emit()

class UpdateChecker(QObject):
    finished = Signal()

    def __init__(self):
        super().__init__()
        self.silent = False
        self.msg_read = False
        self.msg = None
        self.msg_url = None

        self.runner = Runner(self)
        self.runner.error.connect(self.showError)
        self.runner.json.connect(self.processJSON)
        self.runner.finished.connect(self.finished)
        self.dlg = Dialog()

    def run(self, silent = False):
        self.silent = silent
        self.runner.run()
        self.msg_read = False
        self.msg = None
        self.msg_url = None
    
    def showError(self, msg):
        if not self.silent:
            self.dlg.show(msg)

    def processJSON(self, json):
        def isKeyEmpty(json, key):
            value = json.get(key, None)
            if isinstance(value, str):
                return not value.strip()
            else:
                return True
    
        if not self.silent:
            if not isKeyEmpty(json, "message"):
                self.msg = json["message"]
                if not isKeyEmpty(json, "message_url"):
                    self.msg_url = json["message_url"]

            if self.msg:
                try:
                    self.dlg.closed.disconnect()
                except:
                    pass
                self.dlg.closed.connect(self.displayMessage)

        if not isKeyEmpty(json, "latest_version"):
            if json["latest_version"] != VERSION:
                self.dlg.show(f"New version is available ({json['latest_version']}).",json.get("download_url", None), "Download")
            elif not self.silent:
                self.dlg.show("This version is up to date.")
        elif not self.silent:
            self.dlg.show("JSON is missing 'latest_version' key")
    
    def displayMessage(self):
        if not self.msg_read and self.msg:
            self.msg_read = True
            self.dlg.show(self.msg, self.msg_url, "Read More")