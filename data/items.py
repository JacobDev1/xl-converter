from statistics import mean
from pathlib import Path
import os
import logging

from data.constants import ALLOWED_INPUT

EST_TIME_TRAIL_RANGE = 30

class Items():
    def __init__(self):
        self.items = []
        self.item_count = 0
        self.completed_items = []

        self.completion_times = []
        self.prev_completion_time = None

    def parseData(self, *items):
        """Populate the structure with proper data."""
        for item in items:
            try:
                path = Path(item).resolve()
                ext = path.suffix[1:]
            except Exception as e:
                logging.error(f"[Items] Error parsing item: {e}")
                continue

            if ext.lower() in ALLOWED_INPUT:
                self.items.append(path)
            else:
                logging.info(f"[Items] File not allowed for current format ({ext})")
        
        self.item_count = len(self.items)

    def getItem(self, n) -> Path:
        return self.items[n]

    def getItemCount(self) -> int:
        return self.item_count
    
    def getCommonPath(self) -> Path:
        """Computation heavy, use with caution. Returns None when there is no common path."""
        items_str = [str(path) for path in self.items]
        try:
            commonpath = Path(os.path.commonpath(items_str))
        except Exception as e:
            return None

        return commonpath

    def getCompletedItemCount(self) -> int:
        return len(self.completed_items)
    
    def getTimeRemainingText(self) -> str:
        completed_len = self.getCompletedItemCount()
        if completed_len < 2:
            return "Time left: <calculating>"

        # Extrapolate
        remaining = (self.getItemCount() - self.getCompletedItemCount()) * mean(self.completion_times)
        d = int(remaining / (3600 * 24))
        h = int((remaining // 3600) % 24)
        m = int((remaining // 60) % 60)
        s = int(remaining % 60)
        
        output = ""
        if d:   output += f"{d} d "
        if h:   output += f"{h} h "
        if m:   output += f"{m} m "
        if s:   output += f"{s} s"

        if output == "":
            output = "Almost done..."
        else:
            output += " left"

        return output
        
    def appendCompletionTime(self, n: float):
        if self.prev_completion_time != None:
            self.completion_times.append(n - self.prev_completion_time)
            if EST_TIME_TRAIL_RANGE < len(self.completion_times):
                self.completion_times.pop(0)

        self.prev_completion_time = n

    def appendCompletedItem(self, n):
        self.completed_items.append(n)
    
    def clear(self):
        self.items = []
        self.completed_items = []
        self.item_count = 0
        self.completion_times = []
        self.prev_completion_time = None
    
    def getStatusText(self):
        out = f"Converted {self.getCompletedItemCount()} out of {self.getItemCount()} images\n"
        out += self.getTimeRemainingText()
        return out