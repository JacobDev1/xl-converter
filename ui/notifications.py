from data.constants import ICON_SVG

from PySide6.QtWidgets import(
    QMessageBox
)

from PySide6.QtGui import(
    QIcon
)


class Notifications():
    def __init__(self):
        self.dlg = QMessageBox()
        self.dlg.setWindowIcon(QIcon(ICON_SVG))
    
    def notify(self, title, msg):
        self.dlg.setDetailedText(None)
        self.dlg.setWindowTitle(title)
        self.dlg.setText(msg)
        return self.dlg.exec()

    def notifyDetailed(self, title, msg, details):
        self.dlg.setDetailedText(None)  # Resets the state of the "Show Details..." button
        self.dlg.setDetailedText(details)
        self.dlg.setWindowTitle(title)
        self.dlg.setText(msg)
        return self.dlg.exec()