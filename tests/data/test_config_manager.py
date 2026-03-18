from unittest.mock import patch, MagicMock
import configparser
from pathlib import Path
import logging

import pytest

from data.config_manager import ConfigManager

@pytest.fixture(autouse=True)
def reset_singleton():
    ConfigManager._instance = None
    ConfigManager._config = configparser.ConfigParser()
    ConfigManager()  # Init

def test_singleton_instance():
    assert ConfigManager() is ConfigManager()

def test_ConfigManager_lock():
    with (
        patch.object(ConfigManager, "_lock") as mock_lock,
        patch.object(ConfigManager, "_initialize"),
    ):
        ConfigManager()
        mock_lock.__enter__.assert_called_once()
    mock_lock.__exit__.assert_called_once()

def test__initialize_file_exists():
    mock_path = MagicMock()
    mock_path.is_file.return_value=True

    with (
        patch.object(ConfigManager, "_config_location", mock_path),
        patch.object(ConfigManager._config, "read") as mock_read,
    ):
        ConfigManager._initialize()
        mock_read.assert_called_once_with(mock_path, encoding="utf-8")

def test__initialize_no_file():
    mock_path = MagicMock()
    mock_path.is_file.return_value=False

    with (
        patch.object(ConfigManager, "_config_location", mock_path),
        patch.object(ConfigManager._config, "read") as mock_read,
    ):
        ConfigManager._initialize()
        mock_read.assert_not_called()

def test__initialize_exception(caplog):
    caplog.set_level(logging.ERROR)
    mock_path = MagicMock()
    mock_path.is_file.return_value=True

    with (
        patch.object(ConfigManager, "_config_location", mock_path),
        patch.object(ConfigManager._config, "read", side_effect=configparser.ParsingError("exception occurred")) as mock_read,
    ):
        ConfigManager._initialize()
        mock_read.assert_called_once()
        assert "exception occurred" in caplog.text

def test_get_value_exists():
    section, option, fallback, expected_value = "Default", "value", False, True
    with (
        patch.object(ConfigManager._config, "get", return_value=expected_value) as mock_get,
    ):
        assert ConfigManager.get(section, option, fallback) == expected_value
        mock_get.assert_called_once_with(section, option, fallback=fallback)

def test_get_fallback():
    section, option, fallback, expected_value = "Default", "value", False, True
    with (
        patch.object(ConfigManager._config, "get", return_value=fallback) as mock_get,
    ):
        assert ConfigManager.get(section, option, fallback) == fallback
        mock_get.assert_called_once_with(section, option, fallback=fallback)

def test_get_exception(caplog):
    section, option, fallback, expected_value = "Default", "value", False, True
    mock_erorr = configparser.NoOptionError(option, section)
    caplog.set_level(logging.ERROR)

    with (
        patch.object(ConfigManager._config, "get", side_effect=mock_erorr) as mock_get,
    ):
        assert ConfigManager.get(section, option, fallback) == fallback
        mock_get.assert_called_once_with(section, option, fallback=fallback)
        assert section in caplog.text
        assert option in caplog.text

def test_getboolean_value_exists():
    section, option, fallback, expected_value = "Default", "value", False, True
    with (
        patch.object(ConfigManager._config, "getboolean", return_value=expected_value) as mock_getboolean,
    ):
        assert ConfigManager.getboolean(section, option, fallback) == expected_value
        mock_getboolean.assert_called_once_with(section, option, fallback=fallback)

def test_getboolean_fallback():
    section, option, fallback, expected_value = "Default", "value", False, True
    with (
        patch.object(ConfigManager._config, "getboolean", return_value=fallback) as mock_getboolean,
    ):
        assert ConfigManager.getboolean(section, option, fallback) == fallback
        mock_getboolean.assert_called_once_with(section, option, fallback=fallback)

def test_getboolean_exception(caplog):
    section, option, fallback, expected_value = "Default", "value", False, True
    mock_erorr = configparser.NoOptionError(option, section)
    caplog.set_level(logging.ERROR)

    with (
        patch.object(ConfigManager._config, "getboolean", side_effect=mock_erorr) as mock_getboolean,
    ):
        assert ConfigManager.getboolean(section, option, fallback) == fallback
        mock_getboolean.assert_called_once_with(section, option, fallback=fallback)
        assert section in caplog.text
        assert option in caplog.text

def test_reload():
    with (
        patch.object(ConfigManager._config, "clear") as mock_clear,
        patch.object(ConfigManager, "_initialize") as mock__initialize,
    ):
        ConfigManager.reload()
        mock_clear.assert_called_once()
        mock__initialize.assert_called_once()
