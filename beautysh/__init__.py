#!/usr/bin/env python3
"""A beautifier for Bash shell scripts written in Python.

This package provides tools for automatically formatting Bash scripts with
proper indentation using a PEG-based parser.

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

import logging

# Public API exports
from .cli import BeautyshCLI
from .config import (
    load_config_from_editorconfig,
    load_config_from_pyproject,
    merge_configs,
)
from .diff import DiffFormatter
from .formatter import BashFormatter
from .transformers import FunctionStyleParser
from .types import BeautyshConfig, FunctionStyle, VariableStyle

# Configure default logging
logging.basicConfig(
    level=logging.WARNING,
    format="%(name)s - %(levelname)s: %(message)s",
)

__version__ = "6.3.3"

__all__ = [
    # Main classes
    "BashFormatter",
    "BeautyshCLI",
    "DiffFormatter",
    "FunctionStyleParser",
    # Configuration
    "BeautyshConfig",
    "FunctionStyle",
    "VariableStyle",
    "load_config_from_pyproject",
    "load_config_from_editorconfig",
    "merge_configs",
]
