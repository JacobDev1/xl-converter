from dataclasses import dataclass

import qdarktheme
from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPalette
            
@dataclass
class ThemeColors:
    accent: str
    font: str
    canvas: str
    border: str

class Colors:
    dark = ThemeColors(
        accent="#F18000",
        font="#E4E7EB",
        canvas="#202124",
        border="#3F4042",
    )
    light = ThemeColors(
        accent="#EF7202",
        font="#4E5258",
        canvas="#F8F9FA",
        border="#DADCE0",
    )

def setTheme(theme="dark"):
    match theme:
        case "dark":
            qdarktheme.setup_theme(
                "dark",
                corner_shape="sharp",
                custom_colors={ "primary": Colors.dark.accent },
                additional_qss=f"""
                    QTableWidget QWidget, QTableWidget, QHeaderView {{ background-color: {Colors.dark.canvas}; }}
                    QTableWidget::item:focus {{ border: none; outline: none; }}
                    QToolTip {{
                        color: {Colors.dark.font};
                        background-color: {Colors.dark.canvas};
                        padding: 10px;
                        border: 1px solid {Colors.dark.border};
                    }}
                """
            )
        case "light":
            qdarktheme.setup_theme(
                "light",
                corner_shape="sharp",
                custom_colors={"primary": Colors.light.accent},
                additional_qss=f"""
                    QToolTip {{
                        color: {Colors.light.font};
                        background-color: {Colors.light.canvas};
                        padding: 10px;
                        border: 1px solid {Colors.light.border};
                    }}
                """
            )

def getPaletteInfo(widget: QWidget) -> str:
    palette = widget.palette()
    groups = {
        QPalette.Active: "Active",
        QPalette.Inactive: "Inactive",
        QPalette.Disabled: "Disabled",
    }

    buff = ""
    for group, name in groups.items():
        buff += f"{name} Group:\n"
        for role in QPalette.ColorRole:
            if role == QPalette.NColorRoles:
                continue
            color = palette.color(group, role)
            buff += f"\t{role.name:15}: {color.name()}\n"
    return buff