from unittest.mock import patch
import sys
from importlib import reload
import platform

import pytest

import data.constants as constants

@pytest.mark.parametrize("mock_os", ["Windows", "Linux"])
def test_vars_filled(mock_os):
    assert constants.VERSION != ""
    assert constants.VERSION_FILE_URL != ""

    assert constants.PROGRAM_FOLDER != ""
    assert constants.ICON_SVG != ""
    assert constants.LICENSE_PATH != ""
    assert constants.LICENSE_3RD_PARTY_PATH != ""

    with patch("data.constants.platform.system", return_value=mock_os):
        reload(constants)
        assert constants.CONFIG_LOCATION != ""

        assert constants.CJXL_PATH != "" and constants.CJXL_PATH != "cjxl"
        assert constants.DJXL_PATH != "" and constants.DJXL_PATH != "djxl"
        assert constants.JXLINFO_PATH != "" and constants.JXLINFO_PATH != "jxlinfo"
        assert constants.CJPEGLI_PATH != "" and constants.CJPEGLI_PATH != "cjpegli"
        assert constants.IMAGE_MAGICK_PATH != "" and constants.IMAGE_MAGICK_PATH != "magick"
        assert constants.AVIFENC_PATH != "" and constants.AVIFENC_PATH != "avifenc"
        assert constants.AVIFDEC_PATH != "" and constants.AVIFDEC_PATH != "avifdec"
        assert constants.OXIPNG_PATH != "" and constants.OXIPNG_PATH != "oxipng"
        
        if platform.system() == "Windows":
            assert constants.EXIFTOOL_PATH != "" and constants.EXIFTOOL_PATH != "exiftool"
    
    assert len(constants.ALLOWED_INPUT) > 0

def test_program_folder_frozen():
    with patch.object(sys, "frozen", True, create=True), \
         patch.object(sys, "_MEIPASS", "/tmp/frozen", create=True):
        reload(constants)       # Reload and apply patches
        assert constants.PROGRAM_FOLDER == "/tmp/frozen"

def test_program_folder_not_frozen():
    with patch.object(sys, "frozen", False, create=True), \
         patch("os.path.realpath", return_value="/path/to/program/data/constants.py"):
        reload(constants)
        assert constants.PROGRAM_FOLDER == "/path/to/program"