import logging
from dataclasses import dataclass
from typing import Literal, Optional
import os
import re

from PySide6.QtCore import (
    QThreadPool,
)

import core.convert as convert

@dataclass
class OptimizationRule:
    scope: Literal["all", "JPEG XL", "SVT-AV1-PSY"]     # Acivation scope. "all" means all applicable (after being filtered by RAMOptimizer.isNecessary)...
    threshold: float                                    # Activation threshold in megapixels.
    target: str                                         # The amount of concurrent encoders. Either 1 or a fraction. 

class RAMOptimizer:
    """Singleton for optimizing RAM. Not thread safe."""
    _instance: Optional["RAMOptimizer"] = None
    enabled: bool = False
    used_thread_count: Optional[int] = None
    rules: list[OptimizationRule] = []

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        RAMOptimizer.threadpool = QThreadPool.globalInstance()
    
    @classmethod
    def setEnabled(cls, enabled: bool) -> None:
        cls.enabled = enabled
    
    @classmethod
    def isEnabled(cls) -> bool:
        return cls.enabled

    @classmethod
    def setUsedThreadCount(cls, used_thread_count: int) -> None:
        """Set before using the optimizer."""
        if used_thread_count < 1:
            logging.error("[RAM Optimizer - setUsedThreadCount] Expected used_thread_count >= 1.")
            return
        cls.used_thread_count = used_thread_count

    @classmethod
    def setOptimizationRules(cls, rules: list[OptimizationRule]) -> None:
        cls.rules = rules

    @staticmethod
    def parseOptimizationRules(rules_str: str) -> list[OptimizationRule]:
        VALID_SCOPES = {"all", "JPEG XL", "SVT-AV1-PSY"}
        rules = []
        for re_match in re.finditer(r'\("([^"]+)",\s*(\d+(?:\.\d+)?),\s*"([1-9]+\/[1-9]+|1)"\)', rules_str):
            try:
                # Get
                scope, threshold, target = re_match.groups()
                threshold = float(threshold)

                # Validate
                if scope not in VALID_SCOPES:
                    raise ValueError(f"Unknown scope field. Available: {', '.join(VALID_SCOPES)}")

                if threshold < 0:
                    raise ValueError("Invalid threshold field. Cannot be lower than 0.")

                if "/" in target:
                    num, den = map(int, target.split("/"))
                    if min(num, den) < 1:
                        raise ValueError("Invalid target field. Numerator and denominator must be 1 or higher.")
                elif target != "1":
                    raise ValueError("Invalid target field. Must be either 1 or a fraction (string).")

                # Append
                rules.append(OptimizationRule(scope, threshold, target))
            except Exception as e:
                logging.error(f"[RAM Optimizer] Failed to parse optimization rule. {re_match.group(0)}. {e}")
                continue
        
        return rules

    @classmethod
    def setOptimizationRulesStr(cls, rules_str: str) -> None:
        """Parses a string into a list of optimization rules and sets it."""
        rules = cls.parseOptimizationRules(rules_str)
        cls.setOptimizationRules(rules)

        if rules:
            logging.info(f"[RAM Optimizer] Successfully parsed {len(rules)} rules.")
        else:
            logging.info(f"[RAM Optimizer] No rules found.")

    @staticmethod
    def _doesRuleApply(rule: OptimizationRule, file_format: str, avif_encoder: str) -> bool:
        is_jpeg_xl = file_format == "JPEG XL"
        is_svt_av1_psy = file_format == "AVIF" and avif_encoder == "SVT-AV1-PSY"

        if rule.scope == "all":
            return is_jpeg_xl or is_svt_av1_psy
        elif rule.scope == "JPEG XL":
            return is_jpeg_xl
        elif rule.scope == "SVT-AV1-PSY":
            return is_svt_av1_psy

        return False

    @classmethod
    def applicableRuleExists(cls, file_format: str, avif_encoder: str) -> bool:
        for rule in cls.rules:
            if cls._doesRuleApply(rule, file_format, avif_encoder):
                return True
    
        logging.info(f"[RAM Optimizer] No applicable rules found.")
        return False

    @classmethod
    def _getMaxWorkerCount(cls, current_res_mp: float, file_format: str, avif_encoder: str) -> int:
        """Interprets rules and returns new maximum concurrent worker count."""
        for rule in sorted(cls.rules, key=lambda x: x.threshold, reverse=True):
            if (
                current_res_mp >= rule.threshold and
                cls._doesRuleApply(rule, file_format, avif_encoder)
            ):
                if rule.target == "1":
                    return 1
                else:
                    num, den = rule.target.split("/")
                    try:
                        num = int(num)
                        den = int(den)
                        optimized_worker_count = int(cls.used_thread_count * num // den)
                        if optimized_worker_count < 1:
                            return 1
                        return optimized_worker_count
                    except Exception:
                        logging.error(f"[RAM Optimizer] Applying rule failed. ({rule.target})")
                        return cls.used_thread_count
        
        # No rules applied
        return cls.used_thread_count

    @classmethod
    def run(cls,
        thread_count_per_worker: int,
        src_image_path: str,
        dst_file_format: str,
        avif_encoder: str,
        jpeg_xl_effort: int,
        jpeg_xl_lossy_modular: bool,
        jpeg_xl_lossless: bool,
        jpeg_xl_intelligent_effort: bool,
    ) -> int:
        """Sets maximum thread count in the global QThreadPool instance and returns recalculated thread_count_per_worker. Not thread safe."""
        # Check if can run
        if cls.enabled == False:
            logging.error("[RAM Optimizer - run] Cannot run while disabled.")
            return thread_count_per_worker

        if cls.used_thread_count is None:
            logging.error("[RAM Optimizer - run] used_thread_count not set.")
            cls.setEnabled(False)
            return thread_count_per_worker
        
        if not cls.rules:
            cls.setEnabled(False)
            return thread_count_per_worker
        
        # Get resolution
        res_in_mp = convert.getImageResMp(src_image_path)

        if res_in_mp < 0:     # Invalid
            cls.threadpool.setMaxThreadCount(1)
            return thread_count_per_worker

        # Interpret and apply rules
        max_worker_count = cls._getMaxWorkerCount(res_in_mp, dst_file_format, avif_encoder)
        new_thread_count_per_worker = cls.used_thread_count // max_worker_count
        cls.threadpool.setMaxThreadCount(max_worker_count)

        # Return
        logging.info(f"[RAM Optimizer] Max concurrent workers: {max_worker_count}; threads per worker: {new_thread_count_per_worker}; src: {os.path.basename(src_image_path)}; res: {round(res_in_mp, 2)} MP")

        return new_thread_count_per_worker
    
    @staticmethod
    def isNecessary(
        dst_file_format: str,
        avif_encoder: str,
        jpeg_xl_effort: int,
        jpeg_xl_lossy_modular: bool,
        jpeg_xl_lossless: bool,
        jpeg_xl_intelligent_effort: bool,
    ) -> bool:
        """Returns if True if the optimizer is necessary."""
        if dst_file_format == "JPEG XL" and jpegXlHighRamUsage(jpeg_xl_effort, jpeg_xl_lossy_modular, jpeg_xl_lossless, jpeg_xl_intelligent_effort):
            return True
        
        if dst_file_format == "AVIF" and avif_encoder == "SVT-AV1-PSY":
            return True
        
        return False

def jpegXlHighRamUsage(effort: int, lossy_modular: bool, lossless: bool, intelligent_effort: bool) -> bool:
    if lossy_modular:
        return True
    
    if lossless and effort <= 9:
        return False

    if lossless and 10 > effort:
        return True
    
    if not lossless and effort <= 7 and not intelligent_effort:
        return False
    
    return True
