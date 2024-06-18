from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtCore import QMutex

from core.proxy import Proxy
from core.exceptions import FileException

@pytest.fixture
def proxy():
    return Proxy()

def test_isProxyNeeded_png(proxy):
    assert proxy.isProxyNeeded("PNG", "png") == False

@pytest.mark.parametrize("file_format,src_ext,expected", [
    ("JPEG XL", "png", False),
    ("JPEG XL", "avif", True),
    ("AVIF", "png", False),
    ("AVIF", "jxl", True),
    ("WebP", "png", False),
    ("WebP", "exr", True),
    ("Smallest Lossless", "png", True),
])
def test_test_isProxyNeeded_base(proxy, file_format, src_ext, expected):
    assert proxy.isProxyNeeded(file_format, src_ext) == expected

def test_test_isProxyNeeded_jpegli(proxy):
    assert not proxy.isProxyNeeded("JPEG", "jpg", jpegli=True)

def test_test_isProxyNeeded_unknown(proxy):
    assert proxy.isProxyNeeded("JPEG XL", "exr")

def test_isProxyNeeded_downscaling(proxy):
    assert proxy.isProxyNeeded("JPEG XL", "exr", downscaling_enabled=True)
    assert not proxy.isProxyNeeded("JPEG XL", "png", downscaling_enabled=True)

@pytest.fixture
def generate_patches():
    with (
        patch("core.proxy.os.path.isfile", return_value=True) as mock_isfile,
        patch("core.proxy.convert") as mock_convert,
        patch("core.proxy.getUniqueFilePath", return_value="/proxy/dst/proxy.png") as mock_getUniqueFilePath,
    ):
        yield mock_isfile, mock_convert, mock_getUniqueFilePath

def test_generate_proxy_success(generate_patches, proxy):
    proxy.generate("/path/to/src.avif", "avif", "/proxy/dst", "src", 0, QMutex())
    assert proxy.proxy_path == "/proxy/dst/proxy.png"

def test_generate_proxy_failure(generate_patches, proxy):
    mock_isfile, *_ = generate_patches
    mock_isfile.return_value = False

    with pytest.raises(FileException):
        proxy.generate("/path/to/src.avif", "avif", "/proxy/dst", "src", 0, QMutex())

def test_getPath_empty(proxy):
    assert not proxy.proxyExists()

def test_getPath(proxy):
    proxy.proxy_path = "/proxy/path/proxy.png"
    assert proxy.getPath() == "/proxy/path/proxy.png"

def test_proxyExists_empty(proxy):
    assert not proxy.proxyExists()

def test_proxyExists(proxy):
    proxy.proxy_path = "/proxy/path/proxy.png"
    assert proxy.proxyExists()

def test_cleanup(proxy):
    proxy.proxy_path = "/proxy/path/proxy.png"
    with patch("core.proxy.os.remove") as mock_remove:
        proxy.cleanup()
        mock_remove.assert_called_once_with("/proxy/path/proxy.png")
        assert proxy.proxy_path is None