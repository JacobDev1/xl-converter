from unittest.mock import MagicMock, patch
from contextlib import ExitStack
import logging

import pytest
from PySide6.QtCore import QMutex

from core.proxy import Proxy
from core.exceptions import FileException, CancellationException

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
    ("PNG Optimization", "png", False),
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
def proxy_generate_patched(proxy):
    patches = {
        "isfile": patch("core.proxy.os.path.isfile", return_value=True),
        "runBinary": patch("core.proxy.runBinary", return_value=("", "")),
        "getUniqueTmpFilePath": patch("core.proxy.getUniqueTmpFilePath", return_value="/proxy/dst/proxy.png"),
        "getDecoder": patch("core.proxy.getDecoder"),
    }

    with ExitStack() as stack:
        mocks = {name: stack.enter_context(patcher) for name, patcher in patches.items()}
        yield proxy, mocks

def test_generate_proxy_success(proxy_generate_patched):
    proxy, mocks = proxy_generate_patched
    src, src_ext, dst_dir, file_name = "/path/to/src.avif", "avif", "/proxy/dst", "src"
    proxy_path = "/proxy/dst/proxy.png"
    mocks["getUniqueTmpFilePath"].return_value = proxy_path

    proxy.generate(src, src_ext, dst_dir, file_name, 0, QMutex())

    assert proxy.proxy_path == proxy_path
    mocks["runBinary"].assert_called_once_with(
        mocks["getDecoder"].return_value,
        [],
        src,
        proxy_path,
        delete_if_canceled=[proxy_path],
    )
    mocks["isfile"].assert_called_once_with(proxy_path)

def test_generate_proxy_canceled(proxy_generate_patched):
    proxy, mocks = proxy_generate_patched
    mocks["runBinary"].side_effect = CancellationException()

    with pytest.raises(CancellationException) as excinfo:
        proxy.generate("/path/to/src.avif", "avif", "/proxy/dst", "src", 0, QMutex())

def test_generate_proxy_failure(proxy_generate_patched):
    proxy, mocks = proxy_generate_patched
    stderr = "stderr"
    mocks["isfile"].return_value = False
    mocks["runBinary"].return_value = ("", stderr)

    with pytest.raises(FileException) as excinfo:
        proxy.generate("/path/to/src.avif", "avif", "/proxy/dst", "src", 0, QMutex())
        
    assert excinfo.value.id == "Proxy1"
    assert "Generating proxy failed." in excinfo.value.msg
    assert stderr in excinfo.value.msg

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

def test_cleanUp_no_proxy(proxy):
    assert proxy.proxy_path is None
    with (
        patch("core.proxy.os.remove") as mock_remove,
        patch("core.proxy.os.path.isfile", return_value=True),
    ):
        proxy.cleanUp()
        mock_remove.assert_not_called()

def test_cleanUp_happy_path(proxy):
    proxy_file = "/proxy/path/proxy.png"
    proxy.proxy_path = proxy_file
    with (
        patch("core.proxy.os.remove") as mock_remove,
        patch("core.proxy.os.path.isfile", return_value=True),
    ):
        proxy.cleanUp(raising=True)
        mock_remove.assert_called_once_with(proxy_file)
        assert proxy.proxy_path is None

def test_cleanUp_sad_path_raising(proxy):
    proxy_file = "/proxy/path/proxy.png"
    proxy.proxy_path = proxy_file
    with (
        patch("core.proxy.os.remove", side_effect=OSError) as mock_remove,
        patch("core.proxy.os.path.isfile", return_value=True),
        pytest.raises(FileException),
    ):
        proxy.cleanUp(raising=True)
    mock_remove.assert_called_once_with(proxy_file)
    assert proxy.proxy_path is None

def test_cleanUp_sad_path_not_raising(proxy, caplog):
    proxy_file = "/proxy/path/proxy.png"
    proxy.proxy_path = proxy_file
    with (
        patch("core.proxy.os.remove", side_effect=OSError) as mock_remove,
        patch("core.proxy.os.path.isfile", return_value=True),
        caplog.at_level(logging.ERROR)
    ):
        proxy.cleanUp(raising=False)
        mock_remove.assert_called_once_with(proxy_file)
        assert proxy.proxy_path is None
        assert "Failed to clean up proxy" in caplog.text

def test_cleanUp_no_file(proxy, caplog):
    proxy_file = "/proxy/path/proxy.png"
    proxy.proxy_path = proxy_file
    with (
        patch("core.proxy.os.remove", side_effect=OSError) as mock_remove,
        patch("core.proxy.os.path.isfile", return_value=False),
    ):
        proxy.cleanUp(raising=True)
        mock_remove.assert_not_called()
