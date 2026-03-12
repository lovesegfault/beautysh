#!/usr/bin/env python3
"""A beautifier for Bash shell scripts written in Python.

This package provides tools for automatically formatting Bash scripts with
proper indentation, consistent function styles, and variable transformations.

Example:
    >>> from beautysh import BashFormatter
    >>> formatter = BashFormatter(indent_size=2)
    >>> script = 'if true;then\\necho "test"\\nfi'
    >>> result = formatter.beautify_string(script)
    >>> print(result.output)
    if true; then
      echo "test"
    fi
    >>> result.error is None
    True
"""

from importlib.metadata import version as _version

from .cli import BeautyshCLI
from .config import (
    ConfigError,
    load_config_from_editorconfig,
    load_config_from_pyproject,
    merge_configs,
)
from .diff import DiffFormatter
from .formatter import BashFormatter
from .function_styles import FunctionStyle
from .types import FormatResult

try:
    __version__ = _version("beautysh")
except Exception:  # pragma: no cover
    __version__ = "unknown"

__all__ = [
    "BashFormatter",
    "BeautyshCLI",
    "ConfigError",
    "DiffFormatter",
    "FormatResult",
    "FunctionStyle",
    "load_config_from_editorconfig",
    "load_config_from_pyproject",
    "merge_configs",
]
