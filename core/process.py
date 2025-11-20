import subprocess
import platform
import logging

import psutil

from data.process_manager import ProcessManager, ProcessPriorityManager

SYSTEM = platform.system()

def runProcess2(*cmd: str, cwd: str | None = None) -> (str, str):
    """Replacement for runProcess() and runProcessOutput().
    
    Returns:
        (stdout, stderr)
    """
    logging.info(f"[runProcess2] {cmd}")

    if SYSTEM == "Windows":
        creationflags = subprocess.CREATE_NO_WINDOW
    else:
        creationflags = 0

    process = psutil.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=cwd,
        creationflags=creationflags,
    )

    _setProcessPriority(process, ProcessPriorityManager.getPriorityFlag())
    ProcessManager.addProcess(process)
    stdout, stderr = process.communicate()
    ProcessManager.removeProcess(process)

    try:
        if stdout:
            stdout = stdout.decode("utf-8")
            logging.info(f"[runProcess2] {stdout}")

        if stderr:
            stderr = stderr.decode("utf-8")
            logging.info(f"[runProcess2] {stderr}")
    except Exception as err:
        logging.error(f"[runProcess2] Failed to decode process output. {err}")

    return (stdout or "", stderr or "")

def _setProcessPriority(process: psutil.Popen, priority: int | None) -> None:
    """An internal function for setting the priority of a given process."""
    if priority is None:
        logging.error(f"[_setProcessPriority] Received None priority, ignoring.")
        return

    try:
        process.nice(priority)
    except psutil.NoSuchProcess:
        return
    except (psutil.Error, ValueError) as e:
        logging.error(f"[_setProcessPriority] Failed to set process priority: {e}")
        return

def runProcessOutput(*cmd, cwd=None) -> (str, str):
    """Run process then return its output.
    
    Output: (stdout, stderr)
    """
    logging.info(f"[runProcessOutput] {cmd}")

    if SYSTEM == "Windows":
        creationflags = subprocess.CREATE_NO_WINDOW
    else:
        creationflags = 0

    process = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        creationflags=creationflags,
        cwd=cwd
    )

    try:
        stdout, stderr = "", ""
        if process.stdout:
            stdout = process.stdout.decode("utf-8")
            logging.info(f"[runProcessOutput] {stdout}")
        if process.stderr:
            stderr = process.stderr.decode("utf-8")
            logging.info(f"[runProcessOutput] {stderr}")
    except Exception as err:
        logging.error(f"Failed to decode process output. {err}")

    return (stdout, stderr)
