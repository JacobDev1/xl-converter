from unittest.mock import patch
import requests

import pytest
from PySide6.QtTest import QSignalSpy

from core.update_checker import (
    Worker,
    Runner,
    SIMULATE_SERVER_JSON
)
from data.constants import VERSION, VERSION_FILE_URL

@pytest.fixture
def worker():
    return Worker()

@pytest.fixture
def runner():
    r = Runner()
    yield r
    r.handleFinish()

def test_worker_simulate_server(worker):
    with patch("core.update_checker.SIMULATE_SERVER", True):
        json_spy = QSignalSpy(worker.json)
        finished_spy = QSignalSpy(worker.finished)

        worker.run()
    
        try:
            assert json_spy.at(0)[0] == SIMULATE_SERVER_JSON
        except:
            pytest.fail("QSignalSpy instance error")
        assert json_spy.count() == 1
        assert finished_spy.count() == 1

def test_worker_connection_success(worker, requests_mock):
    tmp = {"latest_version": VERSION}
    requests_mock.get(VERSION_FILE_URL, json=tmp, status_code=200)
    json_spy = QSignalSpy(worker.json)
    finished_spy = QSignalSpy(worker.finished)

    worker.run()

    try:
        assert json_spy.at(0)[0] == tmp
    except:
        pytest.fail("QSignalSpy instance error")
    assert json_spy.count() == 1
    assert finished_spy.count() == 1

def test_worker_connection_failed(worker, requests_mock, caplog):
    requests_mock.get(VERSION_FILE_URL, exc=requests.ConnectionError("No internet connection"))
    misc_spy = QSignalSpy(worker.misc_error)
    finished_spy = QSignalSpy(worker.finished)
    
    worker.run()

    try:
        assert misc_spy.at(0)[0] == "Couldn't connect to the server."
    except:
        pytest.fail("QSignalSpy instance error")
    assert "No internet connection" in caplog.text
    assert finished_spy.count() == 1

def test_worker_status_code_error(worker, requests_mock):
    requests_mock.get(VERSION_FILE_URL, json={}, status_code=404)
    status_code_error_spy = QSignalSpy(worker.status_code_error)
    finished_spy = QSignalSpy(worker.finished)

    worker.run()

    try:
        assert status_code_error_spy.at(0)[0] == 404
    except:
        pytest.fail("QSignalSpy instance error")
    assert finished_spy.count() == 1

def test_worker_parse_json_failed(worker, requests_mock):
    requests_mock.get(VERSION_FILE_URL, json=None, status_code=200)
    misc_error_spy = QSignalSpy(worker.misc_error)
    finished_spy = QSignalSpy(worker.finished)

    worker.run()

    try:
        assert misc_error_spy.at(0)[0] == "Parsing JSON failed."
    except:
        pytest.fail("QSignalSpy instance error")
    assert finished_spy.count() == 1
    
@patch("core.update_checker.Worker")
@patch("core.update_checker.QThread")
def test_runner_run(mock_qthread, mock_worker, runner):
    worker_instance = mock_worker.return_value
    thread_instance = mock_qthread.return_value

    runner.run()

    thread_instance.started.connect.assert_called_once_with(worker_instance.run)
    worker_instance.finished.connect.assert_called_once_with(runner.handleFinish)
    worker_instance.json.connect.assert_called_once_with(runner.json)
    worker_instance.status_code_error.connect.assert_called_once_with(runner.handleErrorStatusCode)
    worker_instance.misc_error.connect.assert_called_once_with(runner.handleError)
    worker_instance.moveToThread.assert_called_once_with(thread_instance)
    thread_instance.start.assert_called_once()

def test_runner_handleErrorStatusCode(runner):
    error_spy = QSignalSpy(runner.error)
    
    runner.handleErrorStatusCode(404)
    runner.handleErrorStatusCode(500)
    runner.handleErrorStatusCode(123)
    
    try:
        assert error_spy.at(0)[0] == "Version file not found."
        assert error_spy.at(1)[0] == "Internal server error."
        assert error_spy.at(2)[0] == "Error, status code: 123"
    except:
        pytest.fail("QSignalSpy instance error")

def test_runner_handleError(runner):
    error_spy = QSignalSpy(runner.error)

    runner.handleError("Custom error.")

    try:
        assert error_spy.at(0)[0] == "Custom error."
    except:
        pytest.fail("QSignalSpy instance error")

@patch("core.update_checker.Worker")
@patch("core.update_checker.QThread")
def test_runner_handleFinish(mock_qthread, mock_worker, runner):
    worker_instance = mock_worker.return_value
    thread_instance = mock_qthread.return_value
    runner.thread = thread_instance
    runner.worker = worker_instance

    runner.handleFinish()

    thread_instance.isRunning.assert_called_once()
    thread_instance.requestInterruption.assert_called_once()
    thread_instance.quit.assert_called_once()
    thread_instance.wait.assert_called_once()
    thread_instance.deleteLater.assert_called_once()
    assert runner.thread is None
    worker_instance.deleteLater.assert_called_once()
    assert runner.worker is None

def test_runner_handleFinish_not_started(runner):
    finished_spy = QSignalSpy(runner.finished)

    runner.handleFinish()
    
    assert finished_spy.count() == 1