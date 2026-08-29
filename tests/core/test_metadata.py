from unittest.mock import patch, MagicMock

import pytest

import core.metadata as metadata
import data.constants as constants
from core.exceptions import FileException

def test_runExifTool():
    with (
        patch("core.metadata._runExifTool") as mock_run,
    ):
        metadata.runExifTool(
            "/path/to/src.jpg",
            "/path/to/dst.jpg",
            ["-tagsFromFile", "$src", "$dst", "-overwrite_original"],
        )
        mock_run.assert_called_once_with(
            "-tagsFromFile",
            "/path/to/src.jpg",
            "/path/to/dst.jpg",
            "-overwrite_original"
        )

# @pytest.mark.parametrize("system", [ "Linux", "Darwin" ])
# def test__runExifTool_posix(system):
#     with (
#         patch("platform.system", return_value=system),
#         patch("core.metadata.runProcess2") as mock_runProcess2,
#     ):
#         et_args = "-arg1", "-arg2"
#         metadata._runExifTool(et_args)
#         mock_runProcess2.assert_called_once_with("exiftool", et_args)

def test__runExifTool_linux():
    with (
        patch("platform.system", return_value="Linux"),
        patch("core.metadata.runProcess2") as mock_runProcess2,
    ):
        et_args = "-arg1", "-arg2"
        metadata._runExifTool(et_args)
        mock_runProcess2.assert_called_once_with("exiftool", et_args)

def test__runExifTool_darwin():
    with (
        patch("platform.system", return_value="Darwin"),
        patch("core.metadata.runProcess2") as mock_runProcess2,
        patch("core.metadata.EXIFTOOL_PATH", "/tmp/exiftool") as var_EXIFTOOL_PATH,
    ):
        et_args = "-arg1", "-arg2"
        metadata._runExifTool(et_args)
        mock_runProcess2.assert_called_once_with(var_EXIFTOOL_PATH, et_args)

def test__runExifTool_windows():
    with (
        patch("platform.system", return_value="Windows"),
        patch("core.metadata.runProcess2") as mock_run,
        patch("os.unlink") as mock_unlink,
        patch("tempfile.NamedTemporaryFile") as mock_tempfile,
        patch("os.path.basename", return_value="tmp_file_name"),
        patch("os.path.dirname", return_value="tmp_dir_name"),
    ):
        # Arrange
        mock_file = MagicMock()
        mock_file.name = "/tmp/xl-converter/test.txt"
        mock_tempfile.return_value.__enter__.return_value = mock_file
        
        # Run
        metadata._runExifTool("-arg1", "-arg2")

        # Assert
        mock_file.write.assert_called_once_with("-arg1\n-arg2")
        mock_unlink.assert_called_once_with("/tmp/xl-converter/test.txt")
        mock_run.assert_called_once_with(
            constants.EXIFTOOL_PATH,
            "-charset",
            "filename=UTF8",
            "-@",
            "tmp_file_name",
            cwd="tmp_dir_name",
        )

def test__runExifTool_windows_cleanup_exc():
    with (
        patch("platform.system", return_value="Windows"),
        patch("core.metadata.runProcess2"),
        patch("os.unlink"),
        patch("tempfile.NamedTemporaryFile") as mock_tempfile,
    ):
        mock_tempfile.side_effect = OSError("error")

        with pytest.raises(FileException) as exc:
            metadata._runExifTool("-arg1", "-arg2")
        assert "error" in str(exc.value)

def test__runExifTool_windows_file_exc():
    with (
        patch("platform.system", return_value="Windows"),
        patch("core.metadata.runProcess2"),
        patch("os.unlink", side_effect=OSError("error")),
        patch("tempfile.NamedTemporaryFile") as mock_tempfile,
    ):
        mock_tempfile.return_value.__enter__.return_value = MagicMock()

        with pytest.raises(FileException) as exc:
            metadata._runExifTool("-arg1", "-arg2")
        assert "error" in str(exc.value)

@pytest.fixture
def reset_data():
    metadata.Data.exiftool_available = None
    metadata.Data.exiftool_err_msg = ""
    yield
    metadata.Data.exiftool_available = None
    metadata.Data.exiftool_err_msg = ""

@pytest.mark.parametrize("system, output, expected", [
    ("Darwin", ("", ""), (True, "")),
    ("Windows", ("12.40",""), (True, "")),
    ("Windows", ("",""), (False, "Please reinstall this program")),
    ("Windows", ("","assertion failed"), (False, "Please reinstall this program")),
])
def test_isExifToolAvailable_win(reset_data, system, output, expected):
    with (
        patch("core.metadata.platform.system", return_value=system),
        patch("core.metadata.runProcess2", return_value=output)
    ):
        is_available, err_msg = metadata.isExifToolAvailable()
        assert is_available == expected[0]
        assert type(expected[1]) is str
        assert expected[1] in err_msg

@pytest.mark.parametrize(
    "shutil_which, expected_exiftool_available, expected_err_msg", [
    ("/usr/bin/exiftool", True, ""),
    (None, False, "ExifTool not found"),
])
def test_isExifToolAvailable_linux(reset_data, shutil_which, expected_exiftool_available, expected_err_msg):
    with (
        patch("core.metadata.platform.system", return_value="Linux"),
        patch("core.metadata.shutil.which", return_value=shutil_which),
    ):
        is_available, err_msg = metadata.isExifToolAvailable()
        assert is_available == expected_exiftool_available
        if expected_err_msg:
            assert expected_err_msg in err_msg
        else:
            assert not err_msg

def test_cached_data(reset_data):
    metadata.Data.exiftool_available = False
    metadata.Data.exiftool_err_msg = "Cached error"
    assert metadata.isExifToolAvailable() == (False, "Cached error")
    
    metadata.Data.exiftool_available = True
    metadata.Data.exiftool_err_msg = "No error"
    assert metadata.isExifToolAvailable() == (True, "No error")

@pytest.mark.parametrize("encoder, mode, jpg_to_jxl_lossless, expected", [
    ("any", "any", False, []),
    ("any", "Encoder - Preserve", False, []),
    ("any", "Encoder - Wipe", False, []),
    (constants.CJXL_PATH, "Encoder - Wipe", False, ["-x strip=exif", "-x strip=xmp", "-x strip=jumbf"]),
    (constants.CJXL_PATH, "Encoder - Wipe", True, []),
    (constants.IMAGE_MAGICK_PATH, "Encoder - Wipe", False, ["-strip"]),
    (constants.AVIFENC_PATH, "Encoder - Wipe", False, ["--ignore-exif", "--ignore-xmp"]),
])
def test_getArgs(encoder, mode, jpg_to_jxl_lossless, expected):
    assert metadata.getArgs(
        encoder, mode, jpg_to_jxl_lossless
    ) == expected
