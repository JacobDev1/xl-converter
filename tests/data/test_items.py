from pathlib import Path

import pytest

from data.items import Items

@pytest.fixture
def items():
    items = Items()
    return items

def test_parseData_valid(items):
    items.parseData(
        (Path("images/1/image.jpg"), Path("images/1")),
        (Path("images/1/image 2.jpg"), Path("images/1")),
    )
    assert items.getItemCount() == 2
    assert items.getItem(0) == (Path("images/1/image.jpg"), Path("images/1"))
    assert items.getItem(1) == (Path("images/1/image 2.jpg"), Path("images/1"))

def test_parseData_partially_valid(items):
    items.parseData(
        (Path("images/1/image.jpg"), "images/1"),
        (Path("images/1/image 2.jpg"), Path("images/1")),
    )
    assert items.getItemCount() == 1
    assert items.getItem(0) == (Path("images/1/image 2.jpg"), Path("images/1"))

def test_parseData_invalid(items, caplog):
    items.parseData((Path("images/1/image.exr"), Path("images/1")))
    assert caplog.records[0].message == "[Items] Extension not allowed (exr)"
    items.parseData((Path("images/1/image.jpg"), "images/1"))
    assert caplog.records[1].message == "[Items] anchor_path is not a Path object (<class 'str'>)"

def test_clear(items):
    assert items.items == []
    assert items.completed_item_count == 0
    assert items.item_count == 0