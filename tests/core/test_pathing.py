import time
from unittest.mock import patch
from pathlib import Path
import threading
import stat
from contextlib import ExitStack

import pytest

import core.pathing as pathing
from core.exceptions import GenericException

@pytest.fixture
def UniquePathStore():
    yield pathing.UniquePathStore
    pathing.UniquePathStore.clear()

def test_UniquePathStore_init(UniquePathStore):
    assert UniquePathStore._lock.locked() == False
    assert UniquePathStore._paths == set()

def test_UniquePathStore_add_and_exists(UniquePathStore):
    test_path = "/tmp/test/path.jpg"
    assert not UniquePathStore.exists(test_path)
    UniquePathStore.add(test_path)
    assert UniquePathStore.exists(test_path)

def test_UniquePathStore_clear(UniquePathStore):
    test_path = "/tmp/test/path.jpg"
    UniquePathStore.add(test_path)
    UniquePathStore.clear()
    assert UniquePathStore._paths == set()

def test_UniquePathStore_concurrency(UniquePathStore):
    paths = [f"/tmp/test/image ({i}).jpg" for i in range(100)]

    def addPaths():
        for path in paths:
            UniquePathStore.add(path)
            time.sleep(0.0001)
    
    def checkPaths():
        for path in paths:
            UniquePathStore.exists(path)
            time.sleep(0.0001)
    
    threads = []
    for _ in range(6):
        threads.append(threading.Thread(target=addPaths))
        threads.append(threading.Thread(target=checkPaths))

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()
    
    assert len(UniquePathStore._paths) == len(paths)
    for path in paths:
        assert UniquePathStore.exists(path)

def test_UniquePathStore_mutex_release(UniquePathStore):
    test_path = "/tmp/test/path.jpg"

    UniquePathStore.add(test_path)
    assert not UniquePathStore._lock.locked()
    
    UniquePathStore.exists(test_path)
    assert not UniquePathStore._lock.locked()
    
    UniquePathStore.clear()
    assert not UniquePathStore._lock.locked()

@pytest.mark.parametrize("file_name, file_ext, output_dir, isfile_side_effect, exists_side_effect, expected_path", [
    # Base
    ("image", "jxl", Path("/home/user/images"), [False], [False], Path("/home/user/images/image.jxl")),
    ("image", "jxl", Path("/home/user/images"), [True, False], [False], Path("/home/user/images/image (1).jxl")),
    ("image", "jxl", Path("/home/user/images"), [True, True, False], [False], Path("/home/user/images/image (2).jxl")),
    ("image (10)", "jxl", Path("/home/user/images"), [False], [False], Path("/home/user/images/image (10).jxl")),
    ("image (10)", "jxl", Path("/home/user/images"), [True, True, False], [False], Path("/home/user/images/image (11).jxl")),  # Needs one more pass to acknowledge parenthesis
    
    # UniquePathStore
    ("image (10)", "jxl", Path("/home/user/images"), [False, False], [True, False], Path("/home/user/images/image (10).jxl")),
    ("image (10)", "jxl", Path("/home/user/images"), [False, False, False], [True, True, False], Path("/home/user/images/image (11).jxl")),
    ("image (10)", "jxl", Path("/home/user/images"), [True, True, False, False], [True, False], Path("/home/user/images/image (12).jxl")),
])
def test_getUniqueFilePath(file_name, file_ext, output_dir, isfile_side_effect, exists_side_effect, expected_path):
    with (
        patch("os.path.isfile", side_effect=isfile_side_effect),
        patch("core.pathing.UniquePathStore.exists", side_effect=exists_side_effect),
    ):
        assert pathing.getUniqueFilePath(str(output_dir), file_name, file_ext) == str(expected_path)

def test_getUniqueTmpFilePath_happy_path():
    with (
        patch("core.pathing.os.path.isfile", return_value=False),
        patch("core.pathing.UniquePathStore.exists", return_value=False),
        patch("core.pathing.secrets.token_hex", return_value="abcdef12"),
    ):
        assert pathing.getUniqueTmpFilePath(str(Path("/tmp")), "jpg") == str(Path("/tmp", f"tmp_abcdef12.jpg"))

def test_getUniqueTmpFilePath_isfile_true():
    with (
        patch("core.pathing.os.path.isfile", side_effect=[True, False]),
        patch("core.pathing.UniquePathStore.exists", return_value=False),
        patch("core.pathing.secrets.token_hex", side_effect=["1"*8, "2"*8]),
    ):
        assert pathing.getUniqueTmpFilePath(str(Path("/tmp")), "jpg") == str(Path("/tmp", f"tmp_{'2'*8}.jpg"))

def test_getUniqueTmpFilePath_path_store_exists():
    with (
        patch("core.pathing.os.path.isfile", return_value=False),
        patch("core.pathing.UniquePathStore.exists", side_effect=[True, False]),
        patch("core.pathing.secrets.token_hex", side_effect=["1"*8, "2"*8]),
    ):
        assert pathing.getUniqueTmpFilePath(str(Path("/tmp")), "jpg") == str(Path("/tmp", f"tmp_{'2'*8}.jpg"))

def test_getUniqueTmpFilePath_path_store_exists_and_isfile_true():
    with (
        patch("core.pathing.os.path.isfile", side_effect=[True, False, False]),
        patch("core.pathing.UniquePathStore.exists", side_effect=[True, False]),
        patch("core.pathing.secrets.token_hex", side_effect=["1"*8, "2"*8, "3"*8]),
    ):
        assert pathing.getUniqueTmpFilePath(str(Path("/tmp")), "jpg") == str(Path("/tmp", f"tmp_{'3'*8}.jpg"))

@pytest.mark.parametrize("file_format, extension", [
    ("JPEG XL", "jxl"),
    ("AVIF", "avif"),
    ("WebP", "webp"),
    ("JPEG", "jpg"),
    ("PNG", "png"),
    ("Smallest Lossless", None),
])
def test_getExtension(file_format, extension):
    assert pathing.getExtension(file_format) == extension

def test_getExtension_exception():
    with pytest.raises(GenericException) as exc:
        pathing.getExtension("FLIF")
    assert "No extension declared" in exc.value.msg

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
    assert pathing.getOutputDir(str(item_dir_path), item_anchor_path, custom_dir, str(custom_dir_path), keep_dir_struct) == str(expected)

@pytest.mark.parametrize(
    "item_dir_path,item_anchor_path,custom_dir,custom_dir_path,keep_dir_struct", [
        ("/home/user/Pictures", Path("/home/different_user/Pictures"), True, "/home/user/Files", True)
    ]
)
def test_getOutputDir_exception(item_dir_path, item_anchor_path, custom_dir, custom_dir_path, keep_dir_struct, caplog):
    pathing.getOutputDir(item_dir_path, item_anchor_path, custom_dir, custom_dir_path, keep_dir_struct)
    assert "[Pathing] Failed to calculate relative path." in caplog.text

def test_isANSICompatible_compatible():
    assert pathing.isANSICompatible("C:\\Users\\User\\Pictures")

def test_isANSICompatible_not_compatible():
    assert not pathing.isANSICompatible("D:\\画像")

@pytest.fixture
def removeFile_patches():
    mocks = {
        "remove": patch("core.pathing.os.remove"),
        "isfile": patch("core.pathing.os.path.isfile", return_value=True),
        "chmod": patch("core.pathing.os.chmod"),
        "system": patch("core.pathing.platform.system", return_value="Windows"),
    }

    with ExitStack() as stack:
        _mocks = { name: stack.enter_context(patcher) for name, patcher in mocks.items() }
        yield _mocks

def test_removeFile_happy_path(removeFile_patches):
    pathing.removeFile("/tmp/sample_file.jpg")
    removeFile_patches["remove"].assert_called_once_with("/tmp/sample_file.jpg")

def test_removeFile_sad_path(removeFile_patches):
    removeFile_patches["remove"].side_effect = OSError
    with pytest.raises(OSError):
        pathing.removeFile("/tmp/sample_file.jpg")
    removeFile_patches["remove"].assert_called_once_with("/tmp/sample_file.jpg")

def test_removeFile_re_raise_permission_exc(removeFile_patches):
    removeFile_patches["remove"].side_effect = PermissionError
    removeFile_patches["system"].return_value = "Linux"

    with pytest.raises(PermissionError):
        pathing.removeFile("/tmp/sample_file.jpg")

    removeFile_patches["remove"].assert_called_once_with("/tmp/sample_file.jpg")
    removeFile_patches["chmod"].assert_not_called()

def test_removeFile_clear_read_only_win(removeFile_patches):
    removeFile_patches["remove"].side_effect = [PermissionError, None]
    removeFile_patches["system"].return_value = "Windows"

    pathing.removeFile("/tmp/sample_file.jpg")
    assert removeFile_patches["remove"].call_count == 2
    for i in range(2):
        assert removeFile_patches["remove"].call_args_list[i][0][0] == "/tmp/sample_file.jpg"
    removeFile_patches["chmod"].assert_called_once_with("/tmp/sample_file.jpg", stat.S_IWRITE)

def test_removeFile_ignore_missing_true(removeFile_patches):
    removeFile_patches["isfile"].return_value = False
    pathing.removeFile("/tmp/sample_file.jpg", ignore_missing=True)
    removeFile_patches["remove"].assert_not_called()

def test_removeFile_ignore_missing_false(removeFile_patches):
    removeFile_patches["remove"].side_effect = [FileNotFoundError, None]
    removeFile_patches["isfile"].return_value = False

    with pytest.raises(FileNotFoundError):
        pathing.removeFile("/tmp/sample_file.jpg", ignore_missing=False)

    removeFile_patches["remove"].assert_called_once_with("/tmp/sample_file.jpg")
