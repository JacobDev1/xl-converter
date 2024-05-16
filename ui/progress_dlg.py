from PySide6.QtWidgets import QProgressDialog
from PySide6.QtGui import QIcon
from PySide6.QtCore import Signal, QObject

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
            self.parent
        )
        self.dlg.setWindowTitle(self.title)
        self.dlg.setWindowIcon(QIcon(ICON_SVG))
        self.dlg.canceled.connect(self.canceled.emit)

        self.dlg.setMinimumWidth(350)
        self.dlg.setMinimumHeight(115)
        self.dlg.show()

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
