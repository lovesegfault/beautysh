"""Bash script parsing utilities.

All functions here are pure: they take a line (or simplified test record) and
return an analysis result. No state, no I/O.
"""

import logging
from typing import Optional

from .constants import (
    ARITHMETIC_PATTERN,
    BACKTICK_STRING,
    CASE_SPLIT_PATTERN,
    COMMENT,
    DO_CASE_PATTERN,
    DOUBLE_QUOTED_STRING,
    ESCAPED_CHAR,
    ESCAPED_DOUBLE_QUOTE,
    ESCAPED_SINGLE_QUOTE,
    HEREDOC_PATTERN,
    HEREDOC_QUOTED_PATTERN,
    HEREDOC_TERMINATOR,
    HERESTRING_PATTERN,
    LET_SHIFT_PATTERN,
    LINE_CONTINUATION,
    SINGLE_QUOTED_STRING,
    WEIRD_BACKTICK_STRING,
)
from .types import QuoteChar

logger = logging.getLogger(__name__)


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
        >>> get_test_record('if [ "$x" = "y" ]; then  # comment')
        'if [ = ]; then  '
        >>> get_test_record("echo 'hello world'")
        'echo '
    """
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


def detect_unclosed_quote(test_record: str) -> Optional[QuoteChar]:
    """Detect an unclosed quote on a test record.

    After get_test_record() has collapsed all properly closed quotes on
    the same line, any remaining quote indicates an unclosed multiline string.

    Args:
        test_record: Simplified line from get_test_record()

    Returns:
        The unclosed quote character, or None if all quotes are balanced.
        Double quotes take precedence if both are unclosed.

    Example:
        >>> detect_unclosed_quote('echo "test')
        '"'
        >>> detect_unclosed_quote("echo 'test")
        "'"
        >>> detect_unclosed_quote('echo ')
    """
    if test_record.count('"') % 2 == 1:
        return '"'
    if test_record.count("'") % 2 == 1:
        return "'"
    return None


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
        >>> normalize_do_case_lines(script)
        'while true; do\\ncase $x in'
    """
    lines = []

    for line in data.split("\n"):
        # Check if line contains both 'do' and 'case' or 'then' and 'case'
        test_line = get_test_record(line)

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


def detect_heredoc(test_record: str, stripped_record: str) -> Optional[str]:
    """Detect a here-document and extract its termination string.

    Detects here-docs (<<EOF or <<-EOF) while avoiding false positives
    from:
    - Here-strings (<<<)
    - Arithmetic expressions with shift operator ($((x << 2)))

    Args:
        test_record: Simplified line from get_test_record()
        stripped_record: Original stripped line

    Returns:
        The terminator string, or None if this line does not start a heredoc.

    Example:
        >>> detect_heredoc('cat <<EOF', 'cat <<EOF')
        'EOF'
        >>> detect_heredoc('cat <<-"END"', 'cat <<-"END"')
        'END'
        >>> detect_heredoc('echo <<<$var', 'echo <<<$var')
        >>> detect_heredoc('$(( x << 2 ))', '$(( x << 2 ))')
    """
    has_heredoc = HEREDOC_PATTERN.search(test_record)
    is_herestring = HERESTRING_PATTERN.search(test_record)
    is_arithmetic = ARITHMETIC_PATTERN.search(test_record) or LET_SHIFT_PATTERN.search(test_record)

    if has_heredoc and not is_herestring and not is_arithmetic:
        match = HEREDOC_TERMINATOR.search(stripped_record)
        if match:
            here_string = match.group(1)
            logger.debug(f"Detected here-doc with terminator: {here_string}")
            return here_string

    return None


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
        >>> is_heredoc_quoted("cat <<'EOF'")
        True
        >>> is_heredoc_quoted('cat <<"END"')
        True
        >>> is_heredoc_quoted(r'cat <<\MARKER')
        True
        >>> is_heredoc_quoted("cat <<EOF")
        False
    """
    # Handles: <<'...'  <<"..."  <<\...  <<-'...'  <<-"..."  <<-\...
    # Also handles partial escaping like <<E\OF (backslash anywhere means quoted)
    return bool(HEREDOC_QUOTED_PATTERN.search(heredoc_line))


def is_line_continuation(line: str) -> bool:
    """Check if line ends with backslash continuation.

    Args:
        line: Line to check

    Returns:
        True if line ends with backslash

    Example:
        >>> is_line_continuation('echo "test" \\\\')
        True
        >>> is_line_continuation('echo "test"')
        False
    """
    return LINE_CONTINUATION.search(line) is not None
