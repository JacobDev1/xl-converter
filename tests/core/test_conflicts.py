from unittest.mock import patch
from contextlib import ExitStack

import pytest

import core.conflicts as conflicts
from core.exceptions import GenericException, FileException

@pytest.mark.parametrize("src_ext", [
    "jpg", "png", "jxl", "avif",
])
def test_checkForConflicts_no_conflict(src_ext):
    conflicts.checkForConflicts(src_ext, "/tmp/image.jpg", "JPEG XL", False)  # Expecting no exception raised

@pytest.mark.parametrize("src_ext, target_format", [
    ("gif", "JPEG XL"),
    ("gif", "WebP"),
    ("apng", "JPEG XL"),
])
def test_checkForConflicts_supported(src_ext, target_format):
    conflicts.checkForConflicts(src_ext, "/tmp/image.jpg", target_format, False)

@pytest.mark.parametrize("src_ext, target_format", [
    ("gif", "JPEG"),
    ("gif", "PNG"),
    ("gif", "AVIF"),
    ("apng", "WebP"),
])
def test_checkForConflicts_unsupported(src_ext, target_format):
    with pytest.raises(GenericException) as exc_info:
        conflicts.checkForConflicts(src_ext, "/tmp/image.jpg", target_format, False)

    assert f"Transcoding {src_ext.upper()} -> {target_format} is not supported" == exc_info.value.msg

def test_checkForConflicts_downscaling():
    with pytest.raises(GenericException) as exc_info:
        conflicts.checkForConflicts("gif", "/tmp/image.jpg", "JPEG XL", True)
    
    assert "Downscaling is not supported for animation" == exc_info.value.msg

@pytest.fixture
def checkForConflicts_patches():
    mocks = {
        "getImageCount": patch("core.conflicts.getImageCount", return_value=(1, ""))
    }

    with ExitStack() as stack:
        _mocks = { name: stack.enter_context(patcher) for name, patcher in mocks.items() }
        yield _mocks

@pytest.mark.parametrize("src_ext", [
    "tif", "tiff", "webp"
])
def test_checkForConflicts_no_conflict(src_ext, checkForConflicts_patches):
    mocks = checkForConflicts_patches
    src_image_path = "/tmp/image.jpg"

    conflicts.checkForConflicts(src_ext, src_image_path, "JPEG XL", False)
    mocks["getImageCount"].assert_called_once_with(src_image_path)

def test_checkForConflicts_cannot_detect_page_count(checkForConflicts_patches):
    mocks = checkForConflicts_patches
    stderr = "Error"
    mocks["getImageCount"].return_value = (-1, stderr)

    with (
        pytest.raises(FileException) as exc_info,
    ):
        conflicts.checkForConflicts("tiff", "path/to/src.tiff", "JPEG XL", False)
    
    assert "CF2" == exc_info.value.id
    assert "Cannot detect image's page count." in exc_info.value.msg
    assert stderr in exc_info.value.msg

def test_checkForConflicts_multipage(checkForConflicts_patches):
    mocks = checkForConflicts_patches
    stderr = "Error"
    mocks["getImageCount"].return_value = (2, stderr)

    with (
        pytest.raises(GenericException) as exc_info,
    ):
        conflicts.checkForConflicts("tiff", "path/to/src.tiff", "JPEG XL", False)
    
    assert "CF3" == exc_info.value.id
    assert "Multipage images are not supported" in exc_info.value.msg

def test_checkForConflicts_animated_webp_source(checkForConflicts_patches):
    mocks = checkForConflicts_patches
    stderr = "Error"
    mocks["getImageCount"].return_value = (2, stderr)

    with (
        pytest.raises(GenericException) as exc_info,
    ):
        conflicts.checkForConflicts("webp", "path/to/src.tiff", "JPEG XL", False)
    
    assert "CF3" == exc_info.value.id
    assert "Animated WebP is not supported as input" in exc_info.value.msg
