import subprocess
import os
import logging

def _getStartupInfo():
    """Get startup info for Windows. Prevents console window from showing."""
    startupinfo = None
    if os.name == 'nt':
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE
    return startupinfo

def runProcess(*cmd, cwd=None):
    """Run process."""
    logging.info(f"Running command: {cmd}")

    process = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=_getStartupInfo(), cwd=cwd)
    
    try:
        if process.stdout:
            logging.debug(process.stdout.decode())
        if process.stderr:
            logging.debug(process.stderr.decode())
    except Exception as err:
        logging.error(f"Failed to decode process output. {err}")

def runProcessOutput(*cmd):
    """Run process then return its output."""
    logging.info(f"Running command with output: {cmd}")

    process = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, startupinfo=_getStartupInfo())

    try:
        if process.stdout:
            logging.debug(process.stdout.decode())
        if process.stderr:
            logging.debug(process.stderr.decode())    
    except Exception as err:
        logging.error(f"Failed to decode process output. {err}")

    return process.stdout