import qdarktheme

def setTheme(theme="dark"):
    match theme:
        case "dark":
            qdarktheme.setup_theme(corner_shape="sharp", custom_colors={"primary":"#F18000"}, additional_qss="""
                QTableWidget, QHeaderView { background-color: #202124; }
                QTableWidget::item:focus { border: none; outline: none; }
                QTableWidget QWidget { background-color: #202124; }
            """)
        case "light":
            qdarktheme.setup_theme("light", corner_shape="sharp", custom_colors={"primary":"#EF7202"})