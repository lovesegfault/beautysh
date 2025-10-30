"""Style transformation utilities for Bash scripts."""

import logging
import re
from typing import Optional

from .constants import (
    FUNCTION_STYLE_PATTERNS,
    FUNCTION_STYLE_REPLACEMENTS,
    SIMPLE_VARIABLE,
    SPACE_BEFORE_DOUBLE_SEMICOLON,
    VARIABLE_STYLE_BRACES,
)

logger = logging.getLogger(__name__)


class StyleTransformer:
    """Handles style transformations for Bash scripts.

    This class provides utilities for transforming function declaration
    styles and variable reference styles according to user preferences.
    """

    @staticmethod
    def change_function_style(
        stripped_record: str,
        detected_style: Optional[int],
        target_style: Optional[int],
    ) -> str:
        """Convert function declaration from one style to another.

        Converts between three Bash function styles:
        0. function foo()  - fnpar style
        1. function foo    - fnonly style
        2. foo()          - paronly style

        Args:
            stripped_record: The line containing function declaration
            detected_style: The style detected in the line (0-2), or None
            target_style: The desired target style (0-2), or None for no change

        Returns:
            Line with function style converted, or unchanged if no conversion needed

        Example:
            >>> StyleTransformer.change_function_style('function foo() {', 0, 2)
            'foo() {'
            >>> StyleTransformer.change_function_style('foo() {', 2, 1)
            'function foo {'
            >>> StyleTransformer.change_function_style('echo test', None, 0)
            'echo test'
        """
        if detected_style is None:
            return stripped_record

        if target_style is None:
            # User does not want to enforce any specific function style
            return stripped_record

        # Always apply the replacement to normalize spacing, even if same style
        regex = FUNCTION_STYLE_PATTERNS[detected_style]
        replacement = FUNCTION_STYLE_REPLACEMENTS[target_style]
        changed_record = re.sub(regex, replacement, stripped_record)

        logger.debug(
            f"Changed function style from {detected_style} to {target_style}: "
            f"{stripped_record} -> {changed_record.strip()}"
        )

        return changed_record.strip()

    @staticmethod
    def apply_variable_style(line: str, style: Optional[str]) -> str:
        """Apply variable style transformation to a line.

        Currently supports:
        - 'braces': Transform $VAR to ${VAR}

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
        """
        if style != VARIABLE_STYLE_BRACES:
            return line

        # Transform $VAR to ${VAR}, but only for simple variables
        # Pattern: $ followed by alphanumeric/underscore, but not already in braces
        # Negative lookbehind (?<!{) ensures we don't match ${VAR}
        # \b word boundary ensures we get complete variable names
        transformed = SIMPLE_VARIABLE.sub(r"${\1}", line)

        if transformed != line:
            logger.debug(f"Applied variable braces style: {line} -> {transformed}")

        return transformed

    @staticmethod
    def ensure_space_before_double_semicolon(line: str, in_case: bool) -> str:
        """Ensure space before ;; terminators in case statements.

        Args:
            line: Line to process
            in_case: Whether we're currently in a case statement

        Returns:
            Line with space added before ;; if needed

        Example:
            >>> StyleTransformer.ensure_space_before_double_semicolon('foo;;', True)
            'foo ;;'
            >>> StyleTransformer.ensure_space_before_double_semicolon('foo ;;', True)
            'foo ;;'
        """
        if not in_case:
            return line

        return SPACE_BEFORE_DOUBLE_SEMICOLON.sub(r"\1 ;;", line)


class FunctionStyleParser:
    """Parser for function style command-line arguments."""

    STYLE_NAMES = {
        "fnpar": 0,
        "fnonly": 1,
        "paronly": 2,
    }

    @classmethod
    def parse_function_style(cls, style_name: str) -> Optional[int]:
        """Parse function style name to internal index.

        Args:
            style_name: Style name ('fnpar', 'fnonly', or 'paronly')

        Returns:
            Style index (0, 1, or 2) or None if invalid

        Example:
            >>> FunctionStyleParser.parse_function_style('fnpar')
            0
            >>> FunctionStyleParser.parse_function_style('paronly')
            2
            >>> FunctionStyleParser.parse_function_style('invalid')
            None
        """
        return cls.STYLE_NAMES.get(style_name)

    @classmethod
    def get_style_names(cls) -> list:
        """Get list of valid style names.

        Returns:
            List of valid style name strings

        Example:
            >>> FunctionStyleParser.get_style_names()
            ['fnpar', 'fnonly', 'paronly']
        """
        return list(cls.STYLE_NAMES.keys())
