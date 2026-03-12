"""Style transformation utilities for Bash scripts.

Pure functions that rewrite a single line to match a requested style.
"""

import logging
import re
from typing import Optional

from .constants import SIMPLE_VARIABLE, SPACE_BEFORE_DOUBLE_SEMICOLON
from .function_styles import FunctionStyle
from .types import VariableStyle

logger = logging.getLogger(__name__)


def change_function_style(
    stripped_record: str,
    detected_style: FunctionStyle,
    target_style: Optional[FunctionStyle],
) -> str:
    """Convert function declaration from one style to another.

    Args:
        stripped_record: The line containing a function declaration
        detected_style: The style detected in the line
        target_style: The desired target style, or None for no change

    Returns:
        Line with function style converted, or unchanged if no target requested

    Example:
        >>> change_function_style(
        ...     'function foo() {', FunctionStyle.FNPAR, FunctionStyle.PARONLY)
        'foo() {'
    """
    if target_style is None:
        return stripped_record

    # Always apply the replacement to normalize spacing, even if same style
    changed_record = detected_style.transform_to(stripped_record, target_style)

    logger.debug(
        f"Changed function style from {detected_style.style_name} to "
        f"{target_style.style_name}: {stripped_record} -> {changed_record}"
    )

    return changed_record


def apply_variable_style(line: str, style: VariableStyle) -> str:
    """Apply variable style transformation to a line.

    Currently supports:
    - 'braces': Transform $VAR to ${VAR}

    Variables inside single-quoted strings are skipped since bash doesn't
    expand them (issue #268).

    Args:
        line: The line to transform
        style: Variable style to apply (callers guard None themselves)

    Returns:
        Transformed line with variable style applied

    Example:
        >>> apply_variable_style('echo $HOME', 'braces')
        'echo ${HOME}'
        >>> apply_variable_style('echo ${VAR}', 'braces')
        'echo ${VAR}'
        >>> apply_variable_style('echo $1', 'braces')
        'echo $1'
        >>> apply_variable_style("foo='$bar'", 'braces')
        "foo='$bar'"
    """
    assert style == "braces"  # only supported value; Literal enforces at call site

    # Find all single-quoted string regions (variables inside are not expanded in bash)
    single_quote_regions = [(m.start(), m.end()) for m in re.finditer(r"'[^']*'", line)]

    def is_in_single_quotes(pos: int) -> bool:
        return any(start <= pos < end for start, end in single_quote_regions)

    # Transform $VAR to ${VAR}, but only for variables outside single quotes
    # Pattern: $ followed by alphanumeric/underscore, but not already in braces
    result = []
    last_end = 0

    for match in SIMPLE_VARIABLE.finditer(line):
        result.append(line[last_end : match.start()])

        if is_in_single_quotes(match.start()):
            result.append(match.group(0))
        else:
            result.append(f"${{{match.group(1)}}}")

        last_end = match.end()

    result.append(line[last_end:])
    transformed = "".join(result)

    if transformed != line:
        logger.debug(f"Applied variable braces style: {line} -> {transformed}")

    return transformed


def ensure_space_before_double_semicolon(line: str) -> str:
    """Ensure space before ;; terminators in case statements.

    Args:
        line: Line to process

    Returns:
        Line with space added before ;; if needed

    Example:
        >>> ensure_space_before_double_semicolon('foo;;')
        'foo ;;'
        >>> ensure_space_before_double_semicolon('foo ;;')
        'foo ;;'
    """
    return SPACE_BEFORE_DOUBLE_SEMICOLON.sub(r"\1 ;;", line)
