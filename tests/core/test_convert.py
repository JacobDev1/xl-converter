from unittest.mock import patch, MagicMock
from contextlib import ExitStack

import pytest

import core.convert as convert
from core.exceptions import GenericException
from data.constants import AVIFENC_PATH, IMAGE_MAGICK_PATH, DJXL_PATH, AVIFDEC_PATH, ALLOWED_INPUT_IMAGE_MAGICK, OXIPNG_PATH
from core.exceptions import CancellationException

def test_runBinary_happy_path():
    stdout, stderr = "completed", "test"
    with (
        patch("core.convert.task_status.wasCanceled", return_value=False),
        patch("core.convert.runProcess2", return_value=(stdout, stderr)) as mock_runProcess2,
    ):
        assert convert.runBinary(
            "path/bin",
            ["-arg1", "-arg2"],
            "path/src.png",
            "path/dst.jxl"
        ) == (stdout, stderr)
        mock_runProcess2.assert_called_once_with(
            "path/bin",
            "-arg1", "-arg2",
            "path/src.png",
            "path/dst.jxl"
        )

def test_runBinary_no_dst():
    stdout, stderr = "completed", "test"
    with (
        patch("core.convert.task_status.wasCanceled", return_value=False),
        patch("core.convert.runProcess2", return_value=(stdout, stderr)) as mock_runProcess2,
    ):
        assert convert.runBinary(
            "path/bin",
            ["-arg1", "-arg2"],
            "path/src.png",
        ) == (stdout, stderr)
        mock_runProcess2.assert_called_once_with(
            "path/bin",
            "-arg1", "-arg2",
            "path/src.png",
        )

def test_runBinary_canceled():
    with (
        patch("core.convert.task_status.wasCanceled", return_value=True),
        patch("core.convert.runProcess2", return_value=("", "")) as mock_runProcess2,
        pytest.raises(CancellationException)
    ):
        convert.runBinary(
            "path/bin",
            ["-arg1", "-arg2"],
            "path/src.png",
            "path/dst.jxl"
        )
    mock_runProcess2.assert_called_once()

def test_runBinary_args_after_input():
    with (
        patch("core.convert.task_status.wasCanceled", return_value=False),
        patch("core.convert.runProcess2", return_value=("", "")) as mock_runProcess2,
    ):
        convert.runBinary(
            "path/bin",
            ["-arg1", "-arg2"],
            "path/src.png",
            "path/dst.jxl",
            args_after_input=False,
        )
        assert mock_runProcess2.call_args_list[0][0][1] == "-arg1"
        assert mock_runProcess2.call_args_list[0][0][2] == "-arg2"
        convert.runBinary(
            "path/bin",
            ["-arg1", "-arg2"],
            "path/src.png",
            "path/dst.jxl",
            args_after_input=True,
        )
        assert mock_runProcess2.call_args_list[1][0][2] == "-arg1"
        assert mock_runProcess2.call_args_list[1][0][3] == "-arg2"

def test_runBinary_delete_if_canceled_not_empty():
    tmp_files = ["/tmp/file1.jpg", "/tmp/file2.jpg", "/tmp/file3.jpg"]
    with (
        patch("core.convert.task_status.wasCanceled", return_value=True),
        patch("core.convert.runProcess2", return_value=("", "")) as mock_runProcess2,
        patch("core.convert.os.path.isfile", side_effect=(False, True, True)) as mock_isfile,
        patch("core.convert.os.remove") as mock_remove,
    ):
        with pytest.raises(CancellationException):
            convert.runBinary(
                "path/bin",
                ["-arg1", "-arg2"],
                "path/src.png",
                "path/dst.jxl",
                args_after_input=False,
                delete_if_canceled=tmp_files,
            )
    
        assert mock_isfile.call_count == 3
        assert mock_remove.call_count == 2
        assert mock_remove.call_args_list[0][0][0] == tmp_files[1]
        assert mock_remove.call_args_list[1][0][0] == tmp_files[2]

def test_runBinary_delete_if_canceled_empty():
    with (
        patch("core.convert.task_status.wasCanceled", return_value=True),
        patch("core.convert.runProcess2", return_value=("", "")) as mock_runProcess2,
        patch("core.convert.os.path.isfile", return_value=False) as mock_isfile,
        patch("core.convert.os.remove") as mock_remove,
    ):
        with pytest.raises(CancellationException):
            convert.runBinary(
                "path/bin",
                ["-arg1", "-arg2"],
                "path/src.png",
                "path/dst.jxl",
                args_after_input=False,
                delete_if_canceled=[],
            )
        mock_isfile.assert_not_called()
        mock_remove.assert_not_called()

def test_runBinary_runProcess2_exc():
    with (
        patch("core.convert.runProcess2", side_effect=PermissionError) as mock_runProcess2,
        pytest.raises(PermissionError),
    ):
        convert.runBinary(
            "path/bin",
            ["-arg1", "-arg2"],
            "path/src.png",
            "path/dst.jxl",
            args_after_input=False,
            delete_if_canceled=[],
        )

def test_runJPEGtran_happy_path():
    stdout, stderr = "completed", "test"
    with (
        patch("core.convert.JPEGTRAN_PATH", "djxl_path") as var_DJXL_PATH,
        patch("core.convert.task_status.wasCanceled", return_value=False),
        patch("core.convert.runProcess2", return_value=(stdout, stderr)) as mock_runProcess2,
    ):
        assert convert.runJPEGtran(
            ["-copy", "all"],
            "path/src.jpg",
            "path/dst.jpg",
        ) == (stdout, stderr)
    mock_runProcess2.assert_called_once_with(
        var_DJXL_PATH,
        "-copy", "all",
        "-outfile",
        "path/dst.jpg",
        "path/src.jpg",
    )

def test_runJPEGtran_sad_path():
    stdout, stderr = "completed", "test"
    with (
        patch("core.convert.JPEGTRAN_PATH", "djxl_path") as var_DJXL_PATH,
        patch("core.convert.task_status.wasCanceled", return_value=True),
        patch("core.convert.runProcess2", return_value=(stdout, stderr)) as mock_runProcess2,
        pytest.raises(CancellationException) as excinfo,
    ):
        convert.runJPEGtran(
            ["-copy", "all"],
            "path/src.jpg",
            "path/dst.jpg",
        )
    mock_runProcess2.assert_called_once_with(
        var_DJXL_PATH,
        "-copy", "all",
        "-outfile",
        "path/dst.jpg",
        "path/src.jpg",
    )

@pytest.fixture
def runOxipng_patches():
    mocks = {
        "wasCanceled": patch("core.convert.task_status.wasCanceled", return_value=False),
        "runProcess2": patch("core.convert.runProcess2", return_value=("", "")),
        "isfile": patch("core.convert.os.path.isfile", return_value=True),
        "remove": patch("core.convert.os.remove"),
    }

    with ExitStack() as stack:
        yield {name: stack.enter_context(patcher) for name, patcher in mocks.items()}

@pytest.mark.parametrize(
    "inplace, dst_path, expected_cmd", [
        (True, None, (OXIPNG_PATH, "--np", "/tmp/src.png")),
        (False, "/tmp/dst.png", (OXIPNG_PATH, "--np", "/tmp/src.png", "--out", "/tmp/dst.png")),
    ]
)
def test_runOxipng_inplace(inplace, dst_path, expected_cmd, runOxipng_patches):
    runProcess2_return = ("stdout", "")
    runOxipng_patches["runProcess2"].return_value = runProcess2_return
    assert convert.runOxipng(
        ["--np"],
        "/tmp/src.png",
        dst_path,
        inplace=inplace,
    ) == runProcess2_return
    runOxipng_patches["runProcess2"].assert_called_once_with(*expected_cmd)

def test_runOxipng_inplace_false_no_dst(runOxipng_patches):
    src_path = "/tmp/src.png"

    with (
        pytest.raises(ValueError, match="dst_path is required if inplace is False."),
    ):
        convert.runOxipng([], src_path)
    runOxipng_patches["runProcess2"].assert_not_called()

def test_runOxipng_canceled_no_delete_list(runOxipng_patches):
    runOxipng_patches["wasCanceled"].return_value = True
    with (
        patch("core.convert.cleanUp") as mock_cleanUp,
        pytest.raises(CancellationException),
    ):
        convert.runOxipng([], "/tmp/src.png", "/tmp/dst.png")
    runOxipng_patches["runProcess2"].assert_called_once()
    mock_cleanUp.assert_not_called()

def test_runOxipng_canceled_delete_list_exists(runOxipng_patches):
    tmp_files = ["/tmp/image_0.png", "/tmp/image_1.png", "/tmp/image_2.png"]
    runOxipng_patches["wasCanceled"].return_value = True
    runOxipng_patches["isfile"].side_effect = (True, False, True)
    with (
        pytest.raises(CancellationException),
    ):
        convert.runOxipng(
            [],
            "/tmp/src.png",
            "/tmp/dst.png",
            delete_if_canceled=tmp_files,
        )
    runOxipng_patches["runProcess2"].assert_called_once()
    assert runOxipng_patches["isfile"].call_count == 3
    assert runOxipng_patches["remove"].call_count == 2
    assert runOxipng_patches["remove"].call_args_list[0].args[0] == tmp_files[0]
    assert runOxipng_patches["remove"].call_args_list[1].args[0] == tmp_files[2]

def test_runOxipng_src_in_delete_if_canceled(runOxipng_patches):
    src_path = "/tmp/src.png"
    with (
        pytest.raises(ValueError),
    ):
        convert.runOxipng(
            [],
            src_path,
            "/tmp/dst.png",
            delete_if_canceled=[src_path],
        )
    runOxipng_patches["runProcess2"].assert_not_called()

def test_parseArgs():
    assert convert.parseArgs(["--quality=50", "-m 1"]) == ["--quality=50", "-m", "1"]

def test_getDecoder_known():
    assert convert.getDecoder("png") == IMAGE_MAGICK_PATH
    assert convert.getDecoder("jxl") == DJXL_PATH
    assert convert.getDecoder("avif") == AVIFDEC_PATH
    assert convert.getDecoder(ALLOWED_INPUT_IMAGE_MAGICK[0]) == IMAGE_MAGICK_PATH

def test_getDecoder_unknown():
    with pytest.raises(GenericException):
        assert convert.getDecoder("exr")

def test_getDecoderArgs_known():
    assert convert.getDecoderArgs(AVIFDEC_PATH, 4) == ["-j 4"]
    assert convert.getDecoderArgs(DJXL_PATH, 4) == ["--num_threads=4"]

def test_getDecoderArgs_unknown():
    assert convert.getDecoderArgs("unknown", 4) == []

@pytest.fixture
def getImageRes_patches():
    mocks = {
        "runBinary": patch("core.convert.runBinary", return_value=("1000x1000", "")),
    }

    variables = {
        "IMAGE_MAGICK_PATH": patch("core.convert.IMAGE_MAGICK_PATH", "im_path"),
    }

    with ExitStack() as stack:
        _mocks = {name: stack.enter_context(patcher) for name, patcher in mocks.items()}
        _variables = {name: stack.enter_context(patcher) for name, patcher in variables.items()}
        yield _mocks, _variables

def test_getImageRes_happy_path(getImageRes_patches):
    mocks, variables = getImageRes_patches
    res = (2000, 3000)
    image_path = "/tmp/file.jpg"
    mocks["runBinary"].return_value = (f"{res[0]}x{res[1]}", "")

    assert convert.getImageRes(image_path) == res
    mocks["runBinary"].assert_called_once_with(
        variables["IMAGE_MAGICK_PATH"],
        ["identify", "-ping", "-format", "%[page]"],
        f"{image_path}[0]",
    )

@pytest.mark.parametrize("invalid_process_output", [
    "1a00x2000", "", "1000xa000", "x2000", "2000x", "1a00x2000a"
])
def test_getImageRes_invalid_process_output(invalid_process_output, getImageRes_patches, caplog):
    mocks, variables = getImageRes_patches
    mocks["runBinary"].return_value = (invalid_process_output, "")

    assert convert.getImageRes("/tmp/file.jpg") == (-1, -1)
    mocks["runBinary"].assert_called_once()
    assert "Cannot determine resolution" in caplog.records[0].message

def test_getImageRes_parsing_error(getImageRes_patches, caplog):
    mocks, variables = getImageRes_patches
    mock_re_output = MagicMock()
    mock_re_output.group.side_effect = ("a", "b")

    with patch("core.convert.re.match", return_value=mock_re_output) as mock_re:
        assert convert.getImageRes("/tmp/file.jpg") == (-1, -1)

    assert "Failed to parse resolution" in caplog.records[0].message

def test_getImageRes_invalid_res(getImageRes_patches, caplog):
    mocks, variables = getImageRes_patches
    mocks["runBinary"].return_value = ("0x0", "")

    assert convert.getImageRes("/tmp/file.jpg") == (-1, -1)
    assert "Cannot determine resolution" in caplog.records[0].message

def test_getImageResMp_happy_path():
    image_path = "/tmp/file.jpg"
    res = (2000, 3000)

    with patch("core.convert.getImageRes", return_value=res) as mock_getImageRes:
        assert convert.getImageResMp(image_path := "/tmp/file.jpg") == res[0] * res[1] / 1_000_000
        mock_getImageRes.assert_called_once_with(image_path)

def test_getImageResMp_sad_path():
    with patch("core.convert.getImageRes", return_value=(-1, -1)) as mock_getImageRes:
        assert convert.getImageResMp("/tmp/file.jpg") == -1

def test_getImageCount_happy_path(caplog):
    image_path = "/tmp/image.jpg"

    with (
        patch("core.convert.runBinary", return_value=("5\n" * 5, "")) as mock_runBinary,      # typical IM output
        patch("core.convert.IMAGE_MAGICK_PATH", "im_path") as var_IMAGE_MAGICK_PATH,
    ):
        assert convert.getImageCount(image_path) == (5, "")
        mock_runBinary.assert_called_once_with(
            var_IMAGE_MAGICK_PATH,
            ["identify", "-ping", "-format", "%n\n"],
            image_path
        )
        assert not caplog.records

def test_getImageCount_image_count_not_available(caplog):
    image_path = "/tmp/image.jpg"
    stderr = "error"

    with (
        patch("core.convert.runBinary", return_value=("not found", stderr)) as mock_runBinary,
        patch("core.convert.IMAGE_MAGICK_PATH", "im_path") as var_IMAGE_MAGICK_PATH,
    ):
        assert convert.getImageCount(image_path) == (-1, stderr)
        mock_runBinary.assert_called_once_with(
            var_IMAGE_MAGICK_PATH,
            ["identify", "-ping", "-format", "%n\n"],
            image_path
        )
        assert "Cannot determine image count" in caplog.records[0].message 
        assert stderr in caplog.records[0].message 

def test_getImageCount_parsing_failed(caplog):
    mock_match = MagicMock()
    mock_match.group.side_effect = ValueError("invalid literal for int()")

    with (
        patch("core.convert.runBinary", return_value=("5\n" * 5, "")) as mock_runBinary,
        patch("core.convert.re.search", return_value=mock_match)
    ):
        assert convert.getImageCount("/tmp/image.jpg") == (-1, "")
        mock_runBinary.assert_called_once()
        assert "Parsing failed" in caplog.records[0].message 
        assert "invalid literal for int()" in caplog.records[0].message

def test_cleanUp_files_exist():
    tmp_files = ["/tmp/file1.jpg", "/tmp/file2.jpg", "/tmp/file3.jpg"]
    with (
        patch("core.convert.os.path.isfile", side_effect=(False, True, True)) as mock_isfile,
        patch("core.convert.os.remove") as mock_remove,
    ):
        convert.cleanUp(tmp_files)
    
        assert mock_isfile.call_count == 3
        assert mock_remove.call_count == 2
        assert mock_remove.call_args_list[0][0][0] == tmp_files[1]
        assert mock_remove.call_args_list[1][0][0] == tmp_files[2]

def test_cleanUp_empty():
    with (
        patch("core.convert.os.path.isfile", return_value=False) as mock_isfile,
        patch("core.convert.os.remove") as mock_remove,
    ):
        convert.cleanUp([])
        mock_isfile.assert_not_called()
        mock_remove.assert_not_called()
