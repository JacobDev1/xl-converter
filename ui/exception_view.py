import csv
import platform
from pathlib import Path

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
    QSpacerItem,
    QSizePolicy,
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
    def __init__(self, settings, parent=None):
        super(ExceptionView, self).__init__(parent)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        
        self.notifications = Notifications(self)
        self.report_data = {}

        # Table
        headers = [
            "ID",
            "Exception",
            "Source",
        ]

        self.table = QTableWidget(0, len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setSortingEnabled(False)
        self.table.setShowGrid(False)

        # Bottom
        btm_lt = QHBoxLayout()
        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.close)
        self.save_to_file_btn = QPushButton("Save to File")
        self.save_to_file_btn.clicked.connect(self.saveToFile)

        btm_lt.addItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))
        btm_lt.addWidget(self.save_to_file_btn)
        btm_lt.addWidget(self.close_btn)

        btm_lt.setStretch(0, 2)
        btm_lt.setStretch(1, 1)
        btm_lt.setStretch(2, 2)

        # Layout
        self.main_lt = QVBoxLayout()
        self.main_lt.addWidget(self.table)
        self.main_lt.addLayout(btm_lt)
        self.setLayout(self.main_lt)

        self.setWindowTitle("Exceptions Occured")
        self.setWindowIcon(QIcon(ICON_SVG))
        self.resize(650,300)

    def addItem(self, _id, exception, source):
        row_pos = self.table.rowCount()
        self.table.insertRow(row_pos)

        self._setItem(row_pos, 0, _id, Qt.AlignCenter)
        self._setItem(row_pos, 1, exception)
        self._setItem(row_pos, 2, source, Qt.AlignCenter)

    def _setItem(self, row, col, value, align = Qt.AlignVCenter | Qt.AlignLeft):
        item = QTableWidgetItem()
        item.setTextAlignment(align)
        item.setData(Qt.DisplayRole, value)
        self.table.setItem(row, col, item)

    def clear(self):
        while self.table.rowCount() > 0:
            self.table.removeRow(0)

    def updateReportHeader(self, *data):
        """Include additional information in the debug file (If one is saved)."""
        self.report_data = {}
        for e in data:
            self.report_data.update(e)

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
                
                # Header
                writer.writerow(("Version", VERSION))
                writer.writerow(("OS", platform.system()))

                # Additional data
                if self.report_data:
                    writer.writerow([])
                    for k, v in self.report_data.items():
                        writer.writerow((k,))
                        for row in v:
                            writer.writerow(row)
                        writer.writerow([])

                # Row data
                writer.writerow(("Exceptions",))
                writer.writerow(("ID", "Exception", "Extension"))
                for row in range(self.table.rowCount()):
                    row_data = (
                        self.table.item(row, 0).text(),
                        self.table.item(row, 1).text(),
                        Path(self.table.item(row, 2).text()).suffix,
                    )
                    writer.writerow(row_data)
        except OSError as err:
            self.notifications.notifyDetailed("Error", "Failed to save file", str(err))

    def resizeToContent(self):
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        # self.table.setColumnWidth(1, 450)
        self.table.resizeRowsToContents()
    
    def isEmpty(self):
        return self.table.rowCount() == 0