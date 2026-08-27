from pathlib import Path
from unittest.mock import MagicMock, patch, call
from contextlib import ExitStack, contextmanager

import pytest
from PySide6.QtCore import QMutex
from PySide6.QtTest import QSignalSpy

from core.worker import Worker, WorkerSignals
from core.proxy import Proxy
from core.exceptions import FileException, GenericException, CancellationException

@pytest.fixture
def worker():
    mutex = QMutex()
    worker_signals = WorkerSignals()
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
            "jxl_verify": False,
            "jxl_normalize_enable": False,
            "jxl_normalize_when": "On Fail",
            "aom_av1_chroma_subsampling": "Default",
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
                "megapixels": 2.0,
                "resample": "Default",
            },
            "misc": {
                "keep_metadata": "Encoder - Wipe",
                "keep_timestamps": False,
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
            "jxl_auto_lossless_jpeg": False,
            "copy_if_larger": False,
            "keep_if_larger": False,
            "exiftool_args": {
                "ExifTool - Wipe": "-all= -tagsFromFile @ -icc_profile:all -ColorSpace:all -Orientation $dst -overwrite_original",
                "ExifTool - Preserve": "-tagsFromFile $src $dst -overwrite_original",
            },
            "avif_encoder": "AOM AV1",
            "avif_aom_iq_tune": False,
            "avif_bit_depth": "Auto",
            "png_opt_pixel_format": False,
        },
        4,
        mutex,
        worker_signals,
    )
    w.proxy = MagicMock(spec=Proxy)
    w.scl_params = {}
    w.output_dir = "output/dir/"

    return w

def normalizePath(path: str):
    return str(Path(path))

def getSuffix(path: str):
    return Path(path).suffix[1:]

def test_logException(worker):
    id_str, msg, source = "ID0", "Exception", str(Path("/test/path/image.png"))

    worker.org_item_abs_path = source
    spy = QSignalSpy(worker.signals.exception)
    worker.logException(id_str, msg)

    assert spy.at(0)[0] == id_str
    assert spy.at(0)[1] == msg
    assert spy.at(0)[2] == source

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

def test_run_finally(worker):
    spy_completed = QSignalSpy(worker.signals.completed)
    worker.run()
    worker.proxy.cleanUp.assert_called_once_with(raising=False)
    assert spy_completed.count() == 1

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

@pytest.fixture
def setupConversion_patches():
    mocks = {
        "isProxyNeeded": patch("core.worker.Proxy.isProxyNeeded", return_value=False),
        "makedirs": patch("core.worker.os.makedirs", side_effect=None),
        "getUniqueTmpFilePath": patch("core.worker.getUniqueTmpFilePath", return_value=normalizePath("/output/dir/image.jpg")),
        "getOutputDir": patch("core.worker.getOutputDir", return_value="/output/dir/"),
        "isfile": patch("core.worker.os.path.isfile", side_effect=[True, True]),
        "getsize": patch("core.worker.os.path.getsize", return_value=300_000),
        "getFreeSpaceLeft": patch("core.worker.getFreeSpaceLeft", return_value=300_000_000_000),
        "getExtension": patch("core.worker.getExtension", return_value="jxl"),
        "hasReconstructionData": patch("core.worker.lossless_jpeg.hasReconstructionData", return_value=True),
    }

    with ExitStack() as stack:
        _mock = {name: stack.enter_context(patcher) for name, patcher in mocks.items()}
        yield _mock


def test_setupConversion_regular(setupConversion_patches, worker):
    mocks = setupConversion_patches
    output = normalizePath("/output/dir/image_unique.jpg")
    output_dir = normalizePath("/output/dir/")
    final_output = normalizePath("/output/dir/image.jpg")
    worker.item_name = "image"
    worker.params["format"] = "JPEG"
    mocks["getUniqueTmpFilePath"].return_value = output
    mocks["getOutputDir"].return_value = output_dir
    mocks["getExtension"].return_value = "jpg"

    worker.setupConversion()
    
    assert worker.output == output
    assert worker.final_output == final_output
    assert worker.output_dir == output_dir
    assert worker.output_ext == "jpg"

def test_setupConversion_makedirs_error(setupConversion_patches, worker):
    setupConversion_patches["makedirs"].side_effect = OSError
    
    with pytest.raises(FileException) as exc:
        worker.setupConversion()

    assert "Failed to create output directory" in exc.value.msg

def test_setupConversion_space_left_pass(setupConversion_patches, worker):
    worker.setupConversion()

def test_setupConversion_space_left_exception(setupConversion_patches, worker):
    setupConversion_patches["getFreeSpaceLeft"].return_value = 10_000
    with pytest.raises(FileException) as exc:
        worker.setupConversion()

    assert "No space left on device" in exc.value.msg

@pytest.mark.parametrize("jxl_png_fallback", [True, False])
def test_setupConversion_jpeg_reconstruction_rec_data_found(jxl_png_fallback, setupConversion_patches, worker):
    setupConversion_patches["hasReconstructionData"].return_value = True
    worker.params["format"] = "JPEG Reconstruction"
    worker.params["jxl_png_fallback"] = jxl_png_fallback
    worker.item_ext = "jxl"

    worker.setupConversion()
    assert worker.output_ext == "jpg"

@pytest.mark.parametrize("jxl_png_fallback", [True, False])
def test_setupConversion_jpeg_reconstruction_rec_data_not_found(jxl_png_fallback, setupConversion_patches, worker):
    worker.params["format"] = "JPEG Reconstruction"
    worker.params["jxl_png_fallback"] = jxl_png_fallback
    setupConversion_patches["hasReconstructionData"].return_value = False
    worker.item_ext = "jxl"

    if jxl_png_fallback:
        worker.setupConversion()
        assert worker.output_ext == "png"
    else:
        with pytest.raises(FileException) as exc:
            worker.setupConversion()
        assert "Reconstruction data not found" in exc.value.msg

def test_setupConversion_jpeg_reconstruction_bad_input(setupConversion_patches, worker):
    worker.params["format"] = "JPEG Reconstruction"
    worker.item_ext = "jpg"

    with pytest.raises(FileException) as exc:
        worker.setupConversion()

    assert "Only JPEG XL images are allowed" in exc.value.msg

def test_setupConversion_png_opt_reconstruction_bad_input(setupConversion_patches, worker):
    worker.params["format"] = "PNG Optimization"
    worker.item_ext = "jpg"

    with pytest.raises(FileException) as exc:
        worker.setupConversion()

    assert "Only PNG images are allowed" in exc.value.msg

def test_setupConversion_assign_output_path(setupConversion_patches, worker):
    mocks = setupConversion_patches
    mocks["getUniqueTmpFilePath"].return_value = normalizePath("/tmp/path/image.jxl")
    mocks["getOutputDir"].return_value = normalizePath("/tmp/path/")
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
    worker.proxy.generate = MagicMock(return_value="/tmp/path/image.png")
    setupConversion_patches["isProxyNeeded"].return_value = True

    worker.setupConversion()

    assert worker.item_abs_path == "/tmp/path/image.png"

def test_setupConversion_downscaling_no_key_error(setupConversion_patches, worker):
    worker.params["downscaling"]["enabled"] = True
    worker.setupConversion()
    assert worker.scl_params is not None

@pytest.fixture
def worker_convert_patches(worker):
    patches = {
        "runBinary": patch("core.worker.runBinary", return_value=("stdout", "stderr")),
        "remove": patch("core.worker.os.remove"),
        "rename": patch("core.worker.os.rename"),
        "getsize": patch("core.worker.os.path.getsize", return_value=[300_000, 400_00]),
        "isfile": patch("core.worker.os.path.isfile", return_value=True),
        "getUniqueTmpFilePath": patch("core.worker.getUniqueTmpFilePath", return_value="final/path/img.jpg"),
        "getDecoder": patch("core.worker.getDecoder", return_value="path/to/decoder"),
        "getDecoderArgs": patch("core.worker.getDecoderArgs", return_value=[]),
        "getArgs": patch("core.metadata.getArgs", return_value=[]),
        "downscale": patch("core.worker.downscale"),
        "decodeAndDownscale": patch("core.worker.decodeAndDownscale"),
        "wasCanceled": patch("core.worker.task_status.wasCanceled", return_value=False),
    }

    worker.params["misc"]["keep_metadata"] = True

    with ExitStack() as stack:
        _mocks = {name: stack.enter_context(patcher) for name, patcher in patches.items()}
        yield worker, _mocks

@pytest.mark.parametrize("quality, effort, lossless, modular, intelligent_effort, jxl_auto_lossless_jpeg, item_ext, expected_args, expected_jpg_to_jxl_lossless", [
    (80, 7, True, False, False, True, "png", ["-q 100", "-e 7", "--lossless_jpeg=1", "--num_threads=4"], False),
    (80, 7, False, False, False, False, "png", ["-q 80", "-e 7", "--lossless_jpeg=0", "--num_threads=4"], False),
    (80, 7, False, True, False, False, "png", ["-q 80", "-e 7", "--lossless_jpeg=0", "--num_threads=4", "--modular=1"], False),
    (80, 7, False, True, True, False, "png", ["-q 80", "-e 9", "--lossless_jpeg=0", "--num_threads=4", "--modular=1"], False),
    (80, 7, True, False, True, True, "png", ["-q 100", "-e 9", "--lossless_jpeg=1", "--num_threads=4"], False),
    (80, 7, True, False, False, True, "jpg", ["-q 100", "-e 7", "--lossless_jpeg=1", "--num_threads=4"], True),
])
def test_convert_args_jpeg_xl(
    quality, effort, lossless, modular, intelligent_effort, jxl_auto_lossless_jpeg, item_ext, expected_args, expected_jpg_to_jxl_lossless, worker_convert_patches
):
    worker, mocks = worker_convert_patches
    worker.params["format"] = "JPEG XL"
    worker.params["quality"] = quality
    worker.params["lossless"] = lossless
    worker.params["effort"] = effort
    worker.params["jxl_modular"] = modular
    worker.params["intelligent_effort"] = intelligent_effort
    worker.settings["jxl_auto_lossless_jpeg"] = jxl_auto_lossless_jpeg
    worker.item_ext = item_ext

    worker.convert()

    assert mocks["runBinary"].call_args[0][1] == expected_args
    assert worker.lossless_jpeg == expected_jpg_to_jxl_lossless

def test_convert_jpeg_xl_error_auto_jpeg_transcoding(worker_convert_patches):
    worker, mocks = worker_convert_patches

    worker.params["format"] = "JPEG XL"
    worker.params["lossless"] = True
    worker.settings["jxl_auto_lossless_jpeg"] = True
    worker.item_ext = "jpg"
    mocks["runBinary"].return_value = ("JPEG XL encoder", "JPEG bitstream reconstruction data could not be created")
    mocks["isfile"].return_value = False

    with pytest.raises(FileException) as exc_info:
        worker.convert()
    
    assert "The JPEG image could not be transcoded" in exc_info.value.msg 
    
def test_convert_jpeg_xl_error_default(worker_convert_patches):
    worker, mocks = worker_convert_patches

    worker.params["format"] = "JPEG XL"
    worker.params["lossless"] = True
    mocks["runBinary"].return_value = ("JPEG XL encoder", "Error message")
    mocks["isfile"].return_value = False

    with pytest.raises(FileException) as exc_info:
        worker.convert()
    
    assert "Error message" in exc_info.value.msg 

@pytest.mark.parametrize("encoder, quality, speed, chroma_subsampling, expected_args", [
    ("AOM AV1", 80, 6, "Default", ["-q 80", "-s 6", "-j 4", "-c aom", "-a c:tune=ssim"]),
    ("AOM AV1", 80, 6, "4:4:4", ["-q 80", "-s 6", "-j 4", "-c aom", "-y 444", "-a c:tune=ssim"]),
    ("AOM AV1", 80, 6, "4:2:2", ["-q 80", "-s 6", "-j 4", "-c aom", "-y 422", "-a c:tune=ssim"]),
    ("AOM AV1", 80, 6, "4:2:0", ["-q 80", "-s 6", "-j 4", "-c aom", "-y 420", "-a c:tune=ssim"]),
    ("SVT-AV1-PSY", 90, 5, "4:4:4", ["-q 90", "-s 5", "-j 4", "-c svt", "-y 420", "-a tune=4"]),
])
def test_convert_args_avif(encoder, quality, speed, chroma_subsampling, expected_args, worker_convert_patches):
    worker, mocks = worker_convert_patches

    worker.settings["avif_encoder"] = encoder
    worker.params["format"] = "AVIF"
    worker.params["quality"] = quality
    worker.params["effort"] = speed
    worker.params["aom_av1_chroma_subsampling"] = chroma_subsampling

    worker.convert()
    
    assert mocks["runBinary"].call_args[0][1] == expected_args

def test_avif_bit_depth_auto(worker_convert_patches):
    worker, mocks = worker_convert_patches
    worker.params["format"] = "AVIF"
    worker.settings["avif_bit_depth"] = "Auto"

    worker.convert()

    for arg in mocks["runBinary"].call_args[0][1]:
        assert arg[:3] != "-d "

def test_avif_bit_depth_specified(worker_convert_patches):
    worker, mocks = worker_convert_patches
    worker.params["format"] = "AVIF"
    worker.settings["avif_bit_depth"] = "8"

    worker.convert()

    assert "-d 8" in mocks["runBinary"].call_args[0][1]

@pytest.mark.parametrize("iq_tune", [True, False])
def test_avif_iq_tune(iq_tune, worker_convert_patches):
    worker, mocks = worker_convert_patches
    worker.params["format"] = "AVIF"
    worker.settings["avif_aom_iq_tune"] = iq_tune

    worker.convert()

    assert ("-a c:tune=iq" in mocks["runBinary"].call_args[0][1]) == iq_tune

@pytest.mark.parametrize("quality, encoder, chroma_subsampling, disable_progressive_jpegli, expected_args", [
    (80, "JPEGLI", "Default", False, ["-q 80"]),
    (80, "JPEGLI", "4:4:4", False, ["-q 80", "--chroma_subsampling=444"]),
    (80, "JPEGLI", "Default", True, ["-q 80", "-p 0"]),
    (80, "libjpeg", "Default", False, ["-quality 80"]),
    (80, "libjpeg", "4:4:4", False, ["-quality 80", "-sampling-factor 4:4:4"]),
])
def test_convert_args_jpeg(quality, encoder, chroma_subsampling, disable_progressive_jpegli, expected_args, worker_convert_patches):
    worker, mocks = worker_convert_patches
    worker.params["format"] = "JPEG"
    worker.settings["jpg_encoder"] = encoder
    worker.params["quality"] = quality
    worker.settings["disable_progressive_jpegli"] = disable_progressive_jpegli
    if encoder == "JPEGLI":
        worker.params["jpegli_chroma_subsampling"] = chroma_subsampling
    else:
        worker.params["jpg_chroma_subsampling"] = chroma_subsampling

    worker.convert()

    assert mocks["runBinary"].call_args[0][1] == expected_args

@pytest.mark.parametrize("quality, method, lossless, expected_args", [
    (80, 6, False, ["-quality 80", "-define webp:thread-level=1", "-define webp:method=6"]),
    (50, 5, True, ["-define webp:lossless=true", "-define webp:thread-level=1", "-define webp:method=5"]),
    (50, 5, False, ["-quality 50", "-define webp:thread-level=1", "-define webp:method=5"]),
])
def test_convert_args_webp(quality, method, lossless, expected_args, worker_convert_patches):
    worker, mocks = worker_convert_patches
    worker.params["format"] = "WebP"
    worker.params["quality"] = quality
    worker.params["lossless"] = lossless
    worker.params["effort"] = method

    worker.convert()

    assert mocks["runBinary"].call_args[0][1] == expected_args

def test_convert_args_png(worker_convert_patches):
    worker, mocks = worker_convert_patches
    mocks["getDecoderArgs"].return_value = ["--test_arg=1"]

    worker.convert()

    assert mocks["runBinary"].call_args[0][0] == mocks["getDecoder"].return_value
    assert mocks["runBinary"].call_args[0][1] == ["--test_arg=1"]

def test_convert_args_unknown(worker_convert_patches):
    worker, mocks = worker_convert_patches

    worker.params["format"] = "Unknown"

    with pytest.raises(GenericException):
        worker.convert()

def test_convert_metadata_args(worker_convert_patches):
    worker, mocks = worker_convert_patches
    mocks["getArgs"].return_value = ["--metadata_arg"]
    
    worker.convert()

    assert mocks["runBinary"].call_args[0][1] == mocks["getArgs"].return_value

def test_convert_custom_args(worker):
    assert "enable_custom_args" in worker.settings
    assert "avifenc_args" in worker.settings
    assert "cjxl_args" in worker.settings
    assert "cjpegli_args" in worker.settings
    assert "im_args" in worker.settings

def test_convert_downscale(worker_convert_patches):
    worker, mocks = worker_convert_patches
    worker.params["format"] = "JPEG"
    worker.params["downscaling"]["enabled"] = True
    
    worker.convert()

    mocks["downscale"].assert_called_once_with(worker.scl_params, worker.mutex)

def test_convert_downscale_png(worker_convert_patches):
    worker, mocks = worker_convert_patches
    worker.params["format"] = "PNG"
    worker.params["downscaling"]["enabled"] = True
    
    worker.convert()

    mocks["decodeAndDownscale"].assert_called_once_with(
        worker.scl_params,
        worker.item_ext,
        worker.params["misc"]["keep_metadata"],
        worker.mutex,
    )

def test_convert_jpeg_xl_intelligent_effort_e9_smaller(worker_convert_patches):
    worker, mocks = worker_convert_patches
    mocks["getsize"].side_effect = [300_000, 400_000]
    mocks["getUniqueTmpFilePath"].side_effect = ["path_e7", "path_e9"]
    worker.params["format"] = "JPEG XL"
    worker.params["intelligent_effort"] = True
    
    worker.convert()

    assert mocks["runBinary"].call_count == 2
    assert mocks["runBinary"].call_args_list[0][0][3] == "path_e7"
    assert mocks["runBinary"].call_args_list[1][0][3] == "path_e9"
    mocks["remove"].assert_called_once_with("path_e7")
    mocks["rename"].assert_called_once_with("path_e9", worker.output)

def test_convert_jpeg_xl_intelligent_effort_e7_smaller(worker_convert_patches):
    worker, mocks = worker_convert_patches
    mocks["getsize"].side_effect=[400_000, 300_000]
    mocks["getUniqueTmpFilePath"].side_effect = ["path_e7", "path_e9"]
    worker.params["format"] = "JPEG XL"
    worker.params["intelligent_effort"] = True
    
    worker.convert()

    assert mocks["runBinary"].call_count == 2
    assert mocks["runBinary"].call_args_list[0][0][3] == "path_e7"
    assert mocks["runBinary"].call_args_list[1][0][3] == "path_e9"
    mocks["remove"].assert_called_once_with("path_e9")
    mocks["rename"].assert_called_once_with("path_e7", worker.output)

def test_convert_regular(worker_convert_patches):
    worker, mocks = worker_convert_patches
        
    worker.convert()

    mocks["runBinary"].assert_called_once()

@pytest.fixture
def finishConversion_patches(worker):
    mocks = {
        "remove": patch("core.worker.os.remove"),
        "removeFile": patch("core.worker.removeFile"),
        "send2trash": patch("core.worker.send2trash"),
        "rename": patch("core.worker.os.rename"),
        "removeFile": patch("core.worker.removeFile"),
        "getsize": patch("core.worker.os.path.getsize", return_value=300_000),
        "isfile": patch("core.worker.os.path.isfile", side_effect=[True, True, True]),
        "getUniqueFilePath": patch("core.worker.getUniqueFilePath", return_value="final/path/img.jpg"),
        "copyfile": patch("core.worker.shutil.copyfile"),
        "isSamePath": patch("core.worker.isSamePath", return_value=False),
    }

    with ExitStack() as stack:
        _mocks = { name: stack.enter_context(patcher) for name, patcher in mocks.items() }
        yield worker, _mocks

def test_finishConversion_proxy(finishConversion_patches):
    worker, mocks = finishConversion_patches

    worker.item_abs_path = "item_abs_path"
    worker.org_item_abs_path = "org_item_abs_path"
    worker.proxy.proxyExists = MagicMock(return_value=True)

    worker.finishConversion()
    
    worker.proxy.proxyExists.assert_called_once()
    worker.proxy.cleanUp.assert_called_once()
    assert worker.item_abs_path == "org_item_abs_path"

def test_finishConversion_no_proxy(finishConversion_patches):
    worker, mocks = finishConversion_patches
    
    worker.proxy.proxyExists = MagicMock(return_value=False)

    worker.finishConversion()

    worker.proxy.proxyExists.assert_called_once()
    worker.proxy.cleanUp.assert_not_called()

def test_finishConversion_no_output(finishConversion_patches):
    worker, mocks = finishConversion_patches
    mocks["isfile"].side_effect = [False, True, True]

    with pytest.raises(FileException) as exc:
        worker.finishConversion()

    assert "output not found" in exc.value.msg

def test_finishConversion_empty_output(finishConversion_patches):
    worker, mocks = finishConversion_patches
    mocks["getsize"].return_value = 0

    with pytest.raises(FileException) as exc:
        worker.finishConversion()

    assert "output is empty" in exc.value.msg

@pytest.mark.parametrize("mode", ["Rename", "Skip"])
def test_finishConversion_rename_or_skip(finishConversion_patches, mode):
    worker, mocks = finishConversion_patches
    worker.params["if_file_exists"] = mode

    worker.finishConversion()

    mocks["rename"].assert_called_once_with(worker.output, "final/path/img.jpg")

def test_finishConversion_replace(finishConversion_patches):
    worker, mocks = finishConversion_patches
    worker.output = "temp/path/img.jpg"
    worker.final_output = "final/path/img.jpg"
    worker.params["if_file_exists"] = "Replace"

    worker.finishConversion()

    mocks["removeFile"].assert_called_once_with("final/path/img.jpg")
    mocks["rename"].assert_called_once_with("temp/path/img.jpg", "final/path/img.jpg")

@pytest.mark.parametrize("delete_original_mode, delete_method ", (
    ("To Trash", "send2trash"),
    ("Permanently", "removeFile"),
))
def test_finishConversion_replace_edge_case_delete_original(delete_original_mode, delete_method, finishConversion_patches):
    worker, mocks = finishConversion_patches
    worker.output = "temp/path/img.jpg"
    worker.final_output = "final/path/img.jpg"
    worker.params["if_file_exists"] = "Replace"
    worker.params["custom_output_dir"] = False
    worker.params["delete_original"] = True
    worker.params["delete_original_mode"] = delete_original_mode
    mocks["isSamePath"].return_value = True

    worker.finishConversion()

    mocks[delete_method].assert_called_once_with("final/path/img.jpg")

@pytest.mark.parametrize("file_format, getsize_side_effect, copy_if_larger_enabled, expected_to_run", [
    ("JPEG XL", [300_000, 300_000, 400_000], True, True),
    ("JPEG XL", [300_000, 300_000, 300_000], True, False),
    ("JPEG XL", [300_000, 300_000, 299_000], True, False),
    ("JPEG XL", [300_000, 300_000, 400_000], False, False),
    ("PNG", [300_000, 300_000, 400_000], True, False),
    ("Lossless JPEG Transcoding", [300_000, 300_000, 400_000], True, False),
    ("JPEG Reconstruction", [300_000, 300_000, 400_000], True, False),
])
def test_finishConversion_copy_if_larger(finishConversion_patches, file_format, getsize_side_effect, copy_if_larger_enabled, expected_to_run):
    worker, mocks = finishConversion_patches
    worker.params["format"] = file_format
    worker.settings["copy_if_larger"] = copy_if_larger_enabled
    mocks["getsize"].side_effect = getsize_side_effect
    
    worker.finishConversion()

    assert mocks["remove"].call_count == (1 if expected_to_run else 0)
    assert mocks["copyfile"].call_count == (1 if expected_to_run else 0)
    if expected_to_run:
        assert mocks["remove"].call_args[0][0] == mocks["getUniqueFilePath"].return_value
        assert mocks["copyfile"].call_args[0] == (worker.org_item_abs_path, worker.final_output)

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

    worker.lossless_jpeg = True
    worker.runExifTool()
    mocks["runExifTool"].assert_not_called()

    worker.lossless_jpeg = False
    worker.params["format"] = "JPEG XL"
    worker.params["misc"]["keep_metadata"] = "Not ExifTool"
    worker.runExifTool()
    mocks["runExifTool"].assert_not_called()

@pytest.fixture
def postConversionRoutines_patched(worker):
    mocks = {
        "isfile": patch("core.worker.os.path.isfile", return_value=True),
        "runExifTool": patch("core.worker.metadata.runExifTool", return_value=[]),
        "applyTimestamps": patch("core.worker.timestamps.applyTimestamps"),
        "remove": patch("core.worker.os.remove"),
        "removeFile": patch("core.worker.removeFile"),
        "send2trash": patch("core.worker.send2trash"),
        "isSamePath": patch("core.worker.isSamePath", return_value=False),
    }

    with ExitStack() as stack:
        _mocks = {name: stack.enter_context(patcher) for name, patcher in mocks.items()}
        yield worker, _mocks

def test_postConversionRoutines_no_output(postConversionRoutines_patched):
    worker, mocks = postConversionRoutines_patched
    mocks["isfile"].return_value = False

    with pytest.raises(FileException) as exc:
        worker.postConversionRoutines()

    assert "Output not found" in exc.value.msg

def test_postConversionRoutines_keep_timestamps(postConversionRoutines_patched):
    worker, mocks = postConversionRoutines_patched
    worker.params["misc"]["keep_timestamps"] = True
    mock_timestamps = MagicMock()
    worker.src_timestamps = mock_timestamps
    sample_output = "/tmp/sample_out.jpg"
    worker.final_output = sample_output

    worker.postConversionRoutines()

    mocks["applyTimestamps"].assert_called_once_with(sample_output, mock_timestamps)

def test_postConversionRoutines_keep_timestamps_exc(postConversionRoutines_patched):
    worker, mocks = postConversionRoutines_patched
    mocks["applyTimestamps"].side_effect = OSError("sample exc")
    worker.params["misc"]["keep_timestamps"] = True
    worker.src_timestamps = MagicMock()

    with pytest.raises(FileException):
        worker.postConversionRoutines()

    mocks["applyTimestamps"].assert_called_once()

def test_postConversionRoutines_keep_timestamps_src_timestamps_unavailable(postConversionRoutines_patched):
    worker, mocks = postConversionRoutines_patched
    worker.params["misc"]["keep_timestamps"] = True
    worker.src_timestamps = None

    worker.postConversionRoutines()

    mocks["applyTimestamps"].assert_not_called()

def test_postConversionRoutines_do_not_keep_timestamps(postConversionRoutines_patched):
    worker, mocks = postConversionRoutines_patched
    worker.params["misc"]["keep_timestamps"] = False
    worker.src_timestamps = MagicMock()

    worker.postConversionRoutines()

    mocks["applyTimestamps"].assert_not_called()

@pytest.mark.parametrize("mode, send2trash_called, remove_called", [
    ("To Trash", True, False),
    ("Permanently", False, True),
])
def test_postConversionRoutines_delete_to_trash(
    mode, send2trash_called, remove_called,
    postConversionRoutines_patched
):
    worker, mocks = postConversionRoutines_patched
    worker.params["delete_original"] = True
    worker.params["delete_original_mode"] = mode
    
    worker.postConversionRoutines()

    assert mocks["send2trash"].called == send2trash_called
    assert mocks["removeFile"].called == remove_called

def test_postConversionRoutines_delete_failed(postConversionRoutines_patched):
    worker, mocks = postConversionRoutines_patched
    mocks["send2trash"].side_effect = OSError
    worker.params["delete_original"] = True
    worker.params["delete_original_mode"] = "To Trash"

    with pytest.raises(FileException) as exc:
        worker.postConversionRoutines()

    assert "Failed to delete original file" in exc.value.msg

@pytest.fixture
def smallestLossless_patches_v2():
    def getsize_side_effect(file_path):
        size_map = {
            "png": 250_000,
            "webp": 200_000,
            "jxl": 150_000,
        }
        suffix = Path(file_path).suffix[1:]
        return size_map.get(suffix)

    def getUniqueTmpFilePath_side_effect(output_dir, key):
        size_map = {
            "png": "tmp/image.png",
            "webp": "tmp/image.webp",
            "jxl": "tmp/image.jxl",
        }
        return size_map.get(key)
    
    mocks = {
        "getsize": patch("core.worker.os.path.getsize", side_effect=getsize_side_effect),
        "getUniqueTmpFilePath": patch("core.worker.getUniqueTmpFilePath", side_effect=getUniqueTmpFilePath_side_effect),
        "getArgs": patch("core.worker.metadata.getArgs", return_value=[]),
        "copy": patch("core.worker.shutil.copy"),
        "runBinary": patch("core.worker.runBinary", return_value=("", "")),
        "remove": patch("core.worker.os.remove"),
        "os.path.isfile": patch("core.worker.os.path.isfile", return_value=True),
        "os.path.isfile": patch("core.worker.os.path.isfile", return_value=True),
        "cleanUp": patch("core.worker.cleanUp"),
    }

    with ExitStack() as stack:
        _mocks = {name: stack.enter_context(patcher) for name, patcher in mocks.items()}
        yield _mocks

@pytest.mark.parametrize("png, webp, jxl", [
    (True, True, True),
    (False, True, True),
    (False, False, True),
])
def test_smallestLossless_path_pool_filled(png, webp, jxl, smallestLossless_patches_v2, worker):
    mocks = smallestLossless_patches_v2
    worker.params["smallest_format_pool"]["png"] = png
    worker.params["smallest_format_pool"]["jxl"] = webp
    worker.params["smallest_format_pool"]["webp"] = jxl

    worker.smallestLossless()

    assert mocks["getUniqueTmpFilePath"].call_count == sum([png, webp, jxl])

def test_smallestLossless_path_pool_empty(smallestLossless_patches_v2, worker):
    worker.params["smallest_format_pool"] = {}
    with pytest.raises(GenericException) as exc:
        worker.smallestLossless()

    assert "No formats selected" in exc.value.msg

def test_smallestLossless_generate_files(smallestLossless_patches_v2, worker):
    mocks = smallestLossless_patches_v2
    worker.params["smallest_format_pool"]["png"] = True
    worker.params["smallest_format_pool"]["jxl"] = True
    worker.params["smallest_format_pool"]["webp"] = True
    
    worker.smallestLossless()

    assert mocks["copy"].called
    assert mocks["runBinary"].call_count == 3

def test_smallestLossless_generate_files_failed(smallestLossless_patches_v2, worker):
    error_txt = "sample error"

    mocks = smallestLossless_patches_v2
    mocks["os.path.isfile"].return_value = False
    mocks["runBinary"].return_value = ("", error_txt)
    worker.params["smallest_format_pool"]["webp"] = True
    worker.params["smallest_format_pool"]["png"] = False
    worker.params["smallest_format_pool"]["jxl"] = False

    with pytest.raises(FileException, match=error_txt):
        worker.smallestLossless()

    assert mocks["runBinary"].call_count == 1
    mocks["cleanUp"].assert_called_once()

@pytest.mark.parametrize("jxl_auto_lossless_jpeg", [True, False])
def test_smallestLossless_jpg_to_jxl_lossless(jxl_auto_lossless_jpeg, smallestLossless_patches_v2, worker):
    mocks = smallestLossless_patches_v2
    worker.item_ext = "jpg"
    worker.item_abs_path = "proxy/image"
    worker.org_item_abs_path = "original/image"
    worker.params["smallest_format_pool"]["png"] = False
    worker.params["smallest_format_pool"]["jxl"] = True
    worker.params["smallest_format_pool"]["webp"] = False
    worker.settings["jxl_auto_lossless_jpeg"] = jxl_auto_lossless_jpeg

    worker.smallestLossless()

    assert worker.lossless_jpeg == jxl_auto_lossless_jpeg
    assert mocks["runBinary"].call_args[0][2] == "original/image" if jxl_auto_lossless_jpeg else "proxy/image"

@pytest.mark.parametrize("png_size, webp_size, jxl_size, expected_smallest", [
    (100_000, 150_000, 150_000, "png"),
    (150_000, 100_000, 150_000, "webp"),
    (150_000, 150_000, 100_000, "jxl"),
])
def test_smallestLossless_smallest_file(png_size, webp_size, jxl_size, expected_smallest, smallestLossless_patches_v2, worker):
    worker.params["smallest_format_pool"]["png"] = True
    worker.params["smallest_format_pool"]["jxl"] = True
    worker.params["smallest_format_pool"]["webp"] = True
    mocks = smallestLossless_patches_v2
    mocks["getsize"].side_effect = lambda file_path: {
       "png": png_size,
        "webp": webp_size,
        "jxl": jxl_size, 
    }.get(getSuffix(file_path), 0)

    worker.smallestLossless()

    for args, kwargs in mocks["remove"].call_args_list:     # Remove bigger 
        assert expected_smallest not in args[0]

    # Finish
    assert worker.output_ext == expected_smallest 
    assert getSuffix(worker.output) == expected_smallest
    assert getSuffix(worker.final_output) == expected_smallest

def test_smallestLossless_getsize_failed_cleanup(smallestLossless_patches_v2, worker):
    mocks = smallestLossless_patches_v2
    mocks["getsize"].side_effect = OSError()
    with pytest.raises(FileException) as exc:
        worker.smallestLossless()

    assert "Failed to get file sizes" in exc.value.msg
    mocks["cleanUp"].assert_called_once()
    for path in ["tmp/image.png", "tmp/image.webp","tmp/image.jxl"]:
        assert path in mocks["cleanUp"].call_args_list[0][0][0]

def test_smallestLossless_getsize_failed_cleanup_failed(smallestLossless_patches_v2, worker):
    mocks = smallestLossless_patches_v2
    mocks["getsize"].side_effect = OSError()
    mocks["remove"].side_effect = OSError()
    with pytest.raises(FileException) as exc:
        worker.smallestLossless()

    mocks["cleanUp"].assert_called_once()
    for path in ["tmp/image.png", "tmp/image.webp","tmp/image.jxl"]:
        assert path in mocks["cleanUp"].call_args_list[0][0][0]

def test_smallestLossless_remove_bigger_failed(smallestLossless_patches_v2, worker):
    mocks = smallestLossless_patches_v2
    mocks["remove"].side_effect = OSError()
    with pytest.raises(FileException) as exc:
        worker.smallestLossless()

    assert "Failed to delete tmp files" in exc.value.msg
    assert "SL4" in exc.value.id
    assert mocks["remove"].call_count == 1

@pytest.mark.parametrize("jxl_auto_lossless_jpeg", [True, False])
def test_smallestLossless_args(jxl_auto_lossless_jpeg, smallestLossless_patches_v2, worker):
    mocks = smallestLossless_patches_v2
    mocks["getArgs"].return_value = ["--metadata_arg"]
    worker.settings["jxl_auto_lossless_jpeg"] = jxl_auto_lossless_jpeg
    worker.item_ext = "jpg"

    worker.smallestLossless()

    assert mocks["runBinary"].call_count == 3
    assert mocks["runBinary"].call_args_list[0][0][1] == [
        "-o 2",
        "-t 4",
        "--nb", "--nc", "--np", "--ng",
        "--fast",
        "--metadata_arg"
    ]
    assert mocks["runBinary"].call_args_list[1][0][1] == [
        "-define webp:thread-level=1",
        "-define webp:method=6",
        "-define webp:lossless=true",
        "--metadata_arg"
    ]
    assert mocks["runBinary"].call_args_list[2][0][1] == [
        "-q 100",
        "-e 7",
        "--num_threads=4",
        "--override_bitdepth=8",
        f"--lossless_jpeg={1 if jxl_auto_lossless_jpeg else 0}",
        "--metadata_arg"
    ]

@pytest.fixture
def worker_losslesslyTranscodeJPEG_patches(worker):
    variables = {
        "output": patch.object(worker, "output", "path/to/output.jxl"),
        "item_abs_path": patch.object(worker, "item_abs_path", "path/to/item_abs_path.jpeg"),
        "item_name": patch.object(worker, "item_name", "path/to/item.jpeg"),
        "output_dir": patch.object(worker, "output_dir", "path/to"),
    }

    mocks = {
        "remove": patch("core.worker.remove"),
        "QMutexLocker": patch("core.worker.QMutexLocker"),
        "getUniqueTmpFilePath": patch("core.worker.getUniqueTmpFilePath", return_value="tmp_path"),
        "transcodeJPEGtoJPEGXL": patch("core.worker.lossless_jpeg.transcodeJPEGtoJPEGXL", return_value=(True, "stdout", "stdout")),
        "normalizeJPEG": patch("core.worker.lossless_jpeg.normalizeJPEG", return_value=(True, "stdout", "stdout")),
        "verifyJPEGXLReconstructionData": patch("core.worker.lossless_jpeg.verifyJPEGXLReconstructionData", return_value=(True, "stdout", "stdout")),
    }

    with ExitStack() as stack:
        _mocks = {name: stack.enter_context(patcher) for name, patcher in mocks.items()}
        _variables = {name: stack.enter_context(patcher) for name, patcher in variables.items()}
        yield worker, _mocks, _variables

def test_losslesslyTranscodeJPEG_happy_path(worker_losslesslyTranscodeJPEG_patches):
    worker, mocks, variables = worker_losslesslyTranscodeJPEG_patches

    worker.losslesslyTranscodeJPEG()

    mocks["transcodeJPEGtoJPEGXL"].assert_called_once_with(
        variables["item_abs_path"],
        variables["output"],
        worker.params["effort"],
        worker.available_threads,
    )
    mocks["normalizeJPEG"].assert_not_called()
    mocks["verifyJPEGXLReconstructionData"].assert_not_called()
    mocks["remove"].assert_not_called()

def test_losslesslyTranscodeJPEG_transcoding_failed(worker_losslesslyTranscodeJPEG_patches):
    worker, mocks, variables = worker_losslesslyTranscodeJPEG_patches
    mocks["transcodeJPEGtoJPEGXL"].return_value = (False, "stdout", "stderr")

    with pytest.raises(FileException) as exc_info:
        worker.losslesslyTranscodeJPEG()

    assert exc_info.value.id == "lossless_jpeg_5"
    assert "Transcoding failed" in exc_info.value.msg
    assert "stderr" in exc_info.value.msg

    mocks["transcodeJPEGtoJPEGXL"].assert_called_once()
    mocks["remove"].assert_not_called()

def test_losslesslyTranscodeJPEG_verify_happy_path(worker_losslesslyTranscodeJPEG_patches):
    worker, mocks, variables = worker_losslesslyTranscodeJPEG_patches
    worker.params["jxl_verify"] = True

    worker.losslesslyTranscodeJPEG()

    mocks["transcodeJPEGtoJPEGXL"].assert_called_once_with(
        variables["item_abs_path"],
        variables["output"],
        worker.params["effort"],
        worker.available_threads,
    )
    mocks["getUniqueTmpFilePath"].assert_called_once_with(
        variables["output_dir"],
        "jpg",
    )
    mocks["verifyJPEGXLReconstructionData"].assert_called_once_with(
        variables["output"],
        variables["item_abs_path"],
        mocks["getUniqueTmpFilePath"].return_value,
        worker.available_threads,
    )
    mocks["normalizeJPEG"].assert_not_called()

def test_losslesslyTranscodeJPEG_verify_failed(worker_losslesslyTranscodeJPEG_patches):
    worker, mocks, variables = worker_losslesslyTranscodeJPEG_patches
    worker.params["jxl_verify"] = True
    mocks["verifyJPEGXLReconstructionData"].return_value = (False, "", "Checksum mismatch")

    with pytest.raises(FileException) as exc_info:
        worker.losslesslyTranscodeJPEG()
    
    assert "lossless_jpeg_0" == exc_info.value.id
    assert "Verification failed" in exc_info.value.msg
    assert "Checksum mismatch" in exc_info.value.msg
    mocks["remove"].assert_called_once_with(variables["output"], exc_id="lossless_jpeg_1")
    mocks["transcodeJPEGtoJPEGXL"].assert_called_once_with(
        variables["item_abs_path"],
        variables["output"],
        worker.params["effort"],
        worker.available_threads,
    )
    mocks["getUniqueTmpFilePath"].assert_called_once_with(variables["output_dir"], "jpg")
    mocks["verifyJPEGXLReconstructionData"].assert_called_once_with(
        variables["output"],
        variables["item_abs_path"],
        mocks["getUniqueTmpFilePath"].return_value,
        worker.available_threads,
    )
    mocks["normalizeJPEG"].assert_not_called()

def test_losslesslyTranscodeJPEG_verify_remove_tmp_failed(worker_losslesslyTranscodeJPEG_patches):
    worker, mocks, variables = worker_losslesslyTranscodeJPEG_patches
    worker.params["jxl_verify"] = True
    mocks["verifyJPEGXLReconstructionData"].return_value = (False, "", "Checksum mismatch")
    mocks["remove"].side_effect = FileException("id", "msg")

    with pytest.raises(FileException) as exc_info:
        worker.losslesslyTranscodeJPEG()
    
    mocks["remove"].assert_called_once_with(variables["output"], exc_id="lossless_jpeg_1")

def test_losslesslyTranscodeJPEG_normalize_always(worker_losslesslyTranscodeJPEG_patches):
    worker, mocks, variables = worker_losslesslyTranscodeJPEG_patches
    worker.params["jxl_normalize_enable"] = True
    worker.params["jxl_normalize_when"] = "Always"

    worker.losslesslyTranscodeJPEG()

    mocks["getUniqueTmpFilePath"].assert_called_once_with(
        variables["output_dir"],
        "jpg",
    )
    mocks["normalizeJPEG"].assert_called_once_with(
        worker.org_item_abs_path,
        mocks["getUniqueTmpFilePath"].return_value,
    )
    assert worker.item_abs_path == mocks["getUniqueTmpFilePath"].return_value
    mocks["remove"].assert_called_once_with(mocks["getUniqueTmpFilePath"].return_value, exc_id="lossless_jpeg_7")
    mocks["verifyJPEGXLReconstructionData"].assert_not_called()
    mocks["transcodeJPEGtoJPEGXL"].assert_called_once()

def test_losslesslyTranscodeJPEG_normalize_failed(worker_losslesslyTranscodeJPEG_patches):
    worker, mocks, variables = worker_losslesslyTranscodeJPEG_patches
    worker.params["jxl_normalize_enable"] = True
    worker.params["jxl_normalize_when"] = "Always"
    mocks["normalizeJPEG"].return_value = (False, "", "stderr")

    with pytest.raises(FileException) as exc_info:
        worker.losslesslyTranscodeJPEG()

    assert "lossless_jpeg_2" == exc_info.value.id
    assert "Normalizing failed" in exc_info.value.msg
    assert "stderr" in exc_info.value.msg
    mocks["getUniqueTmpFilePath"].assert_called_once()
    mocks["normalizeJPEG"].assert_called_once()
    mocks["verifyJPEGXLReconstructionData"].assert_not_called()

def test_losslesslyTranscodeJPEG_normalize_on_fail_happy_path(worker_losslesslyTranscodeJPEG_patches):
    worker, mocks, variables = worker_losslesslyTranscodeJPEG_patches
    worker.params["jxl_normalize_enable"] = True
    worker.params["jxl_normalize_when"] = "On Fail"
    mocks["transcodeJPEGtoJPEGXL"].side_effect = (
        (False, "", "stderr"),
        (True, "", ""),
    )

    worker.losslesslyTranscodeJPEG()

    assert mocks["transcodeJPEGtoJPEGXL"].call_count == 2
    mocks["normalizeJPEG"].assert_called_once()
    mocks["remove"].assert_called_once()

def test_losslesslyTranscodeJPEG_normalize_on_fail_sad_path(worker_losslesslyTranscodeJPEG_patches):
    worker, mocks, variables = worker_losslesslyTranscodeJPEG_patches
    worker.params["jxl_normalize_enable"] = True
    worker.params["jxl_normalize_when"] = "On Fail"
    mocks["transcodeJPEGtoJPEGXL"].return_value = (False, "", "stderr")

    with pytest.raises(FileException) as exc_info:
        worker.losslesslyTranscodeJPEG()

    assert exc_info.value.id == "lossless_jpeg_3"
    assert "Transcoding failed. Image may be CMYK or of other unsupported type." in exc_info.value.msg
    assert "stderr" in exc_info.value.msg
    mocks["normalizeJPEG"].assert_called_once()
    mocks["remove"].assert_called_once()
    assert mocks["transcodeJPEGtoJPEGXL"].call_count == 2
    
def test_losslesslyTranscodeJPEG_normalize_always_failed(worker_losslesslyTranscodeJPEG_patches):
    worker, mocks, variables = worker_losslesslyTranscodeJPEG_patches
    worker.params["jxl_normalize_enable"] = True
    worker.params["jxl_normalize_when"] = "Always"
    mocks["transcodeJPEGtoJPEGXL"].return_value = (False, "", "stderr")

    with pytest.raises(FileException) as exc_info:
        worker.losslesslyTranscodeJPEG()

    assert exc_info.value.id == "lossless_jpeg_4"
    assert "Transcoding failed. Image may be CMYK or of other unsupported type." in exc_info.value.msg
    assert "stderr" in exc_info.value.msg
    mocks["transcodeJPEGtoJPEGXL"].assert_called_once()
    mocks["normalizeJPEG"].assert_called_once()

@pytest.fixture
def worker_reconstructJPEG_patched(worker):
    variables = {
        "output": patch.object(worker, "output", "/tmp/output/image.jxl"),
        "org_item_abs_path": patch.object(worker, "org_item_abs_path", "/original/item/path/image.jxl"),
    }

    mocks = {
        "reconstructJPEGfromJPEGXL": patch("core.lossless_jpeg.reconstructJPEGfromJPEGXL", return_value=(True, "", "")),
    }

    with ExitStack() as stack:
        _mocks = {name: stack.enter_context(patcher) for name, patcher in mocks.items()}
        _variables = {name: stack.enter_context(patcher) for name, patcher in variables.items()}
        yield worker, _mocks, _variables

@pytest.mark.parametrize(
    "jxl_png_fallback, reconstruction_data_found, explicit_expected", [
    (True, True, True),
    (True, False, False),
    (False, True, True),
    (False, False, True),
])
def test_reconstructJPEG_happy_path(jxl_png_fallback, reconstruction_data_found, explicit_expected, worker_reconstructJPEG_patched):
    worker, mocks, variables = worker_reconstructJPEG_patched
    worker.params["jxl_png_fallback"] = jxl_png_fallback
    worker.reconstruction_data_found = reconstruction_data_found

    worker.reconstructJPEG()
    
    mocks["reconstructJPEGfromJPEGXL"].assert_called_once_with(
        variables["org_item_abs_path"],
        variables["output"],
        worker.available_threads,
        explicit=explicit_expected,
    )
    assert worker.lossless_jpeg

def test_reconstructJPEG_sad_path(worker_reconstructJPEG_patched):
    worker, mocks, variables = worker_reconstructJPEG_patched
    worker.reconstruction_data_found = True
    stdout, stderr = "stdout", "stderr"
    mocks["reconstructJPEGfromJPEGXL"].return_value = (False, stdout, stderr)

    with (
        pytest.raises(FileException) as excinfo,
    ):
        worker.reconstructJPEG()

    assert excinfo.value.id == "reconstruct_0"
    assert stderr in excinfo.value.msg
    assert "Reconstruction failed." in excinfo.value.msg
    mocks["reconstructJPEGfromJPEGXL"].assert_called_once_with(
        variables["org_item_abs_path"],
        variables["output"],
        worker.available_threads,
        explicit=True,
    )
    assert worker.lossless_jpeg

def test_runDynamicRamOptimizer_enabled(worker):
    org_available_threads = 4
    new_available_threads = 5
    worker.available_threads = org_available_threads

    with (
        patch("core.worker.RAMOptimizer.isEnabled", return_value=True),
        patch("core.worker.RAMOptimizer.run", return_value=new_available_threads) as mock_run,
    ):
        worker.runDynamicRamOptimizer()
        mock_run.assert_called_once_with(
            org_available_threads,
            worker.org_item_abs_path,
            worker.params["format"],
            worker.settings["avif_encoder"],
            worker.params["effort"],
            worker.params["jxl_modular"],
            worker.params["lossless"],
            worker.params["intelligent_effort"],
        )
        assert worker.available_threads == new_available_threads

def test_runDynamicRamOptimizer_disabled(worker):
    with (
        patch("core.worker.RAMOptimizer.isEnabled", return_value=False),
        patch("core.worker.RAMOptimizer.run") as mock_run,
    ):
        worker.runDynamicRamOptimizer()
        mock_run.assert_not_called()

def test_PNGOptimization_happy_path(worker):
    level = 4
    available_threads = 3
    worker.params["effort"] = level
    worker.available_threads = 3
    worker.params["misc"]["keep_metadata"] = "Encoder - Wipe"
    worker.output = "/tmp/out.png"

    with (
        patch("core.worker.runOxipng", return_value=("", "")) as mock_runOxipng,
        patch("core.worker.os.path.isfile", return_value=True),
    ):
        worker.PNGOptimization()
        mock_runOxipng.assert_called_once_with(
            [
                f"-o {level}",
                f"-t {available_threads}",
                "--fast",
                "--np", "--nb", "--nc", "--ng",
                "--strip", "safe",
            ],
            worker.item_abs_path,
            worker.output,
        )

def test_PNGOptimization_sad_path(worker):
    level = 4
    available_threads = 3
    stderr = "error"
    worker.params["effort"] = level

    with (
        patch("core.worker.runOxipng", return_value=("", stderr)) as mock_runOxipng,
        patch("core.worker.os.path.isfile", return_value=False),
        pytest.raises(FileException) as exc_info,
    ):
        worker.PNGOptimization()

    mock_runOxipng.assert_called_once()
    assert exc_info.value.id == "png_opt_0"
    assert exc_info.value.msg == f"Optimization failed. {stderr}"
