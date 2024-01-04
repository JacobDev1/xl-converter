import subprocess

from data.constants import PROCESS_LOGS, PROCESS_LOGS_VERBOSE

def runProcess(*cmd):
    """Run process."""
    if PROCESS_LOGS:
        print(f"Running command: {cmd}")

    if PROCESS_LOGS_VERBOSE:
        subprocess.run(cmd)
    else:
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

def runProcessFromPath(*cmd, path):
    """Run process from the specified directory."""
    if PROCESS_LOGS:
        print(f"Running command from \"{path}\": {cmd}")
    
    if PROCESS_LOGS_VERBOSE:
        subprocess.run(cmd, cwd=path)
    else:
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT, cwd=path)

def runProcessOutput(*cmd):
    """Run process then return its output."""
    if PROCESS_LOGS:
        print(f"Running command with output: {cmd}")

    out = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL).stdout
    if PROCESS_LOGS_VERBOSE:
        print(out)
    return out