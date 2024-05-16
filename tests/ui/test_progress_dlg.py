from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtWidgets import QProgressDialog

from ui.progress_dlg import ProgressDialog

@pytest.fixture
def progress_dialog():
    return ProgressDialog()

def test_init(progress_dialog):
    assert progress_dialog.parent == None
    assert progress_dialog.title == "XL Converter"
    assert progress_dialog.minimum == 0
    assert progress_dialog.maximum == 100
    assert progress_dialog.cancelable == True
    
def test_show_first_time(progress_dialog):
    progress_dialog.show()
    assert isinstance(progress_dialog.dlg, QProgressDialog)

def test_show_reuse(progress_dialog):
    progress_dialog.show()
    obj_1 = progress_dialog.dlg
    progress_dialog.show()
    obj_2 = progress_dialog.dlg
    assert obj_1 is obj_2

def test_finished_none(progress_dialog):
    progress_dialog.finished()      # Exceptions make tests fail

def test_finished_instance(progress_dialog):
    progress_dialog.show()
    assert progress_dialog.dlg is not None
    progress_dialog.finished()
    assert progress_dialog.dlg is None

def test_setValue_none(progress_dialog):
    progress_dialog.setValue(50)

def test_setValue_instance(progress_dialog):
    progress_dialog.dlg = MagicMock(spec=QProgressDialog)
    progress_dialog.setValue(50)
    progress_dialog.dlg.setValue.assert_called_once_with(50)

def test_setLabelText_instance(progress_dialog):
    progress_dialog.dlg = MagicMock(spec=QProgressDialog)
    progress_dialog.setLabelText("test")

    assert progress_dialog.dlg.setLabelText.called_with("test")

def test_setLabelText_none(progress_dialog):
    progress_dialog.setLabelText("test")

def test_wasCanceled_instance(progress_dialog):
    progress_dialog.dlg = MagicMock(spec=QProgressDialog)
    assert progress_dialog.wasCanceled() is progress_dialog.dlg.wasCanceled()    

def test_wasCanceled_none(progress_dialog):
    assert progress_dialog.wasCanceled() == False
