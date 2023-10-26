import subprocess, psutil

VERBOSE = False

class Process():
    def __init__(self):
        pass
    
    def runProcess(self, cmd):
        if VERBOSE:
            print(f"Running command: {cmd}")
            subprocess.run(cmd, shell=True)
        else:
            subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    
    def runProcessFromPath(self, cmd, path):
        """Run process from the specified directory."""
        if VERBOSE:
            print(f"Running command from \"{path}\": {cmd}")
            subprocess.run(cmd, shell=True, cwd=path)
        else:
            subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT, cwd=path)

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