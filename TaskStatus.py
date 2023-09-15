# Module-wide global variable
canceled = [False]
# This needs to stay as a list. Otherwise, Python will create multiple copies

def wasCanceled():
    return canceled[0]

def cancel():
    canceled[0] = True

def reset():
    canceled[0] = False