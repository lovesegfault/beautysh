"""PEG grammar definitions for Bash parsing.

This module provides the parsimonious-based grammar for parsing Bash
scripts into an AST. The grammar handles the full Bash syntax including
control structures, functions, redirections, and expansions.
"""

from beautysh.grammar.bash import BASH_GRAMMAR, parse_bash, BashParseError

__all__ = [
    "BASH_GRAMMAR",
    "parse_bash",
    "BashParseError",
]
