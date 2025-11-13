import os
from unittest.mock import patch, MagicMock, call

import pytest
from PySide6.QtCore import QMutex

import core.downscale as downscale
from core.exceptions import CancellationException, FileException, GenericException
from data.constants import IMAGE_MAGICK_PATH, ALLOWED_RESAMPLING

# ------------------------------------------------------------
#                           Math
# ------------------------------------------------------------

def test__linearRegression():
    x = [1, 2, 3]
    y = [2, 4, 6]

    slope, intercept = downscale._linearRegression(x, y)

    assert slope == 2
    assert intercept == 0

def test__extrapolateScale():
    sample_points = [
        [100*1024, 66],
        [40*1024, 33],
    ]

    assert downscale._extrapolateScale(sample_points, 40*1024) == 33
    assert downscale._extrapolateScale(sample_points, 100*1024) == 66

# ------------------------------------------------------------
#                           Helper
# ------------------------------------------------------------

def test__downscaleToPercent_happy_path():
    custom_resampling = ALLOWED_RESAMPLING[0]
    with patch("core.downscale.runBinary") as mock_runBinary:
        downscale._downscaleToPercent("src.png", "dst.png", 33, custom_resampling)
        mock_runBinary.assert_called_once_with(
            IMAGE_MAGICK_PATH,
            [f"-filter {custom_resampling}", "-resize 33%"],
            "src.png", "dst.png",
            args_after_input=True, delete_if_canceled=[]
        )

def test__downscaleToPercent_cleanup():
    custom_resampling = ALLOWED_RESAMPLING[0]
    with patch("core.downscale.runBinary") as mock_runBinary:
        downscale._downscaleToPercent(
            "src.png", "dst.png",
            33, custom_resampling,
            delete_if_canceled=["dst.png"]
        )
        mock_runBinary.assert_called_once_with(
            IMAGE_MAGICK_PATH,
            [f"-filter {custom_resampling}", "-resize 33%"],
            "src.png", "dst.png",
            args_after_input=True, delete_if_canceled=["dst.png"],
        )

def test__getFileSize_getsize_success():
    sample_size = 300 * 1024
    sample_file_path = "/tmp/file.jpg"
    with (
        patch("core.downscale.os.path.getsize", return_value=sample_size) as mock_getsize,
        patch("core.downscale.os.remove") as mock_remove,
    ):
        assert downscale._getFileSize(sample_file_path) == sample_size
        mock_getsize.assert_called_once_with(sample_file_path)
        mock_remove.assert_not_called()

def test__getFileSize_getsize_failed():
    sample_file_path = "/tmp/file.jpg"
    with (
        patch("core.downscale.os.path.getsize", side_effect=OSError("Failed")) as mock_getsize,
        patch("core.downscale.os.remove") as mock_remove,
        pytest.raises(OSError) as exc_info,
    ):
        downscale._getFileSize(sample_file_path)
    assert "Failed" == str(exc_info.value)
    mock_getsize.assert_called_once_with(sample_file_path)
    mock_remove.assert_not_called()

def test__getFileSize_cleanup_on_getsize_failed():
    sample_cleanup_targets = [
        "/tmp/file1.jpg", "/tmp/file2.jpg",
    ]
    with (
        patch("core.downscale.os.path.getsize", side_effect=OSError) as mock_getsize,
        patch("core.downscale.os.remove") as mock_remove,
        pytest.raises(OSError) as exc_info,
    ):
        downscale._getFileSize("/tmp/file.jpg", cleanup_targets=sample_cleanup_targets)
    assert mock_remove.call_count == 2
    for i, target in enumerate(sample_cleanup_targets):
        assert mock_remove.call_args_list[i][0][0] == target

def test__checkForSuccess_file_exists():
    with (
        patch("core.downscale.os.path.isfile", return_value=True) as mock_isfile,
        patch("core.downscale.os.remove") as mock_remove,
    ):
        downscale._checkForSuccess("NO_ID", "/tmp/file.jpg")
        mock_isfile.assert_called_once_with("/tmp/file.jpg")
        mock_remove.assert_not_called()

def test__checkForSuccess_file_missing():
    with (
        patch("core.downscale.os.path.isfile", return_value=False) as mock_isfile,
        patch("core.downscale.os.remove") as mock_remove,
        pytest.raises(FileException) as exc_info,
    ):
        downscale._checkForSuccess("ID0", "/tmp/file.jpg")
    mock_isfile.assert_called_once_with("/tmp/file.jpg")
    assert "ID0" == exc_info.value.id

def test__checkForSuccess_cleanup():
    sample_cleanup_targets = [
        "/tmp/file1.jpg", "/tmp/file2.jpg",
    ]
    with (
        patch("core.downscale.os.path.isfile", return_value=False) as mock_isfile,
        patch("core.downscale.os.remove") as mock_remove,
        pytest.raises(FileException) as exc_info,
    ):
        downscale._checkForSuccess("ID0", "/tmp/file.jpg", sample_cleanup_targets)
    mock_isfile.assert_called_once_with("/tmp/file.jpg")
    assert "ID0" == exc_info.value.id
    assert mock_remove.call_count == 2
    for i, target in enumerate(sample_cleanup_targets):
        mock_remove.args_call_list[i][0][0] == target

def test__checkForSuccess_cleanup_failed():
    sample_cleanup_targets = [
        "/tmp/file1.jpg", "/tmp/file2.jpg",
    ]
    with (
        patch("core.downscale.os.path.isfile", return_value=False) as mock_isfile,
        patch("core.downscale.os.remove", side_effect=OSError) as mock_remove,
        # Testing if FileException, not OSError is raised.
        pytest.raises(FileException) as exc_info,
    ):
        downscale._checkForSuccess("ID0", "/tmp/file.jpg", sample_cleanup_targets)
    mock_isfile.assert_called_once_with("/tmp/file.jpg")
    assert mock_remove.call_count == 2

def test__deleteFile_happy_path():
    with (
        patch("core.downscale.os.remove") as mock_remove,
    ):
        downscale._deleteFile("/tmp/image.jpg")
        mock_remove.assert_called_once_with("/tmp/image.jpg")
        # No exceptions raised...

def test__deleteFile_sad_path_raising_false():
    with (
        patch("core.downscale.os.remove", side_effect=OSError) as mock_remove,
    ):
        downscale._deleteFile("/tmp/image.jpg", raising=False)
        # No exceptions raised...

def test__deleteFile_sad_path_raising_true():
    with (
        patch("core.downscale.os.remove", side_effect=OSError) as mock_remove,
        pytest.raises(FileException) as exc_info,
    ):
        downscale._deleteFile("/tmp/image.jpg", raising=True, exc_id="ID0")
    assert "ID0" == exc_info.value.id

# ------------------------------------------------------------
#                           Scaling
# ------------------------------------------------------------

@pytest.fixture
def params_fixture():
    return {
        "mode": "Percent",
        "enc": "path/to/enc",
        "format": "JPEG XL",
        "jxl_int_e": False,
        "src": "path/to/src.png",
        "dst": "path/to/dst.png",
        "dst_dir": "path/to",
        "name": "image",
        "args": [],
        "percent": 50,
        "resample": "Default",
        "n": 0,
    }

def test__downscaleToFileSize_gather_data(params_fixture):
    params_fixture.update({
        "mode": "File Size",
        "max_size": 300,
        "jxl_int_e": False,
        "args": ["-arg1", "-arg2"],
    })
    mutex = MagicMock(spec=QMutex)
    proxy_src = "/tmp/proxy.png"
    with (
        patch("core.downscale.getUniqueTmpFilePath", return_value=proxy_src) as mock_getUniqueTmpFilePath,
        patch("core.downscale._downscaleToPercent") as mock__downscaleToPercent,
        patch("core.downscale._getFileSize", side_effect=[500_000, 200_000, 300_000]) as mock__getFileSize,
        patch("core.downscale.runBinary") as mock_runBinary,
        patch("core.downscale.QMutexLocker") as mock_QMutexLocker,
        patch("core.downscale._checkForSuccess") as mock__checkForSuccess,
        patch("core.downscale._deleteFile") as mock__deleteFile,
        patch("core.downscale._extrapolateScale", return_value=40) as mock__extrapolatedScale,
    ):
        downscale._downscaleToFileSize(params_fixture, mutex)
        mock_QMutexLocker.assert_called_once_with(mutex)
        assert mock__downscaleToPercent.call_args_list[0] == call(
            params_fixture["src"],
            proxy_src,
            66,
            params_fixture["resample"],
            [proxy_src, params_fixture["dst"]],
        )
        assert mock__checkForSuccess.call_args_list[0] == call("D0", proxy_src, [params_fixture["dst"]])
        assert mock_runBinary.call_args_list[0] == call(
            params_fixture["enc"],
            params_fixture["args"],
            proxy_src,
            params_fixture["dst"],
            args_after_input=False,
            delete_if_canceled=[proxy_src, params_fixture["dst"]],
        )
        assert mock__checkForSuccess.call_args_list[1] == call("D1", params_fixture["dst"], [proxy_src])
        assert mock__deleteFile.call_args_list[0] == call(proxy_src, raising=True, exc_id="D28")
        assert mock__deleteFile.call_args_list[1] == call(params_fixture["dst"], raising=True, exc_id="D30")

        assert mock__downscaleToPercent.call_args_list[1] == call(
            params_fixture["src"],
            proxy_src,
            33,
            params_fixture["resample"],
            [proxy_src, params_fixture["dst"]],
        )
        assert mock__checkForSuccess.call_args_list[2] == call("D23", proxy_src, [params_fixture["dst"]])
        assert mock_runBinary.call_args_list[0] == call(
            params_fixture["enc"],
            params_fixture["args"],
            proxy_src,
            params_fixture["dst"],
            args_after_input=False,
            delete_if_canceled=[proxy_src, params_fixture["dst"]],
        )
        assert mock__checkForSuccess.call_args_list[3] == call("D24", params_fixture["dst"], [proxy_src])
        assert mock__deleteFile.call_args_list[2] == call(proxy_src, raising=True, exc_id="D32")
        assert mock__deleteFile.call_args_list[3] == call(params_fixture["dst"], raising=True, exc_id="D25")

        mock__extrapolatedScale.assert_called_once_with(
            [
                [500_000, 66],
                [200_000, 33],
            ],
                params_fixture["max_size"] * 1024,
        )
        # Downscaling tested in elsewhere...
        mock__deleteFile.call_args_list[4] == call(proxy_src, raising=True, exc_id="D31")

class RunBinaryRecorder:
    def __init__(self):
        self.call_args_list = []
        self.call_count = 0

    def __call__(self, enc, enc_args, src, dst, **kwargs):
        self.call_args_list.append(
            call(
                enc, list(enc_args), src, dst, **kwargs
            )
        )
        self.call_count += 1

@pytest.mark.parametrize("e7_size, e9_size", [
    (300_000, 305_000),
    (305_000, 300_000),
])
def test__downscaleToFileSize_int_e(e7_size, e9_size, params_fixture):
    params_fixture.update({
        "mode": "File Size",
        "format": "JPEG XL",
        "jxl_int_e": True,
        "max_size": 300,
        "args": ["-q 90", "-e 9"],
    })
    mutex = MagicMock(spec=QMutex)
    proxy_src = "/tmp/proxy.png"
    e9_tmp = "/tmp/e9_tmp.jxl"
    with (
        patch("core.downscale.getUniqueTmpFilePath", side_effect=[proxy_src, e9_tmp]) as mock_getUniqueTmpFilePath,
        patch("core.downscale._downscaleToPercent") as mock__downscaleToPercent,
        patch("core.downscale._getFileSize", side_effect=[500_000, 200_000, 300_000, e7_size, e9_size]) as mock__getFileSize,
        patch("core.downscale.runBinary", new=RunBinaryRecorder()) as mock_runBinary,
        patch("core.downscale.QMutexLocker") as mock_QMutexLocker,
        patch("core.downscale._checkForSuccess") as mock__checkForSuccess,
        patch("core.downscale._deleteFile") as mock__deleteFile,
        patch("core.downscale._extrapolateScale", return_value=40) as mock__extrapolatedScale,
        patch("core.downscale.os.remove") as mock_remove,
        patch("core.downscale.os.rename") as mock_rename,
    ):
        downscale._downscaleToFileSize(params_fixture, mutex)
        assert mock_runBinary.call_args_list[0] == call(
            params_fixture["enc"],
            ["-q 90", "-e 7"],
            proxy_src,
            params_fixture["dst"],
            args_after_input=False,
            delete_if_canceled=[proxy_src, params_fixture["dst"]],
        )
        assert mock_QMutexLocker.call_args_list[1] == call(mutex)
        assert mock_runBinary.call_args_list[3] == call(
            params_fixture["enc"],
            ["-q 90", "-e 9"],
            proxy_src,
            e9_tmp,
            delete_if_canceled=[proxy_src, e9_tmp, params_fixture["dst"]],
        )
        assert mock__checkForSuccess.call_args_list[6] == call("D8", e9_tmp, [proxy_src])
        assert mock__getFileSize.call_args_list[3] == call(params_fixture["dst"], [proxy_src, e9_tmp, params_fixture["dst"]])
        assert mock__getFileSize.call_args_list[4] == call(e9_tmp, [proxy_src, e9_tmp, params_fixture["dst"]])

        if e9_size < e7_size:
            mock_remove.assert_called_once_with(params_fixture["dst"])
            mock_rename.assert_called_once_with(e9_tmp, params_fixture["dst"])
        else:
            mock_rename.assert_not_called()
            mock_remove.assert_called_once_with(e9_tmp)

def test__downscaleToFileSize_int_e_exception(params_fixture):
    params_fixture.update({
        "mode": "File Size",
        "format": "JPEG XL",
        "jxl_int_e": True,
        "max_size": 300,
        "args": ["-q 90", "-e 9"],
    })
    mutex = MagicMock(spec=QMutex)
    proxy_src = "/tmp/proxy.png"
    e9_tmp = "/tmp/e9_tmp.jxl"
    with (
        patch("core.downscale.getUniqueTmpFilePath", side_effect=[proxy_src, e9_tmp]) as mock_getUniqueTmpFilePath,
        patch("core.downscale._downscaleToPercent") as mock__downscaleToPercent,
        patch("core.downscale._getFileSize", side_effect=[500_000, 200_000, 300_000, 300_000, 305_000]) as mock__getFileSize,
        patch("core.downscale.runBinary", new=RunBinaryRecorder()) as mock_runBinary,
        patch("core.downscale.QMutexLocker") as mock_QMutexLocker,
        patch("core.downscale._checkForSuccess") as mock__checkForSuccess,
        patch("core.downscale._deleteFile") as mock__deleteFile,
        patch("core.downscale._extrapolateScale", return_value=40) as mock__extrapolatedScale,
        patch("core.downscale.os.remove", side_effect=OSError) as mock_remove,
        patch("core.downscale.os.rename") as mock_rename,
        patch("core.downscale.cleanUp") as mock_cleanUp,
        pytest.raises(FileException),
    ):
        downscale._downscaleToFileSize(params_fixture, mutex)
        mock_cleanUp.assert_called_once_with([params_fixture["dst"], e9_tmp, proxy_src])

def test__downscaleToFileSize_negative_extrapolated_scale(params_fixture):
    params_fixture.update({
        "mode": "File Size",
        "max_size": 300,
        "jxl_int_e": False,
        "args": ["-arg1", "-arg2"],
    })
    mutex = MagicMock(spec=QMutex)
    proxy_src = "/tmp/proxy.png"
    with (
        patch("core.downscale.getUniqueTmpFilePath", return_value=proxy_src) as mock_getUniqueTmpFilePath,
        patch("core.downscale._downscaleToPercent") as mock__downscaleToPercent,
        patch("core.downscale._getFileSize", side_effect=[500_000, 200_000, 300_000]) as mock__getFileSize,
        patch("core.downscale.runBinary") as mock_runBinary,
        patch("core.downscale.QMutexLocker") as mock_QMutexLocker,
        patch("core.downscale._checkForSuccess") as mock__checkForSuccess,
        patch("core.downscale._deleteFile") as mock__deleteFile,
        patch("core.downscale._extrapolateScale", return_value=0) as mock__extrapolatedScale,
        pytest.raises(GenericException),
    ):
        downscale._downscaleToFileSize(params_fixture, mutex)

def test__downscaleToFileSize_do_not_downscale_common_formats(params_fixture):
    params_fixture.update({
        "mode": "File Size",
        "format": "JPEG XL",
        "jxl_int_e": False,
        "max_size": 300,
        "args": ["-q 90", "-e 9"],
        "src": "path/to/src.jpg",
    })
    mutex = MagicMock(spec=QMutex)
    proxy_src = "/tmp/proxy.png"
    e9_tmp = "/tmp/e9_tmp.jxl"
    with (
        patch("core.downscale.getUniqueTmpFilePath", side_effect=[proxy_src, e9_tmp]) as mock_getUniqueTmpFilePath,
        patch("core.downscale._downscaleToPercent") as mock__downscaleToPercent,
        patch("core.downscale._getFileSize", side_effect=[500_000, 200_000, 300_000, 300_000, 305_000]) as mock__getFileSize,
        patch("core.downscale.runBinary", new=RunBinaryRecorder()) as mock_runBinary,
        patch("core.downscale.QMutexLocker") as mock_QMutexLocker,
        patch("core.downscale._checkForSuccess") as mock__checkForSuccess,
        patch("core.downscale._deleteFile") as mock__deleteFile,
        patch("core.downscale._extrapolateScale", return_value=150) as mock__extrapolatedScale,
        patch("core.downscale.os.remove", side_effect=OSError) as mock_remove,
        patch("core.downscale.os.rename") as mock_rename,
        patch("core.downscale.cleanUp") as mock_cleanUp,
    ):
        downscale._downscaleToFileSize(params_fixture, mutex)
        assert mock_runBinary.call_args_list[2] == call(
            params_fixture["enc"],
            params_fixture["args"],
            params_fixture["src"],
            params_fixture["dst"],
            args_after_input=False,
            delete_if_canceled=[proxy_src, params_fixture["dst"]],
        )
        assert mock__checkForSuccess.call_args_list[4] == call("D26", params_fixture["dst"], [proxy_src])

def test__downscaleToFileSize_do_not_downscale_uncommon_formats(params_fixture):
    params_fixture.update({
        "mode": "File Size",
        "format": "JPEG XL",
        "jxl_int_e": False,
        "max_size": 300,
        "args": ["-q 90", "-e 9"],
        "src": "path/to/src.avif",
    })
    mutex = MagicMock(spec=QMutex)
    proxy_src = "/tmp/proxy.png"
    e9_tmp = "/tmp/e9_tmp.jxl"
    with (
        patch("core.downscale.getUniqueTmpFilePath", side_effect=[proxy_src, e9_tmp]) as mock_getUniqueTmpFilePath,
        patch("core.downscale._downscaleToPercent") as mock__downscaleToPercent,
        patch("core.downscale._getFileSize", side_effect=[500_000, 200_000, 300_000, 300_000, 305_000]) as mock__getFileSize,
        patch("core.downscale.runBinary", new=RunBinaryRecorder()) as mock_runBinary,
        patch("core.downscale.QMutexLocker") as mock_QMutexLocker,
        patch("core.downscale._checkForSuccess") as mock__checkForSuccess,
        patch("core.downscale._deleteFile") as mock__deleteFile,
        patch("core.downscale._extrapolateScale", return_value=150) as mock__extrapolatedScale,
        patch("core.downscale.os.remove", side_effect=OSError) as mock_remove,
        patch("core.downscale.os.rename") as mock_rename,
        patch("core.downscale.cleanUp") as mock_cleanUp,
    ):
        downscale._downscaleToFileSize(params_fixture, mutex)
        assert mock__deleteFile.call_args_list[4] == call(proxy_src, raising=True, exc_id="D21")
        assert mock_runBinary.call_args_list[2] == call(
            IMAGE_MAGICK_PATH,
            [],
            params_fixture["src"],
            proxy_src,
            args_after_input=True,
            delete_if_canceled=[proxy_src],
        )
        assert mock__checkForSuccess.call_args_list[4] == call("D5", proxy_src)
        assert mock_runBinary.call_args_list[3] == call(
            params_fixture["enc"],
            params_fixture["args"],
            proxy_src,
            params_fixture["dst"],
            args_after_input=False,
            delete_if_canceled=[proxy_src, params_fixture["dst"]],
        )
        assert mock__checkForSuccess.call_args_list[5] == call("D6", params_fixture["dst"], [proxy_src])
        assert mock__deleteFile.call_args_list[5] == call(proxy_src, raising=True, exc_id="D22")

@pytest.mark.parametrize("resample,expected_filter", [
    ("Default", None),
    ("Lanczos", "-filter Lanczos"),
    ("Point", "-filter Point"),
    ("Box", "-filter Box"),
])
def test__downscaleManualModes_resample(resample, expected_filter, params_fixture):
    params_fixture.update({
        "enc": IMAGE_MAGICK_PATH,
        "resample": resample,
        "mode": "Percent",
        "args": [],
    })
    with (
        patch("core.downscale.runBinary") as mock_runBinary,
        patch("core.downscale._checkForSuccess") as mock__checkForSuccess,
    ):
        downscale._downscaleManualModes(params_fixture, MagicMock(spec=QMutex))
        args = params_fixture["args"]

        if expected_filter is None:
            args.append("-resize 50%")
        else:
            args.extend([expected_filter, "-resize 50%"])

        mock_runBinary.assert_called_once_with(
            IMAGE_MAGICK_PATH,
            args,
            params_fixture["src"],
            params_fixture["dst"],
            args_after_input=True,
            delete_if_canceled=[params_fixture["dst"]],
        )

@pytest.mark.parametrize("mode,expected_arg", [
    ("Percent", "-resize 50%"),
    ("Resolution", "-resize 1920x1080>"),
    ("Shortest Side", "-resize 1000x1000^>"),
    ("Longest Side", "-resize 2000x2000>"),
])
def test__downscaleManualModes_mode(mode, expected_arg, params_fixture):
    params_fixture.update({
        "enc": IMAGE_MAGICK_PATH,
        "mode": mode,
        "width": 1920,
        "height": 1080,
        "shortest_side": 1000,
        "longest_side": 2000,
        "resample": "Default",
    })
    with (
        patch("core.downscale.runBinary") as mock_runBinary,
        patch("core.downscale._checkForSuccess") as mock__checkForSuccess,
    ):
        downscale._downscaleManualModes(params_fixture, MagicMock(spec=QMutex))
        mock_runBinary.assert_called_once_with(
            IMAGE_MAGICK_PATH,
            [expected_arg],
            params_fixture["src"],
            params_fixture["dst"],
            args_after_input=True,
            delete_if_canceled=[params_fixture["dst"]],
        )
        mock__checkForSuccess.assert_called_once_with("D9", params_fixture["dst"])

@pytest.mark.parametrize("width, height, expected_arg", [
    (float("inf"), 1000, "-resize x1000>"),
    (1000, float("inf"), "-resize 1000x>"),
    (1920, 1080, "-resize 1920x1080>"),
])
def test__downscaleManualModes_resolution(width, height, expected_arg, params_fixture):
    params_fixture.update({
        "enc": IMAGE_MAGICK_PATH,
        "mode": "Resolution",
        "width": width,
        "height": height,
    })
    with (
        patch("core.downscale.runBinary") as mock_runBinary,
        patch("core.downscale._checkForSuccess") as mock__checkForSuccess,
    ):
        downscale._downscaleManualModes(params_fixture, MagicMock(spec=QMutex))
        mock_runBinary.assert_called_once_with(
            IMAGE_MAGICK_PATH,
            [expected_arg],
            params_fixture["src"],
            params_fixture["dst"],
            args_after_input=True,
            delete_if_canceled=[params_fixture["dst"]],
        )
        mock__checkForSuccess.assert_called_once_with("D9", params_fixture["dst"])

def test__downscaleManualModes_resolution_exception(params_fixture):
    params_fixture.update({
        "mode": "Resolution",
        "width": float("inf"),
        "height": float("inf"),
    })
    with pytest.raises(GenericException):
        downscale._downscaleManualModes(params_fixture, MagicMock(spec=QMutex))

def test__downscaleManualModes_mode_unknown(params_fixture):
    params_fixture.update({
        "enc": IMAGE_MAGICK_PATH,
        "mode": "unknown",
    })
    with pytest.raises(GenericException):
        downscale._downscaleManualModes(params_fixture, MagicMock(spec=QMutex))

def test__downscaleManualModes_no_imagemagick(params_fixture):
    params_fixture.update({
        "mode": "Percent",
        "percent": 50,
        "enc": "custom/enc/path",
        "args": ["-arg1", "-arg2"],
    })
    mutex = MagicMock(spec=QMutex)
    with (
        patch("core.downscale.getUniqueTmpFilePath", return_value="/tmp/image.jpg") as mock_getUniqueTmpFilePath,
        patch("core.downscale.runBinary") as mock_runBinary,
        patch("core.downscale.QMutexLocker") as mock_QMutexLocker,
        patch("core.downscale._checkForSuccess") as mock__checkForSuccess,
        patch("core.downscale._deleteFile") as mock__deleteFile,
    ):
        downscale._downscaleManualModes(params_fixture, mutex)
        mock_QMutexLocker.assert_called_once_with(mutex)
        assert mock_runBinary.call_args_list[0] == call(
            IMAGE_MAGICK_PATH,
            ["-resize 50%"],
            params_fixture["src"],
            mock_getUniqueTmpFilePath.return_value,
            args_after_input=True,
            delete_if_canceled=[mock_getUniqueTmpFilePath.return_value],
        )
        assert mock__checkForSuccess.call_args_list[0] == call("D10", mock_getUniqueTmpFilePath.return_value)
        assert mock_runBinary.call_args_list[1] == call(
            params_fixture["enc"],
            params_fixture["args"],
            mock_getUniqueTmpFilePath.return_value,
            params_fixture["dst"],
            args_after_input=False,
            delete_if_canceled=[mock_getUniqueTmpFilePath.return_value, params_fixture["dst"]],
        )
        assert mock__checkForSuccess.call_args_list[1] == call(
            "D11",
            params_fixture["dst"],
            [mock_getUniqueTmpFilePath.return_value]
        )
        mock__deleteFile.assert_called_once_with("/tmp/image.jpg", raising=True, exc_id="D4")
        assert mock_runBinary.call_count == 2
        assert mock__checkForSuccess.call_count == 2

@pytest.mark.parametrize("file_sizes, removed_file", [
    ([200, 300], "path/to/jxl_e9.jxl"),
    ([300, 200], "path/to/jxl.jxl"),
])
def test__downscaleManualModes_no_imagemagick_jxl_int_e_happy_path(file_sizes, removed_file, params_fixture):
    params_fixture.update({
        "format": "JPEG XL",
        "jxl_int_e": True,
        "mode": "Percent",
        "percent": 50,
        "args": ["-q 80", "-e 7"],
        "enc": "custom/enc/path",
        "dst": "path/to/jxl.jxl",
    })
    mutex = MagicMock(spec=QMutex)
    with (
        patch("core.downscale.getUniqueTmpFilePath", side_effect=["/tmp/image.png", "path/to/jxl_e9.jxl"]) as mock_getUniqueTmpFilePath,
        patch("core.downscale.runBinary") as mock_runBinary,
        patch("core.downscale.QMutexLocker") as mock_QMutexLocker,
        patch("core.downscale._checkForSuccess") as mock__checkForSuccess,
        patch("core.downscale._deleteFile") as mock__deleteFile,
        patch("core.downscale.os.remove") as mock_remove,
        patch("core.downscale.os.rename") as mock_rename,
        patch("core.downscale._getFileSize", side_effect=file_sizes) as mock__getFileSize,
        patch("core.downscale.cleanUp") as mock_cleanUp,
    ):
        downscale._downscaleManualModes(params_fixture, mutex)
        args, kwargs = mock_runBinary.call_args_list[2]
        assert args == (
            params_fixture["enc"],
            ["-q 80", "-e 9"],
            "/tmp/image.png",
            "path/to/jxl_e9.jxl",
        )
        assert kwargs["args_after_input"] == False
        assert kwargs["delete_if_canceled"] == ["/tmp/image.png", "path/to/jxl_e9.jxl", params_fixture["dst"]]
        assert mock__checkForSuccess.call_args_list[2] == call("D29", "path/to/jxl_e9.jxl", ["/tmp/image.png", "path/to/jxl.jxl"])
        assert mock__getFileSize.call_args_list[0] == call("path/to/jxl.jxl", ["/tmp/image.png", "path/to/jxl_e9.jxl", "path/to/jxl.jxl"])
        assert mock__getFileSize.call_args_list[1] == call("path/to/jxl_e9.jxl", ["/tmp/image.png", "path/to/jxl_e9.jxl", "path/to/jxl.jxl"])
        mock_remove.assert_called_once_with(removed_file)
        if file_sizes[0] > file_sizes[1]:
            mock_rename.assert_called_once_with("path/to/jxl_e9.jxl", "path/to/jxl.jxl")
        else:
            mock_rename.assert_not_called()
        assert mock_runBinary.call_count == 3
        assert mock__checkForSuccess.call_count == 3

def test__downscaleManualModes_no_imagemagick_jxl_int_e_sad_path(params_fixture):
    params_fixture.update({
        "format": "JPEG XL",
        "jxl_int_e": True,
        "mode": "Percent",
        "percent": 50,
        "args": ["-q 80", "-e 7"],
        "enc": "custom/enc/path",
        "dst": "path/to/jxl.jxl",
    })
    mutex = MagicMock(spec=QMutex)
    with (
        patch("core.downscale.getUniqueTmpFilePath", side_effect=["/tmp/image.png", "path/to/jxl_e9.jxl"]) as mock_getUniqueTmpFilePath,
        patch("core.downscale.runBinary") as mock_runBinary,
        patch("core.downscale.QMutexLocker") as mock_QMutexLocker,
        patch("core.downscale._checkForSuccess") as mock__checkForSuccess,
        patch("core.downscale._deleteFile") as mock__deleteFile,
        patch("core.downscale.os.remove", side_effect=OSError("Cannot remove file")) as mock_remove,
        patch("core.downscale.os.rename") as mock_rename,
        patch("core.downscale._getFileSize", side_effect=[200_000, 300_00]) as mock__getFileSize,
        patch("core.downscale.cleanUp") as mock_cleanUp,
        pytest.raises(FileException) as exc_info,
    ):
        downscale._downscaleManualModes(params_fixture, mutex)
        mock_cleanUp.assert_called_once_with(["path/to/jxl.jxl", "path/to/jxl_e9.jxl", "/tmp/image.png"])
        assert "D3" == exc_info.value.id
        assert "Cannot remove file" == exc_info.value.msg

# ------------------------------------------------------------
#                           Public
# ------------------------------------------------------------

def test_decodeAndDownscale_imagemagick(params_fixture):
    with (
        patch("core.downscale.downscale") as mock_downscale,
        patch("core.downscale.getDecoder", return_value=IMAGE_MAGICK_PATH),
    ):
        mutex = MagicMock(spec=QMutex())
        downscale.decodeAndDownscale(params_fixture, "png", "Encoder - Wipe", mutex)
        mock_downscale.assert_called_once_with(params_fixture, mutex)

def test_decodeAndDownscale_other(params_fixture):
    mutex = MagicMock(spec=QMutex())
    init_src = params_fixture["src"]
    with (
        patch("core.downscale.getDecoder", return_value="path/to/decoder") as mock_getDecoder,
        patch("core.downscale.metadata.getArgs", return_value=[]) as mock_getArgs,
        patch("core.downscale.downscale") as mock_downscale,
        patch("core.downscale.getUniqueTmpFilePath", return_value="/tmp/tmp_image.jpg") as mock_getUniqueTmpFilePath,
        patch("core.downscale.runBinary") as mock_runBinary,
        patch("core.downscale.os.remove") as mock_remove,
        patch("core.downscale._checkForSuccess") as mock__checkForSuccess,
        patch("core.downscale._deleteFile") as mock__deleteFile,
        patch("core.downscale.QMutexLocker") as mock_QMutexLocker,
    ):
        downscale.decodeAndDownscale(params_fixture, "jxl", "Encoder - Wipe", mutex)
        mock_QMutexLocker.assert_called_once_with(mutex)
        mock_runBinary.assert_called_once_with(
            mock_getDecoder.return_value,
            [],
            init_src,
            mock_getUniqueTmpFilePath.return_value,
            delete_if_canceled=[mock_getUniqueTmpFilePath.return_value],
        )
        mock__checkForSuccess.assert_called_once_with("D27", mock_getUniqueTmpFilePath.return_value)
        mock_downscale.assert_called_once_with(params_fixture, mutex)
        assert params_fixture["src"] == mock_getUniqueTmpFilePath.return_value
        assert params_fixture["enc"] == IMAGE_MAGICK_PATH
        mock__deleteFile.assert_called_once_with(
            mock_getUniqueTmpFilePath.return_value,
            raising=True,
            exc_id="D19",
        )

@patch("core.downscale.os.remove", side_effect=OSError("Clean-up failed"))
def test_decodeAndDownscale_cleanup_failed(params_fixture):
    with (
        patch("core.downscale.getDecoder", return_value="path/to/decoder") as mock_getDecoder,
        patch("core.downscale.metadata.getArgs", return_value=[]) as mock_getArgs,
        patch("core.downscale.downscale") as mock_downscale,
        patch("core.downscale.getUniqueTmpFilePath", return_value="/tmp/tmp_image.jpg") as mock_getUniqueTmpFilePath,
        patch("core.downscale.runBinary") as mock_runBinary,
        patch("core.downscale.os.remove") as mock_remove,
        patch("core.downscale._checkForSuccess") as mock__checkForSuccess,
        patch("core.downscale._deleteFile", side_effect=FileException("D19", "Cleanup failed")) as mock__deleteFile,
        patch("core.downscale.QMutexLocker") as mock_QMutexLocker,
        pytest.raises(FileException) as exc_info,
    ):
        downscale.decodeAndDownscale(params_fixture, "png", "Encoder - Wipe", MagicMock(spec=QMutex))

    assert exc_info.value.id == "D19"
    assert exc_info.value.msg == "Cleanup failed"

def test_downscale_canceled(params_fixture):
    with (
        patch("core.downscale.task_status.wasCanceled", return_value=True),
        pytest.raises(CancellationException),
    ):
        downscale.downscale(params_fixture, MagicMock(spec=QMutex))

def test_downscale_file_size(params_fixture):
    mutex = MagicMock(spec=QMutex)
    params_fixture.update({ "mode": "File Size" })
    with (
        patch("core.downscale._downscaleToFileSize") as mock__downscaleToFileSize,
        patch("core.downscale.task_status.wasCanceled", return_value=False),
    ):
        downscale.downscale(params_fixture, mutex)
        mock__downscaleToFileSize.assert_called_once_with(params_fixture, mutex)

def test_downscale_manual(params_fixture):
    mutex = MagicMock(spec=QMutex)
    params_fixture.update({ "mode": "Resolution" })
    with (
        patch("core.downscale._downscaleManualModes") as mock__downscaleManualModes,
        patch("core.downscale.task_status.wasCanceled", return_value=False),
    ):
        downscale.downscale(params_fixture, mutex)
        mock__downscaleManualModes.assert_called_once_with(params_fixture, mutex)
