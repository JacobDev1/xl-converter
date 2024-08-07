from pathlib import Path
from unittest.mock import MagicMock, patch
from contextlib import ExitStack, contextmanager

import pytest
from PySide6.QtCore import QMutex
from PySide6.QtTest import QSignalSpy

from core.worker import Worker
from core.proxy import Proxy
from core.exceptions import FileException, GenericException, CancellationException

@pytest.fixture
def worker():
    mutex = QMutex()
    w = Worker(
        0,
        Path("/path/to/images/image.png"),
        Path("/path/to/images"),
        {
            "format": "PNG",
            "custom_output_dir": False,
            "custom_output_dir_path": "",
            "keep_dir_struct": False,
            "if_file_exists": "Rename",
            "downscaling": {"enabled": False},
            "delete_original": False,
            "delete_original_mode": "To Trash",
            "smallest_format_pool": {"png": True, "webp": True, "jxl": True},
            "max_compression": False,
            "intelligent_effort": False,
            "quality": 80,
            "effort": 7,
            "lossless": False,
            "jxl_modular": False,
            "avif_chroma_subsampling": "Default",
            "jpegli_chroma_subsampling": "Default",
            "jxl_png_fallback": False,
            "downscaling": {
                "enabled": False,
                "mode": "Percent",
                "file_size": 300,
                "percent": 80,
                "width": 2000,
                "height": 2000,
                "shortest_side": 2000,
                "longest_side": 2000,
                "resample": "Default",
            },
            "misc": {
                "keep_metadata": "Encoder - Wipe",
                "attributes": False,
            }
        },
        {
            "disable_progressive_jpegli": False,
            "webp_method": 6,
            "enable_custom_args": False,
            "avifenc_args": "",
            "cjxl_args": "",
            "cjpegli_args": "",
            "im_args": "",
            "jpg_encoder": "JPEGLI",
            "jxl_lossless_jpeg": False,
            "copy_if_larger": False,
            "keep_if_larger": False,
            "exiftool_args": {
                "ExifTool - Wipe": "-all= -tagsFromFile @ -icc_profile:all -ColorSpace:all -Orientation $dst -overwrite_original",
                "ExifTool - Preserve": "-tagsFromFile $src $dst -overwrite_original",
            },
        },
        4,
        mutex,
    )
    w.proxy = MagicMock(spec=Proxy)
    w.scl_params = {}
    w.output_dir = "output/dir/"

    return w

def normalizePath(path: str):
    return str(Path(path))

def getSuffix(path: str):
    return Path(path).suffix[1:]

@contextmanager
def convert_patches(
    getDecoder_return_value = "sample_decoder",
    getDecoderArgs_return_value = [],
    metadata_getArgs_return_value = [],
    getUniqueFilePath_side_effect=["/path/image1.jxl", "/path/image1.jxl"],
    getsize_side_effect=[300000, 400000]
):
    stack = ExitStack()
    with stack:
        stack.enter_context(patch("core.downscale.downscale"))
        stack.enter_context(patch("core.worker.convert"))
        stack.enter_context(patch("core.worker.getDecoder", return_value=getDecoder_return_value))
        stack.enter_context(patch("core.worker.getDecoderArgs", return_value=getDecoderArgs_return_value))
        stack.enter_context(patch("core.metadata.getArgs", return_value=metadata_getArgs_return_value))
        stack.enter_context(patch("core.worker.getUniqueFilePath", side_effect=getUniqueFilePath_side_effect))
        stack.enter_context(patch("core.worker.os.path.getsize", side_effect=getsize_side_effect))
        stack.enter_context(patch("core.worker.os.remove"))
        stack.enter_context(patch("core.worker.os.rename"))
        
        yield stack

@pytest.fixture
def finishConversion_patches():
    with (
        patch("core.worker.os.remove") as mock_remove,
        patch("core.worker.os.rename") as mock_rename,
        patch("core.worker.os.path.getsize", return_value=300_000) as mock_getsize,
        patch("core.worker.os.path.isfile", side_effect=[True, True, True]) as mock_isfile,
        patch("core.worker.getUniqueFilePath", return_value="final/path/img.jpg") as mock_getUniqueFilePath,
    ):
        yield mock_remove, mock_rename, mock_getsize, mock_isfile, mock_getUniqueFilePath 

@pytest.fixture
def postConversionRoutines_patches():
    with (
        patch("core.worker.os.path.isfile", return_value=True) as mock_isfile,
        patch("core.worker.metadata.runExifTool", return_value=[]) as mock_runExifTool,
        patch("core.worker.shutil.copystat") as mock_copystat,
        patch("core.worker.os.remove") as mock_remove,
        patch("core.worker.send2trash") as mock_send2trash,
    ):
        yield mock_isfile, mock_runExifTool, mock_copystat, mock_remove, mock_send2trash

@pytest.fixture
def smallestLossless_patches():
    def getsize_side_effect(file_path):
        size_map = {
            "png": 250_000,
            "webp": 200_000,
            "jxl": 150_000,
        }
        suffix = Path(file_path).suffix[1:]
        return size_map.get(suffix, 0)

    def getUniqueFilePath_side_effect(output_dir, item_name, key, random):
        size_map = {
            "png": "tmp/image.png",
            "webp": "tmp/image.webp",
            "jxl": "tmp/image.jxl",
        }
        return size_map.get(key, 0)

    with (
        patch("core.worker.os.path.getsize", side_effect=getsize_side_effect) as mock_getsize,
        patch("core.worker.getUniqueFilePath", side_effect=getUniqueFilePath_side_effect) as mock_getUniqueFilePath,
        patch("core.worker.metadata.getArgs", return_value=[]) as mock_getArgs,
        patch("core.worker.shutil.copy") as mock_copy,
        patch("core.worker.optimize") as mock_optimize,
        patch("core.worker.convert") as mock_convert,
        patch("core.worker.os.remove") as mock_remove,
    ):
        yield mock_getsize, mock_getUniqueFilePath, mock_getArgs, mock_copy, mock_optimize, mock_convert, mock_remove

def test_logException(worker):
    worker.item_abs_path = str(Path("/test/path/image.png"))
    spy = QSignalSpy(worker.signals.exception)
    worker.logException("ID0", "Exception")

    assert spy.at(0)[0] == "ID0", "Exception"
    assert spy.at(0)[1] == "Exception"
    assert spy.at(0)[2] == "image.png"

@patch("core.worker.task_status.wasCanceled", return_value=True)
def test_run_canceled(mock_wasCanceled, worker):
    spy_canceled = QSignalSpy(worker.signals.canceled)
    worker.run()
    assert spy_canceled.count() == 1

@patch("core.worker.task_status.wasCanceled", return_value=False)
def test_run_started(mock_wasCanceled, worker):
    spy_started = QSignalSpy(worker.signals.started)
    worker.run()
    assert spy_started.count() == 1

@patch("core.worker.os.path.isfile", return_value=False)
def test_runChecks_file_not_found(mock_isfile, worker):
    with pytest.raises(FileException) as exc:
        worker.runChecks()
    
    assert "File not found" == exc.value.msg

@patch("core.worker.os.path.isfile", return_value=True)
@patch("core.worker.conflicts")
def test_runChecks(mock_conflicts, mock_isfile, worker):
    worker.conflicts = MagicMock()
    worker.runChecks()
    mock_conflicts.checkForConflicts.assert_called_once()
    mock_conflicts.checkForMultipage.assert_called_once()

@pytest.fixture
def setupConversion_patches():
    with (
        patch("core.worker.Proxy.isProxyNeeded", return_value=False) as mock_isProxyNeeded,
        patch("core.worker.os.makedirs", side_effect=None) as mock_makedirs,
        patch("core.worker.getUniqueFilePath", return_value=normalizePath("/output/dir/image.jpg")) as mock_getUniqueFilePath,
        patch("core.worker.getOutputDir", return_value="/output/dir/") as mock_getOutputDir,
        patch("core.worker.getExtensionJxl", return_value="jpg") as mock_getExtensionJxl,
        patch("core.worker.os.path.isfile", side_effect=[True, True]) as mock_isfile,
        patch("core.worker.os.path.getsize", return_value=300_000) as mock_getsize,
        patch("core.worker.getFreeSpaceLeft", return_value=300_000_000_000) as mock_getFreeSpaceLeft,
        patch("core.worker.getExtension", return_value="jxl") as mock_getExtension,
    ):
        yield (
            mock_getUniqueFilePath,     # 0
            mock_getOutputDir,          # 1
            mock_isProxyNeeded,         # 2
            mock_makedirs,              # 3
            mock_getExtensionJxl,       # 4
            mock_isfile,                # 5
            mock_getsize,               # 6
            mock_getFreeSpaceLeft,      # 7
            mock_getExtension,          # 8
        )

def test_setupConversion_regular(setupConversion_patches, worker):
    output = normalizePath("/output/dir/image_unique.jpg")
    output_dir = normalizePath("/output/dir/")
    final_output = normalizePath("/output/dir/image.jpg")
    worker.item_name = "image"
    worker.params["format"] = "JPEG"
    mock_getUniqueFilePath = setupConversion_patches[0]
    mock_getOutputDir = setupConversion_patches[1]
    mock_getExtension = setupConversion_patches[8]
    mock_getUniqueFilePath.return_value = output
    mock_getOutputDir.return_value = output_dir
    mock_getExtension.return_value = "jpg"

    worker.setupConversion()
    
    assert worker.output == output
    assert worker.final_output == final_output
    assert worker.output_dir == output_dir
    assert worker.output_ext == "jpg"

def test_setupConversion_makedirs_error(setupConversion_patches, worker):
    mock_makedirs = setupConversion_patches[3]
    mock_makedirs.side_effect = OSError
    
    with pytest.raises(FileException) as exc:
        worker.setupConversion()

    assert "Failed to create output directory" in exc.value.msg

def test_setupConversion_space_left_pass(setupConversion_patches, worker):
    worker.setupConversion()

def test_setupConversion_space_left_exception(setupConversion_patches, worker):
    mock_getFreeSpaceLeft = setupConversion_patches[7]
    mock_getFreeSpaceLeft.return_value = 10_000
    with pytest.raises(FileException) as exc:
        worker.setupConversion()

    assert "No space left on device" in exc.value.msg

def test_setupConversion_jpeg_reconstruction_rec_data_found(setupConversion_patches, worker):
    worker.params["format"] = "JPEG Reconstruction"
    worker.item_ext = "jxl"

    worker.setupConversion()
    assert worker.jpeg_rec_data_found
    assert worker.output_ext == "jpg"

def test_setupConversion_jpeg_reconstruction_rec_data_not_found(setupConversion_patches, worker):
    mock_getExtensionJxl = setupConversion_patches[4]
    mock_getExtensionJxl.return_value = "png"
    worker.params["format"] = "JPEG Reconstruction"
    worker.item_ext = "jxl"

    with pytest.raises(FileException) as exc:
        worker.setupConversion()

    assert "Reconstruction data not found" in exc.value.msg
    assert not worker.jpeg_rec_data_found
    assert worker.output_ext == "png"

def test_setupConversion_jpeg_reconstruction_rec_data_not_found_png_fallback(setupConversion_patches, worker):
    mock_getExtensionJxl = setupConversion_patches[4]
    mock_getExtensionJxl.return_value = "png"
    worker.params["format"] = "JPEG Reconstruction"
    worker.item_ext = "jxl"
    worker.params["jxl_png_fallback"] = True

    worker.setupConversion()

    assert not worker.jpeg_rec_data_found
    assert worker.output_ext == "png"

def test_setupConversion_jpeg_reconstruction_bad_input(setupConversion_patches, worker):
    worker.params["format"] = "JPEG Reconstruction"
    worker.item_ext = "jpg"

    with pytest.raises(FileException) as exc:
        worker.setupConversion()

    assert "Only JPEG XL images are allowed" in exc.value.msg

def test_setupConversion_assign_output_path(setupConversion_patches, worker):
    mock_getUniqueFilePath, mock_getOutputDir = setupConversion_patches[0], setupConversion_patches[1]
    mock_getUniqueFilePath.return_value = normalizePath("/tmp/path/image.jxl")
    mock_getOutputDir.return_value = normalizePath("/tmp/path/")
    worker.params["format"] = "JPEG XL"
    worker.item_name = "image"

    worker.setupConversion()

    assert worker.output == normalizePath("/tmp/path/image.jxl")
    assert worker.final_output == normalizePath("/tmp/path/image.jxl")

def test_setupConversion_skip(setupConversion_patches, worker):
    worker.params["if_file_exists"] = "Skip"
    worker.setupConversion()
    assert worker.skip

def test_setupConversion_proxy_needed(setupConversion_patches, worker):
    worker.proxy.isProxyNeeded = MagicMock(return_value=True)
    mock_isProxyNeeded = setupConversion_patches[2]
    worker.proxy.generate = MagicMock(return_value="/tmp/path/image.png")
    mock_isProxyNeeded.return_value = True

    worker.setupConversion()

    assert worker.item_abs_path == "/tmp/path/image.png"

def test_setupConversion_downscaling_no_key_error(setupConversion_patches, worker):
    worker.params["downscaling"]["enabled"] = True
    worker.setupConversion()
    assert worker.scl_params is not None

@pytest.mark.parametrize("quality, effort, lossless, modular, intelligent_effort, jxl_lossless_jpeg, item_ext, expected_args, expected_jpg_to_jxl_lossless", [
    (80, 7, True, False, False, True, "png", ["-q 100", "-e 7", "--lossless_jpeg=1", "--num_threads=4"], False),
    (80, 7, False, False, False, False, "png", ["-q 80", "-e 7", "--lossless_jpeg=0", "--num_threads=4"], False),
    (80, 7, False, True, False, False, "png", ["-q 80", "-e 7", "--lossless_jpeg=0", "--num_threads=4", "--modular=1"], False),
    (80, 7, False, True, True, False, "png", ["-q 80", "-e 9", "--lossless_jpeg=0", "--num_threads=4", "--modular=1"], False),
    (80, 7, True, False, True, True, "png", ["-q 100", "-e 9", "--lossless_jpeg=1", "--num_threads=4"], False),
    (80, 7, True, False, False, True, "jpg", ["-q 100", "-e 7", "--lossless_jpeg=1", "--num_threads=4"], True),
])
def test_convert_args_jpeg_xl(
    quality, effort, lossless, modular, intelligent_effort, jxl_lossless_jpeg, item_ext, expected_args, expected_jpg_to_jxl_lossless, worker
):
    with convert_patches() as patches:
        mock_convert = patches.enter_context(patch("core.worker.convert"))
        worker.params["format"] = "JPEG XL"
        worker.params["quality"] = quality
        worker.params["lossless"] = lossless
        worker.params["effort"] = effort
        worker.params["jxl_modular"] = modular
        worker.params["intelligent_effort"] = intelligent_effort
        worker.settings["jxl_lossless_jpeg"] = jxl_lossless_jpeg
        worker.item_ext = item_ext

        worker.convert()

        assert mock_convert.call_args[0][3] == expected_args
        assert worker.jpg_to_jxl_lossless == expected_jpg_to_jxl_lossless

@pytest.mark.parametrize("quality, speed, chroma_subsampling, expected_args", [
    (80, 6, "Default", ["-q 80", "-s 6", "-j 4"]),
    (90, 5, "4:4:4", ["-q 90", "-s 5", "-j 4", "-y 444"]),
])
def test_convert_args_avif(quality, speed, chroma_subsampling, expected_args, worker):
    with convert_patches() as patches:
        mock_convert = patches.enter_context(patch("core.worker.convert"))
        worker.params["format"] = "AVIF"
        worker.params["quality"] = quality
        worker.params["effort"] = speed
        worker.params["avif_chroma_subsampling"] = chroma_subsampling

        worker.convert()

        assert mock_convert.call_args[0][3] == expected_args

@pytest.mark.parametrize("quality, encoder, chroma_subsampling, disable_progressive_jpegli, expected_args", [
    (80, "JPEGLI", "Default", False, ["-q 80"]),
    (80, "JPEGLI", "4:4:4", False, ["-q 80", "--chroma_subsampling=444"]),
    (80, "JPEGLI", "Default", True, ["-q 80", "-p 0"]),
    (80, "libjpeg", "Default", False, ["-quality 80"]),
    (80, "libjpeg", "4:4:4", False, ["-quality 80", "-sampling-factor 4:4:4"]),
])
def test_convert_args_jpeg(quality, encoder, chroma_subsampling, disable_progressive_jpegli, expected_args, worker):
    with convert_patches() as patches:
        mock_convert = patches.enter_context(patch("core.worker.convert"))
        worker.params["format"] = "JPEG"
        worker.settings["jpg_encoder"] = encoder
        worker.params["quality"] = quality
        worker.settings["disable_progressive_jpegli"] = disable_progressive_jpegli
        if encoder == "JPEGLI":
            worker.params["jpegli_chroma_subsampling"] = chroma_subsampling
        else:
            worker.params["jpg_chroma_subsampling"] = chroma_subsampling

        worker.convert()

        assert mock_convert.call_args[0][3] == expected_args

@pytest.mark.parametrize("quality, method, lossless, expected_args", [
    (80, 6, False, ["-quality 80", "-define webp:thread-level=1", "-define webp:method=6"]),
    (50, 5, True, ["-define webp:lossless=true", "-define webp:thread-level=1", "-define webp:method=5"]),
    (50, 5, False, ["-quality 50", "-define webp:thread-level=1", "-define webp:method=5"]),
])
def test_convert_args_webp(quality, method, lossless, expected_args, worker):
    with convert_patches() as patches:
        mock_convert = patches.enter_context(patch("core.worker.convert"))
        worker.params["format"] = "WebP"
        worker.params["quality"] = quality
        worker.params["lossless"] = lossless
        worker.params["effort"] = method

        worker.convert()

        assert mock_convert.call_args[0][3] == expected_args

def test_convert_args_png(worker):
    with convert_patches(
        getDecoder_return_value="sample_decoder_path",
        getDecoderArgs_return_value=["--test_arg=1"]
    ) as patches:
        mock_convert = patches.enter_context(patch("core.worker.convert"))

        worker.convert()

        assert mock_convert.call_args[0][0] == "sample_decoder_path"
        assert mock_convert.call_args[0][3] == ["--test_arg=1"]

def test_convert_args_unknown(worker):
    with convert_patches():
        worker.params["format"] = "Unknown"

        with pytest.raises(GenericException):
            worker.convert()

def test_convert_metadata_args(worker):
    with convert_patches(
        metadata_getArgs_return_value=["--metadata_arg"]
    ) as patches:
        mock_convert = patches.enter_context(patch("core.worker.convert"))
        
        worker.convert()

        assert mock_convert.call_args[0][3] == ["--metadata_arg"]

def test_convert_custom_args(worker):
    assert "enable_custom_args" in worker.settings
    assert "avifenc_args" in worker.settings
    assert "cjxl_args" in worker.settings
    assert "cjpegli_args" in worker.settings
    assert "im_args" in worker.settings

def test_convert_downscale(worker):
    with convert_patches() as patches:
        worker.params["format"] = "JPEG"
        worker.params["downscaling"]["enabled"] = True
        mock_downscale = patches.enter_context(patch("core.worker.downscale"))
        
        worker.convert()

        mock_downscale.assert_called_once_with(worker.scl_params)

def test_convert_downscale_png(worker):
    with convert_patches() as patches:
        worker.params["format"] = "PNG"
        worker.params["downscaling"]["enabled"] = True
        mock_decodeAndDownscale = patches.enter_context(patch("core.worker.decodeAndDownscale"))
        
        worker.convert()

        mock_decodeAndDownscale.assert_called_once_with(
            worker.scl_params,
            worker.item_ext,
            worker.params["misc"]["keep_metadata"]
        )
def test_convert_jpeg_xl_intelligent_effort_canceled(worker):
    with (
        convert_patches() as patches,
        patch("core.worker.task_status.wasCanceled", return_value=True) as mock_canceled,
        patch("core.worker.os.remove") as mock_remove,
    ):
        worker.params["format"] = "JPEG XL"
        worker.params["intelligent_effort"] = True
        
        with pytest.raises(CancellationException):
            worker.convert()

        mock_canceled.assert_called_once()
        mock_remove.assert_called_once()

def test_convert_jpeg_xl_intelligent_effort_e9_smaller(worker):
    with convert_patches(
        getsize_side_effect=[300_000, 400_000],
        getUniqueFilePath_side_effect=["path_e7", "path_e9"]
    ) as patches:
        mock_convert = patches.enter_context(patch("core.worker.convert"))
        mock_remove = patches.enter_context(patch("core.worker.os.remove"))
        mock_rename = patches.enter_context(patch("core.worker.os.rename"))
        worker.params["format"] = "JPEG XL"
        worker.params["intelligent_effort"] = True
        
        worker.convert()

        assert mock_convert.call_count == 2
        assert mock_convert.call_args_list[0][0][2] == "path_e7"
        assert mock_convert.call_args_list[1][0][2] == "path_e9"
        mock_remove.assert_called_once_with("path_e7")
        mock_rename.assert_called_once_with("path_e9", worker.output)

def test_convert_jpeg_xl_intelligent_effort_e7_smaller(worker):
    with convert_patches(
        getsize_side_effect=[400_000, 300_000],
        getUniqueFilePath_side_effect=["path_e7", "path_e9"]
    ) as patches:
        mock_convert = patches.enter_context(patch("core.worker.convert"))
        mock_remove = patches.enter_context(patch("core.worker.os.remove"))
        mock_rename = patches.enter_context(patch("core.worker.os.rename"))
        worker.params["format"] = "JPEG XL"
        worker.params["intelligent_effort"] = True
        
        worker.convert()

        assert mock_convert.call_count == 2
        assert mock_convert.call_args_list[0][0][2] == "path_e7"
        assert mock_convert.call_args_list[1][0][2] == "path_e9"
        mock_remove.assert_called_once_with("path_e9")
        mock_rename.assert_called_once_with("path_e7", worker.output)

def test_convert_regular(worker):
    with convert_patches() as patches:
        mock_convert = patches.enter_context(patch("core.worker.convert"))
        
        worker.convert()

        mock_convert.assert_called_once()

def test_finishConversion_proxy(finishConversion_patches, worker):
    worker.item_abs_path = "item_abs_path"
    worker.org_item_abs_path = "org_item_abs_path"
    worker.proxy.proxyExists = MagicMock(return_value=True)

    worker.finishConversion()
    
    worker.proxy.proxyExists.assert_called_once()
    worker.proxy.cleanup.assert_called_once()
    assert worker.item_abs_path == "org_item_abs_path"

def test_finishConversion_no_proxy(finishConversion_patches, worker):
    worker.proxy.proxyExists = MagicMock(return_value=False)

    worker.finishConversion()
    
    worker.proxy.proxyExists.assert_called_once()
    worker.proxy.cleanup.assert_not_called()

def test_finishConversion_no_output(finishConversion_patches, worker):
    _, _, _, mock_isfile, *_ = finishConversion_patches
    mock_isfile.side_effect = [False, True, True]

    with pytest.raises(FileException) as exc:
        worker.finishConversion()
        
    assert "output not found" in exc.value.msg

def test_finishConversion_empty_output(finishConversion_patches, worker):
    _, _, mock_getsize, *_ = finishConversion_patches
    mock_getsize.return_value = 0

    with pytest.raises(FileException) as exc:
        worker.finishConversion()
        
    assert "output is empty" in exc.value.msg

@pytest.mark.parametrize("mode", ["Rename", "Skip"])
def test_finishConversion_rename_or_skip(finishConversion_patches, mode, worker):
    _, mock_rename, *_ = finishConversion_patches
    worker.params["if_file_exists"] = mode

    worker.finishConversion()
    
    mock_rename.assert_called_once_with(worker.output, "final/path/img.jpg")

def test_finishConversion_replace(finishConversion_patches, worker):
    mock_remove, mock_rename, *_ = finishConversion_patches
    worker.output = "temp/path/img.jpg"
    worker.final_output = "final/path/img.jpg"
    worker.params["if_file_exists"] = "Replace"

    worker.finishConversion()
    
    mock_remove.assert_called_once_with("final/path/img.jpg")
    mock_rename.assert_called_once_with("temp/path/img.jpg", "final/path/img.jpg")


def test_postConversionRoutines_no_output(postConversionRoutines_patches, worker):
    mock_isfile, *_ = postConversionRoutines_patches
    mock_isfile.return_value = False

    with pytest.raises(FileException) as exc:
        worker.postConversionRoutines()

    assert "Output not found" in exc.value.msg

@pytest.fixture
def mock_exiftool_env(worker):
    worker.params["format"] = "JPEG XL"
    worker.params["misc"]["keep_metadata"] = "ExifTool - Wipe"

    # with (
    #     patch("core.worker.metadata.isExifToolAvailable", return_value=(True, "")) as mock_isExifToolAvailable,
    #     patch("core.worker.metadata.runExifTool") as mock_runExifTool,
    #     patch("core.worker.Worker.logException") as mock_logException,
    # ):
    #     yield worker, {
    #         "isExifToolAvailable": mock_isExifToolAvailable,
    #         "runExifTool": mock_runExifTool,
    #         "logException": mock_logException,
    #     }

    patches = {
        "isExifToolAvailable": patch("core.worker.metadata.isExifToolAvailable", return_value=(True, "")),
        "runExifTool": patch("core.worker.metadata.runExifTool"),
        "logException": patch("core.worker.Worker.logException"),
    }

    with ExitStack() as stack:
        mocks = {name: stack.enter_context(patcher) for name, patcher in patches.items()}
        yield worker, mocks

def test_runExifTool_happy_path(mock_exiftool_env):
    worker, mocks = mock_exiftool_env

    worker.runExifTool()

    mocks["runExifTool"].assert_called_once_with(
        worker.org_item_abs_path,
        worker.output,
        worker.settings["exiftool_args"]["ExifTool - Wipe"].strip().split(" "),
    )

def test_runExifTool_dont_run(mock_exiftool_env):
    worker, mocks = mock_exiftool_env

    worker.params["format"] = "Lossless JPEG Recompression"
    worker.runExifTool()
    mocks["runExifTool"].assert_not_called()

    worker.params["format"] = "JPEG XL"
    worker.params["misc"]["keep_metadata"] = "Not ExifTool"
    worker.runExifTool()
    mocks["runExifTool"].assert_not_called()

def test_runExifTool_not_available(mock_exiftool_env):
    worker, mocks = mock_exiftool_env
    mocks["isExifToolAvailable"].return_value = (False, "error msg")

    worker.runExifTool()

    mocks["logException"].assert_called_once()
    assert "error msg" == mocks["logException"].call_args[0][1]

def test_runExifTool_args_empty(mock_exiftool_env):
    worker, mocks = mock_exiftool_env
    worker.settings["exiftool_args"]["ExifTool - Wipe"] = ""

    worker.runExifTool()
    
    mocks["logException"].assert_called_once()
    assert "Argument list for \"ExifTool - Wipe\" is empty." in mocks["logException"].call_args[0][1]

@pytest.mark.parametrize("attributes", [True, False])
def test_postConversionRoutines_attributes(attributes, postConversionRoutines_patches, worker):
    _, _, mock_copystat, *_ = postConversionRoutines_patches
    worker.params["misc"]["attributes"] = attributes

    worker.postConversionRoutines()

    assert mock_copystat.called == attributes

def test_postConversionRoutines_attributes_failed(postConversionRoutines_patches, worker):
    _, _, mock_copystat, *_ = postConversionRoutines_patches
    mock_copystat.side_effect = OSError()
    worker.params["misc"]["attributes"] = True

    with pytest.raises(FileException) as exc:
        worker.postConversionRoutines()

    assert "Failed to apply attributes" in exc.value.msg

@pytest.mark.parametrize("mode, send2trash_called, remove_called", [
    ("To Trash", True, False),
    ("Permanently", False, True),
])
def test_postConversionRoutines_delete_to_trash(
    mode, send2trash_called, remove_called,
    postConversionRoutines_patches, worker
):
    _, _, _, mock_remove, mock_send2trash = postConversionRoutines_patches
    worker.params["delete_original"] = True
    worker.params["delete_original_mode"] = mode
    
    worker.postConversionRoutines()

    assert mock_send2trash.called == send2trash_called
    assert mock_remove.called == remove_called

def test_postConversionRoutines_delete_failed(postConversionRoutines_patches, worker):
    _, _, _, _, mock_send2trash = postConversionRoutines_patches
    mock_send2trash.side_effect = OSError
    worker.params["delete_original"] = True
    worker.params["delete_original_mode"] = "To Trash"

    with pytest.raises(FileException) as exc:
        worker.postConversionRoutines()

    assert "Failed to delete original file" in exc.value.msg

@pytest.mark.parametrize("png, webp, jxl", [
    (True, True, True),
    (False, True, True),
    (False, False, True),
])
def test_smallestLossless_path_pool_filled(png, webp, jxl, smallestLossless_patches, worker):
    _, mock_getUniqueFilePath, *_ = smallestLossless_patches
    worker.params["smallest_format_pool"]["png"] = png
    worker.params["smallest_format_pool"]["jxl"] = webp
    worker.params["smallest_format_pool"]["webp"] = jxl

    worker.smallestLossless()

    assert mock_getUniqueFilePath.call_count == sum([png, webp, jxl])

def test_smallestLossless_path_pool_empty(smallestLossless_patches, worker):
    worker.params["smallest_format_pool"] = {}
    with pytest.raises(GenericException) as exc:
        worker.smallestLossless()

    assert "No formats selected" in exc.value.msg

def test_smallestLossless_generate_files(smallestLossless_patches, worker):
    _, _, _, mock_copy, mock_optimize, mock_convert, *_ = smallestLossless_patches
    worker.params["smallest_format_pool"]["png"] = True
    worker.params["smallest_format_pool"]["jxl"] = True
    worker.params["smallest_format_pool"]["webp"] = True
    
    worker.smallestLossless()

    assert mock_copy.called
    assert mock_optimize.called
    assert mock_convert.call_count == 2

@pytest.mark.parametrize("jxl_lossless_jpeg", [True, False])
def test_smallestLossless_jpg_to_jxl_lossless(jxl_lossless_jpeg, smallestLossless_patches, worker):
    _, _, _, _, _, mock_convert, *_ = smallestLossless_patches
    worker.item_ext = "jpg"
    worker.item_abs_path = "proxy/image"
    worker.org_item_abs_path = "original/image"
    worker.params["smallest_format_pool"]["png"] = False
    worker.params["smallest_format_pool"]["jxl"] = True
    worker.params["smallest_format_pool"]["webp"] = False
    worker.settings["jxl_lossless_jpeg"] = jxl_lossless_jpeg

    worker.smallestLossless()

    assert worker.jpg_to_jxl_lossless == jxl_lossless_jpeg
    assert mock_convert.call_args[0][1] == "original/image" if jxl_lossless_jpeg else "proxy/image"

@pytest.mark.parametrize("png_size, webp_size, jxl_size, expected_smallest", [
    (100_000, 150_000, 150_000, "png"),
    (150_000, 100_000, 150_000, "webp"),
    (150_000, 150_000, 100_000, "jxl"),
])
def test_smallestLossless_smallest_file(png_size, webp_size, jxl_size, expected_smallest, smallestLossless_patches, worker):
    worker.params["smallest_format_pool"]["png"] = True
    worker.params["smallest_format_pool"]["jxl"] = True
    worker.params["smallest_format_pool"]["webp"] = True
    mock_getsize, _, _, _, _, _, mock_remove = smallestLossless_patches
    mock_getsize.side_effect = lambda file_path: {
       "png": png_size,
        "webp": webp_size,
        "jxl": jxl_size, 
    }.get(getSuffix(file_path), 0)

    worker.smallestLossless()

    for args, kwargs in mock_remove.call_args_list:     # Remove bigger 
        assert expected_smallest not in args[0]

    # Finish
    assert worker.output_ext == expected_smallest 
    assert getSuffix(worker.output) == expected_smallest
    assert getSuffix(worker.final_output) == expected_smallest

def test_smallestLossless_getsize_failed_cleanup(smallestLossless_patches, worker):
    mock_getsize, _, _, _, _, _, mock_remove = smallestLossless_patches
    mock_getsize.side_effect = OSError()
    with pytest.raises(FileException) as exc:
        worker.smallestLossless()

    assert "Failed to get file sizes" in exc.value.msg
    assert mock_remove.call_count == 3

def test_smallestLossless_getsize_failed_cleanup_failed(smallestLossless_patches, worker):
    mock_getsize, _, _, _, _, _, mock_remove = smallestLossless_patches
    mock_getsize.side_effect = OSError()
    mock_remove.side_effect = OSError()
    with pytest.raises(FileException) as exc:
        worker.smallestLossless()

    assert "Failed to delete tmp files" in exc.value.msg
    assert mock_remove.call_count == 1

def test_smallestLossless_remove_bigger_failed(smallestLossless_patches, worker):
    mock_getsize, _, _, _, _, _, mock_remove = smallestLossless_patches
    mock_remove.side_effect = OSError()
    with pytest.raises(FileException) as exc:
        worker.smallestLossless()

    assert "Failed to delete tmp files" in exc.value.msg
    assert "SL4" in exc.value.id
    assert mock_remove.call_count == 1

@pytest.mark.parametrize("jxl_lossless_jpeg", [True, False])
def test_smallestLossless_args(jxl_lossless_jpeg, smallestLossless_patches, worker):
    _, _, mock_getArgs, _, mock_optimize, mock_convert, *_ = smallestLossless_patches
    mock_getArgs.return_value = ["--metadata_arg"]
    worker.settings["jxl_lossless_jpeg"] = jxl_lossless_jpeg
    worker.item_ext = "jpg"

    worker.smallestLossless()
    assert mock_optimize.call_args[0][2] == [ "-o 2", "-t 4", "--metadata_arg" ]
    for args, kwargs in mock_convert.call_args_list:
        match getSuffix(args[2]):
            case "webp":
                assert args[3] == [
                    "-define webp:thread-level=1",
                    "-define webp:method=6",
                    "-define webp:lossless=true",
                    "--metadata_arg"
                ]
            case "jxl":
                assert args[3] == [
                    "-q 100",
                    "-e 7",
                    "--num_threads=4",
                    f"--lossless_jpeg={1 if jxl_lossless_jpeg else 0}",
                    "--metadata_arg"
                ]

@pytest.mark.parametrize("effort, expected_args", [
    (7, ["--lossless_jpeg=1", "-e 7", "--num_threads=4"]),
    (9, ["--lossless_jpeg=1", "-e 9", "--num_threads=4"]),
])
def test_losslesslyRecompressJPEG(effort, expected_args, worker):
    worker.params["effort"] = effort
    with (
        patch("core.worker.convert") as mock_convert,
        patch("core.worker.CJXL_PATH", "/path/cjxl"),
    ):
        worker.losslesslyRecompressJPEG()

    mock_convert.assert_called_once_with(
        "/path/cjxl",
        worker.item_abs_path,
        worker.output,
        expected_args,
        0
    )

def test_reconstructJPEG(worker):
    worker.org_item_abs_path = "/original/item/path/image.jxl"
    worker.output = "/tmp/output/image.jxl"
    with (
        patch("core.worker.convert") as mock_convert,
        patch("core.worker.DJXL_PATH", "/path/djxl"),
    ):
        worker.reconstructJPEG()
    
    mock_convert.assert_called_once_with(
        "/path/djxl",
        "/original/item/path/image.jxl",
        "/tmp/output/image.jxl",
        ["--num_threads=4"],
        0
    )