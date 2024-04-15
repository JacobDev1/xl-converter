from pathlib import Path
import os

import pytest

from core.utils import (
    scanDir,
    removeDuplicates,
    listToFilter,
    dictToList,
    clip,
)

@pytest.fixture
def tmp_dir(tmp_path):
    """Creates nested dir with files."""
    d = tmp_path / "dir"
    d.mkdir()
    (d / "test_file.txt").write_text("test")
    (d / "nested").mkdir()
    (d / "nested" / "test_file_2.txt").write_text("test")
    return tmp_path

def test_scanDir_empty(tmp_path):
    assert scanDir(tmp_path) == []

def test_scanDir_files(tmp_dir):
    files = scanDir(tmp_dir)
    assert len(files) == 2
    assert all(os.path.isfile(file) for file in files)
    assert any("test_file.txt" in file for file in files)
    assert any("test_file_2.txt" in file for file in files)

def test_scanDir_non_existent():
    with pytest.raises(FileNotFoundError):
        scanDir("non_existent_dir")

def test_removeDuplicates_empty():
    assert removeDuplicates([]) == []

def test_removeDuplicates_no_duplicates():
    assert removeDuplicates([1, 2, 3]) == [1, 2, 3]

def test_removeDuplicates_with_duplicates():
    assert removeDuplicates([1, 1, 2]) == [1, 2]

def test_removeDuplicates_all_duplicates():
    assert removeDuplicates([1, 1, 1]) == [1]

def test_removeDuplicates_mixed_types():
    assert removeDuplicates([1, "a", 2, "a", 1]) == [1, "a", 2]

def test_removeDuplicates_nested():
    assert removeDuplicates([[1, 2], [1, 2], [3]]) == [[1, 2], [3]]

def test_removeDuplicates_strings():
    assert removeDuplicates(["a", "a", "b"]) == ["a", "b"]

def test_listToFilter_empty():
    assert listToFilter(
        "Images",
        []
    ) == "All Files (*)"

def test_listToFilter_single_ext():
    assert listToFilter(
        "Image",
        ["jpg"]
    ) == "Image (*.jpg)"

def test_listToFilter_multiple_ext():
    assert listToFilter(
        "Images",
        ["jpg", "png", "webp", "jxl", "avif"]
    ) == "Images (*.jpg *.png *.webp *.jxl *.avif)"

def test_dictToList_empty():
    assert dictToList({}) == []

def test_dictToList_flat():
    assert dictToList({
        "a": 0,
        "b": 1,
    }) == [
        ("a", 0),
        ("b", 1),
    ]

def test_dictToList_nested():
    assert dictToList({
        "a": 0,
        "b": {
            "c": 2,
            "d": 3,
        },
    }) == [
        ("a", 0),
        ("b", [
            ("c", 2),
            ("d", 3),
        ]),
    ]

def test_dictToList_deeply_nested():
    assert dictToList({
        "a": 0,
        "b": {
            "c": {
                "d": {
                    "e": 1
                }
            }
        },
    }) == [
        ("a", 0),
        ("b", [
            ("c", [
                ("d", [
                    ("e", 1),
                ]),
            ]),
        ]),
    ]

def test_clip():
    assert clip(150, 0, 100) == 100
    assert clip(-50, 0, 100) == 0
    assert clip(50, 0, 100) == 50