from unittest.mock import patch, call

import pytest
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QPointF, QPoint
from PySide6.QtGui import QMouseEvent, QCursor

from ui.scroll_area import ScrollArea

@pytest.fixture
def app(qtbot):
    app = QApplication.instance()
    if not app:
        app = QApplication([])

    scroll = ScrollArea()
    qtbot.addWidget(scroll)
    return scroll

def test_init(app):
    assert app.horizontalScrollBarPolicy() == Qt.ScrollBarAlwaysOff
    assert app.verticalScrollBarPolicy() == Qt.ScrollBarAsNeeded

def test_enable_horizontal_scroll(qtbot):
    scroll_area = ScrollArea(enable_horizontal=True)
    qtbot.addWidget(scroll_area)
    assert scroll_area.horizontalScrollBarPolicy() == Qt.ScrollBarAsNeeded

def test_enable_vertical_scroll(qtbot):
    scroll_area = ScrollArea(enable_vertical=False)
    qtbot.addWidget(scroll_area)
    assert scroll_area.horizontalScrollBarPolicy() == Qt.ScrollBarAlwaysOff

def test_mousePressEvent(app):
    app.mousePressEvent(QMouseEvent(QMouseEvent.MouseButtonPress, QPointF(0, 0), QCursor.pos(), Qt.LeftButton, Qt.LeftButton, Qt.NoModifier))

    assert app.is_dragging
    assert app.cursor().shape() == Qt.ClosedHandCursor

def test_mouseReleaseEvent(app):
    app.mousePressEvent(QMouseEvent(QMouseEvent.MouseButtonPress, QPointF(0, 0), QCursor.pos(), Qt.LeftButton, Qt.LeftButton, Qt.NoModifier))
    app.mouseReleaseEvent(QMouseEvent(QMouseEvent.MouseButtonRelease, QPointF(0, 0), QCursor.pos(), Qt.LeftButton, Qt.LeftButton, Qt.NoModifier))

    assert app.is_dragging == False
    assert app.cursor().shape() == Qt.ArrowCursor

# Why?
# QtWarningMsg: Mouse event "MousePress" not accepted by receiving widget
# QtWarningMsg: Mouse event "MouseMove" not accepted by receiving widget
# def test_mouseMoveEvent_2(app, qtbot):
#     qtbot.mousePress(app, Qt.LeftButton, pos=QPoint(0, 0))
#     qtbot.mouseMove(app, pos=QPoint(0, 100))
#     assert app.last_position.y() == 100

def test_mouseMoveEvent(app):
    app.mousePressEvent(QMouseEvent(QMouseEvent.MouseButtonPress, QPointF(0, 0), QCursor.pos(), Qt.LeftButton, Qt.LeftButton, Qt.NoModifier))
    app.mouseMoveEvent(QMouseEvent(QMouseEvent.MouseMove, QPointF(0, 100), QCursor.pos(), Qt.LeftButton, Qt.LeftButton, Qt.NoModifier))

    assert app.last_position.y() == 100