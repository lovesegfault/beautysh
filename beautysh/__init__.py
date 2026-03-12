#!/usr/bin/env python3
"""A beautifier for Bash shell scripts written in Python.

This package provides tools for automatically formatting Bash scripts with
proper indentation, consistent function styles, and variable transformations.

Example:
    >>> from beautysh import BashFormatter
    >>> formatter = BashFormatter(indent_size=2)
    >>> script = 'if true;then\\necho "test"\\nfi'
    >>> formatted, error = formatter.beautify_string(script)
    >>> print(formatted)
    if true; then
      echo "test"
    fi
"""

from importlib.metadata import version as _version

# Public API exports
from .cli import BeautyshCLI
from .config import (
    load_config_from_editorconfig,
    load_config_from_pyproject,
    merge_configs,
)
from .diff import DiffFormatter
from .formatter import BashFormatter
from .function_styles import FunctionStyle
from .parser import BashParser
from .transformers import StyleTransformer
from .types import FormatterState

try:
    __version__ = _version("beautysh")
except Exception:
    __version__ = "unknown"

__all__ = [
    # Main classes
    "BashFormatter",
    "BeautyshCLI",
    "BashParser",
    "StyleTransformer",
    "DiffFormatter",
    "FunctionStyle",
    # Configuration
    "load_config_from_pyproject",
    "load_config_from_editorconfig",
    "merge_configs",
    # Types
    "FormatterState",
]
