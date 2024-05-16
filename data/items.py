from pathlib import Path
import logging

from data.constants import ALLOWED_INPUT

class Items():
    def __init__(self):
        self.items = []
        self.item_count = 0
        self.completed_item_count = 0

    def parseData(self, *items):
        """Populate the structure with proper data."""
        for abs_path, anchor_path in items:
            abs_path = Path(abs_path)
            ext = abs_path.suffix[1:]
    
            if ext.lower() not in ALLOWED_INPUT:
                logging.error(f"[Items] Extension not allowed ({ext})")
                continue

            if not isinstance(anchor_path, Path):
                logging.error(f"[Items] anchor_path is not a Path object ({type(anchor_path)})")
                continue

            self.items.append(
                (
                    abs_path,
                    anchor_path,
                )
            )
        
        self.item_count = len(self.items)

    def getItem(self, n) -> Path:
        return self.items[n]

    def getItemCount(self) -> int:
        return self.item_count

    def getCompletedItemCount(self) -> int:
        return self.completed_item_count
    
    def addCompletedItem(self):
        self.completed_item_count += 1

    def clear(self):
        self.items = []
        self.completed_item_count = 0
        self.item_count = 0