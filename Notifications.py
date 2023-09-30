from PySide6.QtWidgets import(
    QMessageBox
)

class Notifications():
    def __init__(self):
        self.dlg = QMessageBox()
    
    def notify(self, title, msg):
        self.dlg.setWindowTitle(title)
        self.dlg.setDetailedText(None)
        self.dlg.setText(msg)
        return self.dlg.exec()

    def notifyDetailed(self, title, msg, details):
        self.dlg.setWindowTitle(title)
        self.dlg.setText(msg)
        self.dlg.setDetailedText(details)
        return self.dlg.exec()