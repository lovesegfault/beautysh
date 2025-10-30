"""Core formatting logic for Bash scripts."""

import logging
import sys
from io import StringIO
from typing import Optional, Tuple

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
    SQUARE_BRACKET_CLOSE,
    SQUARE_BRACKET_OPEN,
)
from .parser import BashParser
from .transformers import StyleTransformer
from .types import FormatterState

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
        apply_function_style: Optional[int] = None,
        variable_style: Optional[str] = None,
    ):
        """Initialize formatter with configuration.

        Args:
            indent_size: Number of spaces (or 1 for tabs) for indentation
            tab_str: String to use for indentation (' ' or '\\t')
            apply_function_style: Function style to enforce (0-2) or None
            variable_style: Variable style to enforce ('braces' or None)
        """
        self.indent_size = indent_size
        self.tab_str = tab_str
        self.apply_function_style = apply_function_style
        self.variable_style = variable_style
        self.parser = BashParser()
        self.transformer = StyleTransformer()

    def beautify_string(self, data: str, path: str = "") -> Tuple[str, bool]:
        """Beautify a Bash script string.

        This is the main entry point for formatting. It processes the script
        line by line, tracking state to determine proper indentation.

        Args:
            data: Complete Bash script as string
            path: File path (for error messages)

        Returns:
            Tuple of (formatted_script, has_error)

        Example:
            >>> formatter = BashFormatter()
            >>> script = 'if true;then\\necho "test"\\nfi'
            >>> formatted, error = formatter.beautify_string(script)
            >>> print(formatted)
            if true; then
                echo "test"
            fi
        """
        # Preprocess: split 'do case' and 'then case' onto separate lines
        data = self.parser.normalize_do_case_lines(data)

        state = FormatterState()
        output = StringIO()
        line_num = 1
        first_line = True

        for record in data.split("\n"):
            formatted_line = self._process_line(record, state, path, line_num)
            if formatted_line is not None:
                # Apply variable style transformation if requested
                if self.variable_style is not None:
                    formatted_line = self.transformer.apply_variable_style(
                        formatted_line, self.variable_style
                    )

                # Write line with newline separator (except before first line)
                if not first_line:
                    output.write("\n")
                output.write(formatted_line)
                first_line = False
            line_num += 1

        error = self._check_final_state(state, path)

        return output.getvalue(), error

    def _process_line(
        self,
        record: str,
        state: FormatterState,
        path: str,
        line_num: int,
    ) -> Optional[str]:
        """Process a single line of the Bash script.

        Args:
            record: The line to process
            state: Current formatter state
            path: File path (for error messages)
            line_num: Current line number

        Returns:
            Formatted line, or None to skip adding to output
        """
        record = record.rstrip()
        stripped_record = record.strip()

        # Preserve blank lines
        if not stripped_record:
            return stripped_record

        # Ensure space before ;; in case statements
        if state.case_level:
            stripped_record = self.transformer.ensure_space_before_double_semicolon(
                stripped_record, True
            )

        test_record = self.parser.get_test_record(stripped_record)

        # Handle multiline strings (without backslash continuation)
        if state.in_multiline_string:
            return self._handle_multiline_string_content(record, stripped_record, state)

        # Check if a new multiline string starts
        if self._check_multiline_string_start(test_record, state):
            return self._indent_line(state.tab, stripped_record)

        # Handle line continuation
        self._update_continuation_state(stripped_record, state)

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
            [test_record, num_subs] = MULTILINE_STRING_END.subn("", test_record)
            state.ended_multiline_quoted_string = num_subs > 0
        else:
            state.ended_multiline_quoted_string = False

        # Pass through here-docs and multiline quoted strings unchanged
        if state.in_here_doc or inside_multiline_quoted or state.ended_multiline_quoted_string:
            # Test for here-doc termination
            if state.here_string is not None:
                if state.here_string in test_record and "<<" not in test_record:
                    state.in_here_doc = False
                    logger.debug(f"Here-doc terminated at line {line_num}")
            return record

        # Handle continued lines and multiline strings with backslash
        self._handle_line_continuation(stripped_record, test_record, state)

        # Detect here-docs
        is_heredoc, here_string = self.parser.detect_heredoc(test_record, stripped_record)
        if is_heredoc:
            state.in_here_doc = True
            state.here_string = here_string

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
        formatted = self._format_line(stripped_record, test_record, state, path, line_num)

        # Count open square brackets for line continuation tracking
        # Only [ ] brackets are counted, not { } or ( )
        state.open_brackets += len(SQUARE_BRACKET_OPEN.findall(test_record))
        state.open_brackets -= len(SQUARE_BRACKET_CLOSE.findall(test_record))

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
        if state.multiline_string_quote_char is not None:
            if state.multiline_string_quote_char in stripped_record:
                quote_count = stripped_record.count(state.multiline_string_quote_char)
                if quote_count % 2 == 1:  # Odd number = closing quote
                    state.in_multiline_string = False
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
        unclosed_double, unclosed_single = self.parser.detect_unclosed_quote(test_record)
        if unclosed_double or unclosed_single:
            state.in_multiline_string = True
            state.multiline_string_quote_char = '"' if unclosed_double else "'"
            logger.debug(
                f"Multiline string started with quote: {state.multiline_string_quote_char}"
            )
            return True
        return False

    def _update_continuation_state(self, stripped_record: str, state: FormatterState) -> None:
        """Update state for line continuation tracking.

        Args:
            stripped_record: Stripped line
            state: Current formatter state
        """
        state.prev_line_had_continue = state.continue_line
        state.continue_line = self.parser.is_line_continuation(stripped_record)

    def _handle_line_continuation(
        self, stripped_record: str, test_record: str, state: FormatterState
    ) -> None:
        """Handle multiline strings with backslash continuation.

        Args:
            stripped_record: Stripped line
            test_record: Test record
            state: Current formatter state
        """
        if state.continue_line:
            if state.prev_line_had_continue:
                # Not starting a multiline-quoted string
                state.started_multiline_quoted_string = False
            else:
                # Remove contents of strings that continue on next line
                [_, num_subs] = MULTILINE_STRING_START.subn("", test_record)
                state.started_multiline_quoted_string = num_subs > 0
        else:
            state.started_multiline_quoted_string = False

    def _format_line(
        self,
        stripped_record: str,
        test_record: str,
        state: FormatterState,
        path: str,
        line_num: int,
    ) -> str:
        """Format a line with proper indentation.

        Args:
            stripped_record: Stripped original line
            test_record: Simplified test record
            state: Current formatter state
            path: File path for error messages
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
                sys.stderr.write(f'File {path}: error: "esac" before "case" in line {line_num}.\n')
            else:
                outc += 1
                state.case_level -= 1

        # Handle case
        if CASE_KEYWORD_PATTERN.search(test_record):
            inc += 1
            state.case_level += 1

        # Handle case choices
        choice_case = 0
        if state.case_level:
            if CASE_CHOICE_PATTERN.search(test_record):
                inc += 1
                choice_case = -1

        # Detect and transform function styles
        func_decl_style = self.parser.detect_function_style(test_record)
        if func_decl_style is not None:
            stripped_record = self.transformer.change_function_style(
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

    def _check_final_state(self, state: FormatterState, path: str) -> bool:
        """Check if formatting ended in a valid state.

        Args:
            state: Final formatter state
            path: File path for error messages

        Returns:
            True if there was an error (indent/outdent mismatch)
        """
        error = state.tab != 0
        if error:
            sys.stderr.write(f"File {path}: error: indent/outdent mismatch: {state.tab}.\n")
            logger.error(f"Indent/outdent mismatch: final tab level = {state.tab}")
        return error
