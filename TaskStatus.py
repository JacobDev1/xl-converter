# Module-wide global variable

class Status:
    canceled = False

def wasCanceled():
    return Status.canceled

def cancel():
    Status.canceled = True

def reset():
    Status.canceled = False