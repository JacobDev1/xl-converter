from unittest.mock import patch, MagicMock

import pytest

from data.fonts import loadFonts, fonts

@patch("data.fonts.Path", return_value=MagicMock())
@patch("data.fonts.QFontDatabase", **{"addApplicationFont.return_value": 0})
@patch("data.fonts.logging")
def test_loadFonts_success(mock_logging, mock_font_database, mock_path):
    loadFonts()

    assert mock_font_database.addApplicationFont.call_count == len(fonts)
    mock_logging.error.assert_not_called()

@patch("data.fonts.Path", return_value=MagicMock())
@patch("data.fonts.QFontDatabase", **{"addApplicationFont.return_value": -1})
@patch("data.fonts.logging")
def test_loadFonts_failure(mock_logging, mock_font_database, mock_path):
    loadFonts()

    assert mock_font_database.addApplicationFont.call_count == len(fonts)
    assert mock_logging.error.call_count == len(fonts)
    mock_logging.error.assert_any_call("[Fonts] Failed to load Ubuntu-Bold.ttf")