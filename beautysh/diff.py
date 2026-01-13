"""Diff output utilities for beautysh."""

import difflib
import logging
from collections.abc import Iterator

from colorama import Fore

logger = logging.getLogger(__name__)


class DiffFormatter:
    """Formats and displays diffs between original and formatted code."""

    def __init__(self, use_color: bool = True):
        """Initialize diff formatter.

        Args:
            use_color: Whether to use colored output
        """
        self.use_color = use_color

    def color_diff(self, diff: Iterator[str]) -> Iterator[str]:
        """Apply color to diff output lines.

        Args:
            diff: Iterator of diff lines from difflib

        Yields:
            Colored diff lines

        Example:
            >>> formatter = DiffFormatter(use_color=True)
            >>> diff = ['+added', '-removed', ' context']
            >>> list(formatter.color_diff(diff))
            ['\x1b[32m+added\x1b[39m', '\x1b[31m-removed\x1b[39m', ' context']
        """
        for line in diff:
            if line.startswith("+"):
                yield Fore.GREEN + line + Fore.RESET
            elif line.startswith("-"):
                yield Fore.RED + line + Fore.RESET
            elif line.startswith("^"):
                yield Fore.BLUE + line + Fore.RESET
            else:
                yield line

    def print_diff(self, original: str, formatted: str) -> None:
        """Print unified diff between original and formatted content.

        Args:
            original: Original file content
            formatted: Formatted file content

        Example:
            >>> formatter = DiffFormatter()
            >>> original = 'if true;then\\necho "test"'
            >>> formatted = 'if true; then\\n    echo "test"'
            >>> formatter.print_diff(original, formatted)
            --- original
            +++ formatted
            @@ -1,2 +1,2 @@
            -if true;then
            -echo "test"
            +if true; then
            +    echo "test"
        """
        original_lines = original.splitlines()
        formatted_lines = formatted.splitlines()

        delta = difflib.unified_diff(
            original_lines,
            formatted_lines,
            fromfile="original",
            tofile="formatted",
            lineterm="",
        )

        if self.use_color:
            delta = self.color_diff(delta)

        diff_output = "\n".join(delta)
        if diff_output:
            print(diff_output)
            logger.debug(f"Printed diff ({len(original_lines)} -> {len(formatted_lines)} lines)")
