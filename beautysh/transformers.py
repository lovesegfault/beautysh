"""Style transformation utilities for Bash scripts."""

from typing import Optional

from .types import FunctionStyle


class FunctionStyleParser:
    """Parser for function style command-line arguments."""

    STYLE_NAMES = {
        "fnpar": FunctionStyle.FNPAR,
        "fnonly": FunctionStyle.FNONLY,
        "paronly": FunctionStyle.PARONLY,
    }

    @classmethod
    def parse_function_style(cls, style_name: str) -> Optional[FunctionStyle]:
        """Parse function style name to FunctionStyle enum.

        Args:
            style_name: Style name ('fnpar', 'fnonly', or 'paronly')

        Returns:
            FunctionStyle enum value or None if invalid
        """
        return cls.STYLE_NAMES.get(style_name)

    @classmethod
    def get_style_names(cls) -> list:
        """Get list of valid style names.

        Returns:
            List of valid style name strings
        """
        return list(cls.STYLE_NAMES.keys())
