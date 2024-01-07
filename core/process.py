import subprocess
import os

from data.constants import PROCESS_LOGS, PROCESS_LOGS_VERBOSE

def _getStartupInfo():
    """Get startup info for Windows. Prevents console window from showing."""
    startupinfo = None
    if os.name == 'nt':
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE
    return startupinfo

def runProcess(*cmd):
    """Run process."""
    if PROCESS_LOGS:
        print(f"Running command: {cmd}")

    if PROCESS_LOGS_VERBOSE:
        subprocess.run(cmd, startupinfo=_getStartupInfo())
    else:
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT, startupinfo=_getStartupInfo())

def runProcessFromPath(*cmd, path):
    """Run process from the specified directory."""
    if PROCESS_LOGS:
        print(f"Running command from \"{path}\": {cmd}")
    
    if PROCESS_LOGS_VERBOSE:
        subprocess.run(cmd, cwd=path, startupinfo=_getStartupInfo())
    else:
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT, cwd=path, startupinfo=_getStartupInfo())

def runProcessOutput(*cmd):
    """Run process then return its output."""
    if PROCESS_LOGS:
        print(f"Running command with output: {cmd}")

    out = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, startupinfo=_getStartupInfo()).stdout
    if PROCESS_LOGS_VERBOSE:
        print(out)
    return out