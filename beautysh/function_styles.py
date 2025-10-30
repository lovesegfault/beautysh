"""Function style definitions with pre-compiled regex patterns."""

import re
from enum import Enum
from typing import Pattern


class FunctionStyle(Enum):
    """Bash function declaration styles with compiled regex patterns.

    Bash supports three function declaration styles:
    - FNPAR: function keyword with parentheses (e.g., function foo())
    - FNONLY: function keyword without parentheses (e.g., function foo)
    - PARONLY: no function keyword, only parentheses (e.g., foo())

    Each style has a pre-compiled regex pattern for detection and a
    replacement string for transformation.
    """

    FNPAR = (
        0,
        "fnpar",
        re.compile(r"\bfunction\s+([\w:@-]+)\s*\(\s*\)\s*"),
        r"function \g<1>() ",
        "function foo()",
    )
    FNONLY = (
        1,
        "fnonly",
        re.compile(r"\bfunction\s+([\w:@-]+)\s*"),
        r"function \g<1> ",
        "function foo",
    )
    PARONLY = (
        2,
        "paronly",
        re.compile(r"\b\s*([\w:@-]+)\s*\(\s*\)\s*"),
        r"\g<1>() ",
        "foo()",
    )

    def __init__(
        self,
        index: int,
        style_name: str,
        pattern: Pattern,
        replacement: str,
        example: str,
    ):
        """Initialize function style.

        Args:
            index: Numeric index (0-2)
            style_name: String name (fnpar/fnonly/paronly)
            pattern: Pre-compiled regex pattern
            replacement: Replacement string for re.sub
            example: Example of this style
        """
        self.index = index
        self.style_name = style_name
        self.pattern = pattern
        self.replacement = replacement
        self.example = example

    def matches(self, line: str) -> bool:
        """Check if line matches this function style.

        Args:
            line: Line to check

        Returns:
            True if line matches this style

        Example:
            >>> FunctionStyle.FNPAR.matches('function foo() {')
            True
            >>> FunctionStyle.FNPAR.matches('foo() {')
            False
        """
        return self.pattern.search(line) is not None

    def transform_to(self, line: str, target_style: "FunctionStyle") -> str:
        """Transform line from this style to target style.

        Args:
            line: Line containing function declaration
            target_style: Target function style

        Returns:
            Transformed line

        Example:
            >>> FunctionStyle.FNPAR.transform_to('function foo() {', FunctionStyle.PARONLY)
            'foo() {'
        """
        return self.pattern.sub(target_style.replacement, line).strip()

    @classmethod
    def detect(cls, line: str) -> "FunctionStyle | None":
        """Detect function style in a line.

        IMPORTANT: Patterns must be tested in sequence (FNPAR -> FNONLY -> PARONLY)
        to avoid false matches.

        Args:
            line: Line to analyze

        Returns:
            Detected FunctionStyle or None

        Example:
            >>> FunctionStyle.detect('function foo() {')
            <FunctionStyle.FNPAR: ...>
            >>> FunctionStyle.detect('function bar {')
            <FunctionStyle.FNONLY: ...>
            >>> FunctionStyle.detect('baz() {')
            <FunctionStyle.PARONLY: ...>
        """
        # Test in order: FNPAR -> FNONLY -> PARONLY
        for style in [cls.FNPAR, cls.FNONLY, cls.PARONLY]:
            if style.matches(line):
                return style
        return None

    @classmethod
    def from_name(cls, name: str) -> "FunctionStyle | None":
        """Get function style by name.

        Args:
            name: Style name (fnpar/fnonly/paronly)

        Returns:
            FunctionStyle or None if invalid

        Example:
            >>> FunctionStyle.from_name('fnpar')
            <FunctionStyle.FNPAR: ...>
            >>> FunctionStyle.from_name('invalid')
            None
        """
        for style in cls:
            if style.style_name == name:
                return style
        return None

    @classmethod
    def from_index(cls, index: int) -> "FunctionStyle | None":
        """Get function style by index.

        Args:
            index: Style index (0-2)

        Returns:
            FunctionStyle or None if invalid

        Example:
            >>> FunctionStyle.from_index(0)
            <FunctionStyle.FNPAR: ...>
            >>> FunctionStyle.from_index(5)
            None
        """
        for style in cls:
            if style.index == index:
                return style
        return None

    @classmethod
    def all_names(cls) -> list[str]:
        """Get all valid style names.

        Returns:
            List of style names

        Example:
            >>> FunctionStyle.all_names()
            ['fnpar', 'fnonly', 'paronly']
        """
        return [style.style_name for style in cls]
