import subprocess
from VARIABLES import PROCESS_LOGS, PROCESS_LOGS_VERBOSE

def runProcess(cmd):
    """Run process."""
    if PROCESS_LOGS:
        print(f"Running command: {cmd}")

    if PROCESS_LOGS_VERBOSE:
        subprocess.run(cmd, shell=True)
    else:
        subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

def runProcessFromPath(cmd, path):
    """Run process from the specified directory."""
    if PROCESS_LOGS:
        print(f"Running command from \"{path}\": {cmd}")
    
    if PROCESS_LOGS_VERBOSE:
        subprocess.run(cmd, shell=True, cwd=path)
    else:
        subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT, cwd=path)

def runProcessOutput(cmd):
    """Run process then return its output."""
    if PROCESS_LOGS:
        print(f"Running command with output: {cmd}")

    out = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL).stdout
    if PROCESS_LOGS_VERBOSE:
        print(out)
    return out