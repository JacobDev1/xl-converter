import csv
import platform
import os

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QAbstractItemView,
    QPushButton,
    QFileDialog,
    QSpacerItem,
    QSizePolicy,
    QTreeWidget,
    QTreeWidgetItem,
    QStyledItemDelegate,
    QStyle,
)
from PySide6.QtCore import (
    Qt,
    QUrl,
)
from PySide6.QtGui import (
    QIcon,
)

from data.constants import ICON_SVG, VERSION
from . import message_box

class ItemDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        return None

    def sizeHint(self, option, index):
        size = super().sizeHint(option, index)
        if widget := option.widget:
            text = index.data()
            metrics = widget.fontMetrics()
            width = widget.columnWidth(index.column())
            rect = metrics.boundingRect(
                0, 0,
                width, 1000,
                Qt.TextWordWrap, str(text)
            )
            size.setHeight(rect.height() + 10)
        return size

    def paint(self, painter, option, index):
        option.state &= ~QStyle.State_MouseOver
        option.state &= ~QStyle.State_HasFocus
        super().paint(painter, option, index)

class ExceptionView(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.parent = parent

        self._setupWidgets()
        self._setupSignals()
        self._setupLayouts()
    
    def _setupWidgets(self):
        self.exceptions_t = QTreeWidget(self)
        self.exceptions_t.setRootIsDecorated(False)
        self.exceptions_t.setHeaderLabels(("Err Location", "Exception", "Source",))
        self.exceptions_t.setItemDelegate(ItemDelegate())
        self.exceptions_t.setWordWrap(True)
        self.exceptions_t.setUniformRowHeights(False)
        self.exceptions_t.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        # self.exceptions_t.setColumnWidth(0, 75)
        self.exceptions_t.setColumnWidth(1, 450)

        self.close_btn = QPushButton("Close")
        self.save_to_file_btn = QPushButton("Save to File")
        self.save_to_file_btn.clicked.connect(self.saveToFile)

    def _setupSignals(self):
        self.close_btn.clicked.connect(self.close)
    
    def _setupLayouts(self):
        # Bottom
        self.buttons_hb = QHBoxLayout()
        self.buttons_hb.addItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))
        self.buttons_hb.addWidget(self.save_to_file_btn)
        self.buttons_hb.addWidget(self.close_btn)

        self.buttons_hb.setStretch(0, 2)
        self.buttons_hb.setStretch(1, 1)
        self.buttons_hb.setStretch(2, 2)

        # Layout
        self.main_lt = QVBoxLayout()
        self.main_lt.addWidget(self.exceptions_t)
        self.main_lt.addLayout(self.buttons_hb)
        self.setLayout(self.main_lt)

        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        self.setWindowTitle("Exceptions Occurred")
        self.setWindowIcon(QIcon(ICON_SVG))
        self.resize(700, 352)

    def addItem(self, id_str: str, exception: str, source: str) -> None:
        item = QTreeWidgetItem()

        item.setText(0, id_str)
        item.setTextAlignment(0, Qt.AlignCenter)
        item.setText(1, exception)
        item.setText(2, source)

        self.exceptions_t.addTopLevelItem(item)

    def clear(self) -> None:
        self.exceptions_t.clear()

    def saveToFile(self) -> None:
        if self.isEmpty():
            message_box.info(self, "Empty List", "Exception list is empty, there is nothing to save.")
            return

        options = QFileDialog.Options()
        if platform.system() == "Darwin":
            # On macOS, clicking "Cancel" on a file dialog, automatically closes the parent widget if it's modal.
            # Using self.setModal(False) prevents the parent from being closed, but the focus returns to the main window, not to the previous dialog.
            # Linux and Windows are fine. This problem is caused by a macOS feature.
            options |= QFileDialog.DontUseNativeDialog

        dlg, _ = QFileDialog.getSaveFileUrl(
            parent=self,
            caption="Save Exceptions",
            dir=QUrl.fromLocalFile(os.path.expanduser("~/xl_converter_exceptions.csv")),
            filter="CSV (*.csv)",
            options=options,
        )

        if not dlg.isValid():
            return
        
        rows = [
            ("Version", VERSION),
            ("OS", platform.system()),
            ("Exceptions",),
            ("Err Location", "Exception", "Filename"),
        ]

        rows.extend([
            (
                self.exceptions_t.topLevelItem(i).text(0),
                self.exceptions_t.topLevelItem(i).text(1),
                self.exceptions_t.topLevelItem(i).text(2),
            ) for i in range(self.exceptions_t.topLevelItemCount())
        ])

        self._writeCsv(dlg.toLocalFile(), rows)

    def _writeCsv(self, file_path: str, rows: list[tuple[str, ...]]) -> None:
        """Internal methods for writing CSV file."""
        try:
            with open(file_path, "w", newline="", encoding="utf-8") as csv_file:
                writer = csv.writer(csv_file, quoting=csv.QUOTE_MINIMAL)
                writer.writerows(rows)
        except OSError as e:
            message_box.info(self, "Error", "Failed to save file", str(e))

    def resizeToContent(self) -> None:
        self.exceptions_t.resizeColumnToContents(0)
    
    def isEmpty(self) -> bool:
        return self.exceptions_t.topLevelItemCount() == 0
    
    def reset(self) -> None:
        """Runs close() then clear()."""
        self.close()
        self.clear()
