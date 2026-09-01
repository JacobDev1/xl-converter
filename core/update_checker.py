from dataclasses import dataclass
import logging

import requests
from PySide6.QtCore import(
    QObject,
    Signal,
    QThread,
)

from data.constants import UPDATE_CHECKER_VER_FILE_URL, VERSION
from data.utils import parseVersion

logger = logging.getLogger(__name__)

# Debug
SIMULATE_SERVER = False
SIMULATE_SERVER_JSON = {
    "latest_version": VERSION,
    "download_url": "https://codepoems.eu/xl-converter",
    "message": "",
    "message_url": ""
}
# Notes:
# Only the "latest_version" key is required. The remaining keys are optional.
# Empty strings are ignored by the UI.

class UpdateCheckerWorker(QObject):
    json_received = Signal(dict)
    error_occurred = Signal(str)
    finished = Signal()

    def run(self):
        if SIMULATE_SERVER:
            self.json_received.emit(SIMULATE_SERVER_JSON)
            self.finished.emit()
            return
        
        try:
            response = requests.get(UPDATE_CHECKER_VER_FILE_URL, timeout=5)
            match response.status_code:
                case 200:
                    self.json_received.emit(response.json())
                case 404:
                    self.error_occurred.emit("Version file not found.")
                case 500:
                    self.error_occurred.emit("Internal server error.")
                case _:
                    self.error_occurred.emit(f"Error, status code: {response.status_code}")
        except requests.ConnectionError:
            self.error_occurred.emit(f"Couldn't connect to the server.")
        except requests.RequestException as e:
            self.error_occurred.emit(str(e))
        finally:
            self.finished.emit()

class UpdateCheckerRunner(QObject):
    json_received = Signal(dict)
    error_occurred = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.worker = None
        self.thread = None
    
    def _cleanup(self):
        self.thread = None
        self.worker = None
        
    def run(self):
        if self.thread and self.thread.isRunning():
            return

        self.worker = UpdateCheckerWorker()
        self.thread = QThread()

        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.json_received.connect(self.json_received)
        self.worker.error_occurred.connect(self.error_occurred)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker.finished.connect(self.thread.quit)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.finished.connect(self._cleanup)
        self.thread.start()

def isNewerVersionAvailable(remote_ver: str) -> bool:
    """Compares the current with the remote version.

    Returns:
        True - if an update is available or the remote version cannot be parsed (e.g. due to a new version scheme).
        False - if the current version is up to date.
    
    Raises:
        ValueError - if the current version cannot be parsed.
    """
    cur_ver = parseVersion(VERSION)
    remote_ver = parseVersion(remote_ver)

    if cur_ver is None:
        logger.error("Failed to parse current version.")
        raise ValueError("Failed to parse current version.")

    if remote_ver is None:
        # In the future, version scheme may get more complex.
        logger.info("Failed to parse remote version.")
        return True
    
    return remote_ver > cur_ver

@dataclass
class UpdateInfo:
    latest_version: str
    download_url: str = ""
    message: str = ""
    message_url: str = ""

    @classmethod
    def fromJson(cls, json_data: dict) -> "UpdateInfo":
        """Creates an UpdateInfo object from JSON data and returns it. Can raise ValueError."""
        if "latest_version" not in json_data:
            raise ValueError("Key \"latest_version\" not found in JSON response.")
        
        def getField(key: str) -> str:
            value = json_data.get(key, "")
            return str(value)

        return cls(
            latest_version=getField("latest_version"),
            download_url=getField("download_url"),
            message=getField("message"),
            message_url=getField("message_url"),
        )
