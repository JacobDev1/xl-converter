from unittest.mock import patch, MagicMock, ANY
import subprocess
import os

import pytest

from core.process import (
    _getStartupInfo,
    runProcess,
    runProcessOutput,
)

def test___getStartupInfo_windows():
    if os.name == "nt":
        with patch("core.process.subprocess.STARTUPINFO") as mock_startupinfo:
            startupinfo_instance = MagicMock()
            mock_startupinfo.return_value = startupinfo_instance
            startupinfo_instance.dwFlags = subprocess.STARTF_USESHOWWINDOW
            startupinfo_instance.wShowWindow = subprocess.SW_HIDE

            assert startupinfo_instance.dwFlags == subprocess.STARTF_USESHOWWINDOW
            assert startupinfo_instance.wShowWindow == subprocess.SW_HIDE
            assert _getStartupInfo() is startupinfo_instance
    else:
        assert _getStartupInfo() is None

# subprocess.run mock
class MockCompletedProcess:
    def __init__(self, stdout, stdin):
        self.stdout = stdout
        self.stdin = stdin

@pytest.mark.parametrize(
    "cmd,expected_stdout", [
        (("echo", "Hello World"), b"Hello World\n"),
    ]
)

def test_runProcess(cmd, expected_stdout):
    with patch("core.process.subprocess.run") as mock_run, \
        patch("core.process.logging") as mock_logging:
    
        mock_run.return_value = MockCompletedProcess(stdout=expected_stdout, stdin=b"")
        runProcess(*cmd)

        mock_run.assert_called_with(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=ANY, cwd=None)

        if expected_stdout:
            mock_logging.debug.assert_any_call(expected_stdout.decode())
        
        mock_logging.info.assert_called_with(f"Running command: {cmd}")

@pytest.mark.parametrize(
    "cmd,expected_stdout", [
        (("echo", "Hello World"), b"Hello World\n"),
    ]
)

def test_runProcessOutput(cmd, expected_stdout):
    with patch("core.process.subprocess.run") as mock_run, \
        patch("core.process.logging") as mock_logging:
    
        mock_run.return_value = MockCompletedProcess(stdout=expected_stdout, stdin=b"")
        output = runProcessOutput(*cmd)

        mock_run.assert_called_with(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, startupinfo=ANY)

        if expected_stdout:
            mock_logging.debug.assert_any_call(expected_stdout.decode())
            assert output == expected_stdout
        else:
            assert output is None

        mock_logging.info.assert_called_with(f"Running command with output: {cmd}")