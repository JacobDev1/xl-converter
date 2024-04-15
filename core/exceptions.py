class GenericException(Exception):
    def __init__(self, id: str, msg: str):
        self.id = id
        self.msg = msg

class FileException(Exception):
    def __init__(self, id: str, msg: str):
        self.id = id
        self.msg = msg

class CancellationException(Exception):
    pass