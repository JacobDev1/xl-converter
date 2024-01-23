class GenericException(Exception):
    def __init__(self, id, msg):
        self.id = id
        self.msg = msg

class FileException(Exception):
    def __init__(self, id, msg):
        self.id = id
        self.msg = msg

class CancellationException(Exception):
    pass