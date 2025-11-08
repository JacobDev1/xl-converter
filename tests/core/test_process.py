from unittest.mock import patch, MagicMock, ANY, call
import subprocess
import os
import logging

import pytest
import psutil

import core.process as process

def test___getStartupInfo_posix():
    with patch("core.process.platform.system", return_value="Linux"):
        assert process._getStartupInfo() is None

def test___getStartupInfo_windows():
    startupinfo_instance = MagicMock()
    startupinfo_instance.dwFlags = 0
    startupinfo_instance.wShowWindow = 0

    with (
        patch("core.process.subprocess.STARTUPINFO", return_value=startupinfo_instance, create=True) as mock_startupinfo,
        patch("core.process.subprocess.STARTF_USESHOWWINDOW", 1, create=True),
        patch("core.process.subprocess.SW_HIDE", 2, create=True),
        patch("core.process.platform.system", return_value="Windows"),
    ):
        assert process._getStartupInfo() is startupinfo_instance
        assert startupinfo_instance.dwFlags == 1
        assert startupinfo_instance.wShowWindow == 2
        mock_startupinfo.assert_called_once()

def test_runProcess():
    cmd = ("echo", "Hello world")
    expected_stdout = b"Hello world\n"
    expected_stderr = b""

    with (
        patch("core.process.subprocess.Popen", autospec=True) as mock_popen,
        patch("core.process.logging.info") as mock_logging_info,
        patch("data.process_manager.ProcessManager.addProcess") as mock_addProcess,
        patch("data.process_manager.ProcessManager.removeProcess") as mock_removeProcess,
    ):
        mock_process = mock_popen.return_value
        mock_process.communicate.return_value = (expected_stdout, expected_stderr)

        process.runProcess(*cmd)

        mock_popen.assert_called_once_with(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=ANY, cwd=None)
        mock_addProcess.assert_called_once_with(mock_process)
        mock_removeProcess.assert_called_once_with(mock_process)
        mock_process.communicate.assert_called_once()
        assert len(mock_logging_info.call_args_list) == 2
        assert mock_logging_info.call_args_list[0][0][0] == f"[runProcess] {cmd}"
        assert mock_logging_info.call_args_list[1][0][0] == f"[runProcess] {expected_stdout.decode('utf-8')}"

def test_runProcessOutput():
    with (
        patch("core.process.subprocess.run") as mock_run,
        patch("core.process.logging") as mock_logging,
    ):
        mock_run.return_value = subprocess.CompletedProcess(args=["echo", "test"], stdout=b"test", stderr=b"err", returncode=0)

        assert process.runProcessOutput(["echo", "test"]) == ("test", "err")

def test_runProcess2_happy_path():
    cmd = ("echo", "Hello world")
    stdout = b"Hello world\n"
    stderr = b""

    with (
        patch("core.process.psutil.Popen") as mock_popen,
        patch("core.process.logging.info") as mock_logging_info,
        patch("data.process_manager.ProcessManager.addProcess") as mock_addProcess,
        patch("data.process_manager.ProcessManager.removeProcess") as mock_removeProcess,
        patch("core.process._setProcessPriority") as mock__setProcessPriority,
        patch("data.process_manager.ProcessPriorityManager.getPriorityFlag", return_value=0b10),
    ):
        mock_process = mock_popen.return_value
        mock_process.communicate.return_value = (stdout, stderr)

        process.runProcess2(*cmd)

        mock_popen.assert_called_once_with(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=ANY, cwd=None)
        mock__setProcessPriority.assert_called_once_with(mock_popen.return_value, 0b10)
        mock_addProcess.assert_called_once_with(mock_process)
        mock_removeProcess.assert_called_once_with(mock_process)
        mock_process.communicate.assert_called_once()
        assert len(mock_logging_info.call_args_list) == 2
        assert mock_logging_info.call_args_list[0][0][0] == f"[runProcess2] {cmd}"
        assert mock_logging_info.call_args_list[1][0][0] == f"[runProcess2] {stdout.decode('utf-8')}"

def test_runProcess2_no_output():
    with (
        patch("core.process.psutil.Popen") as mock_popen,
        patch("core.process.logging.info"),
        patch("data.process_manager.ProcessManager.addProcess"),
        patch("data.process_manager.ProcessManager.removeProcess"),
        patch("core.process._setProcessPriority"),
        patch("data.process_manager.ProcessPriorityManager.getPriorityFlag", return_value=0b10),
    ):
        mock_popen.return_value.communicate.return_value = (None, None)

        assert process.runProcess2(["bin", "-arg", "sample.png"]) == ("", "")

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
