import subprocess, psutil
from VARIABLES import PROCESS_LOGS, PROCESS_LOGS_VERBOSE

VERBOSE = False

class Process():
    def __init__(self):
        pass
    
    def runProcess(self, cmd):
        """Run process."""
        if PROCESS_LOGS:
            print(f"Running command: {cmd}")

        if PROCESS_LOGS_VERBOSE:
            subprocess.run(cmd, shell=True)
        else:
            subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    
    def runProcessFromPath(self, cmd, path):
        """Run process from the specified directory."""
        if PROCESS_LOGS:
            print(f"Running command from \"{path}\": {cmd}")
        
        if PROCESS_LOGS_VERBOSE:
            subprocess.run(cmd, shell=True, cwd=path)
        else:
            subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT, cwd=path)

    def runProcessOutput(self, cmd):
        """Run process then return its output."""
        if PROCESS_LOGS:
            print(f"Running command with output: {cmd}")

        out = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL).stdout
        if PROCESS_LOGS_VERBOSE:
            print(out)
        return out

    def killProcess(self, pid):
        process = psutil.Process(pid)
        for proc in process.children(recursive=True):
            proc.kill()
        process.kill()
    
    def runProcessTimeout(self, cmd, timeout):
        """Run process, but kill it If it runs for too long.
        
        Args:
            cmd - command
            timeout - in seconds
        """
        proc = None
        if VERBOSE:
            print(f"Running command: {cmd}")
            proc = subprocess.Popen(cmd, shell=True)
        else:
            proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        
        try:
            proc.wait(timeout=timeout)
        except:
            self.killProcess(proc.pid)
            self.log(f"Process timed out ({command})", n)