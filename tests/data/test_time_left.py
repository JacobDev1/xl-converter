from unittest.mock import patch, MagicMock

import pytest
from PySide6.QtCore import QTimer
from PySide6.QtTest import QSignalSpy

from data.time_left import TimeLeft

@pytest.fixture
def time_left():
    return TimeLeft()

def test_init(time_left):
    assert time_left.est_time_left_s is None
    assert time_left.start_time is None
    assert time_left.item_count == 0
    assert time_left.completed_item_count == 0
    assert isinstance(time_left.timer, QTimer)
    assert time_left.timer.interval() == 1000

def test_startCounting(time_left):
    time_left.timer = MagicMock()
    time_left._updateEstimation = MagicMock()
    time_left._emitEstimationUpdated = MagicMock()

    time_left.startCounting(10)

    assert time_left.start_time is not None
    assert time_left.item_count == 10
    assert time_left.completed_item_count == 0
    time_left.timer.start.assert_called_once()
    time_left._updateEstimation.assert_called_once()
    time_left._emitEstimationUpdated.assert_called_once()

def test_stopCounting(time_left):
    time_left.timer = MagicMock()

    time_left.stopCounting()

    time_left.timer.stop.assert_called_once()
    assert time_left.est_time_left_s is None
    assert time_left.start_time is None
    assert time_left.item_count == 0
    assert time_left.completed_item_count == 0

def test_addCompletedItem(time_left):
    time_left._updateEstimation = MagicMock()

    time_left.startCounting(100)
    time_left.addCompletedItem()

    assert time_left.completed_item_count == 1

@patch("time.time", side_effect=[10, 20])
def test__updateEstimation(mock_time, caplog, time_left):
    time_left.item_count = 10
    time_left.completed_item_count = 0
    time_left.start_time = 0

    tmp = []
    for i in range(3):
        time_left._updateEstimation()
        time_left.completed_item_count += 1
        tmp.append(time_left.est_time_left_s)

    assert tmp[0] is None
    assert round(tmp[1]) == 90
    assert tmp[2] < 90

def test__updateEstimation_setup_error(caplog, time_left):
    time_left._updateEstimation()
    assert "Setup error" in caplog.text
    caplog.clear()

    time_left.item_count = 20
    time_left.start_time = 0
    time_left.est_time_left_s = 50
    time_left._updateEstimation()
    assert time_left.est_time_left_s is None

def test__emitEstimationUpdated_started(time_left):
    time_left._formatOutput = MagicMock(return_value="100 s left")
    spy = QSignalSpy(time_left.update_time_left)
    time_left.est_time_left_s = 100

    time_left._emitEstimationUpdated()

    time_left._formatOutput.assert_called_once_with(100)
    assert spy.at(0)[0] == "100 s left"

def test__emitEstimationUpdated_not_started(time_left):
    spy = QSignalSpy(time_left.update_time_left)
    time_left._emitEstimationUpdated()
    assert spy.at(0)[0] == "Calculating time left..."

def test__updateEstimationTimer(time_left):
    time_left._updateEstimation = MagicMock()
    time_left.est_time_left_s = 10
    time_left._emitEstimationUpdated = MagicMock()

    time_left._updateEstimationTimer()

    time_left._updateEstimation.assert_called_once()
    time_left._emitEstimationUpdated.assert_called_once()
    assert time_left.est_time_left_s == 9

def test__formatOutput(time_left):
    assert time_left._formatOutput(0.5) == "Almost done..."
    assert time_left._formatOutput(-1) == "Almost done..."
    assert time_left._formatOutput(2) == "2 s left"
    assert time_left._formatOutput(60) == "1 m left"
    assert time_left._formatOutput(90) == "1 m 30 s left"
    assert time_left._formatOutput(120) == "2 m left"
    assert time_left._formatOutput(60 * 60) == "1 h left"
    assert time_left._formatOutput(60 * 60 + 60 * 30 + 30) == "1 h 30 m 30 s left"
    assert time_left._formatOutput(60 * 60 * 24) == "1 d left"
    assert time_left._formatOutput(60 * 60 * 24 + 1) == "1 d 1 s left"