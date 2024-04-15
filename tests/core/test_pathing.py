from unittest.mock import patch

import pytest
from pathlib import Path

from core.pathing import (
    getUniqueFilePath,
    getPathGIF,
    getExtension,
    getOutputDir,
    isANSICompatible,
)

@pytest.mark.parametrize("file_name, file_ext, output_dir, add_random, isfile_side_effect, expected_path", [
    # Base
    ("image", "jxl", Path("/home/user/images"), False, [False], Path("/home/user/images/image.jxl")),
    ("image", "jxl", Path("/home/user/images"), False, [True, False], Path("/home/user/images/image (1).jxl")),
    ("image", "jxl", Path("/home/user/images"), False, [True, True, False], Path("/home/user/images/image (2).jxl")),
    ("image (10)", "jxl", Path("/home/user/images"), False, [False], Path("/home/user/images/image (10).jxl")),
    ("image (10)", "jxl", Path("/home/user/images"), False, [True, True, False], Path("/home/user/images/image (11).jxl")), # Needs two passes
    
    # Add Random
    ("image", "jxl", Path("/home/user/images"), True, [False], Path("/home/user/images/image_abc.jxl")),
    ("image", "jxl", Path("/home/user/images"), True, [True, False], Path("/home/user/images/image (1)_abc.jxl")),
    ("image (3)", "jxl", Path("/home/user/images"), True, [True, True, False], Path("/home/user/images/image (4)_abc.jxl")),
])
def test_getUniqueFilePath(file_name, file_ext, output_dir, add_random, isfile_side_effect, expected_path):
    with patch("os.path.isfile", side_effect=isfile_side_effect), \
        patch("random.choice", side_effect=["a", "b", "c"]):
        
        assert getUniqueFilePath(str(output_dir), file_name, file_ext, add_random) == str(expected_path)

@pytest.mark.parametrize("output_dir, item_name, duplicates, isfile_side_effect, expected_path", [
    (Path("user/images"), "animated", "Rename", [False], Path("user/images/animated.png")),
    (Path("user/images"), "animated", "Rename", [True, False], Path("user/images/animated (1).png")),
    (Path("user/images"), "animated", "Replace", [True], Path("user/images/animated.png")),
])
def test_getPathGIF(output_dir, item_name, duplicates, isfile_side_effect, expected_path):
    with patch("os.path.isfile", side_effect=isfile_side_effect):
        assert getPathGIF(str(output_dir), item_name, duplicates) == str(expected_path)

@pytest.mark.parametrize("file_format, extension", [
    ("JPEG XL", "jxl"),
    ("AVIF", "avif"),
    ("WEBP", "webp"),
    ("JPG", "jpg"),
    ("PNG", "png"),
    ("Smallest Lossless", None),
    ("FLIF", None),
])
def test_getExtension(file_format, extension):
    assert getExtension(file_format) == extension

@pytest.mark.parametrize(
    "item_dir_path,item_anchor_path,custom_dir,custom_dir_path,keep_dir_struct,expected",
    [
        (Path("/home/user/Pictures"), Path("/home/user"), False, Path("/home/user/Files"), False, Path("/home/user/Pictures")),    # src
        (Path("/home/user/Pictures"), Path("/home/user"), True, "Images", False, Path("/home/user/Pictures/Images")),        # rel.
        (Path("/home/user/Pictures"), Path("/home/user"), True, Path("/home/user/Files"), False, Path("/home/user/Files")),        # abs.
        (Path("/home/user/Pictures"), Path("/home/user/Pictures"), False, "", False, Path("/home/user/Pictures")),  # rel.
        (Path("/home/user/Pictures"), Path("/home/user"), True, Path("/home/user/Files"), True, Path("/home/user/Files/Pictures")),        # keep_dir_struct parent
        (Path("/home/user/Pictures/screenshots"), Path("/home/user/Pictures"), True, Path("/home/user/Files"), True, Path("/home/user/Files/screenshots")),        # keep_dir_struct subfolder
    ]
)

def test_getOutputDir(item_dir_path, item_anchor_path, custom_dir, custom_dir_path, keep_dir_struct, expected):
    assert getOutputDir(str(item_dir_path), item_anchor_path, custom_dir, str(custom_dir_path), keep_dir_struct) == str(expected)

@pytest.mark.parametrize(
    "item_dir_path,item_anchor_path,custom_dir,custom_dir_path,keep_dir_struct", [
        ("/home/user/Pictures", Path("/home/different_user/Pictures"), True, "/home/user/Files", True)
    ]
)

def test_getOutputDir_exception(item_dir_path, item_anchor_path, custom_dir, custom_dir_path, keep_dir_struct, caplog):
    getOutputDir(item_dir_path, item_anchor_path, custom_dir, custom_dir_path, keep_dir_struct)
    assert "[Pathing] Failed to calculate relative path." in caplog.text

def test_isANSICompatible_compatible():
    assert isANSICompatible("C:\\Users\\User\\Pictures")

def test_isANSICompatible_not_compatible():
    assert not isANSICompatible("D:\\画像")