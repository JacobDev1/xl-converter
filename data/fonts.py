import logging
from pathlib import Path

from PySide6.QtGui import (
    QFont,
    QFontDatabase,
)

from data.constants import PROGRAM_FOLDER

# Load fonts
fonts = [
    "Ubuntu-Bold.ttf",
    "Ubuntu-BoldItalic.ttf",
    "Ubuntu-Italic.ttf",
    "Ubuntu-Light.ttf",
    "Ubuntu-LightItalic.ttf",
    "Ubuntu-Medium.ttf",
    "Ubuntu-MediumItalic.ttf",
    "Ubuntu-Regular.ttf",
]

def loadFonts():
    """Run after initializing QApplication."""
    for font in fonts:
        font_id = QFontDatabase.addApplicationFont(str(Path(PROGRAM_FOLDER, "fonts", font)))
        if font_id == -1:
            logging.error(f"[Fonts] Failed to load {font}")

# Styles
DEFAULT = QFont("Ubuntu", 10)
MAIN_TABS = QFont("Ubuntu", 10)
MAIN_TABS.setPointSizeF(MAIN_TABS.pointSizeF() * 1.05)
ABOUT_TITLE = QFont("Ubuntu", 18)
ABOUT_VERSION = QFont("Ubuntu", 10, QFont.Bold)
ABOUT_DESC = QFont("Ubuntu", 10)
# UBUNTU_BOLD = QFont("Ubuntu", 10, QFont.Bold)
# UBUNTU_BOLD_ITALIC = QFont("Ubuntu", 10, QFont.Bold, italic=True)
# UBUNTU_LIGHT = QFont("Ubuntu Light", 10)
# UBUNTU_ITALIC = QFont("Ubuntu", 10, italic=True)
# UBUNTU_LIGHT_ITALIC = QFont("Ubuntu Light", 10, italic=True)
# UBUNTU_MEDIUM = QFont("Ubuntu Medium", 10)
# UBUNTU_MEDIUM_ITALIC = QFont("Ubuntu Medium", 10, italic=True)