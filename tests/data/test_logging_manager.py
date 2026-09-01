import logging
import os
from unittest.mock import MagicMock, patch

import pytest

from data.logging_manager import LoggingManager

@pytest.fixture
def reset_logging_manager(monkeypatch):
    monkeypatch.setattr("data.logging_manager.LOGS_DIR", "/tmp/logs_dir")
    monkeypatch.setattr("data.logging_manager.LOGS_PATH", "/tmp/logs_dir/logs.txt")
    LoggingManager._instance = None
    LoggingManager._initialized = False
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
        handler.close()

    yield

    LoggingManager._instance = None
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

def test_loggin_manager_singleton(reset_logging_manager):
    lm1 = LoggingManager()
    lm2 = LoggingManager()
    assert lm1 is lm2
    assert lm1._initialized == True

def test_logging_manager_init(reset_logging_manager):
    lm = LoggingManager()
    root_logger = logging.getLogger()

    assert root_logger.level == logging.WARNING
    assert lm.stream_handler is not None
    assert isinstance(root_logger.handlers[0], logging.StreamHandler)

def test__setupFileHandler_happy_path(reset_logging_manager, monkeypatch):
    logs_dir = "/tmp/logs_dir"
    monkeypatch.setattr("data.logging_manager.LOGS_DIR", logs_dir)
    with (
        patch("data.logging_manager.logging.FileHandler") as mock_FileHandler,
        patch("data.logging_manager.os.makedirs") as mock_makedirs,
    ):
        lm = LoggingManager()
        lm._setupFileHandler()
        mock_makedirs.assert_called_once_with(logs_dir, exist_ok=True)
        assert lm.file_handler is mock_FileHandler.return_value
        mock_FileHandler.return_value.setFormatter.assert_called_once()

def test__setupFileHandler_sad_path(reset_logging_manager, caplog):
    with (
        patch("data.logging_manager.logging.FileHandler") as mock_FileHandler,
        patch("data.logging_manager.os.makedirs", side_effect=OSError("Exception")) as mock_makedirs,
    ):
        lm = LoggingManager()
        lm._setupFileHandler()
        assert lm.file_handler is None
        mock_FileHandler.assert_not_called()
        assert "Failed to create logs dir. Exception" in caplog.text

@pytest.mark.parametrize("level", [
    logging.DEBUG,
    logging.INFO,
    logging.WARNING,
    logging.ERROR,
    logging.CRITICAL,
])
def test_setLevel_valid(level, reset_logging_manager):
    level_str = logging.getLevelName(level)
    LoggingManager().setLevel(level_str)
    assert logging.getLogger().level == level

def test_setLevel_invalid(reset_logging_manager, caplog):
    caplog.set_level(logging.ERROR)
    lm = LoggingManager()
    org_level = logging.getLogger().level

    lm.setLevel("INVALID")

    assert "[Logging - setLevel] Invalid argument (INVALID)" in caplog.text
    assert org_level == logging.getLogger().level

def test_startLoggingToFile_happy_path(reset_logging_manager):
    with (
        patch("data.logging_manager.logging.FileHandler") as mock_FileHandler,
        patch("data.logging_manager.os.makedirs") as mock_makedirs,
        patch.object(LoggingManager, "setLevel") as mock_setLevel,
    ):
        lm = LoggingManager()
        lm.startLoggingToFile(level="DEBUG")
        mock_makedirs.assert_called_once_with("/tmp/logs_dir", exist_ok=True)
        mock_FileHandler.assert_called_once()
        assert lm.isLoggingToFile() is True
        mock_setLevel.assert_called_once_with("DEBUG")
        assert mock_FileHandler.return_value in lm.root_logger.handlers

def test_startLoggingToFile_makedirs_fail(reset_logging_manager, caplog):
    with (
        patch("data.logging_manager.os.makedirs", side_effect=OSError("Exception")) as mock_makedirs,
        patch("data.logging_manager.logging.FileHandler") as mock_FileHandler,
    ):
        lm = LoggingManager()
        lm.startLoggingToFile(level="DEBUG")

        mock_makedirs.assert_called_once_with("/tmp/logs_dir", exist_ok=True)
        mock_FileHandler.assert_not_called()
        assert lm.file_handler is None
        assert lm.isLoggingToFile() is False
        assert "Failed to create logs dir" in caplog.text

        root_logger = logging.getLogger()
        assert None not in root_logger.handlers
        root_logger.error("Logging still works")

def test_stopLoggingToFile(reset_logging_manager):
    with (
        patch("data.logging_manager.logging.FileHandler") as mock_FileHandler,
    ):
        lm = LoggingManager()
        lm.startLoggingToFile()
        assert lm.isLoggingToFile() is True
        lm.stopLoggingToFile()
        assert lm.isLoggingToFile() is False
        assert lm.file_handler is None
        assert logging.getLogger().level == logging.WARNING
        mock_FileHandler.return_value.close.assert_called_once()

def test_isLoggingToFile_true(reset_logging_manager):
    lm = LoggingManager()
    lm.file_handler = MagicMock(spec=logging.FileHandler)
    lm.root_logger.addHandler(lm.file_handler)
    assert lm.isLoggingToFile() is True

def test_isLoggingToFile_false_no_handler(reset_logging_manager):
    lm = LoggingManager()
    lm.file_handler = None
    assert lm.isLoggingToFile() is False

def test_isLoggingToFile_false_handler_not_in_list(reset_logging_manager):
    lm = LoggingManager()
    lm.file_handler = MagicMock(spec=logging.FileHandler)
    assert lm.isLoggingToFile() is False

def test_wipeLogsDir_not_found(reset_logging_manager):
    with (
        patch("data.logging_manager.os.path.exists", return_value=False) as mock_exists,
    ):
        lm = LoggingManager()
        assert lm.wipeLogsDir() == "No logs have been found."
        mock_exists.assert_called_once_with("/tmp/logs_dir")

def test_wipeLogsDir_remove_success(reset_logging_manager):
    with (
        patch("data.logging_manager.os.path.exists", return_value=True) as mock_exists,
        patch("data.logging_manager.shutil.rmtree") as mock_rmtree,
    ):
        lm = LoggingManager()
        assert lm.wipeLogsDir() == "Successfully deleted logs folder."
        mock_rmtree.assert_called_once_with("/tmp/logs_dir")

def test_wipeLogsDir_remove_failed(reset_logging_manager):
    with (
        patch("data.logging_manager.os.path.exists", return_value=True) as mock_exists,
        patch("data.logging_manager.shutil.rmtree", side_effect=OSError("Error")) as mock_rmtree,
    ):
        lm = LoggingManager()
        assert lm.wipeLogsDir() == "Cannot wipe logs folder.\nError"

def test_getLogsDir(reset_logging_manager, monkeypatch):
    logs_dir = "/tmp/logs_dir"
    monkeypatch.setattr("data.logging_manager.LOGS_DIR", logs_dir)
    lm = LoggingManager()
    assert lm.getLogsDir() == logs_dir


