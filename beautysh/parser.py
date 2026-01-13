"""Bash script parsing utilities."""

import logging
import re
from typing import Optional

from .constants import FUNCTION_STYLE_PATTERNS

logger = logging.getLogger(__name__)


class BashParser:
    """Parser for Bash script syntax analysis.

    This class provides utilities for analyzing Bash syntax to determine
    indentation and formatting requirements. It handles the complexities
    of Bash syntax including quotes, comments, and special constructs.
    """

    @staticmethod
    def get_test_record(source_line: str) -> str:
        """Simplify a Bash source line for indentation analysis.

        Removes content that doesn't affect indentation calculation:
        - Escaped special characters (\\', \\")
        - String literals (single/double/backtick quoted)
        - Comments (# ...)
        - Other escaped characters

        This simplification makes it easier to detect keywords and brackets
        that affect indentation without false matches inside strings.

        Args:
            source_line: Raw line from Bash script

        Returns:
            Simplified line with only indent-relevant syntax

        Example:
            >>> BashParser.get_test_record('if [ "$x" = "y" ]; then  # comment')
            'if [ = ]; then  '
            >>> BashParser.get_test_record("echo 'hello world'")
            'echo '
        """
        from .constants import (
            BACKTICK_STRING,
            COMMENT,
            DOUBLE_QUOTED_STRING,
            ESCAPED_CHAR,
            ESCAPED_DOUBLE_QUOTE,
            ESCAPED_SINGLE_QUOTE,
            SINGLE_QUOTED_STRING,
            WEIRD_BACKTICK_STRING,
        )

        # First, remove escaped quotes that may impact later collapsing
        test_record = ESCAPED_SINGLE_QUOTE.sub("", source_line)
        test_record = ESCAPED_DOUBLE_QUOTE.sub("", test_record)

        # Collapse single-quoted strings
        test_record = SINGLE_QUOTED_STRING.sub("", test_record)
        # Collapse double-quoted strings
        test_record = DOUBLE_QUOTED_STRING.sub("", test_record)
        # Collapse backtick command substitutions
        test_record = BACKTICK_STRING.sub("", test_record)
        # Collapse weird case: \\` ... '
        test_record = WEIRD_BACKTICK_STRING.sub("", test_record)
        # Strip out any escaped single characters
        test_record = ESCAPED_CHAR.sub("", test_record)
        # Remove comments (# to end of line)
        test_record = COMMENT.sub("", test_record, 1)

        return test_record

    @staticmethod
    def detect_unclosed_quote(test_record: str) -> tuple[bool, bool]:
        """Detect if test_record has an unclosed quote.

        After get_test_record() has collapsed all properly closed quotes on
        the same line, any remaining quotes indicate an unclosed multiline string.

        Args:
            test_record: Simplified line from get_test_record()

        Returns:
            Tuple of (has_unclosed_double_quote, has_unclosed_single_quote)

        Example:
            >>> BashParser.detect_unclosed_quote('echo "test')
            (True, False)
            >>> BashParser.detect_unclosed_quote("echo 'test")
            (False, True)
            >>> BashParser.detect_unclosed_quote('echo "test" "more')
            (True, False)
        """
        unclosed_double = test_record.count('"') % 2 == 1
        unclosed_single = test_record.count("'") % 2 == 1
        return (unclosed_double, unclosed_single)

    @staticmethod
    def detect_function_style(test_record: str) -> Optional[int]:
        """Detect the function declaration style in a line.

        Bash supports three function declaration styles:
        0. function foo()  - fnpar style (function keyword + parentheses)
        1. function foo    - fnonly style (function keyword only)
        2. foo()          - paronly style (parentheses only)

        IMPORTANT: Patterns must be tested sequentially to avoid false matches.

        Args:
            test_record: Simplified line from get_test_record()

        Returns:
            Style index (0, 1, or 2) if a function declaration is found,
            None otherwise

        Example:
            >>> BashParser.detect_function_style('function foo() {')
            0
            >>> BashParser.detect_function_style('function bar {')
            1
            >>> BashParser.detect_function_style('baz() {')
            2
            >>> BashParser.detect_function_style('echo foo()')
            None
        """
        # IMPORTANT: apply regex sequentially and stop on the first match
        for index, pattern in enumerate(FUNCTION_STYLE_PATTERNS):
            if re.search(pattern, test_record):
                logger.debug(f"Detected function style {index} in: {test_record}")
                return index
        return None

    @staticmethod
    def normalize_do_case_lines(data: str) -> str:
        """Split lines where 'do case' or 'then case' appear together.

        This normalizes Bash code like:
            while x; do case $y in
        Into:
            while x; do
            case $y in

        This makes indentation handling more straightforward by ensuring
        that keywords appear on separate lines.

        Args:
            data: Complete Bash script as string

        Returns:
            Script with do/then and case on separate lines

        Example:
            >>> script = 'while true; do case $x in'
            >>> BashParser.normalize_do_case_lines(script)
            'while true; do\\ncase $x in'
        """
        from .constants import CASE_SPLIT_PATTERN, DO_CASE_PATTERN

        lines = []
        parser = BashParser()

        for line in data.split("\n"):
            # Check if line contains both 'do' and 'case' or 'then' and 'case'
            test_line = parser.get_test_record(line)

            # Look for patterns like 'do case' or 'then case'
            match = DO_CASE_PATTERN.search(test_line)
            if match:
                # Find the position in the original line
                # We need to preserve any content before 'case'
                case_match = CASE_SPLIT_PATTERN.search(line)
                if case_match:
                    split_pos = case_match.start(2)  # Position of 'case'
                    before = line[:split_pos].rstrip()
                    after = line[split_pos:]
                    lines.append(before)
                    lines.append(after)
                    logger.debug("Split 'do/then case' line into two lines")
                else:
                    lines.append(line)
            else:
                lines.append(line)

        return "\n".join(lines)

    @staticmethod
    def detect_heredoc(test_record: str, stripped_record: str) -> tuple[bool, str]:
        """Detect here-document and extract termination string.

        Detects here-docs (<<EOF or <<-EOF) while avoiding false positives
        from:
        - Here-strings (<<<)
        - Arithmetic expressions with shift operator ($((x << 2)))

        Args:
            test_record: Simplified line from get_test_record()
            stripped_record: Original stripped line

        Returns:
            Tuple of (is_heredoc, termination_string)

        Example:
            >>> BashParser.detect_heredoc('cat <<EOF', 'cat <<EOF')
            (True, 'EOF')
            >>> BashParser.detect_heredoc('cat <<-"END"', 'cat <<-"END"')
            (True, 'END')
            >>> BashParser.detect_heredoc('echo <<<$var', 'echo <<<$var')
            (False, '')
            >>> BashParser.detect_heredoc('$(( x << 2 ))', '$(( x << 2 ))')
            (False, '')
        """
        from .constants import (
            ARITHMETIC_PATTERN,
            HEREDOC_PATTERN,
            HEREDOC_TERMINATOR,
            HERESTRING_PATTERN,
        )

        has_heredoc = HEREDOC_PATTERN.search(test_record)
        is_herestring = HERESTRING_PATTERN.search(test_record)
        is_arithmetic = ARITHMETIC_PATTERN.search(test_record)

        if has_heredoc and not is_herestring and not is_arithmetic:
            here_string = HEREDOC_TERMINATOR.sub(r"\1", stripped_record, 1)
            is_heredoc = len(here_string) > 0
            logger.debug(f"Detected here-doc with terminator: {here_string}")
            return (is_heredoc, here_string)

        return (False, "")

    @staticmethod
    def is_heredoc_quoted(heredoc_line: str) -> bool:
        r"""Detect if heredoc terminator is quoted (suppresses expansion).

        In bash, heredoc terminators can be quoted in three ways:
        - Single quotes: <<'EOF'
        - Double quotes: <<"EOF"
        - Backslash escape: <<\EOF (or <<E\OF - any escaping)

        All quoted forms suppress variable expansion inside the heredoc.

        Args:
            heredoc_line: The line containing the heredoc declaration

        Returns:
            True if terminator has any quoting (expansion disabled)
            False if terminator is unquoted (expansion enabled)

        Example:
            >>> BashParser.is_heredoc_quoted("cat <<'EOF'")
            True
            >>> BashParser.is_heredoc_quoted('cat <<"END"')
            True
            >>> BashParser.is_heredoc_quoted(r'cat <<\MARKER')
            True
            >>> BashParser.is_heredoc_quoted("cat <<EOF")
            False
        """
        # Pattern: Check for any quote character or backslash after <<
        # Handles: <<'...'  <<"..."  <<\...  <<-'...'  <<-"..."  <<-\...
        # Also handles partial escaping like <<E\OF (backslash anywhere means quoted)
        quoted_pattern = re.compile(r'<<-?\s*([\'"]|[^\s]*\\)')
        return bool(quoted_pattern.search(heredoc_line))

    @staticmethod
    def is_line_continuation(line: str) -> bool:
        """Check if line ends with backslash continuation.

        Args:
            line: Line to check

        Returns:
            True if line ends with backslash

        Example:
            >>> BashParser.is_line_continuation('echo "test" \\\\')
            True
            >>> BashParser.is_line_continuation('echo "test"')
            False
        """
        from .constants import LINE_CONTINUATION

        return LINE_CONTINUATION.search(line) is not None
