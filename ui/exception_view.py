import csv
import platform

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QCheckBox,
    QTableWidget,
    QAbstractItemView,
    QPushButton,
    QTableWidgetItem,
    QHeaderView,
    QFileDialog,
)
from PySide6.QtCore import (
    Signal,
    Qt,
    QUrl,
)
from PySide6.QtGui import QIcon

from data.constants import ICON_SVG, VERSION
from ui import Notifications

class ExceptionView(QDialog):
    dont_show_again = Signal(bool)

    def __init__(self, settings, parent=None):
        super(ExceptionView, self).__init__(parent)
        self.notifications = Notifications()

        # Table
        headers = [
            "ID",
            "Exception",
            "Source",
        ]

        self.table = QTableWidget(0, len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setSortingEnabled(False)
        self.table.setShowGrid(False)

        # Bottom
        btm_lt = QHBoxLayout()
        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.close)
        self.save_to_file_btn = QPushButton("Save to File")
        self.save_to_file_btn.clicked.connect(self.saveToFile)
        self.dont_show_again_cb = QCheckBox("Don't Show Again")
        self.dont_show_again_cb.toggled.connect(self.dont_show_again.emit)

        btm_lt.addWidget(self.dont_show_again_cb)
        btm_lt.addWidget(self.save_to_file_btn)
        btm_lt.addWidget(self.close_btn)

        # Layout
        self.main_lt = QVBoxLayout()
        self.main_lt.addWidget(self.table)
        self.main_lt.addLayout(btm_lt)
        self.setLayout(self.main_lt)

        self.setWindowTitle("Exceptions Occured")
        self.setWindowIcon(QIcon(ICON_SVG))
        self.resize(650,300)

        self.table.setStyleSheet("""
            QTableWidget, QHeaderView { background-color: #202124; }
            """)
        self.table.viewport().setStyleSheet("background-color: #202124;")

        # Apply settings
        self.dont_show_again_cb.setChecked(settings.get("no_exceptions", False))

    def addItem(self, _id, exception, source):
        row_pos = self.table.rowCount()
        self.table.insertRow(row_pos)

        self._setItem(row_pos, 0, _id, Qt.AlignCenter)
        self._setItem(row_pos, 1, exception)
        self._setItem(row_pos, 2, source)

    def _setItem(self, row, col, value, align = Qt.AlignVCenter | Qt.AlignLeft):
        item = QTableWidgetItem()
        item.setTextAlignment(align)
        item.setData(Qt.DisplayRole, value)
        self.table.setItem(row, col, item)

    def clear(self):
        while self.table.rowCount() > 0:
            self.table.removeRow(0)

    def saveToFile(self):
        if self.table.rowCount() == 0:
            self.notifications.notify("Empty List", "Exception list is empty, there is nothing to save.")
            return

        dlg, _ = QFileDialog.getSaveFileUrl(
            self,
            "Save Exceptions",
            QUrl.fromLocalFile("xl_converter_exceptions.csv"),
            "CSV (*.csv)"
        )

        if not dlg.isValid():
            return
        
        try:
            with open(dlg.toLocalFile(), "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
                writer.writerow(("Version", VERSION))
                writer.writerow(("OS", platform.system()))
                writer.writerow(("ID", "Exception", "Source"))
                for row in range(self.table.rowCount()):
                    row_data = []
                    for col in range(self.table.columnCount()):
                        row_data.append(self.table.item(row, col).text())
                    writer.writerow(row_data)
        except OSError as err:
            self.notifications.notifyDetailed("Error", "Failed to save file", str(err))

    def resizeToContent(self):
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)

    def setDontShowAgain(self, checked):
        self.blockSignals(True)
        self.dont_show_again_cb.setChecked(checked)
        self.blockSignals(False)
    
    def isEmpty(self):
        return self.table.rowCount() == 0