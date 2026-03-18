from contextlib import ExitStack
from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtCore import QThreadPool

from data.thread_manager import ThreadManager

@pytest.fixture
def thread_manager():
    pool = QThreadPool()
    pool.setMaxThreadCount = MagicMock(return_value=None)
    pool.maxThreadCount = MagicMock()
    return ThreadManager(pool)

@pytest.fixture
def configure_patches(thread_manager):
    mocks = {
        "RAMOptimizer.setEnabled": patch("data.thread_manager.RAMOptimizer.setEnabled"),
        "RAMOptimizer.isNecessary": patch("data.thread_manager.RAMOptimizer.isNecessary", return_value=False),
        "RAMOptimizer.setOptimizationRulesStr": patch("data.thread_manager.RAMOptimizer.setOptimizationRulesStr"),
        "RAMOptimizer.applicableRuleExists": patch("data.thread_manager.RAMOptimizer.applicableRuleExists", return_value=False),
        "RAMOptimizer.setUsedThreadCount": patch("data.thread_manager.RAMOptimizer.setUsedThreadCount"),
        "_getBurstThreadPool": patch("data.thread_manager.ThreadManager._getBurstThreadPool", return_value=[]),
    }

    with ExitStack() as stack:
        _mocks = {name: stack.enter_context(patcher) for name, patcher in mocks.items()}
        yield thread_manager, _mocks

def test_configure_no_optimizer_necessary(configure_patches):
    thread_manager, mocks = configure_patches
    thread_manager.threads_per_worker = 1

    thread_manager.configure(1, 10, "Static", "", "", "", 1, False, False, False)

    assert thread_manager.threads_per_worker == 1
    thread_manager.threadpool.setMaxThreadCount.assert_called_once()

def test_configure_burst_threadpool(configure_patches):
    thread_manager, mocks = configure_patches
    used_thread_count = 10
    item_count = 3
    burst_threadpool = [4, 3, 3]
    mocks["_getBurstThreadPool"].return_value = burst_threadpool

    thread_manager.configure(item_count, used_thread_count, "Static", "", "", "", 1, False, False, False)

    assert thread_manager.burst_threadpool == burst_threadpool
    thread_manager.threadpool.setMaxThreadCount.assert_called_once_with(used_thread_count)
    mocks["_getBurstThreadPool"].assert_called_once_with(item_count, used_thread_count)

def test_configure_optimizer_static(configure_patches):
    thread_manager, mocks = configure_patches
    used_thread_count = 10
    thread_manager.burst_threadpool = [4, 3, 3]
    mocks["RAMOptimizer.isNecessary"].return_value = True

    thread_manager.configure(1, used_thread_count, "Static", "", "", "", 1, False, False, False)

    assert thread_manager.burst_threadpool == []
    assert thread_manager.threads_per_worker == used_thread_count
    thread_manager.threadpool.setMaxThreadCount.assert_called_once_with(1)

def test_configure_optimizer_dynamic_args(configure_patches):
    thread_manager, mocks = configure_patches
    rules, dst_format, avif_encoder, used_thread_count = "(\"all\", 10, 1)", "AVIF", "SVT-AV1-PSY", 10
    mocks["RAMOptimizer.applicableRuleExists"].return_value = True
    mocks["RAMOptimizer.isNecessary"].return_value = True

    thread_manager.configure(3, used_thread_count, "Dynamic", rules, dst_format, avif_encoder, 1, False, False, False)

    assert mocks["RAMOptimizer.setEnabled"].call_count == 2
    assert mocks["RAMOptimizer.setEnabled"].call_args_list[1][0][0] == True
    mocks["RAMOptimizer.setOptimizationRulesStr"].assert_called_once_with(rules)
    mocks["RAMOptimizer.applicableRuleExists"].assert_called_once_with(dst_format, avif_encoder)
    mocks["RAMOptimizer.setUsedThreadCount"].assert_called_once_with(used_thread_count)
    mocks["_getBurstThreadPool"].assert_not_called()

def test_configure_optimizer_dynamic_no_args(configure_patches):
    thread_manager, mocks = configure_patches
    mocks["RAMOptimizer.applicableRuleExists"].return_value = False
    mocks["RAMOptimizer.isNecessary"].return_value = True

    thread_manager.configure(3, 10, "Dynamic", "", "", "", 1, False, False, False)

    assert mocks["RAMOptimizer.setEnabled"].call_count == 1
    assert mocks["RAMOptimizer.setEnabled"].call_args_list[0][0][0] == False
    mocks["RAMOptimizer.setOptimizationRulesStr"].assert_called_once()
    mocks["RAMOptimizer.applicableRuleExists"].assert_called_once()
    mocks["_getBurstThreadPool"].assert_called_once()

def test_configure_optimizer_disabled(configure_patches):
    thread_manager, mocks = configure_patches
    mocks["RAMOptimizer.isNecessary"].return_value = True

    thread_manager.configure(1, 1, "Disabled", "", "", "", 1, False, False, False)

    thread_manager._getBurstThreadPool.assert_called_once()

def test_configure_optimizer_unknown(configure_patches, caplog):
    thread_manager, mocks = configure_patches
    mocks["RAMOptimizer.isNecessary"].return_value = True

    thread_manager.configure(1, 1, "Unknown", "", "", "", 1, False, False, False)

    assert "Unrecognized ram_optimizer_mode" in caplog.records[0].message
    thread_manager._getBurstThreadPool.assert_called_once()

def test_getAvailableThreads_burst(thread_manager):
    burst_threadpool = [3, 2, 2]
    thread_manager.burst_threadpool = burst_threadpool
    thread_manager.threads_per_worker = 1
    
    for i, value in enumerate(burst_threadpool):
        assert thread_manager.getAvailableThreads(i) == burst_threadpool[i]
    
    for i in range(len(burst_threadpool), 10):
        assert thread_manager.getAvailableThreads(i) == 1

def test_getAvailableThreads_static(thread_manager, caplog):
    burst_threadpool = []
    thread_manager.threads_per_worker = 1
    
    for i in range(10):
        assert thread_manager.getAvailableThreads(i) == 1

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
