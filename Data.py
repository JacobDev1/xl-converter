from HelperFunctions import stripPathToFilename

class Data():
    def __init__(self):
        self.items = []
        self.item_count = 0
        self.completed_items = []

    def __str__(self):
        output = ""
        for i in range(0,self.item_count):
            output += str(self.items[i][0]) + " | "
            output += str(self.items[i][1]) + " | "
            output += str(self.items[i][2]) + "\n"
        return output

    def parseData(self, root, allowed):  # root type is QTreeWidget.invisibleRootItem()
        """Populates the structure with proper data."""
        for i in range(root.childCount()):
            item = root.child(i)
            file_data = stripPathToFilename(item.text(2))
            if file_data[1].lower() in allowed:
                self.items.append(file_data)
            else:
                print(f"[Data] File not allowed for current format ({file_data[3]})")
        self.item_count = len(self.items)

    def getItem(self, n):
        return self.items[n]

    def getItemCount(self):
        return self.item_count
    
    def getCompletedItemsCount(self):
        return len(self.completed_items)

    def appendCompletedItem(self, n):
        self.completed_items.append(n)
    
    def clear(self):
        self.items = []
        self.completed_items = []
        self.item_count = 0