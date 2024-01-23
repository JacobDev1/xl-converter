import requests
from PySide6.QtCore import(
    QObject,
    Signal,
    QThread,
)

from data.constants import VERSION_FILE_URL, VERSION

SIMULATE_SERVER = False     # For debugging

class Worker(QObject):
    status_code_error = Signal(int)
    misc_error = Signal(str)
    json = Signal(dict)
    finished = Signal()

    def run(self):
        if SIMULATE_SERVER:
            self.json.emit({
                "latest_version": VERSION,
                "download_url": "https://codepoems.eu/xl-converter",
                "message": "",
                "message_url": ""
            })
            self.finished.emit()
            return
        
        try:
            response = requests.get(VERSION_FILE_URL)
        except requests.ConnectionError as err:
            self.misc_error.emit(f"Couldn't connect to the server.\n{err}")
            self.finished.emit()
            return

        if response.status_code != 200:
            self.status_code_error.emit(response.status_code)
            self.finished.emit()
            return
        
        try:
            parsed = response.json()
        except:
            self.misc_error.emit("Parsing JSON failed.")
            self.finished.emit()
            return
        
        self.json.emit(parsed)
        self.finished.emit()

class Runner(QObject):
    """Runs online operation."""
    error = Signal(str)
    json = Signal(dict)
    finished = Signal()

    def __init__(self, parent = None):
        super().__init__(parent)

    def run(self):
        """Sets up the worker thread and connects its signals."""
        self.worker = Worker()
        self.thread = QThread()
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.handleFinish)
        self.worker.json.connect(self.json)
        self.worker.status_code_error.connect(self.handleErrorStatusCode)
        self.worker.misc_error.connect(self.handleError)
        self.worker.moveToThread(self.thread)
        self.thread.start()

    def handleErrorStatusCode(self, code):
        """Handles the status code error."""
        match code:
            case 404:
                self.error.emit("Version file not found.")
            case 500:
                self.error.emit("Internal server error.")
            case _:
                self.error.emit(f"Error, status code: {code}")

    def handleError(self, error):
        """Handles misc. errors."""
        self.error.emit(error)

    def handleFinish(self):
        """Cleans up the thread and worker."""
        if self.thread.isRunning():
            self.thread.requestInterruption()
            self.thread.quit()
            self.thread.wait()
        self.worker.deleteLater()
        self.thread.deleteLater()
        self.finished.emit()