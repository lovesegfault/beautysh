"""Style transformation utilities for Bash scripts."""

import logging
import re
from typing import Optional

from .constants import (
    SIMPLE_VARIABLE,
    SPACE_BEFORE_DOUBLE_SEMICOLON,
    VARIABLE_STYLE_BRACES,
)
from .function_styles import FunctionStyle

logger = logging.getLogger(__name__)


class StyleTransformer:
    """Handles style transformations for Bash scripts.

    This class provides utilities for transforming function declaration
    styles and variable reference styles according to user preferences.
    """

    @staticmethod
    def change_function_style(
        stripped_record: str,
        detected_style: Optional[FunctionStyle],
        target_style: Optional[FunctionStyle],
    ) -> str:
        """Convert function declaration from one style to another.

        Args:
            stripped_record: The line containing function declaration
            detected_style: The style detected in the line, or None
            target_style: The desired target style, or None for no change

        Returns:
            Line with function style converted, or unchanged if no conversion needed

        Example:
            >>> StyleTransformer.change_function_style(
            ...     'function foo() {', FunctionStyle.FNPAR, FunctionStyle.PARONLY)
            'foo() {'
            >>> StyleTransformer.change_function_style('echo test', None, FunctionStyle.FNPAR)
            'echo test'
        """
        if detected_style is None or target_style is None:
            return stripped_record

        # Always apply the replacement to normalize spacing, even if same style
        changed_record = detected_style.transform_to(stripped_record, target_style)

        logger.debug(
            f"Changed function style from {detected_style.style_name} to "
            f"{target_style.style_name}: {stripped_record} -> {changed_record}"
        )

        return changed_record

    @staticmethod
    def apply_variable_style(line: str, style: Optional[str]) -> str:
        """Apply variable style transformation to a line.

        Currently supports:
        - 'braces': Transform $VAR to ${VAR}

        Variables inside single-quoted strings are skipped since bash doesn't
        expand them (issue #268).

        Args:
            line: The line to transform
            style: Variable style to apply ('braces' or None)

        Returns:
            Transformed line with variable style applied

        Example:
            >>> StyleTransformer.apply_variable_style('echo $HOME', 'braces')
            'echo ${HOME}'
            >>> StyleTransformer.apply_variable_style('echo ${VAR}', 'braces')
            'echo ${VAR}'
            >>> StyleTransformer.apply_variable_style('echo $1', 'braces')
            'echo ${1}'
            >>> StyleTransformer.apply_variable_style("foo='$bar'", 'braces')
            "foo='$bar'"
        """
        if style != VARIABLE_STYLE_BRACES:
            return line

        # Find all single-quoted string regions (variables inside are not expanded in bash)
        single_quote_regions = []
        for match in re.finditer(r"'[^']*'", line):
            single_quote_regions.append((match.start(), match.end()))

        # Helper function to check if a position is inside single quotes
        def is_in_single_quotes(pos: int) -> bool:
            return any(start <= pos < end for start, end in single_quote_regions)

        # Transform $VAR to ${VAR}, but only for variables outside single quotes
        # Pattern: $ followed by alphanumeric/underscore, but not already in braces
        result = []
        last_end = 0

        for match in SIMPLE_VARIABLE.finditer(line):
            # Add text before this match
            result.append(line[last_end : match.start()])

            # Check if this variable is inside single quotes
            if is_in_single_quotes(match.start()):
                # Keep the original variable (don't transform)
                result.append(match.group(0))
            else:
                # Transform the variable
                result.append(f"${{{match.group(1)}}}")

            last_end = match.end()

        # Add remaining text after last match
        result.append(line[last_end:])
        transformed = "".join(result)

        if transformed != line:
            logger.debug(f"Applied variable braces style: {line} -> {transformed}")

        return transformed

    @staticmethod
    def ensure_space_before_double_semicolon(line: str) -> str:
        """Ensure space before ;; terminators in case statements.

        Args:
            line: Line to process

        Returns:
            Line with space added before ;; if needed

        Example:
            >>> StyleTransformer.ensure_space_before_double_semicolon('foo;;')
            'foo ;;'
            >>> StyleTransformer.ensure_space_before_double_semicolon('foo ;;')
            'foo ;;'
        """
        return SPACE_BEFORE_DOUBLE_SEMICOLON.sub(r"\1 ;;", line)
