import pdb
import os
from unittest.mock import patch

import pytest

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

@patch("core.downscale.convert") 
def test__downscaleToPercent_default(mock_convert):
    downscale._downscaleToPercent("src.png", "dst.png", 90, "Default")
    mock_convert.assert_called_once_with(IMAGE_MAGICK_PATH, "src.png", "dst.png", ["-resize 90%"], None)

@patch("core.downscale.convert") 
def test__downscaleToPercent_custom(mock_convert):
    custom_resampling = ALLOWED_RESAMPLING[0]
    downscale._downscaleToPercent("src.png", "dst.png", 90, custom_resampling)
    mock_convert.assert_called_once_with(IMAGE_MAGICK_PATH, "src.png", "dst.png", [f"-filter {custom_resampling}", "-resize 90%"], None)

@patch("core.downscale.task_status.wasCanceled", return_value=True)
def test_cancelCheck(mock_wasCanceled, tmp_path):
    tmp_file = tmp_path / "tempfile"
    tmp_file.write_text("temp")
    with pytest.raises(CancellationException):
        downscale.cancelCheck(str(tmp_file))
    
    assert not os.path.isfile(tmp_file)

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
    with patch("core.downscale.convert") as mock_convert:
        downscale._downscaleManualModes(params_fixture)
        args = params_fixture["args"]

        if expected_filter is None:
            args.append("-resize 50%")
        else:
            args.extend([expected_filter, "-resize 50%"])

        mock_convert.assert_called_once_with(IMAGE_MAGICK_PATH, params_fixture["src"], params_fixture["dst"], args, params_fixture["n"])

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
    with patch("core.downscale.convert") as mock_convert:
        downscale._downscaleManualModes(params_fixture)
        mock_convert.assert_called_once_with(params_fixture["enc"], params_fixture["src"], params_fixture["dst"], [expected_arg], params_fixture["n"])

def test__downscaleManualModes_mode_unknown(params_fixture):
    params_fixture.update({
        "enc": IMAGE_MAGICK_PATH,
        "mode": "unknown",
    })
    with pytest.raises(GenericException):
        downscale._downscaleManualModes(params_fixture)


def test__downscaleManualModes_no_imagemagick(params_fixture):
    params_fixture.update({
        "mode": "Percent",
        "percent": 50,
    })
    with patch("core.downscale.getUniqueFilePath", return_value="new/path/image.png") as mock_getUniqueFilePath, \
        patch("core.downscale.convert") as mock_convert, \
        patch("core.downscale.os.remove"):

        downscale._downscaleManualModes(params_fixture)
        mock_getUniqueFilePath.assert_called_once_with(params_fixture["dst_dir"], params_fixture["name"], "png", True)

        mock_convert.assert_any_call(IMAGE_MAGICK_PATH, params_fixture["src"], "new/path/image.png", ["-resize 50%"], params_fixture["n"])
        mock_convert.assert_any_call(params_fixture["enc"], "new/path/image.png", params_fixture["dst"], [], params_fixture["n"])

@pytest.mark.parametrize("side_effect, removed_file", [
    ([200, 300], "path/to/jxl_e9.jxl"),
    ([300, 200], "path/to/jxl_e7.jxl"),
])
def test__downscaleManualModes_no_imagemagick_jxl_int_e_e9(params_fixture, side_effect, removed_file):
    params_fixture.update({
        "format": "JPEG XL",
        "jxl_int_e": "Percent",
        "mode": "Percent",
        "percent": 50,
        "args": ["-q 80", "-e 7"],
    })
    with patch("core.downscale.getUniqueFilePath", side_effect=["path/to/jxl_e7.jxl", "path/to/jxl_e9.jxl"]), \
        patch("core.downscale.convert") as mock_convert, \
        patch("core.downscale.os.remove") as mock_remove, \
        patch("core.downscale.os.rename"), \
        patch("core.downscale.os.path.getsize", side_effect=side_effect):

        downscale._downscaleManualModes(params_fixture)
        mock_convert.assert_any_call(params_fixture["enc"], "path/to/jxl_e7.jxl", params_fixture["dst"], params_fixture["args"], params_fixture["n"])
        mock_remove.assert_any_call(removed_file)

# ------------------------------------------------------------
#                           Public
# ------------------------------------------------------------

@patch("core.downscale.downscale")
def test_decodeAndDownscale_imagemagick(mock_downscale, params_fixture):
    with patch("core.downscale.getDecoder", return_value=IMAGE_MAGICK_PATH):
        downscale.decodeAndDownscale(params_fixture, "png", "Encoder - Wipe")
        mock_downscale.assert_called_once_with(params_fixture)

@patch("core.downscale.getDecoder", return_value="path/to/other/decoder")
@patch("core.downscale.metadata.getArgs", return_value=[])
@patch("core.downscale.downscale")
@patch("core.downscale.getUniqueFilePath", return_value="path/to/proxy/image.png")
@patch("core.downscale.convert")
@patch("core.downscale.os.remove")
def test_decodeAndDownscale_other(mock_getDecoder, mock_downscale,  mock_getUniqueFilePath, mock_convert, mock_remove, params_fixture):
    downscale.decodeAndDownscale(params_fixture, "jxl", "Encoder - Wipe")
    mock_convert.assert_called_once()
    mock_downscale.assert_called_once()
    mock_remove.assert_called_once()

@patch("core.downscale.getDecoder", return_value="path/to/other/decoder")
@patch("core.downscale.metadata.getArgs", return_value=[])
@patch("core.downscale.downscale")
@patch("core.downscale.getUniqueFilePath", return_value="path/to/proxy/image.png")
@patch("core.downscale.convert")
@patch("core.downscale.os.remove", side_effect=OSError("Clean-up failed"))
def test_decodeAndDownscale_cleanup_failed(mock_getDecoder, mock_getArgs, mock_downscale, mock_getUniqueFilePath, mock_convert, mock_remove, params_fixture):
    with pytest.raises(FileException) as exc_info:
        downscale.decodeAndDownscale(params_fixture, "png", "Encoder - Wipe")
    
    assert exc_info.value.id == "D1"
    assert "Clean-up failed" in str(exc_info.value.msg)

@patch("core.downscale.task_status.wasCanceled", return_value=True)
def test_downscale_canceled(mock_wasCanceled, params_fixture):
    with pytest.raises(CancellationException):
        downscale.downscale(params_fixture)

def test_downscale_file_size(params_fixture):
    with patch("core.downscale._downscaleToFileSizeStepAuto") as mock__downscaleToFileSizeStepAuto, \
        patch("core.downscale.task_status.wasCanceled", return_value=False):

        params_fixture.update({ "mode": "File Size" })
        downscale.downscale(params_fixture)
        mock__downscaleToFileSizeStepAuto.assert_called_once_with(params_fixture)

@pytest.mark.parametrize("mode", ["Percent", "Resolution", "Shortest Side", "Longest Side"])
def test_downscale_manual(params_fixture, mode):
    with patch("core.downscale._downscaleManualModes") as mock__downscaleManualModes, \
        patch("core.downscale.task_status.wasCanceled", return_value=False):

        params_fixture.update({ "mode": mode })
        downscale.downscale(params_fixture)
        mock__downscaleManualModes.assert_called_once_with(params_fixture)
        
@patch("core.downscale.task_status.wasCanceled", return_value=False)
def test_downscale_unknown(mock_wasCanceled, params_fixture):
    params_fixture.update({ "mode": "Unknown" })
    with pytest.raises(GenericException):
        downscale.downscale(params_fixture)