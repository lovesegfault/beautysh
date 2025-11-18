"""Type definitions for beautysh."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class FormatterState:
    """State tracking for the Bash formatter.

    This dataclass encapsulates all the state needed during the formatting
    process, making it easier to reason about and test.

    Attributes:
        tab: Current indentation level
        case_level: Nesting level within case statements
        prev_line_had_continue: Whether previous line ended with backslash
        continue_line: Whether current line ends with backslash
        started_multiline_quoted_string: Whether a multiline quoted string with
            backslash continuation started
        ended_multiline_quoted_string: Whether a multiline quoted string ended
        open_brackets: Count of unclosed brackets for multiline conditions
        in_here_doc: Whether we're currently inside a here-document
        in_multiline_string: Whether we're inside a multiline string (no backslash)
        multiline_string_quote_char: The quote character for current multiline string
        here_string: The termination string for current here-doc
        heredoc_quoted: Whether current heredoc has quoted terminator (no expansion)
        formatter_enabled: Whether formatter is enabled (@formatter:off/on)
    """

    tab: int = 0
    case_level: int = 0
    prev_line_had_continue: bool = False
    continue_line: bool = False
    started_multiline_quoted_string: bool = False
    ended_multiline_quoted_string: bool = False
    open_brackets: int = 0
    in_here_doc: bool = False
    in_multiline_string: bool = False
    multiline_string_quote_char: Optional[str] = None
    here_string: str = ""
    heredoc_quoted: bool = False
    formatter_enabled: bool = True


@dataclass
class BeautyshConfig:
    """Configuration for Beautysh formatter.

    This dataclass holds all configuration options with their defaults.
    Configuration priority: CLI args > pyproject.toml > EditorConfig

    Attributes:
        indent_size: Number of spaces for indentation (or 1 for tabs)
        tab_str: String to use for indentation (' ' or '\\t')
        backup: Whether to create .bak backup files
        check_only: Only check formatting without modifying files
        apply_function_style: Function style to enforce (0=fnpar, 1=fnonly, 2=paronly)
        variable_style: Variable style to enforce ('braces' or None)
        color: Whether to use colored diff output
    """

    indent_size: int = 4
    tab_str: str = " "
    backup: bool = False
    check_only: bool = False
    apply_function_style: Optional[int] = None
    variable_style: Optional[str] = None
    color: bool = True
