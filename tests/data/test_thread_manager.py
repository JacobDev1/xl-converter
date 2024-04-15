from unittest.mock import MagicMock

import pytest
from PySide6.QtCore import QThreadPool

from data.thread_manager import ThreadManager

@pytest.fixture
def thread_manager():
    pool = QThreadPool()
    pool.setMaxThreadCount = MagicMock(return_value=None)
    pool.maxThreadCount = MagicMock()
    return ThreadManager(pool)

def test_configure_fixed(thread_manager):
    thread_manager.configure("AVIF", 5, 10)

    assert thread_manager.fixed_threads == 10
    assert thread_manager.burst_threadpool == []
    assert thread_manager.getAvailableThreads(0) == 10
    thread_manager.threadpool.setMaxThreadCount.assert_called_once_with(1)

def test_configure_dynamic(thread_manager):
    thread_manager.configure("JPEG XL", 5, 11)

    assert thread_manager.fixed_threads == 1
    assert thread_manager.burst_threadpool == [3, 2, 2, 2, 2]
    assert thread_manager.getAvailableThreads(0) == 3
    assert thread_manager.getAvailableThreads(1) == 2
    thread_manager.threadpool.setMaxThreadCount.assert_called_once_with(11)

def test_getAvailableThreads_burst(thread_manager):
    thread_manager.configure("JPEG XL", 5, 10)
    
    for i in range(5):
        assert thread_manager.getAvailableThreads(i) == 2

def test_getAvailableThreads_fixed(thread_manager):
    thread_manager.configure("AVIF", 5, 10)
    
    assert thread_manager.getAvailableThreads(0) == 10
    assert thread_manager.getAvailableThreads(5) == 10

def test_getAvailableThreads_index_error(thread_manager, caplog):
    thread_manager.configure("JPEG XL", 5, 10)
    
    assert thread_manager.getAvailableThreads(15) == 1
    assert "IndexError" in caplog.text

@pytest.mark.parametrize("workers, cores, expected", [
    (3, 7, [3, 2, 2]),
    (3, 6, [2, 2, 2]),
    (3, 5, [2, 2, 1]),
    (2, 5, [3, 2]),
    (4, 5, [2, 1, 1, 1]),
    (1, 10, [10]),
    (5, 5, []),
    (6, 5, []),
])
def test__getBurstThreadPool(workers, cores, expected, thread_manager):
    assert thread_manager._getBurstThreadPool(workers, cores) == expected