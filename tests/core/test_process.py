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
        assert cmd[1] in mock_logging.debug.call_args[0][0]
        assert str(cmd) in mock_logging.info.call_args[0][0]

def test_runProcessOutput():
    with (
        patch("core.process.subprocess.run") as mock_run,
        patch("core.process.logging") as mock_logging,
    ):
        mock_run.return_value = subprocess.CompletedProcess(args=["echo", "test"], stdout=b"test", stderr=b"err", returncode=0)

        out, err = runProcessOutput(["echo", "test"])

        assert out == "test"
        assert err == "err"