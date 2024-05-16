from unittest.mock import patch, MagicMock
import json

import pytest
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QVBoxLayout,
    QCheckBox,
    QLineEdit,
    QTextEdit,
    QRadioButton,
    QSlider,
    QSpinBox,
    QComboBox,
)

from ui.widget_manager import WidgetManager

class Widget(QWidget):
    def __init__(self):
        super().__init__()
        self.wm = WidgetManager("unit_test")

@pytest.fixture
def app(qtbot):
    app = QApplication.instance()
    if not app:
        app = QApplication([])

    with patch("ui.widget_manager.open"), \
        patch("os.makedirs"):
        w = Widget()
        qtbot.addWidget(w)
        return w

@patch("ui.widget_manager.CONFIG_LOCATION")
@patch("os.makedirs")
def test_init(mock_makedirs, mock_CONFIG_LOCATION):
    wm = WidgetManager("test")
    mock_makedirs.assert_called_once_with(mock_CONFIG_LOCATION, exist_ok=True)

@patch("ui.widget_manager.CONFIG_LOCATION")
@patch("os.makedirs", side_effect=OSError("file error"))
def test_init_failed(mock_makedirs, mock_CONFIG_LOCATION, caplog):
    WidgetManager("test")
    assert "Cannot create a config folder." in caplog.text

def test_addWidget(app):
    text_l = QLabel()
    assert app.wm.addWidget("text_l", text_l) is text_l
    assert app.wm.widgets["text_l"] is text_l

def test_addWidget_with_tags(app):
    text_l = QLabel()
    assert app.wm.addWidget("text_l", text_l, "tag_0", "tag_1") is text_l
    assert app.wm.widgets["text_l"] is text_l
    assert app.wm.tags["tag_0"][0] == "text_l"
    assert app.wm.tags["tag_1"][0] == "text_l"

def test_addWidget_type_mismatch(caplog, app):
    assert app.wm.addWidget("test_l", None) is None
    assert "Object type is not QWidget" in caplog.text

def test_getWidget(app):
    text_l = QLabel()
    app.wm.addWidget("text_l", text_l)
    assert app.wm.getWidget("text_l") is text_l

def test_getWidget_no_widget(caplog, app):
    assert app.wm.getWidget("text_l") is None
    assert "Widget not found (text_l)" in caplog.text

def test_addTag_new(app):
    text_l = QLabel()
    app.wm.addWidget("text_l", text_l)
    app.wm.addTag("tag_0", "text_l")
    assert app.wm.tags["tag_0"] == ["text_l"]

def test_addTag_exists(app):
    text_l = QLabel()
    text_2_l = QLabel()
    app.wm.addWidget("text_l", text_l)
    app.wm.addWidget("text_2_l", text_2_l)
    app.wm.addTag("tag_0", "text_l")
    app.wm.addTag("tag_0", "text_2_l")
    tag_0 = app.wm.tags["tag_0"]
    assert "text_l" in tag_0
    assert "text_2_l" in tag_0

def test_addTag_no_widget(caplog, app):
    app.wm.addTag("tag_0", "text_l")
    assert "Widget not found" in caplog.text

def test_addTag(app):
    text_l = QLabel() 
    text_2_l = QLabel()
    app.wm.addWidget("text_l", text_l)
    app.wm.addWidget("text_2_l", text_2_l)
    app.wm.addTags("text_l", "tag_0", "tag_1")
    app.wm.addTags("text_2_l", "tag_0", "tag_1")
    tag_0 = app.wm.tags["tag_0"]
    tag_1 = app.wm.tags["tag_1"]
    assert "text_l" in tag_0
    assert "text_2_l" in tag_0
    assert "text_l" in tag_1
    assert "text_2_l" in tag_1

def test_addTag_no_widget(caplog, app):
    app.wm.addTags("text_l", "tag_0", "tag_1")
    assert "Widget not found" in caplog.text

def test_getWidgetsByTag(app):
    text_l = QLabel()
    text_2_l = QLabel()
    app.wm.addWidget("text_l", text_l)
    app.wm.addWidget("text_2_l", text_2_l)
    app.wm.addTag("tag_0", "text_l")
    app.wm.addTag("tag_0", "text_2_l")
    out = app.wm.getWidgetsByTag("tag_0")
    assert text_l in out
    assert text_2_l in out

def test_getWidgetsByTag_no_tag(caplog, app):
    out = app.wm.getWidgetsByTag("tag_0")
    assert "Tag not found" in caplog.text

def test_setEnabledByTag(app):
    text_l = QLabel()
    text_2_l = QLabel()
    app.wm.addWidget("text_l", text_l, "tag_0")
    app.wm.addWidget("text_2_l", text_2_l, "tag_0")
    app.wm.setEnabledByTag("tag_0", False)
    widgets = app.wm.getWidgetsByTag("tag_0")

    assert widgets != []
    for w in widgets:
        assert w.isEnabled() == False

def test_setEnabledByTag_no_tag(caplog, app):
    app.wm.setEnabledByTag("tag_0", False)
    assert "Tag not found" in caplog.text

def test_setVisibleByTag(app):
    text_l = QLabel()
    text_2_l = QLabel()
    layout = QVBoxLayout()
    layout.addWidget(text_l)
    layout.addWidget(text_2_l)
    app.setLayout(layout)
    app.wm.addWidget("text_l", text_l, "tag_0")
    app.wm.addWidget("text_2_l", text_2_l, "tag_0")
    assert text_l.isVisibleTo(app)
    assert text_2_l.isVisibleTo(app)
    
    app.wm.setVisibleByTag("tag_0", False)
    widgets = app.wm.getWidgetsByTag("tag_0")

    assert widgets != []
    for w in widgets:
        assert w.isVisibleTo(app) == False

def test_setVisibleByTag_no_tag(caplog, app):
    app.wm.setVisibleByTag("tag_0", False)
    assert "Tag not found" in caplog.text

def test_setCheckedByTag_qcheckbox(app):
    sample_cb = QCheckBox()
    app.wm.addWidget("sample_cb", sample_cb, "tag_0")
    app.wm.setCheckedByTag("tag_0", True)

    assert app.wm.getWidget("sample_cb").isChecked()

def test_setCheckedByTag_qcombobox(app):
    sample_cmb = QCheckBox()
    app.wm.addWidget("sample_cmb", sample_cmb, "tag_0")
    app.wm.setCheckedByTag("tag_0", True)

    assert app.wm.getWidget("sample_cmb").isChecked()

def test_setCheckedByTag_no_tag(caplog, app):
    app.wm.setCheckedByTag("tag_0", False)
    assert "Tag not found" in caplog.text

def test_getVar(app):
    app.wm.setVar("sample_var", 10)
    assert app.wm.getVar("sample_var") == 10

def test_getVar_no_var(caplog, app):
    app.wm.getVar("sample_var")
    assert "Var not found" in caplog.text

def test_applyVar(app):
    app.wm._applyValue = MagicMock()
    app.wm.addWidget("widget_l", QLabel())
    app.wm.setVar("sample_var", 1)
    app.wm.applyVar("sample_var", "widget_l", 0)
    app.wm._applyValue.assert_called_once_with("widget_l", 1)

def test_applyVar_no_widget(caplog, app):
    app.wm._applyValue = MagicMock()
    app.wm.applyVar("sample_var", "widget_l", 0)
    assert "Widget not found" in caplog.text

def test_applyVar_no_var(app):
    app.wm._applyValue = MagicMock()
    app.wm.addWidget("widget_l", QLabel())
    app.wm.applyVar("sample_var", "widget_l", 0)
    app.wm._applyValue.assert_called_once_with("widget_l", 0)

@pytest.mark.parametrize("widget, value, get_method", [
    (QLineEdit, "test", "text"),
    (QComboBox, "test", "currentText"),
    (QTextEdit, "test", "toPlainText"),
    (QCheckBox, True, "isChecked"),
    (QRadioButton, True, "isChecked"),
    (QSlider, 50, "value"),
    (QSpinBox, 50, "value"),
])
def test__applyValue(widget, value, get_method, caplog, app):
    w = widget()
    if w.__class__.__name__ == "QComboBox":
        w.addItems(["test1", "test"])

    app.wm.addWidget("widget", w)
    app.wm._applyValue("widget", value)
    assert "Type mismatch" not in caplog.text
    assert "Unsupported widget" not in caplog.text
    assert getattr(w, get_method)() == value

@pytest.mark.parametrize("widget, value, get_method", [
    (QLineEdit, True, "text"),
    (QComboBox, True, "currentText"),
    (QTextEdit, True, "toPlainText"),
    (QCheckBox, "test", "isChecked"),
    (QRadioButton, "test", "isChecked"),
    (QSlider, False, "value"),
    (QSpinBox, False, "value"),
])
def test__applyValue_value_mismatch(widget, value, get_method, caplog, app):
    w = widget()

    app.wm.addWidget("widget", w)
    app.wm._applyValue("widget", value)
    assert "Type mismatch" in caplog.text

def test__applyValue_unsupported_widget_type(caplog, app):
    app.wm.addWidget("widget", QWidget())
    app.wm._applyValue("widget", 10)
    assert "Unsupported widget" in caplog.text

def test__applyValue_cmb_text_not_found(app):
    w = QComboBox()
    w.addItems(["one", "two"])

    app.wm.addWidget("w_cmb", w)
    app.wm._applyValue("w_cmb", "three")
    assert w.currentIndex() == 0

def test__applyValue_no_widget(caplog, app):
    app.wm._applyValue("sample", 1)
    assert "Widget not found" in caplog.text

def test_cleanVars(app):
    app.wm.setVar("var", 1)
    app.wm.cleanVars()
    assert app.wm.variables == {}

def test_disableAutoSaving(app):
    app.wm.addWidget("text_1_l", QLabel())
    app.wm.addWidget("text_2_l", QLabel())
    app.wm.disableAutoSaving("text_1_l", "text_2_l")
    assert "text_1_l" in app.wm.exceptions
    assert "text_2_l" in app.wm.exceptions

def test_disableAutoSaving_no_widget(caplog, app):
    app.wm.addWidget("text_1_l", QLabel())
    app.wm.disableAutoSaving("text_1_l", "text_2_l")
    assert "text_1_l" in app.wm.exceptions
    assert "Widget not found (text_2_l)" in caplog.text

@patch("ui.widget_manager.os.path.isdir", return_value=False)
def test_saveState_not_dir_CONFIG_LOCATION(mock_isdir, caplog, app):
    app.wm.saveState()
    assert "Config location not found" in caplog.text

@patch("ui.widget_manager.os.path.isdir", return_value=True)
@patch("ui.widget_manager.open")
def test_saveState(mock_open, mock_isdir, app):
    cb = QCheckBox()
    sl = QSlider()
    sb = QSpinBox()
    cmb = QComboBox()
    cmb.addItems(["item_0", "item_1"])
    rb = QRadioButton()
    le = QLineEdit()
    te = QTextEdit()

    cb.setChecked(True)
    sl.setValue(50)
    sb.setValue(50)
    cmb.setCurrentIndex(1)
    rb.setChecked(True)
    le.setText("sample_0")
    te.setText("sample_1")

    app.wm.addWidget("cb", cb)
    app.wm.addWidget("sl", sl)
    app.wm.addWidget("sb", sb)
    app.wm.addWidget("cmb", cmb)
    app.wm.addWidget("rb", rb)
    app.wm.addWidget("le", le)
    app.wm.addWidget("te", te)
    app.wm.setVar("var_0", 50)
    app.wm.setVar("var_1", False)

    app.wm.saveState()

    written_json = json.loads(mock_open.return_value.__enter__.return_value.writelines.call_args[0][0])

    assert written_json["widgets"]["cb"] == cb.isChecked()
    assert written_json["widgets"]["sl"] == sl.value()
    assert written_json["widgets"]["sb"] == sb.value()
    assert written_json["widgets"]["cmb"] == cmb.currentText()
    assert written_json["widgets"]["rb"] == rb.isChecked()
    assert written_json["widgets"]["le"] == le.text()
    assert written_json["widgets"]["te"] == te.toPlainText()
    assert written_json["variables"]["var_0"] == 50
    assert written_json["variables"]["var_1"] == False

@patch("ui.widget_manager.os.path.isdir", return_value=True)
@patch("ui.widget_manager.open")
def test_saveState_exceptions(mock_open, mock_isdir, app):
    cb1 = QCheckBox()
    cb2 = QCheckBox()
    app.wm.addWidget("cb1", cb1)
    app.wm.addWidget("cb2", cb2)
    app.wm.disableAutoSaving("cb2")

    app.wm.saveState()

    written_json = json.loads(mock_open.return_value.__enter__.return_value.writelines.call_args[0][0])
    assert "cb1" in written_json["widgets"]
    assert not "cb2" in written_json["widgets"]

@patch("ui.widget_manager.os.path.isdir", return_value=True)
@patch("ui.widget_manager.open")
def test_saveState_empty(mock_open, mock_isdir, app):
    app.wm.saveState()
    mock_open.return_value.__enter__.return_value.writelines.assert_not_called()

@patch("ui.widget_manager.WidgetManager._applyValue")
@patch("ui.widget_manager.json.load")
@patch("ui.widget_manager.os.path.isfile", return_value=True)
@patch("ui.widget_manager.open")
def test_loadState(mock_open, mock_isfile, mock_json_load, mock__applyValue, app):
    app.wm.addWidget("cb", QCheckBox())

    sample_dict = {
        "widgets": {
            "cb": True,
        },
        "variables": {
            "var_0": False,
        },
    }
    mock_json_load.return_value = sample_dict
    app.wm.loadState()
    assert app.wm.variables == sample_dict["variables"]
    mock__applyValue.assert_called_once_with("cb", True)

@patch("ui.widget_manager.WidgetManager._applyValue")
@patch("ui.widget_manager.json.load")
@patch("ui.widget_manager.os.path.isfile", return_value=True)
@patch("ui.widget_manager.open")
def test_loadState_empty(mock_open, mock_isfile, mock_json_load, mock__applyValue, app):
    mock_json_load.return_value = {}
    app.wm.loadState()
    mock__applyValue.assert_not_called()

@patch("ui.widget_manager.os.path.isfile")
@patch("ui.widget_manager.os.remove")
def test_wipeSettings(mock_remove, mock_isfile, app):
    app.wm.save_state_path = MagicMock(return_value="/path/to/state.json")
    app.wm.wipeSettings()
    mock_remove.assert_called_once_with(app.wm.save_state_path)

def test_error(caplog, app):
    app.wm.error("error", "func")
    assert "error" in caplog.text
    assert "func" in caplog.text

def test_exit(app):
    app.wm.cleanVars = MagicMock()

    mock_w1 = MagicMock(spec=QLabel)
    mock_w2 = MagicMock(spec=QLabel)

    app.wm.addWidget("w1", mock_w1, "sample_tag")
    app.wm.addWidget("w2", mock_w2)
    app.wm.disableAutoSaving("w1")

    app.wm.exit()

    mock_w1.deleteLater.assert_called_once()
    mock_w2.deleteLater.assert_called_once()
    app.wm.cleanVars.assert_called_once()
    assert app.wm.widgets == {}
    assert app.wm.exceptions == {}
    assert app.wm.tags == {}