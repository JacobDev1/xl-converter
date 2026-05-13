from typing import Any, Union
from collections.abc import Hashable
import os
import re
from enum import StrEnum, auto
import platform

SYSTEM = platform.system()

def removeDuplicatesHashable(data: list[Hashable]) -> list[Hashable]:
    """Removes duplicates from a list while preserving order. All entries must be hashable.
    
    Hashable: str, int, float, tuple
    Unhashable: list, dict, set
    """ 
    return list(dict.fromkeys(data))

def _caseInsensitiveExtGlob(ext: str) -> str:
    """A helper function for listToFilter()"""
    if SYSTEM == "Linux":
        return "*." + "".join(
            f"[{char.lower()}{char.upper()}]" if char.isalpha() else char
            for char in ext
        )

    # Filters are case insensitive on Windows already.
    return f"*.{ext}"

def listToFilter(title: str, ext: list[str]) -> str:
    """Convert a list of extensions into a name filter for file dialogs."""
    if len(ext) == 0:
        return f"All Files (*)"
    
    filters = [_caseInsensitiveExtGlob(i) for i in ext]
    return f"{title} ({' '.join(filters)})"

def isRunningInFlatpak() -> bool:
    """Determines if the application is running inside a Flatpak sandbox."""
    if os.environ.get("FLATPAK_ID", None) is not None:
        return True
    
    return False

def parseVersion(version: str | None) -> tuple[int, int, int] | None:
    """Parses XL Converter version string into a tuple. Returns None if it cannot be parsed."""
    if version is None or not isinstance(version, str) or not version:
        return None

    if version[0].lower() == "v":
        version = version[1:]

    ver_match = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)", version)

    if ver_match is None:
        return None

    try:
        return tuple(int(x) for x in ver_match.groups())
    except Exception:
        return None

class VersionParseErrorPolicy(StrEnum):
    ASSUME_OLDER = auto()
    ASSUME_NEWER = auto()
    ASSUME_EQUAL = auto()
    RAISE = auto()

def compareVersions(
    base_version: str | None,
    candidate_version: str | None,
    parse_error_policy: VersionParseErrorPolicy = VersionParseErrorPolicy.RAISE,
) -> int:
    """Returns 1 if candidate is newer, 0 if it's equal, and -1 if it's older. parse_error_policy controls fallback behavior when parsing fails."""
    base = parseVersion(base_version)
    cand = parseVersion(candidate_version)

    if base is None or cand is None:
        match parse_error_policy:
            case VersionParseErrorPolicy.RAISE:
                raise ValueError("Could not parse version(s)")
            case VersionParseErrorPolicy.ASSUME_EQUAL:
                return 0
            case VersionParseErrorPolicy.ASSUME_NEWER:
                return 1
            case VersionParseErrorPolicy.ASSUME_OLDER:
                return -1
            case _:
                raise ValueError(f"Unknown parse_error_policy: {parse_error_policy}")

    return (base < cand) - (base > cand)
