import logging

from PySide6.QtCore import QThreadPool

class ThreadManager:
    def __init__(self, threadpool: QThreadPool) -> None:
        self.threadpool = threadpool
    
        self.fixed_threads = 1
        self.burst_threadpool = []
    
    def configure(self, format: str, item_count: int, used_thread_count: int) -> None:
        if format == "AVIF":    # Use encoder-based multithreading 
            self.fixed_threads = used_thread_count
            self.burst_threadpool = []
            self.threadpool.setMaxThreadCount(1)
        else:
            self.fixed_threads = 1
            self.burst_threadpool = self._getBurstThreadPool(
                item_count,
                used_thread_count,
            )
            self.threadpool.setMaxThreadCount(used_thread_count)  

    def getAvailableThreads(self, index: int) -> int:
        if self.burst_threadpool:
            try:
                available_threads = self.burst_threadpool[index]
            except IndexError:
                logging.error("[ThreadManager] getAvailableThreads - IndexError")
                available_threads = self.fixed_threads
        else:
            available_threads = self.fixed_threads
        
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