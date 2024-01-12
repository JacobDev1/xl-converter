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
    if process.stdout:
        logging.debug(process.stdout.decode())
    if process.stderr:
        logging.debug(process.stderr.decode())

def runProcessOutput(*cmd):
    """Run process then return its output."""
    logging.info(f"Running command with output: {cmd}")

    process = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, startupinfo=_getStartupInfo())
    if process.stdout:
        logging.error("[Process] Output is empty")
        logging.debug(process.stdout.decode())
    if process.stderr:
        logging.debug(process.stderr.decode())    

    return process.stdout