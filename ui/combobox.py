from PySide6.QtGui import QWheelEvent
from PySide6.QtWidgets import QComboBox

class ComboBox(QComboBox):
    def wheelEvent(self, e: QWheelEvent) -> None:
        e.ignore()