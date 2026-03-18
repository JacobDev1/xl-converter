from unittest.mock import patch
from contextlib import ExitStack

import pytest

import core.lossless_jpeg as lossless_jpeg
from core.exceptions import FileException

@pytest.fixture
def transcodeJPEGtoJPEGXL_patches():
    variables = {
        "CJXL_PATH": patch("core.lossless_jpeg.CJXL_PATH", "cjxl_path"),
    }

    mocks = {
        "isfile": patch("core.lossless_jpeg.os.path.isfile", return_value=True),
        "runBinary": patch("core.lossless_jpeg.runBinary", return_value=("stdout", "stderr")),
    }

    with ExitStack() as stack:
        _mocks = {name: stack.enter_context(patcher) for name, patcher in mocks.items()}
        _variables = {name: stack.enter_context(patcher) for name, patcher in variables.items()}
        yield _mocks, _variables

def test_transcodeJPEGtoJPEGXL_happy_path(transcodeJPEGtoJPEGXL_patches):
    mocks, variables = transcodeJPEGtoJPEGXL_patches

    src, dst, effort, num_threads = "/path/to/src.jpg", "/path/to/dst.jxl", 7, 1
    
    assert (True, *mocks["runBinary"].return_value) == lossless_jpeg.transcodeJPEGtoJPEGXL(
        src,
        dst,
        effort,
        num_threads,
    )

    mocks["runBinary"].assert_called_once_with(
        variables["CJXL_PATH"],
        [
            "--lossless_jpeg=1",
            f"-e {effort}",
            f"--num_threads={num_threads}",
        ],
        src,
        dst,
    )

def test_transcodeJPEGtoJPEGXL_missing_output(transcodeJPEGtoJPEGXL_patches):
    mocks, variables = transcodeJPEGtoJPEGXL_patches
    mocks["isfile"].side_effect = (True, False)
    expected_stderr = "custom stderr"
    mocks["runBinary"].return_value = ("", expected_stderr)

    assert (False, "", expected_stderr) == lossless_jpeg.transcodeJPEGtoJPEGXL("/path/to/src.jpg", "/path/to/dst.jxl", 7, 1)

    mocks["runBinary"].assert_called_once()

def test_transcodeJPEGtoJPEGXL_source_missing(transcodeJPEGtoJPEGXL_patches):
    mocks, variables = transcodeJPEGtoJPEGXL_patches
    mocks["isfile"].side_effect = (False, False)

    assert (False, "", "Source file not found.") == lossless_jpeg.transcodeJPEGtoJPEGXL("/path/to/src.jpg", "/path/to/dst.jxl", 7, 1)

    mocks["runBinary"].assert_not_called()

def test_normalizeJPEG_happy_path():
    src, dst = "/path/src.jpg", "/path/dst.jpg"
    with (
        patch("core.lossless_jpeg.os.path.isfile", return_value=True) as mock_isfile,
        patch("core.lossless_jpeg.runJPEGtran", return_value=("stdout", "stderr")) as mock_runJPEGtran,
    ):
        assert (True, "stdout", "stderr") == lossless_jpeg.normalizeJPEG(src, dst)

    mock_runJPEGtran.assert_called_once_with(
        [
            "-copy", "all",
            "-optimize",
        ],
        src,
        dst,
    )

def test_normalizeJPEG_missing_output():
    src, dst = "/path/src.jpg", "/path/dst.jpg"
    with (
        patch("core.lossless_jpeg.os.path.isfile", side_effect=(True, False)) as mock_isfile,
        patch("core.lossless_jpeg.runJPEGtran", return_value=("stdout", "stderr")) as mock_runJPEGtran,
    ):
        assert (False, "stdout", "stderr") == lossless_jpeg.normalizeJPEG(src, dst)

    mock_runJPEGtran.assert_called_once_with(
        [
            "-copy", "all",
            "-optimize",
        ],
        src,
        dst,
    )

def test_normalizeJPEG_missing_source():
    src, dst = "/path/src.jpg", "/path/dst.jpg"
    with (
        patch("core.lossless_jpeg.os.path.isfile", side_effect=(False, False)) as mock_isfile,
        patch("core.lossless_jpeg.runJPEGtran", return_value=("stdout", "stderr")) as mock_runJPEGtran,
    ):
        assert (False, "", "Source file not found.") == lossless_jpeg.normalizeJPEG(src, dst)

    mock_runJPEGtran.assert_not_called()

@pytest.fixture
def verifyJPEGXLReconstructionData_patches():
    mocks = {
        "reconstructJPEGfromJPEGXL": patch("core.lossless_jpeg.reconstructJPEGfromJPEGXL", return_value=(True, "stdout", "stderr")),
        "isfile": patch("core.lossless_jpeg.os.path.isfile", return_value=True),
        "b2sum": patch("core.lossless_jpeg.b2sum", side_effect=("123", "123")),
        "remove": patch("core.lossless_jpeg.os.remove", side_effect=("123", "123")),
    }

    with ExitStack() as stack:
        _mocks = {name: stack.enter_context(patcher) for name, patcher in mocks.items()}
        yield _mocks

def test_verifyJPEGXLReconstructionData_happy_path(verifyJPEGXLReconstructionData_patches):
    mocks = verifyJPEGXLReconstructionData_patches
    src, dst, tmp, num_threads = "/path/src.jpg", "/path/dst.jpg", "/path/tmp.jpg", 4

    assert (True, "stdout", "stderr") == lossless_jpeg.verifyJPEGXLReconstructionData(src, dst, tmp, 4)
    
    mocks["reconstructJPEGfromJPEGXL"].assert_called_once_with(src, tmp, num_threads)

def test_verifyJPEGXLReconstructionData_rec_failed(verifyJPEGXLReconstructionData_patches):
    mocks = verifyJPEGXLReconstructionData_patches
    mocks["reconstructJPEGfromJPEGXL"].return_value = (False, "stdout", "stderr")

    assert (False, "stdout", "stderr") == lossless_jpeg.verifyJPEGXLReconstructionData("/path/src.jpg", "/path/dst.jpg", "/path/tmp.jpg", 4)

def test_verifyJPEGXLReconstructionData_rec_success_no_output(verifyJPEGXLReconstructionData_patches):
    mocks = verifyJPEGXLReconstructionData_patches
    mocks["isfile"].return_value = False

    assert (False, "stdout", "stderr") == lossless_jpeg.verifyJPEGXLReconstructionData("/path/src.jpg", "/path/dst.jpg", "/path/tmp.jpg", 4)

def test_verifyJPEGXLReconstructionData_checksum_calc_failed(verifyJPEGXLReconstructionData_patches):
    mocks = verifyJPEGXLReconstructionData_patches
    mocks["b2sum"].side_effect = OSError("OSError")

    with pytest.raises(FileException) as excinfo:
        lossless_jpeg.verifyJPEGXLReconstructionData("/path/src.jpg", "/path/dst.jpg", "/path/tmp.jpg", 4)
    
    assert excinfo.value.id == "jxl_verify_1"
    assert "Calculating b2sum failed" in excinfo.value.msg
    assert "OSError" in excinfo.value.msg

def test_verifyJPEGXLReconstructionData_remove_tmp_failed(verifyJPEGXLReconstructionData_patches):
    mocks = verifyJPEGXLReconstructionData_patches
    mocks["remove"].side_effect = OSError("OSError")

    with pytest.raises(FileException) as excinfo:
        lossless_jpeg.verifyJPEGXLReconstructionData("/path/src.jpg", "/path/dst.jpg", "/path/tmp.jpg", 4)
    
    assert excinfo.value.id == "jxl_verify_0"
    assert "Failed to remove tmp file" in excinfo.value.msg
    assert "OSError" in excinfo.value.msg

def test_verifyJPEGXLReconstructionData_checksum_mismatch(verifyJPEGXLReconstructionData_patches):
    mocks = verifyJPEGXLReconstructionData_patches
    mocks["b2sum"].side_effect = ("123", "321")

    assert (False, "", "Checksum mismatch.") == lossless_jpeg.verifyJPEGXLReconstructionData("/path/src.jpg", "/path/dst.jpg", "/path/tmp.jpg", 4)

def test_reconstructJPEGfromJPEGXL_happy_path():
    src, dst = "/path/src.jpg", "/path/dst.jpg"
    with (
        patch("core.lossless_jpeg.DJXL_PATH", "djxl") as var_DJXL_PATH,
        patch("core.lossless_jpeg.os.path.isfile", return_value=True) as mock_isfile,
        patch("core.lossless_jpeg.runBinary", return_value=("stdout", "stderr")) as mock_runBinary,
    ):
        assert (True, "stdout", "stderr") == lossless_jpeg.reconstructJPEGfromJPEGXL(src, dst, 4)

    mock_runBinary.assert_called_once_with(
        var_DJXL_PATH,
        ["--num_threads=4"],
        src,
        dst,
    )

def test_reconstructJPEGfromJPEGXL_missing_source():
    src, dst = "/path/src.jpg", "/path/dst.jpg"
    with (
        patch("core.lossless_jpeg.DJXL_PATH", "djxl") as var_DJXL_PATH,
        patch("core.lossless_jpeg.os.path.isfile", return_value=False) as mock_isfile,
        patch("core.lossless_jpeg.runBinary", return_value=("stdout", "stderr")) as mock_runBinary,
    ):
        assert (False, "", "Source file not found.") == lossless_jpeg.reconstructJPEGfromJPEGXL(src, dst, 4)

    mock_runBinary.assert_not_called()
