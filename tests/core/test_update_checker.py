from unittest.mock import patch, MagicMock
import requests
import logging

import pytest
from PySide6.QtTest import QSignalSpy
from PySide6.QtCore import QThread

import core.update_checker as update_checker

@pytest.fixture
def worker(app):
    return update_checker.UpdateCheckerWorker()

def getSampleUpdateFileUrl() -> str:
    return "https://codepoems.eu/downloads/xl-converter/version.json"

def test_worker_simulate_server(worker):
    with (
        patch("core.update_checker.SIMULATE_SERVER", True),
        patch("core.update_checker.SIMULATE_SERVER_JSON", {"latest_version": "1.0.0"}) as var_SIMULATE_SERVER_JSON,
    ):
        json_received_spy = QSignalSpy(worker.json_received)
        finished_spy = QSignalSpy(worker.finished)

        worker.run()
    
        assert json_received_spy.count() == 1
        assert finished_spy.count() == 1
        assert json_received_spy.at(0)[0] == var_SIMULATE_SERVER_JSON

def test_worker_connection_success(worker, requests_mock):
    sample_json_data = {"latest_version": "1.0.0"}
    sample_update_file_url = getSampleUpdateFileUrl()
    requests_mock.get(
        sample_update_file_url,
        json=sample_json_data,
        status_code=200
    )
    json_received_spy = QSignalSpy(worker.json_received)
    finished_spy = QSignalSpy(worker.finished)

    with (
        patch("core.update_checker.SIMULATE_SERVER", False),
        patch("core.update_checker.UPDATE_CHECKER_VER_FILE_URL", sample_update_file_url),
    ):
        worker.run()

        assert json_received_spy.count() == 1
        assert finished_spy.count() == 1
        assert json_received_spy.at(0)[0] == sample_json_data

def test_worker_connection_error(worker, requests_mock):
    sample_update_file_url = getSampleUpdateFileUrl()
    requests_mock.get(
        sample_update_file_url,
        exc=requests.ConnectionError("No internet connection")
    )
    error_occurred_spy = QSignalSpy(worker.error_occurred)
    finished_spy = QSignalSpy(worker.finished)
    
    with (
        patch("core.update_checker.SIMULATE_SERVER", False),
        patch("core.update_checker.UPDATE_CHECKER_VER_FILE_URL", sample_update_file_url),
    ):
        worker.run()

        assert finished_spy.count() == 1
        assert error_occurred_spy.count() == 1
        assert error_occurred_spy.at(0)[0] == "Couldn't connect to the server."

@pytest.mark.parametrize("error_code, error_message", [
    (404, "Version file not found"),
    (500, "Internal server error"),
    (401, "Error, status code: 401"),
])
def test_worker_status_code_error(error_code, error_message, worker, requests_mock):
    sample_update_file_url = getSampleUpdateFileUrl()
    requests_mock.get(sample_update_file_url, json={}, status_code=error_code)
    error_occurred_spy = QSignalSpy(worker.error_occurred)
    finished_spy = QSignalSpy(worker.finished)

    with (
        patch("core.update_checker.SIMULATE_SERVER", False),
        patch("core.update_checker.UPDATE_CHECKER_VER_FILE_URL", sample_update_file_url),
    ):
        worker.run()

        assert finished_spy.count() == 1
        assert error_occurred_spy.count() == 1
        assert error_message in error_occurred_spy.at(0)[0]

def test_worker_generic_exception(worker, requests_mock):
    sample_update_file_url = getSampleUpdateFileUrl()
    requests_mock.get(
        sample_update_file_url,
        exc=requests.RequestException("Failed to parse JSON."),
    )
    error_occurred_spy = QSignalSpy(worker.error_occurred)
    finished_spy = QSignalSpy(worker.finished)

    with (
        patch("core.update_checker.SIMULATE_SERVER", False),
        patch("core.update_checker.UPDATE_CHECKER_VER_FILE_URL", sample_update_file_url),
    ):
        worker.run()

        assert finished_spy.count() == 1
        assert error_occurred_spy.count() == 1
        assert "Failed to parse JSON." in error_occurred_spy.at(0)[0]

@pytest.fixture
def runner(app):
    return update_checker.UpdateCheckerRunner()

def test_runner_run_happy_path(runner):
    mock_UpdateCheckerWorker = MagicMock(spec=update_checker.UpdateCheckerWorker)
    mock_QThread = MagicMock(spec=QThread)

    with (
        patch("core.update_checker.UpdateCheckerWorker", return_value=mock_UpdateCheckerWorker),
        patch("core.update_checker.QThread", return_value=mock_QThread),
    ):    
        runner.run()

        mock_UpdateCheckerWorker.moveToThread.assert_called_once_with(mock_QThread)
        mock_QThread.started.connect.assert_called_once_with(mock_UpdateCheckerWorker.run)
        mock_UpdateCheckerWorker.json_received.connect.assert_called_once_with(runner.json_received)
        mock_UpdateCheckerWorker.error_occurred.connect.assert_called_once_with(runner.error_occurred)
        mock_UpdateCheckerWorker.finished.connect.assert_called_once_with(runner._cleanup)
        mock_QThread.start.assert_called_once()

def test_runner_run_already_running(runner):
    mock_UpdateCheckerWorker = MagicMock(spec=update_checker.UpdateCheckerWorker)
    mock_QThread = MagicMock(spec=QThread)
    mock_QThread.isRunning.return_value = True
    runner.thread = mock_QThread

    with (
        patch("core.update_checker.UpdateCheckerWorker", return_value=mock_UpdateCheckerWorker),
        patch("core.update_checker.QThread", return_value=mock_QThread),
    ):  
        runner.run()

        mock_QThread.start.assert_not_called()

# More thorough tests are available in tests/data/test_data_utils.py
@pytest.mark.parametrize("current_ver, remote_ver, expected", [
    ("0.9.9", "0.9.8", False),
    ("1.0.0", "1.0.0", False),
    ("1.0.0", "1.0.1", True),
    ("1.0.1", "1.1.0", True),
    ("1.0.0", "1.1.0", True),
    ("0.0.0", "1.0.0", True),
])
def test_isVersionNewer_happy_path(current_ver, remote_ver, expected):
    with patch("core.update_checker.VERSION", current_ver):
        assert update_checker.isNewerVersionAvailable(remote_ver) == expected

def test_isVersionNewer_cur_ver_parsing_failed(caplog):
    with (
        patch("core.update_checker.VERSION", "invalid"),
        pytest.raises(ValueError),
        caplog.at_level(logging.ERROR),
    ):
        update_checker.isNewerVersionAvailable("v1.2.0")
    assert "Failed to parse current version." in caplog.text

def test_isVersionNewer_remote_ver_parsing_failed(caplog):
    with (
        patch("core.update_checker.VERSION", "v1.2.0"),
        caplog.at_level(logging.INFO),
    ):
        assert update_checker.isNewerVersionAvailable("invalid") == True
        assert "Failed to parse remote version." in caplog.text

def test_UpdateInfo_happy_path():
    json_data = {
        "latest_version": "1.0.0",
        "download_url": "https://codepoems.eu/xl-converter",
        "message": "Sample message",
        "message_url": "https://codepoems.eu/sample_url"
    }

    update_info = update_checker.UpdateInfo.fromJson(json_data)
    assert update_info.latest_version == json_data["latest_version"]
    assert update_info.download_url == json_data["download_url"]
    assert update_info.message == json_data["message"]
    assert update_info.message_url == json_data["message_url"]

def test_UpdateInfo_only_required():
    json_data = {
        "latest_version": "1.0.0",
    }

    update_info = update_checker.UpdateInfo.fromJson(json_data)
    assert update_info.latest_version == json_data["latest_version"]
    assert update_info.download_url == ""
    assert update_info.message == ""
    assert update_info.message_url == ""

def test_UpdateInfo_missing_required():
    json_data = {
        "download_url": "",
        "message": "",
        "message_url": ""
    }

    with pytest.raises(ValueError, match="\"latest_version\" not found") as exc_info:
        update_info = update_checker.UpdateInfo.fromJson(json_data)
