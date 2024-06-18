from unittest.mock import patch
from typing import Any

import pytest

from ui.theme import setTheme

@pytest.mark.parametrize("theme, expected_args, expected_kwargs", [
    ("dark", (), {"corner_shape": "sharp", "custom_colors": {"primary":"#F18000"}}),
    ("light", ("light",), {"corner_shape": "sharp", "custom_colors": {"primary":"#EF7202"}}),
])
def test_setTheme(theme, expected_args, expected_kwargs):
    with patch('qdarktheme.setup_theme') as mock_setup_theme:
        setTheme(theme)
        
        mock_setup_theme.assert_called_once()
        args, kwargs = mock_setup_theme.call_args
        assert args == expected_args
        for key, value in kwargs.items():
            if key != "additional_qss":
                assert expected_kwargs[key] == value