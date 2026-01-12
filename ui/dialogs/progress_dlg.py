from PySide6.QtWidgets import QProgressDialog
from PySide6.QtGui import QIcon
from PySide6.QtCore import Signal, QObject, QPoint, Qt

from data.constants import ICON_SVG

# QProgressDialog shows up when declared
# This wrapper allows it to be declared and shown independently

class ProgressDialog(QObject):
    canceled = Signal()

    def __init__(self, parent=None, title="XL Converter", minimum=0, maximum=100, cancelable=True):
        QObject.__init__(self)
        self.dlg = None
        self.title = title
        self.minimum = minimum
        self.maximum = maximum
        self.cancelable = cancelable
        self.parent = parent

        self.label_line_1_cached = None
        self.label_line_2_cached = None

        self.is_processing = False

    def show(self):
        """Creates a new progress dialog and shows it. Call before setting any values."""
        if self.dlg is not None:
            self.dlg.show()
            return

        self.dlg = QProgressDialog(
            "",
            "Cancel" if self.cancelable else None,
            self.minimum,
            self.maximum,
            parent=self.parent
        )
        self.dlg.setWindowTitle(self.title)
        self.dlg.setWindowIcon(QIcon(ICON_SVG))
        self.dlg.canceled.connect(self._canceled)

        self.dlg.setMinimumWidth(350)
        self.dlg.setMinimumHeight(115)
        self.dlg.setWindowModality(Qt.ApplicationModal)
        self.dlg.setWindowFlags(
            Qt.Dialog |
            Qt.WindowTitleHint |
            Qt.WindowCloseButtonHint |
            Qt.CustomizeWindowHint
        )
        self.dlg.show()
        self.is_processing = True
        self.updatePosition()

    def _canceled(self):
        self.canceled.emit()
        self.is_processing = False

    def finished(self):
        """Clean up progress dialog."""
        if self.dlg is None:
            return
        
        self.dlg.canceled.disconnect()  # Prevents from calling on finish
        self.dlg.close()
        self.dlg.deleteLater()
        self.dlg = None
        self.label_line_1_cached = None
        self.label_line_2_cached = None

    def setValue(self, value):
        if self.dlg is None:
            return
        
        self.dlg.setValue(value)
    
    def setRange(self, minimum, maximum):
        self.maximum = maximum
        self.minimum = minimum
        if self.dlg is not None:
            self.dlg.setRange(minimum, maximum)
    
    def setLabelText(self, text):
        if self.dlg is None:
            return
        
        self.dlg.setLabelText(text)

    def setLabelTextLine1(self, text):
        self.label_line_1_cached = text
        self._updateLabelTextLines()
    
    def setLabelTextLine2(self, text):
        self.label_line_2_cached = text
        self._updateLabelTextLines()

    def _updateLabelTextLines(self):
        out = ""
        if self.label_line_1_cached:
            out += self.label_line_1_cached
        
        if self.label_line_2_cached:
            out += f"\n{self.label_line_2_cached}"
        
        self.setLabelText(out)

    def wasCanceled(self):
        if self.dlg is None:
            return False
        
        return self.dlg.wasCanceled()

    def updatePosition(self):
        """Follow the parent's position. Requires parent to be specified in the constructor."""
        if (
            self.is_processing and
            self.parent and
            self.dlg is not None
        ):
            parent_geometry = self.parent.frameGeometry()
            dlg_geometry = self.dlg.frameGeometry()

            x = parent_geometry.x() + (parent_geometry.width() - dlg_geometry.width()) // 2
            y = parent_geometry.y() + (parent_geometry.height() - dlg_geometry.height()) // 2

            self.dlg.move(QPoint(x, y))
