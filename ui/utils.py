from PySide6.QtWidgets import QWidget

def setToolTip(tooltip: str, *widget_ids: QWidget) -> None:
    try:
        for widget in widget_ids:
            widget.setToolTip(tooltip)
    except Exception as e:
        logging.error(f"[ui.utils.setToolTip] Failed to apply tooltip ({e})")