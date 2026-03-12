"""Type definitions for beautysh."""

from dataclasses import dataclass
from typing import Literal, NamedTuple, Optional

#: The only variable style currently supported. Promote to an Enum (mirroring
#: FunctionStyle) when a second style is added.
VariableStyle = Literal["braces"]

#: Quote character that opens a multiline string.
QuoteChar = Literal['"', "'"]


class FormatResult(NamedTuple):
    """Result of beautify_string.

    Attributes:
        output: Formatted script (best-effort even on error).
        error: None on success, otherwise a human-readable error message.
    """

    output: str
    error: Optional[str]


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
        multiline_string_quote_char: The quote char for the current multiline
            string, or None if we're not inside one
        here_string: The termination string for current here-doc
        heredoc_quoted: Whether current heredoc has quoted terminator (no expansion)
        formatter_enabled: Whether formatter is enabled (@formatter:off/on)
        error_message: First error encountered during formatting, if any
    """

    tab: int = 0
    case_level: int = 0
    prev_line_had_continue: bool = False
    continue_line: bool = False
    started_multiline_quoted_string: bool = False
    ended_multiline_quoted_string: bool = False
    open_brackets: int = 0
    in_here_doc: bool = False
    multiline_string_quote_char: Optional[QuoteChar] = None
    here_string: str = ""
    heredoc_quoted: bool = False
    formatter_enabled: bool = True
    error_message: Optional[str] = None
