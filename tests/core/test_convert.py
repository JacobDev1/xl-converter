from unittest.mock import patch

import pytest

import core.convert as convert
from core.exceptions import GenericException
from data.constants import AVIFENC_PATH, IMAGE_MAGICK_PATH, DJXL_PATH, AVIFDEC_PATH, ALLOWED_INPUT_IMAGE_MAGICK

def test_convert_avifenc():
    with patch("core.convert.runProcess") as mock_runProcess:
        convert.convert(AVIFENC_PATH, "src.png", "dst.avif", ["-q", "50"])
        mock_runProcess.assert_called_once_with(AVIFENC_PATH, "-q", "50", "src.png", "dst.avif")

def test_convert_other():
    with patch("core.convert.runProcess") as mock_runProcess:
        convert.convert("encoder_path", "src.png", "dst.avif", ["-q", "50"])
        mock_runProcess.assert_called_once_with("encoder_path", "src.png","-q", "50", "dst.avif")

def test_optimize():
    with patch("core.convert.runProcess") as mock_runProcess:
        convert.optimize("path/to/optimizer", "target.png", ["-o 4"])
        mock_runProcess.assert_called_once_with("path/to/optimizer", "-o", "4", "target.png")

def test_getExtensionJxl_jpg():
    with patch("core.convert.runProcessOutput", return_value=("JPEG bitstream reconstruction data available", "")):
        assert convert.getExtensionJxl("src.jxl") == "jpg"

def test_getExtensionJxl_png():
    with patch("core.convert.runProcessOutput", return_value=("", "")):
        assert convert.getExtensionJxl("src.jxl") == "png"

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

def test_log():
    with patch("logging.info") as mock_logging:
        convert.log("test")
        mock_logging.assert_called_once_with("[Convert] test")

def test_log_worker():
    with patch("logging.info") as mock_logging:
        convert.log("test", 3)
        mock_logging.assert_called_once_with("[Worker #3 - Convert] test")