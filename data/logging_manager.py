import logging
import os
import shutil

from data.constants import LOGS_DIR

# Config
LOGS_PATH = os.path.join(LOGS_DIR, "logs.txt")
DEFAULT_LEVEL = logging.WARNING      # DEBUG, INFO, WARNING, ERROR, CRITICAL

class LoggingManager:   # Singleton
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LoggingManager, cls).__new__(cls)
            cls._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        
        self.file_handler = None
        self.stream_handler = None
        self.root_logger = logging.getLogger()
        
        self._setupStreamHandler()
        self.root_logger.setLevel(DEFAULT_LEVEL)

        self._initialized = True

    def _setupStreamHandler(self):
        if self.stream_handler is None:
            self.stream_handler = logging.StreamHandler()
            self.stream_handler.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
            self.root_logger.addHandler(self.stream_handler)

    def _setupFileHandler(self):
        if not os.path.exists(LOGS_DIR):
            os.makedirs(LOGS_DIR, exist_ok=True)
        if self.file_handler is None:
            self.file_handler = logging.FileHandler(LOGS_PATH, encoding="utf-8")
            self.file_handler.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
    
    def setLevel(self, level: str):
        """Set root logger level."""
        if level not in ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"):
            self.root_logger.error(f"[Logging - setLevel] Invalid argument ({level})")
            return
        self.root_logger.setLevel(getattr(logging, level))
    
    def startLoggingToFile(self, level: str = None):
        self._setupFileHandler()
        if level is not None:
            self.setLevel(level)
        if self.file_handler not in self.root_logger.handlers:
            self.root_logger.addHandler(self.file_handler)
    
    def stopLoggingToFile(self):
        if self.file_handler in self.root_logger.handlers:
            self.file_handler.close()
            self.root_logger.removeHandler(self.file_handler)
        self.root_logger.setLevel(DEFAULT_LEVEL)

    def isLoggingToFile(self):
        if self.file_handler is None or self.file_handler not in self.root_logger.handlers:
            return False
        else:
            return True

    def wipeLogsDir(self) -> str:
        """Wipes logs directory, returns a message."""
        if not os.path.exists(LOGS_DIR):
            return "No logs have been found."

        try:
            shutil.rmtree(LOGS_DIR)
            return "Successfully deleted logs folder."
        except OSError as e:
            return f"Cannot wipe logs folder.\n{e}"

    def getLogsDir(self):
        return LOGS_DIR