"""Core formatting logic for Bash scripts using PEG parser."""

import logging
import re
from typing import Optional

from .grammar import parse_bash
from .types import FunctionStyle, VariableStyle
from .visitors.formatter import FormatterVisitor

logger = logging.getLogger(__name__)


def _preprocess_formatter_directives(source: str) -> tuple[str, dict[int, str]]:
    """Extract @formatter:off/on regions before parsing.

    Content between `# @formatter:off` and `# @formatter:on` is extracted
    and replaced with placeholder comments. This allows the parser to handle
    the remaining code while preserving the original content verbatim.

    Returns:
        - Source with placeholder comments for disabled regions
        - Mapping from region ID to original content
    """
    regions: dict[int, str] = {}
    lines = source.split('\n')
    result_lines = []
    in_disabled_region = False
    region_lines: list[str] = []
    region_id = 0

    for line in lines:
        stripped = line.strip()
        if stripped == '# @formatter:off':
            in_disabled_region = True
            region_lines = [line]
        elif stripped == '# @formatter:on' and in_disabled_region:
            region_lines.append(line)
            regions[region_id] = '\n'.join(region_lines)
            result_lines.append(f'# __BEAUTYSH_NOFORMAT_{region_id}__')
            region_id += 1
            in_disabled_region = False
            region_lines = []
        elif in_disabled_region:
            region_lines.append(line)
        else:
            result_lines.append(line)

    # Handle unclosed @formatter:off (preserve rest of file)
    if in_disabled_region and region_lines:
        regions[region_id] = '\n'.join(region_lines)
        result_lines.append(f'# __BEAUTYSH_NOFORMAT_{region_id}__')

    return '\n'.join(result_lines), regions


def _restore_formatter_regions(formatted: str, regions: dict[int, str]) -> str:
    """Restore original content for @formatter:off regions.

    Replaces placeholder comments with the original verbatim content.
    """
    result = formatted
    for region_id, original_content in regions.items():
        # Match the placeholder with any leading indentation
        pattern = rf'^[ \t]*# __BEAUTYSH_NOFORMAT_{region_id}__$'
        result = re.sub(pattern, original_content, result, flags=re.MULTILINE)
    return result


class BashFormatter:
    """Formatter for Bash scripts using PEG-based parsing.

    This class provides the main API for formatting Bash scripts.
    It uses a PEG grammar to parse scripts into an AST and then
    uses a visitor to produce formatted output.
    """

    def __init__(
        self,
        indent_size: int = 4,
        tab_str: str = " ",
        function_style: Optional[FunctionStyle] = None,
        variable_style: Optional[VariableStyle] = None,
    ):
        """Initialize formatter with configuration.

        Args:
            indent_size: Number of spaces (or 1 for tabs) for indentation
            tab_str: String to use for indentation (' ' or '\\t')
            function_style: Function style to enforce, or None to preserve original
            variable_style: Variable style to enforce, or None to preserve original
        """
        self.indent_size = indent_size
        self.tab_str = tab_str
        self.function_style = function_style
        self.variable_style = variable_style

    def beautify_string(self, data: str, path: str = "") -> tuple[str, bool]:
        """Beautify a Bash script string.

        This is the main entry point for formatting. It parses the script
        into an AST and then produces formatted output.

        Args:
            data: Complete Bash script as string
            path: File path (for error messages)

        Returns:
            Tuple of (formatted_script, has_error)
        """
        try:
            # Preprocess to extract @formatter:off regions
            processed_data, noformat_regions = _preprocess_formatter_directives(data)

            # Parse into AST
            ast = parse_bash(processed_data)

            # Format using visitor
            use_tabs = self.tab_str == "\t"
            formatter = FormatterVisitor(
                indent_size=self.indent_size,
                use_tabs=use_tabs,
                function_style=self.function_style,
                variable_style=self.variable_style,
            )
            result = formatter.visit(ast)

            # Restore @formatter:off regions with original content
            if noformat_regions:
                result = _restore_formatter_regions(result, noformat_regions)

            # Ensure trailing newline if original had one
            if data.endswith('\n') and not result.endswith('\n'):
                result += '\n'

            return result, False

        except Exception as e:
            logger.error(f"Error parsing {path}: {e}")
            # On parse error, return original data unchanged
            return data, True
