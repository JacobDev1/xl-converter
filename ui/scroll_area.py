import time

from PySide6.QtWidgets import(
    QScrollArea,
)
from PySide6.QtCore import(
    Qt,
    QPoint,
)

UPDATE_RATE_LIMIT_MS = 5

class ScrollArea(QScrollArea):
    def __init__(self, parent=None, enable_horizontal=False, enable_vertical=True):
        super().__init__(parent)
        self.setWidgetResizable(True)
        if enable_horizontal == False:
            self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        if enable_vertical == False:
            self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.enable_horizontal = enable_horizontal
        self.enable_vertical = enable_vertical

        self.is_dragging = False
        self.last_position = QPoint()
        self.last_updated = 0
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.is_dragging = True
            self.last_position = event.position().toPoint()
            self.setCursor(Qt.ClosedHandCursor)
            event.accept()
    
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.is_dragging = False
            self.setCursor(Qt.ArrowCursor)
            event.accept()

    def mouseMoveEvent(self, event):
        if self.last_updated > time.time() * 1000 - UPDATE_RATE_LIMIT_MS:
            return

        if self.is_dragging:
            delta = event.position().toPoint() - self.last_position
            requested_horizontal = self.horizontalScrollBar().value() - delta.x()
            requested_vertical = self.verticalScrollBar().value() - delta.y()

            if not requested_horizontal <= 0 and not requested_horizontal > self.horizontalScrollBar().maximum() and self.enable_horizontal:
                self.horizontalScrollBar().setValue(requested_horizontal)

            if not requested_vertical <= 0 and not requested_vertical > self.verticalScrollBar().maximum() and self.enable_vertical:
                self.verticalScrollBar().setValue(requested_vertical)
            
            self.last_position = event.position().toPoint()
            self.last_updated = time.time() * 1000
            event.accept()