import pytest

from core.conflicts import checkForConflicts
from core.exceptions import GenericException

def test_checkForConflicts_no_conflict():
    assert not checkForConflicts("jpg", "WebP")

def test_checkForConflicts_gif_unsupported():
    with pytest.raises(GenericException) as excinfo:
        checkForConflicts("gif", "JPEG")

    assert "GIF -> JPEG conversion is not supported" == excinfo.value.msg

def test_checkForConflicts_gif_supported():
    assert not checkForConflicts("gif", "JPEG XL")

def test_checkForConflicts_apng_unsupported():
    with pytest.raises(GenericException) as excinfo:
        checkForConflicts("apng", "WebP")

    assert "APNG -> WebP conversion is not supported" == excinfo.value.msg

def test_checkForConflicts_apng_supported():
    assert not checkForConflicts("apng", "JPEG XL")

def test_checkForConflicts_downscaling():
    with pytest.raises(GenericException) as excinfo:
        checkForConflicts("gif", "JPEG XL", True)
    
    assert "Downscaling is not supported for animation" == excinfo.value.msg