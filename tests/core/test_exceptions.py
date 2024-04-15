from core.exceptions import (
    GenericException,
    FileException,
    CancellationException,
)

def test_GenericException():
    e_id, e_msg = "T0", "Test exception."
    e = GenericException(e_id, e_msg)
    
    assert e.id == e_id
    assert e.msg == e_msg

def test_FileException():
    e_id, e_msg = "T0", "Test exception."
    e = FileException(e_id, e_msg)

    assert e.id == e_id
    assert e.msg == e_msg

def test_CancellationException():
    e = CancellationException()
    
    assert isinstance(e, CancellationException)