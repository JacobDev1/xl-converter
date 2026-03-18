import logging
from unittest.mock import patch, MagicMock
from contextlib import ExitStack

import pytest
from PySide6.QtCore import QThreadPool

import core.ram_optimizer as ram_optimizer
from core.ram_optimizer import RAMOptimizer, OptimizationRule

@pytest.fixture(autouse=True)
def reset_singleton():
    RAMOptimizer._instance = None
    RAMOptimizer.enabled = False
    RAMOptimizer.used_thread_count = None
    RAMOptimizer.rules = []
    with patch.object(QThreadPool, 'globalInstance', MagicMock(return_value=MagicMock(spec=QThreadPool))):
        RAMOptimizer()  # Init
        yield

def test_singleton_instance():
    assert RAMOptimizer() == RAMOptimizer()

@pytest.mark.parametrize("enabled", [True, False])
def test_isEnabled(enabled):
    RAMOptimizer.setEnabled(enabled)
    assert RAMOptimizer.enabled == enabled

@pytest.mark.parametrize("enabled", [True, False])
def test_isEnabled(enabled):
    RAMOptimizer.enabled = enabled
    assert RAMOptimizer.isEnabled() == enabled

def test_setUsedThreadCount_valid(caplog):
    RAMOptimizer.used_thread_count = 1
    RAMOptimizer.setUsedThreadCount(16)
    assert RAMOptimizer.used_thread_count == 16

def test_setUsedThreadCount_invalid(caplog):
    caplog.set_level(logging.ERROR)
    RAMOptimizer.used_thread_count = 1
    RAMOptimizer.setUsedThreadCount(-1)
    assert "Expected used_thread_count >= 1" in caplog.text
    assert RAMOptimizer.used_thread_count == 1

def test_setOptimizationRules():
    rules = [OptimizationRule("all", 10, "1/2")]
    RAMOptimizer.setOptimizationRules(rules)
    assert RAMOptimizer.rules == rules

@pytest.mark.parametrize("rules_str, expected_dataclasses", [
    ('("all", 10, "1/2")', [OptimizationRule("all", 10.0, "1/2")]),
    ('("all", 8.0, "3/4")', [OptimizationRule("all", 8.0, "3/4")]),
    ('("all", 3.5, "3/4"), ("all", 7.5, "2/4"), ("all", 11, "1/4"), ("all", 14, "1")', [OptimizationRule("all", 3.5, "3/4"), OptimizationRule("all", 7.5, "2/4"), OptimizationRule("all", 7.5, "2/4"), OptimizationRule("all", 14.0, "1")]),
    ('("all", b, "1/2")', []),
    ('("all", -10, "1/2")', []),
    ('("all", 10, "1/0")', []),
    ('("all", 10, "0/1")', []),
    ('("all", 10, "0")', []),
    ('("unsupported", 10, "1/2")', []),
])
def test_parseOptimizationRules_results(rules_str, expected_dataclasses):
    parsed_rules = RAMOptimizer.parseOptimizationRules(rules_str)
    for rule in expected_dataclasses:
        assert rule in parsed_rules

def test_setOptimizationRulesStr_rules_parsed(caplog):
    caplog.set_level(logging.INFO)
    rules = '("all", 10.0, "1/2")'
    rules_native = [OptimizationRule("all", 10.0, "1/2") for _ in range(3)]

    with (
        patch("core.ram_optimizer.RAMOptimizer.parseOptimizationRules", return_value=rules_native) as mock_parseOptimizationRules,
        patch("core.ram_optimizer.RAMOptimizer.setOptimizationRules") as mock_setOptimizationRules,
    ):
        RAMOptimizer.setOptimizationRulesStr(rules)
        mock_setOptimizationRules(rules_native)
        mock_parseOptimizationRules.assert_called_once_with(rules)
        assert "Successfully parsed 3 rules" in caplog.text

def test_setOptimizationRulesStr_no_rules(caplog):
    caplog.set_level(logging.INFO)

    with (
        patch("core.ram_optimizer.RAMOptimizer.parseOptimizationRules", return_value=[]) as mock_parseOptimizationRules,
        patch("core.ram_optimizer.RAMOptimizer.setOptimizationRules") as mock_setOptimizationRules,
    ):
        RAMOptimizer.setOptimizationRulesStr('')
        assert "No rules found" in caplog.text

@pytest.mark.parametrize("rule_scope, file_format, avif_encoder, expected_to_apply", [
    ("all", "JPEG XL", "", True),
    ("JPEG XL", "JPEG XL", "", True),
    ("SVT-AV1-PSY", "JPEG XL", "", False),
    ("JPEG XL", "AVIF", "SVT-AV1-PSY", False),
    ("SVT-AV1-PSY", "AVIF", "SVT-AV1-PSY", True),
    ("all", "AVIF", "SVT-AV1-PSY", True),
    ("SVT-AV1-PSY", "AVIF", "AOM AV1", False),
])
def test__doesRuleApply(rule_scope, file_format, avif_encoder, expected_to_apply):
    assert RAMOptimizer._doesRuleApply(
        OptimizationRule(rule_scope, 10.0, "1"),
        file_format,
        avif_encoder
    ) == expected_to_apply

def test_applicableRuleExists_exists():
    RAMOptimizer.rules = [
        OptimizationRule("all", 10.0, "1/2"),
        OptimizationRule("all", 14.0, "1")
    ]

    with patch("core.ram_optimizer.RAMOptimizer._doesRuleApply", side_effect=(False, True)) as mock__doesRuleApply:
        assert RAMOptimizer.applicableRuleExists("", "") == True
        assert mock__doesRuleApply.call_count == 2
        assert str(mock__doesRuleApply.call_args_list[0][0][0]) == str(RAMOptimizer.rules[0])
        assert str(mock__doesRuleApply.call_args_list[1][0][0]) == str(RAMOptimizer.rules[1])

def test_applicableRuleExists_no_rules(caplog):
    RAMOptimizer.rules = []
    caplog.set_level(logging.INFO)

    with patch("core.ram_optimizer.RAMOptimizer._doesRuleApply") as mock__doesRuleApply:
        assert RAMOptimizer.applicableRuleExists("", "") == False
        mock__doesRuleApply.assert_not_called()
        assert "No applicable rules found" in caplog.text

def test__getMaxWorkerCount_apply_rule_1():
    RAMOptimizer.rules = [
        OptimizationRule("all", 10.0, "1/2"),
        OptimizationRule("all", 14.0, "1")
    ]
    RAMOptimizer.used_thread_count = 16

    with patch("core.ram_optimizer.RAMOptimizer._doesRuleApply", return_value=True):
        assert RAMOptimizer._getMaxWorkerCount(14.0, "JPEG XL", "") == 1

def test__getMaxWorkerCount_apply_rule_fraction():
    RAMOptimizer.rules = [
        OptimizationRule("all", 8.0, "3/4"),
        OptimizationRule("all", 10.0, "1/2"),
        OptimizationRule("all", 14.0, "1")
    ]
    RAMOptimizer.used_thread_count = 16

    with patch("core.ram_optimizer.RAMOptimizer._doesRuleApply", side_effect=(False, True,)):
        assert RAMOptimizer._getMaxWorkerCount(10.0, "JPEG XL", "") == 16 * 3 // 4

def test__getMaxWorkerCount_invalid_worker_count():
    RAMOptimizer.rules = [
        OptimizationRule("all", 8.0, "1/2")
    ]
    RAMOptimizer.used_thread_count = -1

    with patch("core.ram_optimizer.RAMOptimizer._doesRuleApply", return_value=True):
        assert RAMOptimizer._getMaxWorkerCount(10.0, "JPEG XL", "") == 1

def test__getMaxWorkerCount_div_error(caplog):
    RAMOptimizer.rules = [
        OptimizationRule("all", 8.0, "1/0")
    ]
    RAMOptimizer.used_thread_count = 1

    with patch("core.ram_optimizer.RAMOptimizer._doesRuleApply", return_value=True):
        assert RAMOptimizer._getMaxWorkerCount(10.0, "JPEG XL", "") == 1
        assert "Applying rule failed" in caplog.records[0].message

def test__getMaxWorkerCount_no_rules():
    RAMOptimizer.rules = []
    RAMOptimizer.used_thread_count = 4

    assert RAMOptimizer._getMaxWorkerCount(10.0, "JPEG XL", "") == 4

@pytest.fixture
def run_patches():
    mocks = {
        "setEnabled": patch("core.ram_optimizer.RAMOptimizer.setEnabled"),
        "_getMaxWorkerCount": patch("core.ram_optimizer.RAMOptimizer._getMaxWorkerCount", return_value=4),
        "convert.getImageResMp": patch("core.ram_optimizer.convert.getImageResMp", return_value=10.0),
    }

    with ExitStack() as stack:
        _mocks = {name: stack.enter_context(patcher) for name, patcher in mocks.items()}
        yield _mocks

@pytest.mark.parametrize("check", [
    "disabled", "used_thread_count_none", "empty_rules"
])
def test_run_checks(check, run_patches, caplog):
    mocks = run_patches
    caplog.set_level(logging.INFO)
    RAMOptimizer.enabled = False if check == "disabled" else True
    RAMOptimizer.used_thread_count = None if check == "used_thread_count_none" else 4
    RAMOptimizer.rules = [] if check == "empty_rules" else ["stub"]
    org_threads_per_worker = 4
    
    assert RAMOptimizer.run(
        thread_count_per_worker=org_threads_per_worker,
        src_image_path="/tmp/image.jpg",
        dst_file_format="JPEG XL",
        avif_encoder="",
        jpeg_xl_effort=7,
        jpeg_xl_lossy_modular=False,
        jpeg_xl_lossless=False,
        jpeg_xl_intelligent_effort=False,
    ) == org_threads_per_worker
    
    RAMOptimizer.threadpool.assert_not_called()
    if check in {"used_thread_count_none", "empty_rules"}:
        mocks["setEnabled"].assert_called_once_with(False)
    else:
        mocks["setEnabled"].assert_not_called()

    mocks["convert.getImageResMp"].assert_not_called()

def test_run_happy_path(run_patches, caplog):
    mocks = run_patches
    caplog.set_level(logging.INFO)

    dst_file_format = "JPEG XL"
    src_image_path = "/tmp/image.jpg"
    avif_encoder = "encoder"
    org_threads_per_worker = 16
    used_thread_count = 16
    optimized_thread_count = 8
    image_res = 10.0
    
    RAMOptimizer.enabled = True
    RAMOptimizer.used_thread_count = used_thread_count
    RAMOptimizer.rules = ["stub"]
    mocks["_getMaxWorkerCount"].return_value = optimized_thread_count
    mocks["convert.getImageResMp"].return_value = image_res

    assert RAMOptimizer.run(
        thread_count_per_worker=org_threads_per_worker,
        src_image_path=src_image_path,
        dst_file_format=dst_file_format,
        avif_encoder=avif_encoder,
        jpeg_xl_effort=7,
        jpeg_xl_lossy_modular=False,
        jpeg_xl_lossless=False,
        jpeg_xl_intelligent_effort=False,
    ) == used_thread_count // optimized_thread_count

    mocks["setEnabled"].assert_not_called()
    mocks["convert.getImageResMp"].assert_called_once_with(src_image_path)
    mocks["_getMaxWorkerCount"].assert_called_once_with(image_res, dst_file_format, avif_encoder)
    RAMOptimizer.threadpool.setMaxThreadCount.assert_called_once_with(optimized_thread_count)
    assert "Max concurrent workers" in caplog.records[0].message

def test_run_invalid_res(run_patches):
    mocks = run_patches

    used_thread_count = 16
    
    RAMOptimizer.enabled = True
    RAMOptimizer.used_thread_count = used_thread_count
    RAMOptimizer.rules = ["stub"]
    mocks["convert.getImageResMp"].return_value = -1.0

    assert RAMOptimizer.run(
        thread_count_per_worker=4,
        src_image_path="/tmp/image.jpg",
        dst_file_format="JPEG XL",
        avif_encoder="",
        jpeg_xl_effort=7,
        jpeg_xl_lossy_modular=False,
        jpeg_xl_lossless=False,
        jpeg_xl_intelligent_effort=False,
    ) == 4

    mocks["convert.getImageResMp"].assert_called_once()
    mocks["_getMaxWorkerCount"].assert_not_called()
    RAMOptimizer.threadpool.setMaxThreadCount.assert_called_once_with(1)

@pytest.mark.parametrize("high_ram_usage", [
    True, False
])
def test_isNecessary_jpeg_xl(high_ram_usage):
    jpeg_xl_args = [7, False, False, False]
    with patch("core.ram_optimizer.jpegXlHighRamUsage", return_value=high_ram_usage) as mock_jpegXlHighRamUsage:
        assert RAMOptimizer.isNecessary("JPEG XL", "", *jpeg_xl_args) == high_ram_usage
        mock_jpegXlHighRamUsage.assert_called_once_with(*jpeg_xl_args)

@pytest.mark.parametrize("dst_file_format, encoder, expected", [
    ("AVIF", "AOM AV1", False),
    ("AVIF", "SVT-AV1-PSY", True),
    ("AVIF", "", False),
])
def test_isNecessary_avif(dst_file_format, encoder, expected):
    assert RAMOptimizer.isNecessary(
        dst_file_format, encoder, 7, False, False, False
    ) == expected

@pytest.mark.parametrize("dst_file_format", [
    "JPEG",
    "WebP",
    "PNG",
])
def test_isNecessary_other(dst_file_format):
    assert RAMOptimizer.isNecessary(dst_file_format, "", 7, False, False, False) == False

@pytest.mark.parametrize("effort, jxl_modular, lossless, intelligent_effort, expected", [
    # VarDCT
    (0, False, False, False, False),    # Low RAM
    (7, False, False, False, False),
    (8, False, False, False, True),     # High RAM
    (9, False, False, False, True),
    (10, False, False, False, True),
    (7, False, False, True, True),      # Int. effort
    (9, False, False, True, True),

    # Lossy Modular
    (7, True, False, False, True),
    (9, True, False, False, True),
    (10, True, False, False, True),
    (7, True, False, True, True),

    # Lossless
    (7, False, True, False, False),     # Low RAM
    (9, False, True, False, False),
    (10, False, True, False, True),     # High RAM
    (7, False, True, True, False),      # Int. effort
    (9, False, True, True, False),
])
def test_jpegXlHighRamUsage(effort, jxl_modular, lossless, intelligent_effort, expected):
    assert ram_optimizer.jpegXlHighRamUsage(
        effort, jxl_modular, lossless, intelligent_effort
    ) == expected
