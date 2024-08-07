import logging

from PySide6.QtCore import QThreadPool

class ThreadManager:
    def __init__(self, threadpool: QThreadPool) -> None:
        self.threadpool = threadpool
    
        self.threads_per_worker = 1
        self.burst_threadpool = []
    
    def configure(self, format: str, item_count: int, used_thread_count: int, mode="Performance") -> None:
        if mode == "Performance":
            self.burst_threadpool = self._getBurstThreadPool(
                item_count,
                used_thread_count,
            )
            self.threadpool.setMaxThreadCount(used_thread_count)  
        elif mode == "Low RAM":
            self.burst_threadpool = []
            self.threads_per_worker = used_thread_count
            self.threadpool.setMaxThreadCount(1)
        else:
            logging.error(f"[ThreadManager - configure] Mode not recognized ({mode})")

    def getAvailableThreads(self, index: int) -> int:
        if self.burst_threadpool:
            try:
                available_threads = self.burst_threadpool[index]
            except IndexError:
                logging.error("[ThreadManager] getAvailableThreads - IndexError")
                available_threads = self.threads_per_worker
        else:
            available_threads = self.threads_per_worker
        
        return available_threads

    def _getBurstThreadPool(self, workers: int, cores: int) -> list:
        """
        Distributes cores among workers to fully utilize the available cores.

        Args:
            workers - worker count
            cores - available core count
        
        Returns (examples):
            (3, 6) -> [2,2,2]
            (3, 5) -> [2,2,1]
            (2, 5) -> [3,2]
            (5, 5) -> []
            (6, 5) -> []

            If workers >= cores outputs an empty list 
        """
        if workers >= cores or cores <= 0 or workers <= 0:
            return []
        
        base_threads = cores // workers
        extra_threads = cores % workers
        thread_pool = [base_threads for _ in range(workers)]
        
        for i in range(extra_threads):
            thread_pool[i] += 1
        
        return thread_pool