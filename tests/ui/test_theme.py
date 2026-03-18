import logging
from unittest.mock import patch, MagicMock
from contextlib import ExitStack
from pathlib import Path
import re

import pytest

import ui.theme as theme

# ---------------------- theme_manager ----------------------

def test_setTheme_happy_path(caplog):
    caplog.set_level(logging.ERROR)
    mock_qapp_instance = MagicMock()
    mock_qapp_instance.setStyle = MagicMock()
    mock_qapp_instance.setStyleSheet = MagicMock()
    mock_theme = MagicMock()
    mock_accent_big = "#111111"
    mock_theme.colors.accent_big = mock_accent_big
    mock_stylesheet = "sample stylesheet"
    mock_theme_name = "Ralsei"

    with (
        patch("ui.theme.theme_manager.getTheme", return_value=mock_theme) as mock_getTheme,
        patch("ui.theme.theme_manager.getStyleSheet", return_value=mock_stylesheet) as mock_getStyleSheet,
        patch("ui.theme.theme_manager.QApplication.instance", return_value=mock_qapp_instance),
        patch("ui.theme.theme_manager.StyledLabel.updateStyleForAll") as mock_updateStyleForAll,
    ):
        theme.theme_manager.setTheme(mock_theme_name)

        mock_getTheme.assert_called_once_with(mock_theme_name)
        assert len(caplog.records) == 0, [log.msg for log in caplog.records]
        mock_qapp_instance.setStyle.assert_called_once_with("Fusion")
        mock_qapp_instance.setStyleSheet.assert_called_once_with(mock_stylesheet)
        mock_updateStyleForAll.assert_called_once()
        assert mock_accent_big in mock_updateStyleForAll.call_args_list[0][0][0]

def test_setTheme_sad_path(caplog):
    caplog.set_level(logging.ERROR)
    mock_qapp_instance = MagicMock()
    mock_qapp_instance.setStyle = MagicMock()
    mock_theme = MagicMock()
    mock_theme.colors.accent_big = "#111111"

    with (
        patch("ui.theme.theme_manager.getTheme", return_value=mock_theme),
        patch("ui.theme.theme_manager.getStyleSheet", return_value=""),
        patch("ui.theme.theme_manager.QApplication.instance", return_value=None),
        caplog.at_level(logging.ERROR),
    ):
        theme.theme_manager.setTheme()
        mock_qapp_instance.setStyle.assert_not_called()
        assert caplog.records[0].message == "QApplication not found."

# ---------------------- utils ----------------------

@pytest.fixture
def getIconPath_patches():
    patches = {
        "is_file": patch("ui.theme.utils.Path.is_file", return_value=True),
    }

    variables = {
        "ASSETS_ICONS_DIR": patch("ui.theme.utils.constants.ASSETS_ICONS_DIR", "./assets/icons/"),
    }

    with ExitStack() as stack:
        _mocks = {name: stack.enter_context(patcher) for name, patcher in patches.items()}
        _variables = {name: stack.enter_context(patcher) for name, patcher in variables.items()}

        yield _mocks, _variables

def test_getIconPath_happy_path(getIconPath_patches, caplog):
    caplog.set_level(logging.ERROR)
    mocks, variables = getIconPath_patches

    assert theme.utils.getIconPath("test_icon.svg") == Path(variables["ASSETS_ICONS_DIR"], "test_icon.svg").as_posix()
    assert caplog.records == []

def test_getIconPath_sad_path(getIconPath_patches, caplog):
    caplog.set_level(logging.ERROR)
    mocks, variables = getIconPath_patches
    mocks["is_file"].return_value = False

    assert theme.utils.getIconPath("test_icon.svg") == ""
    assert "Cannot find icon" in caplog.records[0].msg

def test_hexToRGBA_happy_path():
    assert theme.utils.hexToRGBA("#111111", 127) == "rgba(17, 17, 17, 127)"

@pytest.mark.parametrize("invalid_hex_color", [
    "#11111",
    "#111111F",
    "#11111G",
])
def test_hexToRGBA_exceptions(invalid_hex_color):
    with pytest.raises(ValueError) as exc_info:
        theme.utils.hexToRGBA(invalid_hex_color)

# ---------------------- themes ----------------------

@pytest.mark.parametrize("available_theme, function_called", [
    ("Ralsei", "_getThemeRalsei"),
    ("Dark Amber", "_getThemeDarkAmber"),
    ("Light Amber", "_getThemeLightAmber"),
])
def test_getTheme_theme_available(available_theme, function_called):
    mock_theme = "theme"

    with patch(f"ui.theme.themes.{function_called}", return_value=mock_theme) as mock_theme_func:
        assert theme.themes.getTheme(available_theme) == mock_theme
        mock_theme_func.assert_called_once()

def test_getTheme_theme_unavailable(caplog):
    caplog.set_level(logging.ERROR)
    mock_theme = "theme"

    with patch(f"ui.theme.themes._getThemeRalsei", return_value=mock_theme) as mock_theme_func:
        assert theme.themes.getTheme("Undefined") == mock_theme
        mock_theme_func.assert_called_once()
        assert "Theme \"Undefined\" not found" in caplog.text

@pytest.mark.parametrize("theme_name, func_name, theme_type", [
    ("Ralsei", "_getThemeRalsei", "dark"),
    ("Dark Amber", "_getThemeDarkAmber", "dark"),
    ("Light Amber", "_getThemeLightAmber", "light"),
])
def test_getTheme_individual(theme_name, func_name, theme_type):
    with patch(f"ui.theme.themes.__get{theme_type.title()}ThemeIconPaths", return_value="mock_icon_path") as mock_icon_path:
        if (theme_func_ref := getattr(theme.themes, func_name)) is None:
            assert False, f"Function {func_name} does not exist"
        output_theme = theme_func_ref()
        assert output_theme.name == theme_name
        assert isinstance(output_theme.colors, theme.models.ThemeColors)
        assert output_theme.icons == mock_icon_path.return_value
        mock_icon_path.assert_called_once()

def test____getThemeIcons():
    with patch("ui.theme.themes.getIconPath") as mock_getIconPath:
        assert isinstance(theme.themes.__getLightThemeIconPaths(), theme.models.ThemeIconPaths)
        assert isinstance(theme.themes.__getDarkThemeIconPaths(), theme.models.ThemeIconPaths)
        mock_getIconPath.assert_called()

@pytest.mark.parametrize("func_name", (
    "__getDarkThemeIconPaths",
    "__getLightThemeIconPaths"
))
def test____getThemeIcons_exist(func_name, caplog):
    with caplog.at_level(logging.ERROR):
        if (func_ref := getattr(theme.themes, func_name)) is None:
            assert False, f"Function {func_name} does not exist"
        
        func_ref()

        assert not [record for record in caplog.records if record.levelname == "ERROR"]

# ---------------------- stylesheet ----------------------

def get_sample_theme():
    return theme.models.Theme(
        name="Test Theme",
        colors=theme.models.ThemeColors(
            accent_big="#FFFFFF",
            accent_small="#FFFF00",
            font="#FFFFFF",
            font_disabled="#AAAAAA",
            canvas="#000000",
            border="#BBBBBB",
            progress_bar_text="#FFFFFF",
        ),
        icons=theme.models.ThemeIconPaths(
            checkmark_svg_url="sample.svg",
            drop_down_arrow_svg_url="sample.svg",
            drop_down_arrow_disabled_svg_url="sample.svg",
            up_arrow_svg_url="sample.svg",
            up_arrow_disabled_svg_url="sample.svg",
            down_arrow_svg_url="sample.svg",
            down_arrow_disabled_svg_url="sample.svg",
        ))

def test_getStyleSheet_syntax():
    stylesheet = theme.stylesheet.getStyleSheet(get_sample_theme())

    assert stylesheet.count("{") == stylesheet.count("}"), "Unbalanced braces"
    
    # Old
    # blocks = re.findall(r'\{([^}]+)\}', stylesheet)
    # for block in blocks:
    #     matches = re.findall(r'^\s*([^;]+\s*:\s*[^;]+)\s*$', block, re.M)
    #     assert not matches, f"Missing semicolon:\nLines:\n\t{matches}\nBlock:\n\t{block}"

    # Check for missing semicolons
    def remove_comments(text: str) -> str:
        replacer = lambda m: "\n" * m.group(0).count("\n")
        text = re.sub(r'/\*.*?\*/', replacer, text, flags=re.DOTALL)
        return re.sub(r'^[^\n]*\*/\s*$', replacer, text, flags=re.MULTILINE)

    semicolon_errors = []
    pattern = re.compile(r'([^{]+)\{([^}]+)\}', re.DOTALL)
    for pattern_match in pattern.finditer(stylesheet):
        selector = pattern_match.group(1).strip()
        block = pattern_match.group(2)

        block_without_comments = remove_comments(block)
        block_start_line = stylesheet[:pattern_match.start(2)].count("\n") + 1

        for idx, line in enumerate(block_without_comments.splitlines(), start=1):
            line_stripped = line.strip()

            if not line_stripped:
                continue
                
            if ":" in line_stripped and not line_stripped.endswith(";"):
                abs_line = block_start_line + idx - 1
                semicolon_errors.append(
                    f"Missing semicolon:\nSelector: {selector}\nLine Position: {abs_line}\nLine: {line_stripped}\n"
                )
    
    assert not semicolon_errors, "\n".join(semicolon_errors)
