from unittest.mock import patch

import pytest

from core.metadata import (
    _runExifTool,
    runExifTool,
    copyMetadata,
    deleteMetadata,
    deleteMetadataUnsafe,
    runExifTool,
    getArgs,
)
from data.constants import (
    EXIFTOOL_BIN_NAME,
    EXIFTOOL_FOLDER_PATH,
    EXIFTOOL_PATH,
)

def test_copyMetadata():
    with patch("core.metadata._runExifTool") as mock__runExifTool:
        copyMetadata("source.png", "target.jpg")
        mock__runExifTool.assert_called_with("-tagsfromfile", "source.png", "-overwrite_original", "target.jpg")

def test_deleteMetadata():
    with patch("core.metadata._runExifTool") as mock__runExifTool:
        deleteMetadata("target.jpg")
        mock__runExifTool.assert_called_with("-all=", "-tagsFromFile", "@", "--icc_profile:all", "--ColorSpace:all", "-overwrite_original", "target.jpg")

def test_deleteMetadataUnsafe():
    with patch("core.metadata._runExifTool") as mock__runExifTool:
        deleteMetadataUnsafe("target.jpg")
        mock__runExifTool.assert_called_with("-all=", "-overwrite_original", "target.jpg")

@pytest.mark.parametrize("mode,expected_call", [
    ("ExifTool - Wipe", "deleteMetadata"),
    ("ExifTool - Preserve", "copyMetadata"),
    ("ExifTool - Unsafe Wipe", "deleteMetadataUnsafe"),
])

def test_runExifTool(mode, expected_call):
    with patch(f"core.metadata.{expected_call}") as mock_method:
        runExifTool("source.png", "target.jpg", mode)
        if "copyMetadata" in expected_call:
            mock_method.assert_called_once_with("source.png", "target.jpg")
        else:
            mock_method.assert_called_once_with("target.jpg")

@pytest.mark.parametrize("system,expected_call,expected_cwd", [
    ("Windows", (EXIFTOOL_PATH), None),
    ("Linux", ("./" + EXIFTOOL_BIN_NAME), EXIFTOOL_FOLDER_PATH),
])

def test__runExifTool(system, expected_call, expected_cwd):
    with patch("core.metadata.platform.system", return_value=system), \
        patch("core.metadata.runProcess") as mock_runProcess:
        copyMetadata("src.png", "dst.jpg")

        if expected_cwd:
            mock_runProcess.assert_called_with(expected_call, "-tagsfromfile", "src.png", "-overwrite_original", "dst.jpg", cwd=expected_cwd)
        else:
            mock_runProcess.assert_called_with(expected_call, "-tagsfromfile", "src.png", "-overwrite_original", "dst.jpg")