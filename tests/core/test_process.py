from unittest.mock import patch, MagicMock, ANY, call
import subprocess
import os
import logging
from contextlib import ExitStack
import importlib

import pytest
import psutil

import core.process as process

def test_runProcessOutput():
    with (
        patch("core.process.subprocess.run") as mock_run,
        patch("core.process.logging") as mock_logging,
    ):
        mock_run.return_value = subprocess.CompletedProcess(args=["echo", "test"], stdout=b"test", stderr=b"err", returncode=0)

        assert process.runProcessOutput(["echo", "test"]) == ("test", "err")

@pytest.fixture
def runProcess2_patches():
    mock_popen = MagicMock()
    mock_popen.communicate.return_value = (b"stdout", b"")

    patches = {
        "Popen": patch("core.process.psutil.Popen", return_value=mock_popen),
        "logging.info": patch("core.process.logging.info"),
        "ProcessManager.addProcess": patch("data.process_manager.ProcessManager.addProcess"),
        "ProcessManager.removeProcess": patch("data.process_manager.ProcessManager.removeProcess"),
        "_setProcessPriority": patch("core.process._setProcessPriority"),
        "ProcessPriorityManager.getPriorityFlag": patch("data.process_manager.ProcessPriorityManager.getPriorityFlag", return_value=0b10),

    }
    with ExitStack() as stack:
        _mocks = { name: stack.enter_context(patcher) for name, patcher in patches.items() }
        yield _mocks

def test_runProcess2_happy_path(runProcess2_patches):
    cmd = ("echo", "Hello world")
    stdout = b"Hello world\n"
    stderr = b""

    mock_process = runProcess2_patches["Popen"].return_value
    mock_process.communicate.return_value = (stdout, stderr)

    process.runProcess2(*cmd)

    runProcess2_patches["Popen"].assert_called_once_with(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        creationflags=ANY,
        cwd=None,
    )

    runProcess2_patches["_setProcessPriority"].assert_called_once_with(mock_process, 0b10)
    runProcess2_patches["ProcessManager.addProcess"].assert_called_once_with(mock_process)
    runProcess2_patches["ProcessManager.removeProcess"].assert_called_once_with(mock_process)
    mock_process.communicate.assert_called_once()

    mock_logging_info = runProcess2_patches["logging.info"]
    assert len(mock_logging_info.call_args_list) == 2
    assert mock_logging_info.call_args_list[0][0][0] == f"[runProcess2] {cmd}"
    assert mock_logging_info.call_args_list[1][0][0] == f"[runProcess2] {stdout.decode('utf-8')}"

def test_runProcess2_no_output(runProcess2_patches):
    runProcess2_patches["Popen"].return_value.communicate.return_value = (None, None)
    assert process.runProcess2(["bin", "-arg", "sample.png"]) == ("", "")

CREATE_NO_WINDOW_FLAG = 0x08000000      # Undefined on POSIX 

@pytest.mark.parametrize("system, expected_creationflags", [
    ("Windows", CREATE_NO_WINDOW_FLAG),
    ("Linux", 0),
])
def test_runProcess2_creationflags(system, expected_creationflags, runProcess2_patches, monkeypatch):
    monkeypatch.setattr(process, "SYSTEM", system)
    monkeypatch.setattr(subprocess, "CREATE_NO_WINDOW", CREATE_NO_WINDOW_FLAG, raising=False)

    process.runProcess2("echo", "test")

    runProcess2_patches["Popen"].assert_called_once_with(
        ("echo", "test"),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=None,
        creationflags=expected_creationflags,
    )

def test__setProcessPriority_none(caplog):
    with caplog.at_level(logging.ERROR):
        process._setProcessPriority(MagicMock(), None)
        assert "Received None priority" in caplog.text

def test__setProcessPriority_valid_priority():
    mock_process = MagicMock()
    process._setProcessPriority(mock_process, 0b10)
    mock_process.nice.assert_called_once_with(0b10)

@pytest.mark.parametrize("exception", [ValueError, psutil.Error])
def test__setProcessPriority_error(exception, caplog):
    mock_process = MagicMock()
    mock_process.nice.side_effect = exception
    with caplog.at_level(logging.ERROR):
        process._setProcessPriority(mock_process, 0b10)
        mock_process.nice.assert_called_once_with(0b10)
        assert "Failed to set process priority" in caplog.text
