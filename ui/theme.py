import qdarktheme

def setTheme(theme="dark"):
    match theme:
        case "dark":
            qdarktheme.setup_theme(corner_shape="sharp", custom_colors={"primary":"#F18000"})
        case "light":
            qdarktheme.setup_theme("light", corner_shape="sharp", custom_colors={"primary":"#EF7202"})