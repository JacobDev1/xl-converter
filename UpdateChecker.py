from VARIABLES import VERSION, VERSION_FILE_URL
import requests

from PySide6.QtWidgets import(
    QDialog,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QLabel
)

from PySide6.QtCore import(
    QUrl,
    QObject,
    Signal,
    Slot,
    QThread,
)

from PySide6.QtGui import(
    QDesktopServices
)

class Worker(QObject):
    status_code_error = Signal(int)
    misc_error = Signal(str)
    json = Signal(dict)
    finished = Signal()

    def run(self):
        response = None
        try:
            response = requests.get(VERSION_FILE_URL)
        except requests.ConnectionError as err:
            self.misc_error.emit(f"Couldn't connect to the server.")
            self.finished.emit()
            return

        if response.status_code != 200:
            self.status_code_error.emit(response.status_code)
            self.finished.emit()
            return
        
        parsed = None
        try:
            parsed = response.json()
        except:
            self.misc_error.emit("Parsing JSON failed.")
            self.finished.emit()
            return
        
        self.json.emit(parsed)

class UpdateChecker(QDialog):
    finished = Signal()

    def __init__(self):
        super(UpdateChecker, self).__init__()
        self.json = {}
        self.message_read = False

        # Threading
        self.thread = QThread(self)
        self.worker = Worker()
        self.thread.started.connect(self.worker.run)
        self.worker.moveToThread(self.thread)

        # Layout
        self.setWindowTitle("Update Checker")
        self.setMinimumSize(250, 100)
        main_lt = QVBoxLayout()
        self.setLayout(main_lt)
    
        # Buttons
        buttons_hb = QHBoxLayout()
        self.ok_btn = QPushButton("Ok", clicked=self.clicked)
        self.download_btn = QPushButton("Download")
        self.read_more_btn = QPushButton("Read More")

        self.ok_btn.setDefault(True)
        self.download_btn.setVisible(False)
        self.read_more_btn.setVisible(False)

        buttons_hb.addWidget(self.download_btn)
        buttons_hb.addWidget(self.read_more_btn)
        buttons_hb.addWidget(self.ok_btn)

        # Text
        self.text_l = QLabel("Sample message...")
        self.text_l.setWordWrap(True)

        # Init
        main_lt.addWidget(self.text_l)
        main_lt.addLayout(buttons_hb)

    def setBtnVisible(self, button_id, visible):
        match button_id:
            case "download":
                self.download_btn.setVisible(visible)
            case "read_more":
                self.read_more_btn.setVisible(visible)
            case "ok":
                self.ok_btn.setVisible(visible)

    def setText(self, text):
        self.text_l.setText(text)

    def openURL(self, url):
        QDesktopServices.openUrl(QUrl(url))
        self.clicked()
    
    def connectURL(self, button, url):
        match button:
            case "download":
                try:
                    self.download_btn.clicked.disconnect()      # Avoid connecting the same function twice
                except:
                    pass
                self.download_btn.clicked.connect(lambda: self.openURL(url))
            case "read_more":
                try:
                    self.read_more_btn.clicked.disconnect()
                except:
                    pass
                self.read_more_btn.clicked.connect(lambda: self.openURL(url))

    def keyExists(self, key):
        if key in self.json:
            if self.json[key] != "":
                return True
        return False


    def miscError(self, error):
        self.setText(error)
        self.show()

    def statusCodeError(self, code):
        match code:
            case 404:
                self.setText("Version file was not found on the server.")
            case _:
                self.setText(f"Status Code: {code}")
        self.show()

    def process(self, json):
        self.json = json

        if self.keyExists("latest_version"):
            if self.json["latest_version"] != VERSION:
                self.setText(f"New version is available ({self.json['latest_version']})")
                if self.keyExists("download_url"):
                    self.setBtnVisible("download", True)
                    self.connectURL("download", self.json["download_url"])
            else:
                self.setText("Your version is up to date.")
        else:
            self.setText(f"Version number not found in the JSON file.")

        self.show()

    def clicked(self):
        # Optional Message
        if self.keyExists("message"):
            if self.message_read != True:
                self.setBtnVisible("download", False)
                self.setText(self.json["message"])

                if self.keyExists("message_url"):
                    self.connectURL("read_more", self.json["message_url"])
                    self.setBtnVisible("read_more", True)

                self.message_read = True
                return

        self.close()
    
    def run(self):
        self.message_read = False
        self.setBtnVisible("read_more", False)
        self.setBtnVisible("download", False)

        if not self.thread.isRunning():
            self.thread.start()
            self.worker.misc_error.connect(self.miscError)
            self.worker.status_code_error.connect(self.statusCodeError)
            self.worker.json.connect(self.process)
            self.worker.finished.connect(self.stopThread)

    def stopThread(self):
        if self.thread.isRunning():
            self.thread.requestInterruption()
            self.thread.quit()
            self.thread.wait()

    def closeEvent(self, e):
        self.stopThread()
        self.finished.emit()
        super(UpdateChecker, self).closeEvent(e)
    
    def beforeExit(self):
        self.close()
        self.stopThread()
        self.thread.deleteLater()