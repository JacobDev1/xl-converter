from VARIABLES import CONFIG_LOCATION, VERSION
import os, json

class WidgetManager():
    """A powerful widget manager.
    
    Features:
        saving & loading with minimal effort.
        tags - iterate easily through groups of widgets or set states.
        variables - for saving multi-purpose widgets.
    """
    def __init__(self, name):
        self.name = name         # Unique indentifier for saving and loading states
        self.widgets = {}        # id: widget
        self.tags = {}           # tag: [id]
        self.variables = {}      # var: value
        self.exceptions = []     # [id, id]... for manually saving 

        self.save_state_path = os.path.join(CONFIG_LOCATION, f"{name}.json")

        # Create Config Folder
        try:
            os.makedirs(CONFIG_LOCATION, exist_ok=True)
        except OSError as err:
            self.log(f"{err}\nCannot create a config folder.")
    
    def addWidget(self, _id: str, widget, *tags):
        self.widgets[_id] = widget

        for tag in tags:
            self.addTag(tag, _id)
    
    def getWidget(self, _id: str):
        if _id in self.widgets:
            return self.widgets[_id]
        else:
            return None
    
    # TAGS

    def addTag(self, tag: str, _id: str):
        if tag in self.tags:
            self.tags[tag].extend([_id])
        else:
            self.tags[tag] = [_id]
    
    def addTags(self, _id: str, *tags):
        for tag in tags:
            self.addTag(tag, _id)

    def getWidgetsByTag(self, tag: str):
        widgets = []
        for i in self.tags[tag]:
            widgets.append(self.getWidget(i))
        return widgets

    def setEnabledByTag(self, tag, enabled):
        for widget in self.getWidgetsByTag(tag):
            widget.setEnabled(enabled)

    def setVisibleByTag(self, tag, enabled):
        for widget in self.getWidgetsByTag(tag):
            widget.setVisible(enabled)

    def setCheckedByTag(self, tag, checked):
        for widget in self.getWidgetsByTag(tag):
            if widget.__class__.__name__ in ("QCheckBox", "QRadioBox"):
                widget.setChecked(checked)

    # VARIABLES

    def setVar(self, var: str, value):
        self.variables[var] = value

    def getVar(self, var):
        if var in self.variables:
            return self.variables[var]
        else:
            return None

    def applyVar(self, var_name, _id, fallback):
        """Apply a (variable) onto an (item) with a (fallback) value if the variable doesn't exist.
        
        Arguments:
            var_name - variable name
            id - id of an item the var will be applied onto
            fallback - alternative value If variable does not exist
        """
        new = self.getVar(var_name)
        if new == None:
            new = fallback
        
        self._applyValue(_id, new)

    def cleanVars(self):
        self.variables = {}

    # SAVING

    def disableAutoSaving(self, ids: []):
        self.exceptions.extend(ids)

    def saveState(self):
        if not os.path.isdir(CONFIG_LOCATION):
            return
        
        widget_states = {}
        for key in self.widgets:
            if key in self.exceptions:
                continue

            match self.widgets[key].__class__.__name__:
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

        if not widget_states:   # If empty
            return
        
        output = {
            "version": VERSION,
            "widgets": widget_states,
            "variables": self.variables
        }

        try:
            with open(self.save_state_path, "w") as file:
                file.writelines(json.dumps(output, indent=4))
        except OSError as err:
            self.log(err)

    def loadState(self):
        if not os.path.isfile(self.save_state_path):
            return

        # Load JSON        
        loaded = ""
        try:
            with open(self.save_state_path, "r") as file:
                try:
                    loaded = json.load(file)
                except:
                    self.log("Parsing JSON failed. Cannot load saved states.")
                    return
        except OSError as err:
            self.log(err)

        if "variables" in loaded:
            if not isinstance(loaded["variables"], dict):
                self.log(f"Type mismatch. Expected dictionary, got {type(loaded['variables'])}")
                return
            self.variables = loaded["variables"]

        # Set values
        if "widgets" in loaded:
            if not isinstance(loaded["widgets"], dict):
                self.log(f"Type mismatch. Expected dictionary, got {type(loaded['widgets'])}")
                return

            widgets = loaded["widgets"]
            for key in widgets:
                if key not in self.widgets:
                    self.log(f"Unrecognized widget id ({key})")
                    continue
                
                self._applyValue(key, widgets[key])
    
    # MISC.

    def wipeSettings(self):
        try:
            if os.path.isfile(self.save_state_path):
                os.remove(self.save_state_path)
        except OSError as err:
            self.log(err)
    
    def log(self, msg):
        print(f"[WidgetManager - {self.name}] {msg}")
    
    def _applyValue(self, _id, val):
        """For internal use only. Applies value based on a class name."""
        widget = self.getWidget(_id)     # Pointer
        widget_class = widget.__class__.__name__

        # Verify value type
        val_mismatch = False
        if widget_class in ("QLineEdit", "QComboBox"):
            if not isinstance(val, str):
                val_mismatch = True
        elif widget_class in ("QCheckBox", "QRadioButton"):
            if not isinstance(val, bool):
                val_mismatch = True
        elif widget_class in ("QSlider", "QSpinBox"):
            if not isinstance(val, int):
                val_mismatch = True

        if val_mismatch:
            self.log(f"Type mismatch (Tried applying {type(val)} onto [{_id}: {widget_class}])")
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
            case _:
                self.log(f"Unrecognized widget type ({widget})")
    
    def exit(self):
        """Purges all widgets and other elements from memory."""
        for key in self.widgets:
            self.widgets[key].deleteLater()
        self.widgets = {}
        self.cleanVars()
        self.exceptions = {}
        self.tags = {}