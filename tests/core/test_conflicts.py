import pytest

from core.conflicts import checkForConflicts
from core.exceptions import GenericException

def test_checkForConflicts_no_conflict():
    assert not checkForConflicts("jpg", "WEBP")

def test_checkForConflicts_gif_unsupported():
    with pytest.raises(GenericException) as excinfo:
        checkForConflicts("gif", "JPG")

    assert "Animation is not supported for GIF -> JPG" == excinfo.value.msg

def test_checkForConflicts_gif_supported():
    assert not checkForConflicts("gif", "JPEG XL")

def test_checkForConflicts_apng_unsupported():
    with pytest.raises(GenericException) as excinfo:
        checkForConflicts("apng", "WEBP")

    assert "Animation is not supported for APNG -> WEBP" == excinfo.value.msg

def test_checkForConflicts_apng_supported():
    assert not checkForConflicts("apng", "JPEG XL")

def test_checkForConflicts_downscaling():
    with pytest.raises(GenericException) as excinfo:
        checkForConflicts("gif", "JPEG XL", True)
    
    assert "Downscaling is not supported for animation" == excinfo.value.msg