from .models import Theme
from .utils import hexToRGBA, getIconPath

def getStyleSheet(theme: Theme) -> str:
    """Creates a stylesheet for QApplication."""
    # Derived
    background_hover = hexToRGBA(theme.colors.accent_big, 20)
    background_selected = hexToRGBA(theme.colors.accent_big, 40)
    border_faded = hexToRGBA(theme.colors.border, 150)
    canvas_faded = hexToRGBA(theme.colors.canvas, 180)
    
    # Theme-specific vars
    if theme.name == "Light Amber":
        scrollbar_handle = theme.colors.border
        scrollbar_handle_hover = hexToRGBA(theme.colors.font, 65)
    else:
        scrollbar_handle = border_faded
        scrollbar_handle_hover = theme.colors.border
    
    return f"""
    * {{
        font-family: "Open Sans";
        font-size: 12px;
        font-weight: 500;
    }}

    QWidget {{
        color: {theme.colors.font};
        background-color: {theme.colors.canvas};
        border: none;
        selection-color: {theme.colors.font};
        selection-background-color: {background_selected};
    }}

    QScrollBar:vertical {{
        border: none;
        width: 16px;
        background-color: {theme.colors.canvas};
        margin: 2px;
    }}

    QScrollBar::handle:vertical {{
        border: none;
        background: {scrollbar_handle};
        min-height: 50px;
    }}

    QScrollBar::handle:vertical:hover, QScrollBar::handle:horizontal:hover {{
        background: {scrollbar_handle_hover};
    }}

    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical, QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        border: none;
        width: 0;
        height: 0;
    }}

    QScrollBar:horizontal {{
        border: none;
        height: 16px;
        background-color: {theme.colors.canvas};
        margin: 2px;
    }}

    QScrollBar::handle:horizontal {{
        border: none;
        background: {scrollbar_handle};
    }}

    QPushButton {{
        color: {theme.colors.accent_big};
        padding: 4px;
        border: 1px solid {theme.colors.border};
        border-radius: 0px;
    }}

    QPushButton:hover {{
        background-color: {background_hover};
    }}

    QPushButton:pressed {{
        background-color: {background_selected};
    }}

    QPushButton:disabled {{
        color: {theme.colors.font_disabled};
    }}

    QPushButton:checked {{
        background-color: {background_selected};
    }}

    QRadioButton::indicator {{
        border-radius: 7px;
        border: 2px solid {theme.colors.font};
    }}

    QRadioButton::indicator:checked {{
        background-color: {theme.colors.accent_big};
        border: none;
    }}

    QRadioButton:disabled {{
        color: {theme.colors.font_disabled};
    }}

    QRadioButton::indicator:disabled {{
        border: 2px solid {theme.colors.font_disabled};
    }}

    QRadioButton::indicator:checked:disabled {{
        background-color: {theme.colors.font_disabled};
    }}

    QLineEdit {{
        padding: 4px;
        color: {theme.colors.font};
        background-color: {theme.colors.canvas};
        border-radius: 0px;
        background-color: {theme.colors.border};
    }}

    QLineEdit:disabled {{
        color: {theme.colors.font_disabled};
    }}

    QTabBar::tab {{
        background-color: transparent;
        padding: 7px;
        margin-right: 10px;
        font-size: 14px;
        font-weight: 400;
    }}

    QTabBar::tab:disabled {{
        color: {theme.colors.font_disabled};
    }}

    QTabBar::tab:first {{
        margin-left: 12px;
    }}

    QTabBar::tab:hover {{
        background-color: {theme.colors.border};
    }}

    QTabBar::tab:selected {{
        color: {theme.colors.accent_big};
        border-bottom: 2px solid {theme.colors.accent_small};
    }}

    QTabBar::tab:selected:disabled {{
        color: {theme.colors.font_disabled};
        border-bottom: 2px solid {theme.colors.font_disabled};
    }}

    QCheckBox {{
        border-radius: 0px;
    }}

    QCheckBox::indicator {{
        width: 12px;
        height: 12px;
        margin-right: 4px;
        border: 2px solid {theme.colors.font};
    }}

    QCheckBox::indicator:checked {{
        color: white;
        background-color: {theme.colors.accent_big};
        border: 2px solid transparent;          /* Keeps text from moving. */
        image: url("{theme.icons.checkmark_svg_url}");
    }}

    QCheckBox::indicator::unchecked:disabled {{
        border: 2px solid {theme.colors.font_disabled};
    }}

    QCheckBox::indicator::checked:disabled {{
        background-color: {theme.colors.font_disabled};
    }}

    QCheckBox:disabled {{
        color: {theme.colors.font_disabled};
    }}

    QSlider {{
        height: 20px;
    }}

    QSlider::handle:horizontal {{
        background-color: {theme.colors.accent_big};
        border-radius: 7px;
        width: 16px;
        height: 16px;
        margin: -6px 0;
        border-radius: 8px;
    }}

    QSlider::groove:horizontal {{
        background-color: {theme.colors.border};
        height: 4px;
    }}

    QSlider::sub-page:horizontal {{
        height: 4px;
        background-color: {theme.colors.accent_big};
    }}

    QSlider::sub-page:horizontal:disabled {{
        height: 4px;
        background-color: {theme.colors.border};
    }}

    QSlider::handle:disabled {{
        background-color: {theme.colors.border};
    }}

    QLabel:disabled {{
        color: {theme.colors.font_disabled};
    }}

    QTextEdit {{
        border-radius: 0px;
        border: 1px solid {theme.colors.border};
        background-color: {theme.colors.border};
        padding: 2px;
    }}

    QTextEdit:disabled {{
        color: {theme.colors.font_disabled};
    }}

    QTreeView {{
        background-color: {theme.colors.canvas};
        border: 1px solid {theme.colors.border};
        border-radius: 0px;
        show-decoration-selected: 0;
    }}

    QTreeView::item {{
        font-size: 9px;
        padding-top: 1px;
        padding-bottom: 1px;
    }}

    QTreeView>QHeaderView::section {{
        color: {theme.colors.font};
        background-color: {theme.colors.border};
        font-weight: 600;
        text-align: left;
        border: none;
        padding: 3px 3px 3px 13px;
    }}

    QTreeView QHeaderView::section:horizontal:!last {{
        border-right: 1px solid {theme.colors.canvas};
    }}

    QTreeView::item:disabled {{
        color: {theme.colors.font_disabled};
    }}

    QTableView {{
        /*
            This line removes the **focus rectangle** outline. It uses a workaround since Qt does not offer a direct way of styling it.

            https://forum.qt.io/topic/18888/how-to-remove-focus-rectangle-on-qlistview-and-similar-using-qstyleditemdelegate-with-style-sheets/11

            This method does not work for QTreeView. A custom delegate is used there.
        */

        outline: 0;
    }}

    QTreeView::item:hover {{
        background-color: {theme.colors.border};
    }}

    QTreeView::item:selected {{
        background-color: {background_selected};
    }}

    QComboBox {{
        background-color: {theme.colors.border};
        color: {theme.colors.font};
        border-radius: 0px;
        padding: 4px;
        padding-left: 6px;
    }}

    QComboBox:disabled {{
        color: {theme.colors.font_disabled};
    }}

    QComboBox::drop-down {{
        border: none;
    }}

    QComboBox QAbstractItemView {{
        /* The black bars on top and bottom are caused by adding `padding` to QComboBox. Is Qt supposed to work like this? */ https://stackoverflow.com/questions/78848355/pyqt6-combobox-weird-black-bars-on-top-and-bottom-sides */

        border-top: none;       /* without this the border does not change */
        border: 1px solid {theme.colors.border};
    }}

    QComboBox::down-arrow {{
        width: 12px;
        height: 12px;
        margin-right: 10px;
        image: url("{theme.icons.drop_down_arrow_svg_url}");
    }}

    QComboBox::down-arrow:disabled {{
        image: url("{theme.icons.drop_down_arrow_disabled_svg_url}");
    }}

    QSpinBox, QDoubleSpinBox {{
        color: {theme.colors.font};
        background-color: {theme.colors.border};
        padding: 4px;
        border: 1px solid {theme.colors.border};
        border-radius: 0px;
    }}

    QSpinBox:disabled, QDoubleSpinBox:disabled {{
        color: {theme.colors.font_disabled};
    }}

    QSpinBox::up-button, QDoubleSpinBox:up-button {{
        subcontrol-origin: border;
        subcontrol-position: top right;
        margin-right: 10px;
        margin-top: 2px;
        border: none;
    }}

    QSpinBox::down-button, QDoubleSpinBox:down-button {{
        subcontrol-origin: border;
        subcontrol-position: bottom right;
        margin-right: 10px;
        margin-bottom: 2px;
        border: none;
    }}

    QSpinBox::up-arrow, QDoubleSpinBox:up-arrow {{
        image: url("{theme.icons.up_arrow_svg_url}");
        width: 7px;
    }}

    QSpinBox::up-arrow:disabled, QDoubleSpinBox::up-arrow:disabled {{
        image: url("{theme.icons.up_arrow_disabled_svg_url}");
    }}

    QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {{
        image: url("{theme.icons.down_arrow_svg_url}");
        width: 7px;
    }}

    QSpinBox::down-arrow:disabled, QDoubleSpinBox::down-arrow:disabled {{
        image: url("{theme.icons.down_arrow_disabled_svg_url}");
    }}

    QToolTip {{
        color: {theme.colors.font};
        background-color: {theme.colors.canvas};
        padding: 10px;
        border: 1px solid {theme.colors.border};
    }}

    QTableWidget QWidget, QTableWidget, QHeaderView {{ 
        background-color: {theme.colors.canvas};
    }}

    QTableWidget::item:focus {{
        border: none;
        outline: none;
    }}

    QGroupBox {{
        border: 1px solid {theme.colors.border};
        padding: 3px;
        margin-top: 7px;
        font-weight: 500;
        color: {theme.colors.font_disabled};
    }}

    QGroupBox::title {{
        subcontrol-origin: margin;
        subcontrol-position: top left;
        left: 10px;
        margin-left: 5px;
        margin-right: 5px;
    }}

    #settingsScrollArea {{
        border: 1px solid {theme.colors.border};
        /* Align with buttons */
        margin-top: 1px;
        margin-bottom: 1px;
    }}

    QScrollArea QScrollBar:vertical {{
        width: 18px;
    }}

    #settingsScrollArea QWidget {{
        margin: 3px;
    }}

    QMessageBox QPushButton {{
        qproperty-icon: none;
        min-width: 80px;
    }}

    QProgressBar {{
        color: {theme.colors.progress_bar_text};
        text-align: center;
        border: 1px solid {theme.colors.border};
    }}

    QProgressBar::chunk {{
        background-color: {theme.colors.accent_big};
    }}
    
    QProgressDialog QPushButton {{
        min-width: 80px;
    }}
    
    QTableWidget {{
        border: 1px solid {theme.colors.border};
    }}

    QTableView QHeaderView::section {{
        color: {theme.colors.font};
        background-color: {theme.colors.border};
        border: none;
        padding: 3px 3px 3px 13px;
    }}

    QTableView QHeaderView::section:horizontal:!last {{
        border-right: 1px solid {theme.colors.canvas};
    }}

    QTableView::item:selected {{
        background-color: {background_selected};
    }}

    /* Set fixed height to 25px */
    QPushButton, QSpinBox, QDoubleSpinBox {{
        min-height: 15px;
        max-height: 15px;
    }}

    QLineEdit, QComboBox {{
        min-height: 17px;
        max-height: 17px;
    }}

    QSpinBox, QDoubleSpinBox {{
        min-width: 20px;
    }}

    QTextEdit {{
        max-height: 45px;
    }}

    QTextEdit QScrollBar:vertical {{
        background-color: {theme.colors.border};
    }}

    QTextEdit QScrollBar::handle:vertical {{
        background-color: {scrollbar_handle};
        min-height: 3px;
    }}

    QTextEdit QScrollBar::handle:vertical:hover {{
        background-color: {scrollbar_handle_hover};
    }}

    /* About tab */
    #title_l {{
        font-family: "Open Sans";
        font-weight: 300;
        font-size: 30px;
    }}

    #version_l {{
        font-family: "Open Sans";
        font-weight: 700;
        font-size: 13px;
    }}

    /* Settings tab */
    QLabel[class="min_width_l"] {{
        min-width: 84px;
    }}

    QComboBox[class="min_width_cmb"] {{
        min-width: 116px;
    }}

    QSpinBox[class="min_width_sb"] {{
        min-width: 84px;
    }}
    """
