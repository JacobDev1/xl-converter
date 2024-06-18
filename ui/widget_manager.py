import os
import json
import logging
from typing import Any

from PySide6.QtWidgets import QWidget, QLineEdit, QComboBox, QTextEdit, QCheckBox, QRadioButton, QSlider, QSpinBox

from data.constants import CONFIG_LOCATION, VERSION

class WidgetManager():
    """A powerful widget manager.
    
    Features:
        saving & loading with minimal effort.
        tags - iterate easily through groups of widgets or set states.
        variables - for saving multi-purpose widgets.
    """
    def __init__(self, name):
        self.name = name         # Unique identifier for saving and loading states
        self.widgets = {}        # id: widget
        self.tags = {}           # tag: [id]
        self.variables = {}      # var: value
        self.exceptions = []     # [id, id]... for manually saving 

        self.save_state_path = os.path.join(CONFIG_LOCATION, f"{name}.json")

        # Create Config Folder
        try:
            os.makedirs(CONFIG_LOCATION, exist_ok=True)
        except OSError as err:
            self.error(f"Cannot create a config folder. {err}", "__init__")
    
    def addWidget(self, _id: str, widget, *tags):
        if not isinstance(widget, QWidget):
            self.error(f"Object type is not QWidget ({type(widget)})", "addWidget")
            return None

        self.widgets[_id] = widget

        for tag in tags:
            self.addTag(tag, _id)
        
        return widget
    
    def getWidget(self, _id: str):
        if _id in self.widgets:
            return self.widgets[_id]
        else:
            self.error(f"Widget not found ({_id})", "getWidget")
            return None
    
    # TAGS

    def addTag(self, tag: str, _id: str):
        if not _id in self.widgets:
            self.error(f"Widget not found ({_id})", "addTag")
            return

        if tag in self.tags:
            self.tags[tag].extend([_id])
        else:
            self.tags[tag] = [_id]
    
    def addTags(self, _id: str, *tags: list[str]):
        if not _id in self.widgets:
            self.error(f"Widget not found ({_id})", "addTags")
            return
        
        for tag in tags:
            self.addTag(tag, _id)

    def getWidgetsByTag(self, tag: str):
        if not tag in self.tags:
            self.error(f"Tag not found ({tag})", "getWidgetsByTag")
            return []
        
        return [self.getWidget(i) for i in self.tags[tag]]

    def setEnabledByTag(self, tag: str, enabled: bool):
        if not tag in self.tags:
            self.error(f"Tag not found ({tag})", "setEnabledByTag")
            return
        
        for widget in self.getWidgetsByTag(tag):
            widget.setEnabled(enabled)

    def setVisibleByTag(self, tag: str, enabled: bool):
        if not tag in self.tags:
            self.error(f"Tag not found ({tag})", "setVisibleByTag")
            return
        
        for widget in self.getWidgetsByTag(tag):
            widget.setVisible(enabled)

    def setCheckedByTag(self, tag: str, checked: bool):
        if not tag in self.tags:
            self.error(f"Tag not found ({tag})", "setCheckedByTag")
            return

        for widget in self.getWidgetsByTag(tag):
            if self._getWidgetSubclass(widget) in ("QCheckBox", "QRadioBox"):
                widget.setChecked(checked)

    # VARIABLES

    def setVar(self, var: str, value: Any):
        self.variables[var] = value

    def getVar(self, var: str) -> Any:
        if not var in self.variables:
            self.error(f"Var not found ({var})", "getVar")
            return None

        return self.variables[var]

    def applyVar(self, var: str, widget_id: str, fallback: Any):
        """Apply a (variable) onto an (item) with a (fallback) value if the variable doesn't exist.
        
        Arguments:
            var - variable name
            widget_id - id of a widget the var will be applied onto
            fallback - alternative value If variable does not exist
        """
        if not widget_id in self.widgets:
            self.error(f"Widget not found ({widget_id})", "applyVar")
            return

        if var in self.variables:
            new = self.getVar(var)
        else:
            new = fallback
        
        self._applyValue(widget_id, new)

    def cleanVars(self):
        self.variables = {}

    def _applyValue(self, _id, val):
        """For internal use only. Applies value based on a class name."""
        widget = self.getWidget(_id)     # Pointer
        
        if widget is None:
            self.error(f"Widget not found ({_id})", "_applyValue")
            return
        
        widget_class = self._getWidgetSubclass(widget)

        # Verify value type
        val_mismatch = False
        if widget_class in ("QLineEdit", "QComboBox", "QTextEdit"):
            if not type(val) is str:
                val_mismatch = True
        elif widget_class in ("QCheckBox", "QRadioButton"):
            if not type(val) is bool:
                val_mismatch = True
        elif widget_class in ("QSlider", "QSpinBox"):
            if not type(val) is int:
                val_mismatch = True

        if val_mismatch:
            self.error(f"Type mismatch (Tried applying {type(val)} onto [{_id}: {widget_class}])", "_applyValue")
            return

        # Apply
        match widget_class:
            case "QCheckBox":
                widget.setChecked(val)
            case "QSlider":
                widget.setValue(val)
            case "QSpinBox":
                widget.setValue(val)
            case "QComboBox":
                index = widget.findText(val)
                if index == -1: # If not found
                    index = 0
                widget.setCurrentIndex(index)
            case "QRadioButton":
                widget.setChecked(val)
            case "QLineEdit":
                widget.setText(val)
            case "QTextEdit":
                widget.setPlainText(val)
            case _:
                self.error(f"Unsupported widget class ({widget_class})", "_applyValue")

    def _getWidgetSubclass(self, widget) -> str:
        supported_widgets = (QCheckBox, QSpinBox, QComboBox, QTextEdit, QSlider, QRadioButton, QLineEdit)     # Sorted by popularity
        
        for w in supported_widgets:
            if isinstance(widget, w):
                return w.__name__
        return widget.__class__.__name__

    # SAVING

    def disableAutoSaving(self, *ids: str):
        for _id in ids:
            if not _id in self.widgets:
                self.error(f"Widget not found ({_id})", "disableAutoSaving")
            else:
                self.exceptions.extend(ids)

    def saveState(self):
        if not os.path.isdir(CONFIG_LOCATION):
            self.error(f"Config location not found ({CONFIG_LOCATION})", "saveState")
            return
        
        widget_states = {}
        for key in self.widgets:
            if key in self.exceptions:
                continue
            
            match self._getWidgetSubclass(self.widgets[key]):
                case "QCheckBox":
                    widget_states[key] = self.widgets[key].isChecked()
                case "QSlider":
                    widget_states[key] = self.widgets[key].value()
                case "QSpinBox":
                    widget_states[key] = self.widgets[key].value()
                case "QComboBox":
                    widget_states[key] = self.widgets[key].currentText()    # Text (not index) in case order was changed
                case "QRadioButton":
                    widget_states[key] = self.widgets[key].isChecked()
                case "QLineEdit":
                    widget_states[key] = self.widgets[key].text()
                case "QTextEdit":
                    widget_states[key] = self.widgets[key].toPlainText()
                # Unsupported widget get skipped when saving.

        if not widget_states and not self.variables:   # If empty
            return
        
        output = {
            "version": VERSION,
            "widgets": widget_states,
            "variables": self.variables
        }

        try:
            with open(self.save_state_path, "w", encoding="utf-8") as f:
                f.writelines(json.dumps(output, indent=4))
        except OSError as err:
            self.error(err, "saveState")

    def loadState(self):
        if not os.path.isfile(self.save_state_path):
            return

        # Load JSON        
        loaded = ""
        try:
            with open(self.save_state_path, "r", encoding="utf-8") as f:
                try:
                    loaded = json.load(f)
                except:
                    self.error("Parsing JSON failed. Cannot load saved states.", "loadState")
                    return
        except OSError as err:
            self.error(f"Loading file failed ({err})", "loadState")
            return

        # Load variables
        if "variables" in loaded:
            if type(loaded["variables"]) == dict:
                self.variables = loaded["variables"]
            else:
                self.error(f"Type mismatch. Expected dictionary, got {type(loaded['variables'])}", "loadState")

        # Load widget states
        if "widgets" in loaded:
            if type(loaded["widgets"]) == dict:
                widgets = loaded["widgets"]
                for key in widgets:
                    if key not in self.widgets:
                        self.error(f"Unrecognized widget id ({key})", "loadState")
                        continue
                    
                    self._applyValue(key, widgets[key])
            else:
                self.error(f"Type mismatch. Expected dictionary, got {type(loaded['widgets'])}", "loadState")
    
    # MISC.

    def wipeSettings(self):
        try:
            if os.path.isfile(self.save_state_path):
                os.remove(self.save_state_path)
        except OSError as err:
            self.error(err, "wipeSettings")
    
    def error(self, msg: str, func_name: str):
        logging.error(f"[WidgetManager - {func_name}] {msg}")

    def exit(self):
        """Purges all widgets and other elements from memory."""
        for key in self.widgets:
            self.widgets[key].deleteLater()
        self.widgets = {}
        self.cleanVars()
        self.exceptions = {}
        self.tags = {}