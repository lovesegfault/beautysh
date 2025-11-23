"""Type definitions for beautysh."""

from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional


class FunctionStyle(Enum):
    """Function definition styles in Bash.

    Examples:
        FNPAR:   function name() { ... }
        FNONLY:  function name { ... }
        PARONLY: name() { ... }
    """

    FNPAR = auto()  # function name()
    FNONLY = auto()  # function name
    PARONLY = auto()  # name()


class VariableStyle(Enum):
    """Variable expansion styles in Bash.

    When set, actively transforms variables to the specified style.
    When None, preserves original style.

    Examples:
        BRACES: ${VAR} - always use braces
        SIMPLE: $VAR - use simple form where possible (remove unnecessary braces)
    """

    BRACES = auto()  # Always use ${VAR}
    SIMPLE = auto()  # Use $VAR where possible, only keep braces where necessary


@dataclass
class BeautyshConfig:
    """Configuration for Beautysh formatter.

    Attributes:
        indent_size: Number of spaces for indentation (or 1 for tabs)
        tab_str: String to use for indentation (' ' or '\\t')
        backup: Whether to create .bak backup files
        check_only: Only check formatting without modifying files
        function_style: Function style to enforce, or None to preserve original
        variable_style: Variable style to enforce, or None to preserve original
        color: Whether to use colored diff output
    """

    indent_size: int = 4
    tab_str: str = " "
    backup: bool = False
    check_only: bool = False
    function_style: Optional[FunctionStyle] = None
    variable_style: Optional[VariableStyle] = None
    color: bool = True
