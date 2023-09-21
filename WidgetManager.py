from VARIABLES import CONFIG_LOCATION
import os, json

class WidgetManager():
    """Widget manager. Supports tags and saving states to file."""
    def __init__(self, name):
        self.name = name    # Unique indentifier for saving and loading states
        self.widgets = {}   # id: widget
        self.tags = {}      # tag: [id]

        self.save_lock_path = os.path.join(CONFIG_LOCATION, "saving_disabled")
        self.save_state_path = os.path.join(CONFIG_LOCATION, f"{name}.json")

        # Create Config Folder
        try:
            os.makedirs(CONFIG_LOCATION, exist_ok=True)
        except OSError as err:
            self.log(f"{err}\nCannot create a config folder.")
    
    def addWidget(self, id: str, widget):
        self.widgets[id] = widget
    
    def getWidget(self, id: str):
        return self.widgets[id]
    
    def addTag(self, tag: str, id: str):
        if tag in self.tags:
            self.tags[tag].extend(id)
        else:
            self.tags[tag] = [id]
    
    def getWidgetsByTag(self, tag: str):
        return self.tags[tag]

    def saveState(self):
        if not os.path.isdir(CONFIG_LOCATION):
            return
        
        widget_states = {}
        for key in self.widgets:
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

        try:
            with open(self.save_state_path, "w") as file:
                file.writelines(json.dumps(widget_states, indent=4))
        except OSError as err:
            self.log(err)

    def loadState(self):
        if self.isSavingDisabled() or not os.path.isfile(self.save_state_path):
            return

        # Load JSON        
        loaded = ""
        try:
            with open(self.save_state_path, "r") as file:
                loaded = json.load(file)
        except OSError as err:
            self.log(err)

        # Set values
        for key in loaded:
            if key not in self.widgets:
                self.log(f"Unrecognized widget id ({key})")
                continue
                        
            match self.widgets[key].__class__.__name__:
                case "QCheckBox":
                    self.getWidget(key).setChecked(loaded[key])
                case "QSlider":
                    self.widgets[key].setValue(loaded[key])
                case "QSpinBox":
                    self.widgets[key].setValue(loaded[key])
                case "QComboBox":
                    index = self.widgets[key].findText(loaded[key])
                    if index == -1: # If not found
                        index = 0
                    self.widgets[key].setCurrentIndex(index)
                case "QRadioButton":
                    self.widgets[key].setChecked(loaded[key])
                case "QLineEdit":
                    self.widgets[key].setText(loaded[key])
                case _:
                    self.log(f"Unrecognized widget type ({key}: {loaded[key]})")
        
    def deleteState(self):
        try:
            os.remove(self.save_state_path)
        except OSError as err:
            self.log(err)

    def enableSaving(self):
        try:
            os.remove(self.save_lock_path)
        except OSError as err:
            self.log(err)

    def disableSaving(self):
        if isSavingDisabled():
            return

        try:
            open(self.save_lock_path, "a").close()
        except OSError as err:
            self.log(err)

    def isSavingDisabled(self):
        return os.path.isfile(self.save_lock_path)
    
    def wipeSettings(self):
        try:
            if self.isSavingDisabled():
                os.remove(self.save_lock_path)
            if os.path.isfile(self.save_state_path):
                os.remove(self.save_state_path)
        except OSError as err:
            self.log(err)
    
    def log(self, msg):
        print(f"[WidgetManager] [{self.name}] {msg}")