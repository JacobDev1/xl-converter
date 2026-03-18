from unittest.mock import patch, MagicMock, call
import importlib
import types
import ctypes

import pytest

import core.timestamps as timestamps

def test_windows_constants():
    mock_kernel32 = MagicMock(name="kernel32")

    with (
        patch("core.timestamps.platform.system", return_value="Windows"),
        patch("core.timestamps.ctypes.WinDLL", return_value=mock_kernel32, create=True),
    ):
        import core.timestamps as win_ts
        importlib.reload(win_ts)
    
    assert win_ts.IS_WINDOWS          == True
    assert win_ts.GENERIC_WRITE       == 0x40000000
    assert win_ts.FILE_SHARE_READ     == 0x00000001
    assert win_ts.FILE_SHARE_WRITE    == 0x00000002
    assert win_ts.OPEN_EXISTING       == 3
    assert win_ts.EPOCH_AS_FILETIME   == 116444736000000000    # 100-ns ticks between 1601-01-01 and 1970-01-01.
    assert isinstance(win_ts.INVALID_HANDLE, int)

    ns = 10**9
    ft = win_ts._unix_to_filetime_ns(ns)
    ticks = ns // 100
    expected = ticks + win_ts.EPOCH_AS_FILETIME
    assert ft.dwLowDateTime == (expected & 0xFFFFFFFF)
    assert ft.dwHighDateTime == (expected >> 32)

    ft0 = win_ts._unix_to_filetime_ns(0)
    assert ft0.dwLowDateTime == (win_ts.EPOCH_AS_FILETIME & 0xFFFFFFFF)
    assert ft0.dwHighDateTime == (win_ts.EPOCH_AS_FILETIME >> 32)

@pytest.mark.parametrize("accessed, modified, created", [
    (0, 0, None),
    (123, 123, None),
    (0, 0, 123),
    (10**9, 10**9, 10**9),
])
def test_Timestamps_init_valid(accessed, modified, created):
    ts = timestamps.Timestamps(
        accessed=accessed,
        modified=modified,
        created=created,
    )
    assert ts.accessed == accessed
    assert ts.modified == modified
    assert ts.created == created

@pytest.mark.parametrize("field, value", [
    ("accessed", -1),
    ("modified", -1),
    ("created", -1),
])
def test_Timestamps_init_negative(field, value):
    kwargs = {
        "accessed": 10**9,
        "modified": 10**9,
        "created": 10**9,
    }
    kwargs[field] = value

    with pytest.raises(ValueError) as exc:
        timestamps.Timestamps(**kwargs)

    assert "cannot be smaller than 0" in str(exc.value)

@pytest.mark.parametrize("field, value", [
    ("accessed", "test"),
    ("modified", object()),
    ("created", {}),
])
def test_Timestamps_type_error(field, value):
    kwargs = {
        "accessed": 10**9,
        "modified": 10**9,
        "created": None,
    }
    kwargs[field] = value

    with pytest.raises(ValueError) as exc:
        timestamps.Timestamps(**kwargs)

    assert "expected int" in str(exc.value)


def test_getTimestamps_happy_path():
    accessed, modified, created = 0, 1, 2
    mock_stat = MagicMock()
    mock_stat.st_atime_ns = accessed
    mock_stat.st_mtime_ns = modified
    mock_stat.st_birthtime_ns = created

    with (
        patch("core.timestamps.os.path.isfile", return_value=True) as mock_isfile,
        patch("core.timestamps.os.stat", return_value=mock_stat) as mock_os_stat,
    ):
        ts = timestamps.getTimestamps("/tmp/test_file.jpg")

        mock_os_stat.assert_called_once_with("/tmp/test_file.jpg")
        mock_isfile.assert_called_once_with("/tmp/test_file.jpg")
        
        assert isinstance(ts, timestamps.Timestamps)
        assert ts.accessed == accessed
        assert ts.modified == modified
        assert ts.created == created

def test_getTimestamps_file_not_found():
    with (
        patch("core.timestamps.os.path.isfile", side_effect=FileNotFoundError) as mock_isfile,
        pytest.raises(FileNotFoundError),
    ):
        timestamps.getTimestamps("/tmp/test_file.jpg")

def test_getTimestamps_stat_exc():
    with (
        patch("core.timestamps.os.path.isfile", return_value=True) as mock_isfile,
        patch("core.timestamps.os.stat", side_effect=OSError),
        pytest.raises(OSError),
    ):
        timestamps.getTimestamps("/tmp/test_file.jpg")

def test_getTimestamps_validation_exc():
    with (
        patch("core.timestamps.os.path.isfile", return_value=True) as mock_isfile,
        patch("core.timestamps.os.stat"),
        patch("core.timestamps.Timestamps", side_effect=ValueError),
        pytest.raises(Exception, match="Timestamps validation failed"),
    ):
        timestamps.getTimestamps("/tmp/test_file.jpg")

def test_win32_handle_valid():
    mock_handle = MagicMock()

    with (
        patch("core.timestamps.kernel32.CreateFileW", return_value=mock_handle, create=True) as mock_CreateFileW,
        patch("core.timestamps.kernel32.CloseHandle", create=True) as mock_CloseHandle,
    ):
        with timestamps._win32_handle("/tmp/test_file.jpg") as handle:
            assert handle is mock_handle
        
        mock_CreateFileW.assert_called_once_with(
            "/tmp/test_file.jpg",
            timestamps.GENERIC_WRITE,
            timestamps.FILE_SHARE_READ | timestamps.FILE_SHARE_WRITE,
            None,
            timestamps.OPEN_EXISTING,
            0,
            None
        )
        mock_CloseHandle.assert_called_once_with(mock_handle)

def test_win32_handle_invalid():
    with (
        patch("core.timestamps.kernel32.CreateFileW", return_value=timestamps.INVALID_HANDLE, create=True) as mock_CreateFileW,
        patch("core.timestamps.kernel32.CloseHandle", create=True) as mock_CloseHandle,
        patch("core.timestamps.ctypes.get_last_error", return_value=5, create=True),
        patch("core.timestamps.ctypes.WinError", side_effect=OSError("win error"), create=True),
        pytest.raises(OSError) as exc,
    ):
        with timestamps._win32_handle("/tmp/test_file.jpg"):
            pass
        
    assert "win error" in str(exc.value)
    mock_CloseHandle.assert_not_called()

def test_applyTimestamps_file_not_found():
    with (
        patch("core.timestamps.os.path.isfile", return_value=False) as mock_isfile,
        pytest.raises(FileNotFoundError),
    ):
        timestamps.applyTimestamps("/tmp/test_file.jpg", MagicMock())

    mock_isfile.assert_called_once_with("/tmp/test_file.jpg")

@pytest.mark.parametrize("created", [True, False])
def test_applyTimestamps_happy_path_utime(created):
    timestamps_obj = timestamps.Timestamps(
        accessed=10**9,
        modified=10**9,
        created=None,
    )

    with (
        patch("core.timestamps.IS_WINDOWS", created),
        patch("core.timestamps.os.path.isfile", return_value=True) as mock_isfile,
        patch("core.timestamps.os.utime") as mock_utime,
    ):
        timestamps.applyTimestamps("/tmp/test_file.jpg", timestamps_obj)

        mock_isfile.assert_called_once_with("/tmp/test_file.jpg")
        mock_utime.assert_called_once_with(
            "/tmp/test_file.jpg",
            ns=(timestamps_obj.accessed, timestamps_obj.modified),
        )

def test_applyTimestamps_sad_path_utime():
    timestamps_obj = timestamps.Timestamps(
        accessed=10**9,
        modified=10**9,
        created=None,
    )

    with (
        patch("core.timestamps.IS_WINDOWS", False),
        patch("core.timestamps.os.path.isfile", return_value=True) as mock_isfile,
        patch("core.timestamps.os.utime", side_effect=OSError) as mock_utime,
        pytest.raises(OSError, match="Applying timestamps with os.utime failed")
    ):
        timestamps.applyTimestamps("/tmp/test_file.jpg", timestamps_obj)

    mock_isfile.assert_called_once_with("/tmp/test_file.jpg")
    mock_utime.assert_called_once_with(
        "/tmp/test_file.jpg",
        ns=(timestamps_obj.accessed, timestamps_obj.modified),
    )

def test_applyTimestamps_windows_happy_path():
    mock_handle = MagicMock()
    timestamps_obj = timestamps.Timestamps(
        accessed=12**9,
        modified=11**9,
        created=10**9,
    )

    with (
        patch("core.timestamps.IS_WINDOWS", True),
        patch("core.timestamps.os.path.isfile", return_value=True),
        patch("core.timestamps._win32_handle", return_value=mock_handle) as mock_win32_handle,
        patch("core.timestamps.kernel32.SetFileTime", return_value=True, create=True) as mock_SetFileTime,
        patch("core.timestamps.byref"),
        patch("core.timestamps._unix_to_filetime_ns") as mock_unix_to_filetime_ns,
    ):
        mock_win32_handle.return_value.__enter__.return_value = mock_handle

        timestamps.applyTimestamps("/tmp/test_file.jpg", timestamps_obj)
        
        mock_SetFileTime.assert_called_once()
        call_args = mock_SetFileTime.call_args[0]
        assert call_args[0] is mock_handle
        assert mock_unix_to_filetime_ns.call_args_list == [
            call(timestamps_obj.created),
            call(timestamps_obj.accessed),
            call(timestamps_obj.modified),
        ]


def test_applyTimestamps_windows_sad_path():
    mock_handle = MagicMock()
    timestamps_obj = timestamps.Timestamps(
        accessed=12**9,
        modified=11**9,
        created=10**9,
    )

    with (
        patch("core.timestamps.IS_WINDOWS", True),
        patch("core.timestamps.os.path.isfile", return_value=True),
        patch("core.timestamps._win32_handle", return_value=mock_handle) as mock_win32_handle,
        patch("core.timestamps.kernel32.SetFileTime", return_value=False, create=True) as mock_SetFileTime,
        patch("core.timestamps.byref"),
        patch("core.timestamps._unix_to_filetime_ns") as mock_unix_to_filetime_ns,
        patch("core.timestamps.ctypes.get_last_error", return_value="error", create=True),
        patch("core.timestamps.ctypes.WinError", side_effect=OSError, create=True),
        pytest.raises(OSError),
    ):
        mock_win32_handle.return_value.__enter__.return_value = mock_handle

        timestamps.applyTimestamps("/tmp/test_file.jpg", timestamps_obj)
        
    mock_SetFileTime.assert_called_once()

