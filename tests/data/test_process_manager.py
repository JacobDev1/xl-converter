import subprocess
import logging
from unittest.mock import patch, MagicMock
import importlib

import pytest
import psutil

from data.process_manager import ProcessManager, ProcessPriority, ProcessPriorityManager
import data.process_manager as process_manager

@pytest.fixture(autouse=True)
def reset():
    ProcessManager.processes.clear()
    yield ProcessManager
    ProcessManager.processes.clear()

def test_addProcess_happy_path():
    mock_process = MagicMock(spec=subprocess.Popen)

    with patch.object(ProcessManager, "lock", MagicMock()) as mock_lock:
        ProcessManager.addProcess(mock_process)
        assert mock_process in ProcessManager.processes
        mock_lock.__enter__.assert_called_once()
        mock_lock.__exit__.assert_called_once()

def test_addProcess_invalid_type():
    with pytest.raises(TypeError):
        ProcessManager.addProcess("invalid")

def test_removeProcess_happy_path():
    process_to_remove = MagicMock(spec=subprocess.Popen)
    ProcessManager.processes = [
        *[MagicMock(spec=subprocess.Popen) for _ in range(3)],
        process_to_remove
    ]

    assert process_to_remove in ProcessManager.processes
    with patch.object(ProcessManager, "lock", MagicMock()) as mock_lock:
        ProcessManager.removeProcess(process_to_remove)
        assert process_to_remove not in ProcessManager.processes
        assert len(ProcessManager.processes) > 0
        mock_lock.__enter__.assert_called_once()
        mock_lock.__exit__.assert_called_once()

def test_removeProcess_invalid_type():
    with pytest.raises(TypeError):
        ProcessManager.removeProcess("invalid")

def test_removeProcess_non_existent():
    ProcessManager.removeProcess(MagicMock(spec=subprocess.Popen))

def test_terminateAll_full():
    mock_processes = [MagicMock(spec=subprocess.Popen) for _ in range(5)]
    ProcessManager.processes = mock_processes

    ProcessManager.terminateAll()

    assert ProcessManager.processes == []
    for mock_process in mock_processes:
        mock_process.terminate.assert_called_once()
        mock_process.wait.assert_called_once()

def test_terminateAll_empty():
    ProcessManager.processes = []
    ProcessManager.terminateAll()
    # Nothing raised

def test_terminateAll_no_such_process():
    mock_process = MagicMock(spec=psutil.Popen)
    mock_process.terminate.side_effect = psutil.NoSuchProcess(pid=123)
    ProcessManager.processes = [mock_process]

    ProcessManager.terminateAll()
    # Nothing raised

    assert ProcessManager.processes == []
    mock_process.terminate.assert_called_once()
    mock_process.wait.assert_called_once()

def test_terminateAll_sad_path(caplog):
    mock_process = MagicMock(spec=psutil.Popen)
    mock_process.terminate.side_effect = psutil.AccessDenied(pid=123)
    ProcessManager.processes = [mock_process]

    ProcessManager.terminateAll()

    assert "Failed to terminate process" in caplog.text

def test_clear():
    ProcessManager.processes = [MagicMock(spec=subprocess.Popen) for _ in range(3)]

    with patch.object(ProcessManager, "lock", MagicMock()) as mock_lock:
        ProcessManager.clear()
        assert ProcessManager.processes == []
        mock_lock.__enter__.assert_called_once()
        mock_lock.__exit__.assert_called_once()

@pytest.mark.parametrize("platform, max_niceness", [
    ("Linux", 19),
    ("Darwin", 20),
])
def test_ProcessPriorityManager_idle_niceness(platform, max_niceness, monkeypatch):
    monkeypatch.setattr("platform.system", lambda: platform)
    importlib.reload(process_manager)
    assert process_manager.ProcessPriorityManager._PROCESS_PRIORITY_MAP[ProcessPriority.IDLE] == max_niceness

def test_ProcessPriorityManager_setPriority_update_state(monkeypatch):
    mock_lock = MagicMock()
    monkeypatch.setattr(ProcessPriorityManager, "lock", mock_lock, raising=False)
    monkeypatch.setattr(ProcessPriorityManager, "priority", ProcessPriority.NORMAL, raising=False)

    ProcessPriorityManager.setPriority(ProcessPriority.HIGH)
    
    assert ProcessPriorityManager.priority == ProcessPriority.HIGH
    mock_lock.__enter__.assert_called_once()
    mock_lock.__exit__.assert_called_once()

def test_ProcessPriorityManager_getPriorityFlag_return_value(monkeypatch):
    mock_lock = MagicMock()
    monkeypatch.setattr(ProcessPriorityManager, "lock", mock_lock, raising=False)
    monkeypatch.setattr(ProcessPriorityManager, "priority", ProcessPriority.HIGH, raising=False)
    monkeypatch.setattr(
        ProcessPriorityManager,
        "_PROCESS_PRIORITY_MAP",
        { ProcessPriority.HIGH: 0b10},
        raising=False,
    )

    assert ProcessPriorityManager.getPriorityFlag() == 0b10
    
    assert ProcessPriorityManager.priority == ProcessPriority.HIGH
    mock_lock.__enter__.assert_called_once()
    mock_lock.__exit__.assert_called_once()


def test_ProcessPriorityManager_getPriorityFlag_unmapped_value(monkeypatch, caplog):
    mock_lock = MagicMock()
    monkeypatch.setattr(ProcessPriorityManager, "lock", mock_lock, raising=False)
    monkeypatch.setattr(ProcessPriorityManager, "priority", ProcessPriority.HIGH, raising=False)
    monkeypatch.setattr(ProcessPriorityManager, "_PROCESS_PRIORITY_MAP", {}, raising=False)

    with caplog.at_level(logging.ERROR):
        assert ProcessPriorityManager.getPriorityFlag() == None
        assert "Priority not mapped" in caplog.text
    
    mock_lock.__enter__.assert_called_once()
    mock_lock.__exit__.assert_called_once()
