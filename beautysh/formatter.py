"""Core formatting logic for Bash scripts."""

import logging
from io import StringIO
from typing import Optional

from . import parser
from .constants import (
    CASE_CHOICE_PATTERN,
    CASE_KEYWORD_PATTERN,
    CLOSING_BRACKETS,
    ELSE_ELIF_PATTERN,
    ESAC_KEYWORD_PATTERN,
    FORMATTER_OFF_DIRECTIVE,
    FORMATTER_ON_DIRECTIVE,
    INDENT_DECREASE_KEYWORDS,
    INDENT_INCREASE_KEYWORDS,
    MULTILINE_STRING_END,
    MULTILINE_STRING_START,
    OPENING_BRACKETS,
    QUOTED_CASE_PATTERN,
    SQUARE_BRACKET_CLOSE,
    SQUARE_BRACKET_OPEN,
)
from .function_styles import FunctionStyle
from .transformers import (
    apply_variable_style,
    change_function_style,
    ensure_space_before_double_semicolon,
)
from .types import FormatResult, FormatterState, VariableStyle

logger = logging.getLogger(__name__)


class BashFormatter:
    """Formatter for Bash scripts.

    This class handles the core formatting logic, including indentation
    calculation, multiline string handling, and applying style transformations.
    """

    def __init__(
        self,
        indent_size: int = 4,
        tab_str: str = " ",
        apply_function_style: Optional[FunctionStyle] = None,
        variable_style: Optional[VariableStyle] = None,
    ):
        """Initialize formatter with configuration.

        Args:
            indent_size: Number of spaces (or 1 for tabs) for indentation
            tab_str: String to use for indentation (' ' or '\\t')
            apply_function_style: Function style to enforce, or None
            variable_style: Variable style to enforce ('braces' or None)
        """
        self.indent_size = indent_size
        self.tab_str = tab_str
        self.apply_function_style = apply_function_style
        self.variable_style: Optional[VariableStyle] = variable_style

    def beautify_string(self, data: str) -> FormatResult:
        """Beautify a Bash script string.

        This is the main entry point for formatting. It processes the script
        line by line, tracking state to determine proper indentation.

        Args:
            data: Complete Bash script as string

        Returns:
            FormatResult with best-effort output and an error message if
            indentation did not balance. No I/O is performed; callers are
            responsible for printing the error.

        Example:
            >>> formatter = BashFormatter()
            >>> script = 'if true;then\\necho "test"\\nfi'
            >>> result = formatter.beautify_string(script)
            >>> print(result.output)
            if true; then
                echo "test"
            fi
            >>> result.error is None
            True
        """
        # Preprocess: split 'do case' and 'then case' onto separate lines
        data = parser.normalize_do_case_lines(data)

        state = FormatterState()
        output = StringIO()
        line_num = 1
        first_line = True

        for record in data.split("\n"):
            formatted_line = self._process_line(record, state, line_num)
            if not first_line:
                output.write("\n")
            output.write(formatted_line)
            first_line = False
            line_num += 1

        error = state.error_message or self._check_final_state(state)
        return FormatResult(output=output.getvalue(), error=error)

    def _process_line(self, record: str, state: FormatterState, line_num: int) -> str:
        """Process a single line of the Bash script.

        Args:
            record: The line to process
            state: Current formatter state
            line_num: Current line number

        Returns:
            Formatted line
        """
        record = record.rstrip()
        stripped_record = record.strip()

        # Preserve blank lines
        if not stripped_record:
            return stripped_record

        # Ensure space before ;; in case statements
        if state.case_level:
            stripped_record = ensure_space_before_double_semicolon(stripped_record)

        test_record = parser.get_test_record(stripped_record)

        # Handle line continuation
        self._update_continuation_state(stripped_record, state)
        # Handle continued lines and multiline strings with backslash.
        # May strip quoted-string content from test_record so brackets/keywords
        # inside the string are not counted for indentation (issue #272).
        test_record = self._handle_line_continuation(test_record, state)

        inside_multiline_quoted = (
            state.prev_line_had_continue
            and state.continue_line
            and state.started_multiline_quoted_string
        )

        if (
            not state.continue_line
            and state.prev_line_had_continue
            and state.started_multiline_quoted_string
        ):
            # Remove contents of strings ending on this line
            test_record, num_subs = MULTILINE_STRING_END.subn("", test_record)
            state.ended_multiline_quoted_string = num_subs > 0
            # Continuation sequence has ended - reset the tracking flag
            state.started_multiline_quoted_string = False
        else:
            state.ended_multiline_quoted_string = False

        # Pass through here-docs and multiline quoted strings unchanged
        # NOTE: This check must come BEFORE multiline string checks to handle
        # heredoc content that might contain quotes/apostrophes (issue #265)
        # NOTE: ended_multiline_quoted_string is NOT checked here - that line
        # may contain keywords after the closing quote (e.g., `hej)"; then`)
        # and must reach _format_line so indentation is tracked correctly.
        if state.in_here_doc or inside_multiline_quoted:
            # Test for here-doc termination. Stricter terminator check: must be
            # on its own line (issue #265). stripped_record is already .strip()'d
            # above, which handles <<- tab indentation.
            if (
                state.in_here_doc
                and stripped_record == state.here_string
                and "<<" not in test_record
            ):
                state.in_here_doc = False
                state.heredoc_quoted = False  # Reset quote tracking
                logger.debug(f"Here-doc terminated at line {line_num}")

            # Apply variable transformation to unquoted heredoc content
            result = record
            if state.in_here_doc and not state.heredoc_quoted and self.variable_style is not None:
                result = apply_variable_style(result, self.variable_style)

            return result

        # Detect here-docs
        here_string = parser.detect_heredoc(test_record, stripped_record)
        if here_string is not None:
            state.in_here_doc = True
            state.here_string = here_string
            # Check if terminator is quoted (suppresses variable expansion)
            state.heredoc_quoted = parser.is_heredoc_quoted(stripped_record)
            logger.debug(
                f"Heredoc started: terminator={here_string}, "
                f"quoted={state.heredoc_quoted}, line={line_num}"
            )

        # Handle multiline strings (without backslash continuation)
        # NOTE: This check comes AFTER heredoc checks so heredoc content
        # with quotes/apostrophes is handled correctly (issue #265)
        if state.multiline_string_quote_char is not None:
            return self._handle_multiline_string_content(record, stripped_record, state)

        # Check if a new multiline string starts
        if self._check_multiline_string_start(test_record, state):
            return self._indent_line(state.tab, stripped_record)

        # Handle @formatter:off/on directives
        if not state.formatter_enabled:
            if FORMATTER_ON_DIRECTIVE.search(stripped_record):
                state.formatter_enabled = True
                logger.debug(f"Formatter re-enabled at line {line_num}")
            return record

        if FORMATTER_OFF_DIRECTIVE.search(stripped_record):
            state.formatter_enabled = False
            logger.debug(f"Formatter disabled at line {line_num}")
            return record

        # Multi-line conditions are often meticulously formatted - preserve them
        if state.open_brackets:
            return record

        # Calculate indentation changes and format the line
        formatted = self._format_line(stripped_record, test_record, state, line_num)

        # Count open square brackets for line continuation tracking
        # Only [ ] brackets are counted, not { } or ( )
        state.open_brackets += len(SQUARE_BRACKET_OPEN.findall(test_record))
        state.open_brackets -= len(SQUARE_BRACKET_CLOSE.findall(test_record))

        # When a backslash-continued quoted string ends on this line, we needed
        # _format_line above for its side effect (updating state.tab from any
        # keywords like `then` that follow the closing quote), but we must
        # preserve the original line since its leading whitespace is part of
        # the string content.
        if state.ended_multiline_quoted_string:
            return record

        return formatted

    def _handle_multiline_string_content(
        self, record: str, stripped_record: str, state: FormatterState
    ) -> str:
        """Handle content inside a multiline string.

        Args:
            record: Original line
            stripped_record: Stripped line
            state: Current formatter state

        Returns:
            Line to output (preserved without indentation)
        """
        # Check if this line closes the string
        quote = state.multiline_string_quote_char
        if quote is not None and quote in stripped_record:
            quote_count = stripped_record.count(quote)
            if quote_count % 2 == 1:  # Odd number = closing quote
                state.multiline_string_quote_char = None
                logger.debug("Multiline string closed")

        # Pass through unchanged to preserve string content
        return record

    def _check_multiline_string_start(self, test_record: str, state: FormatterState) -> bool:
        """Check if a multiline string starts on this line.

        Args:
            test_record: Simplified test record
            state: Current formatter state

        Returns:
            True if multiline string starts
        """
        unclosed = parser.detect_unclosed_quote(test_record)
        if unclosed is not None:
            state.multiline_string_quote_char = unclosed
            logger.debug(f"Multiline string started with quote: {unclosed}")
            return True
        return False

    def _update_continuation_state(self, stripped_record: str, state: FormatterState) -> None:
        """Update state for line continuation tracking.

        Args:
            stripped_record: Stripped line
            state: Current formatter state
        """
        state.prev_line_had_continue = state.continue_line
        state.continue_line = parser.is_line_continuation(stripped_record)

    def _handle_line_continuation(self, test_record: str, state: FormatterState) -> str:
        """Handle multiline strings with backslash continuation.

        Detects when a backslash continuation begins inside an unclosed
        quoted string, and strips the string content from the test_record
        so that brackets and keywords inside the string are not counted
        for indentation.

        The started_multiline_quoted_string flag is only set at the START
        of a continuation sequence and deliberately preserved across middle
        and end lines so the caller can detect the string closing.

        Args:
            test_record: Test record
            state: Current formatter state

        Returns:
            Test record, with string content stripped if a multiline
            quoted string was detected on this line
        """
        if state.continue_line and not state.prev_line_had_continue:
            # First line of a continuation: detect if we're entering a
            # quoted string and strip its content from the test record
            new_test_record, num_subs = MULTILINE_STRING_START.subn("", test_record)
            state.started_multiline_quoted_string = num_subs > 0
            if num_subs > 0:
                return new_test_record
        elif not state.continue_line and not state.prev_line_had_continue:
            # Outside any continuation sequence
            state.started_multiline_quoted_string = False
        # Middle lines (continue=True, prev=True) and end lines
        # (continue=False, prev=True): preserve state so the caller can
        # detect the end of the quoted string via MULTILINE_STRING_END.
        return test_record

    def _is_case_pattern(self, test_record: str, stripped_record: str) -> bool:
        """Detect case patterns including quoted strings.

        This handles:
        - Quoted patterns (including empty): "" or '' or " " (issue #265)
        - Escaped patterns: \\?) or \\*) (issue #270)
        - Prevents false positives from standalone ) (issue #78)

        Args:
            test_record: Simplified test record (after quote removal)
            stripped_record: Original stripped line (before quote removal)

        Returns:
            True if this line is a case pattern, False otherwise
        """
        # Check original line for quoted patterns before quote removal
        # This handles cases where the pattern content disappears after quote removal
        if QUOTED_CASE_PATTERN.search(stripped_record):
            return True

        # Check for patterns with content: foo) or bar)
        # The + quantifier prevents standalone ) from matching (preserves issue #78 fix)
        if CASE_CHOICE_PATTERN.search(test_record):
            return True

        # Escaped patterns like \?) or \*) become bare ) after ESCAPED_CHAR
        # stripping. Distinguish from a standalone ) closing a multiline array
        # (issue #78) by checking whether the original line had content before
        # the ) that get_test_record removed.
        return test_record.lstrip().startswith(")") and not stripped_record.startswith(")")

    def _format_line(
        self,
        stripped_record: str,
        test_record: str,
        state: FormatterState,
        line_num: int,
    ) -> str:
        """Format a line with proper indentation.

        Args:
            stripped_record: Stripped original line
            test_record: Simplified test record
            state: Current formatter state
            line_num: Current line number

        Returns:
            Formatted line with indentation
        """
        # Count indent increase keywords
        inc = len(INDENT_INCREASE_KEYWORDS.findall(test_record))
        inc += len(OPENING_BRACKETS.findall(test_record))

        # Count indent decrease keywords
        outc = len(INDENT_DECREASE_KEYWORDS.findall(test_record))
        outc += len(CLOSING_BRACKETS.findall(test_record))

        # Handle esac
        if ESAC_KEYWORD_PATTERN.search(test_record):
            if state.case_level == 0:
                if state.error_message is None:
                    state.error_message = f'"esac" before "case" in line {line_num}'
            else:
                outc += 1
                state.case_level -= 1

        # Handle case
        if CASE_KEYWORD_PATTERN.search(test_record):
            inc += 1
            state.case_level += 1

        # Handle case choices
        choice_case = 0
        if state.case_level and self._is_case_pattern(test_record, stripped_record):
            inc += 1
            choice_case = -1

        # Detect and transform function styles
        func_decl_style = FunctionStyle.detect(test_record)
        if func_decl_style is not None:
            stripped_record = change_function_style(
                stripped_record, func_decl_style, self.apply_function_style
            )

        # Handle else/elif
        else_case = -1 if ELSE_ELIF_PATTERN.search(test_record) else 0

        # Calculate net indentation change
        net = inc - outc
        state.tab += min(net, 0)

        # Calculate effective tab for this line
        extab = state.tab + else_case + choice_case
        if (
            state.prev_line_had_continue
            and not state.open_brackets
            and not state.ended_multiline_quoted_string
        ):
            extab += 1
        extab = max(0, extab)

        formatted = self._indent_line(extab, stripped_record)
        state.tab += max(net, 0)

        # Apply variable style transformation if requested
        # Skip transformation in quoted heredocs (no expansion in bash)
        if self.variable_style is not None and not state.heredoc_quoted:
            formatted = apply_variable_style(formatted, self.variable_style)

        return formatted

    def _indent_line(self, level: int, line: str) -> str:
        """Add indentation to a line.

        Args:
            level: Indentation level
            line: Line content

        Returns:
            Indented line
        """
        return (self.tab_str * self.indent_size * level) + line

    def _check_final_state(self, state: FormatterState) -> Optional[str]:
        """Check if formatting ended in a valid state.

        Args:
            state: Final formatter state

        Returns:
            Error message if indentation didn't balance, None otherwise.
        """
        if state.tab != 0:
            logger.error(f"Indent/outdent mismatch: final tab level = {state.tab}")
            return f"indent/outdent mismatch: {state.tab}"
        return None
