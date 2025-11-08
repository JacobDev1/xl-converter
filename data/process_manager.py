import threading
import subprocess
import platform
import logging
from enum import StrEnum, auto

import psutil

logger = logging.getLogger(__name__)
SYSTEM = platform.system()

class ProcessManager:
    processes = []
    lock = threading.Lock()

    @classmethod
    def addProcess(cls, process: subprocess.Popen | psutil.Popen) -> None:
        if not isinstance(process, (subprocess.Popen, psutil.Popen)):
            raise TypeError("Process must be a subprocess.Popen object")

        with cls.lock:
            cls.processes.append(process)

    @classmethod
    def removeProcess(cls, process: subprocess.Popen | psutil.Popen) -> None:
        if not isinstance(process, (subprocess.Popen, psutil.Popen)):
            raise TypeError("Process must be a subprocess.Popen object")

        with cls.lock:
            try:
                cls.processes.remove(process)
            except ValueError:
                pass

    @classmethod
    def terminateAll(cls) -> None:
        with cls.lock:
            processes_to_terminate = cls.processes.copy()
            cls.processes.clear()

        for process in processes_to_terminate:
            process.terminate()

        for process in processes_to_terminate:
            process.wait()

    @classmethod
    def clear(cls) -> None:
        with cls.lock:
            cls.processes.clear()

class ProcessPriority(StrEnum):
    IDLE = auto()
    BELOW_NORMAL = auto()
    NORMAL = auto()
    ABOVE_NORMAL = auto()
    HIGH = auto()
    # REALTIME is not needed for this program.

class ProcessPriorityManager:
    """Stores process priority state."""
    priority: ProcessPriority = ProcessPriority.NORMAL
    lock = threading.Lock()
    _PROCESS_PRIORITY_MAP: dict[ProcessPriority, int] = {}

    if SYSTEM == "Windows":
        _PROCESS_PRIORITY_MAP: dict[ProcessPriority, int] = {
            ProcessPriority.IDLE: psutil.IDLE_PRIORITY_CLASS,
            ProcessPriority.BELOW_NORMAL: psutil.BELOW_NORMAL_PRIORITY_CLASS,
            ProcessPriority.NORMAL: psutil.NORMAL_PRIORITY_CLASS,
            ProcessPriority.ABOVE_NORMAL: psutil.ABOVE_NORMAL_PRIORITY_CLASS,
            ProcessPriority.HIGH: psutil.HIGH_PRIORITY_CLASS,
        }
    elif SYSTEM in ("Linux", "Darwin"):
        _PROCESS_PRIORITY_MAP: dict[ProcessPriority, int] = {
            ProcessPriority.IDLE: 19 if SYSTEM == "Linux" else 19,
            ProcessPriority.BELOW_NORMAL: 10,
            ProcessPriority.NORMAL: 0,
            # IMPORTANT: Negative niceness requires elevated privileges on Unix.
            ProcessPriority.ABOVE_NORMAL: -5,
            ProcessPriority.HIGH: -10,
        }

    @classmethod
    def setPriority(cls, priority: ProcessPriority) -> None:
        with cls.lock:
            cls.priority = priority

    @classmethod
    def getPriorityFlag(cls) -> int | None:
        """Returns a priority flag compatible with .nice() method for the current OS. Returns None if priority is unmapped."""
        with cls.lock:
            flag = cls._PROCESS_PRIORITY_MAP.get(cls.priority)
            if flag is None:
                logger.error(f"[getPriorityFlag] Priority not mapped ({cls.priority})")
            return flag
