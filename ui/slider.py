from PySide6.QtGui import QKeyEvent, QMouseEvent, QWheelEvent
from PySide6.QtWidgets import QSlider
from PySide6.QtCore import Qt

class Slider(QSlider):
    def __init__(self, orientation=Qt.Horizontal):
        super().__init__(orientation)

    def mousePressEvent(self, e: QMouseEvent) -> None:
        if e.button() == Qt.LeftButton:
            self._setValueFromClick(e)
    
    def mouseMoveEvent(self, e: QMouseEvent) -> None:
        if e.buttons() & Qt.LeftButton:
            self._setValueFromClick(e)

    def wheelEvent(self, e: QWheelEvent) -> None:
        e.ignore()

    def keyPressEvent(self, e: QKeyEvent) -> None:
        if e.key() == Qt.Key_Left:
            value = self.value() - self._getTickInterval()
            if value % self._getTickInterval() == 0:
                self.setValue(value)
            else:
                self.setValue(value + self._getTickInterval() - value % self._getTickInterval())    # 99 -> 95 instead of 94 [5 tickInterval]
        elif e.key() == Qt.Key_Right:
            value = self.value() + self._getTickInterval()
            if value % self._getTickInterval() == 0:
                self.setValue(value)
            else:
                self.setValue(value - value % self._getTickInterval())                              # 1 -> 5 instead of 6 [5 tickInterval]
        else:
            super().keyPressEvent(e)
    
    def _setValueFromClick(self, e: QMouseEvent) -> None:
        click_pos = e.pos().x()
        total_width = self.width()
        rel_value = (self.maximum() - self.minimum()) * click_pos / total_width

        if self._getTickInterval() > 1:
            value = round(rel_value / self._getTickInterval()) * self._getTickInterval()
        elif self._getTickInterval() == 1:
            value = round(rel_value) + 1    # round() is necessary; otherwise, the slider does not snap correctly.
        else:
            value = rel_value

        self.setValue(int(value))
    
    def _getTickInterval(self) -> int:
        """self.tickInterval() with non-zero output."""
        return 1 if self.tickInterval() <= 0 else self.tickInterval()