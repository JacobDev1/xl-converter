import os
from send2trash import send2trash

class Files():
    def __init__(self):
        pass

    def delete(self, path, trash=False):
        try:
            if trash:
                send2trash(path)
            else:
                os.remove(path)
        except OSError as err:
            print(f"[Error] Deleting file failed {err}")
            return False
        return True