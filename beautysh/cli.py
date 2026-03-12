"""Command-line interface for beautysh."""

import argparse
import logging
import os
import sys
from importlib.metadata import PackageNotFoundError, version
from typing import Any, Optional

from .config import (
    ConfigError,
    load_config_from_editorconfig,
    load_config_from_pyproject,
    merge_configs,
)
from .constants import DEFAULT_TAB_SIZE, TAB_CHARACTER
from .diff import DiffFormatter
from .formatter import BashFormatter
from .function_styles import FunctionStyle

logger = logging.getLogger(__name__)


class BeautyshCLI:
    """Command-line interface handler for beautysh."""

    def __init__(self) -> None:
        """Initialize CLI handler."""
        self.formatter: Optional[BashFormatter] = None
        self.diff_formatter: Optional[DiffFormatter] = None
        self.backup = False
        self.check_only = False
        self.force = False

    def get_version(self) -> str:
        """Get beautysh version.

        Returns:
            Version string or "Not Available"
        """
        try:
            return version("beautysh")
        except PackageNotFoundError:
            return "Not Available"

    def print_help(self, parser: argparse.ArgumentParser) -> None:
        """Print help message with additional information.

        Args:
            parser: Argument parser to print help from
        """
        parser.print_help()
        sys.stdout.write(
            "\nBash function styles that can be specified via --force-function-style are:\n"
        )
        for style in FunctionStyle:
            sys.stdout.write(f"  {style.style_name}: {style.description}\n")
        sys.stdout.write("\n")

    def create_parser(self, config: dict[str, Any]) -> argparse.ArgumentParser:
        """Create argument parser with defaults from config.

        Args:
            config: Configuration dictionary with default values

        Returns:
            Configured ArgumentParser instance
        """
        parser = argparse.ArgumentParser(
            description=f"A Bash beautifier for the masses, version {self.get_version()}",
            add_help=False,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        )
        parser.add_argument(
            "--indent-size",
            "-i",
            type=int,
            default=config.get("indent_size", DEFAULT_TAB_SIZE),
            help="Sets the number of spaces to be used in indentation.",
        )
        parser.add_argument(
            "--backup",
            "-b",
            action="store_true",
            default=config.get("backup", False),
            help="Beautysh will create a backup file in the same path as the original.",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            default=config.get("force", False),
            help="Write output even if the formatter reports an error (best-effort mode).",
        )
        parser.add_argument(
            "--check",
            "-c",
            action="store_true",
            default=config.get("check", False),
            help="Beautysh will just check the files without doing any in-place beautify.",
        )
        parser.add_argument(
            "--tab",
            "-t",
            action="store_true",
            default=config.get("tab", False),
            help="Sets indentation to tabs instead of spaces.",
        )
        parser.add_argument(
            "--force-function-style",
            "-s",
            type=str,
            default=config.get("force_function_style"),
            help="Force a specific Bash function formatting. See below for more info.",
        )
        parser.add_argument(
            "--variable-style",
            type=str,
            choices=["braces"],
            default=config.get("variable_style"),
            help="Force a specific variable style. 'braces' transforms $VAR to ${VAR}.",
        )
        parser.add_argument(
            "--version",
            "-v",
            action="store_true",
            help="Prints the version and exits.",
        )
        parser.add_argument(
            "--help",
            "-h",
            action="store_true",
            help="Print this help message.",
        )
        parser.add_argument(
            "files",
            metavar="FILE",
            nargs="*",
            help="Files to be beautified. This is mandatory. "
            "If - is provided as filename, then beautysh reads "
            "from stdin and writes on stdout.",
        )
        return parser

    def load_configuration(self, argv: list[str]) -> dict[str, Any]:
        """Load configuration from all sources.

        Priority: EditorConfig < pyproject.toml < CLI args

        Args:
            argv: Command-line arguments

        Returns:
            Merged configuration dictionary
        """
        editorconfig_settings: dict[str, Any] = {}

        # Load EditorConfig if processing a file
        if argv and argv[0] not in ["-h", "--help", "-v", "--version"]:
            for arg in argv:
                if not arg.startswith("-") and arg != "-":
                    editorconfig_settings = load_config_from_editorconfig(arg)
                    break

        # Load pyproject.toml config
        pyproject_config = load_config_from_pyproject()

        # Merge configs
        return merge_configs(editorconfig_settings, pyproject_config)

    def configure_formatter(self, args: argparse.Namespace) -> None:
        """Configure formatter based on parsed arguments.

        Args:
            args: Parsed command-line arguments
        """
        indent_size = args.indent_size
        tab_str = " "

        if args.tab:
            indent_size = 1
            tab_str = TAB_CHARACTER

        apply_function_style = None
        if args.force_function_style is not None:
            apply_function_style = FunctionStyle.from_name(args.force_function_style)
            if apply_function_style is None:
                raise ValueError(
                    f"Invalid value {args.force_function_style!r} for --force-function-style. "
                    f"See --help for details."
                )

        self.formatter = BashFormatter(
            indent_size=indent_size,
            tab_str=tab_str,
            apply_function_style=apply_function_style,
            variable_style=args.variable_style,
        )

        use_color = "NO_COLOR" not in os.environ
        self.diff_formatter = DiffFormatter(use_color=use_color)
        self.backup = args.backup
        self.check_only = args.check
        self.force = args.force

        logger.debug(
            f"Configured formatter: indent_size={indent_size}, "
            f"tab_str={tab_str!r}, function_style={apply_function_style}"
        )

    def read_file(self, filepath: str) -> str:
        """Read file content.

        Args:
            filepath: Path to file

        Returns:
            File content as string
        """
        with open(filepath, encoding="utf-8") as f:
            return f.read()

    def write_file(self, filepath: str, content: str) -> None:
        """Write content to file.

        Args:
            filepath: Path to file
            content: Content to write
        """
        with open(filepath, "w", newline="\n", encoding="utf-8") as f:
            f.write(content)

    def beautify_file(self, path: str) -> bool:
        """Beautify a single file.

        Args:
            path: File path, or "-" for stdin

        Returns:
            True if there was an error
        """
        if self.formatter is None:
            raise RuntimeError("Formatter not configured")

        if path == "-":
            # Read from stdin, write to stdout
            data = sys.stdin.read()
            result = self.formatter.beautify_string(data)
            if result.error:
                sys.stderr.write(f"(stdin): {result.error}\n")
            sys.stdout.write(result.output)
            return result.error is not None

        # Process named file
        data = self.read_file(path)
        result = self.formatter.beautify_string(data)

        if result.error:
            sys.stderr.write(f"{path}: {result.error}\n")

        if data != result.output:
            if self.check_only:
                # Check mode: any diff is a failure. Only show the diff if the
                # formatter succeeded (otherwise the output is unreliable).
                if result.error is None and self.diff_formatter:
                    self.diff_formatter.print_diff(data, result.output, path)
                return True
            elif result.error is not None and not self.force:
                sys.stderr.write(
                    f"Not writing {path}: formatter reported an error "
                    f"(use --force to write anyway)\n"
                )
            else:
                if self.backup:
                    self.write_file(path + ".bak", data)
                    logger.info(f"Created backup: {path}.bak")

                self.write_file(path, result.output)
                logger.info(f"Formatted: {path}")

        return result.error is not None

    def main(self, argv: list[str]) -> int:
        """Main entry point for CLI.

        Args:
            argv: Command-line arguments (excluding program name)

        Returns:
            Exit code (0 for success, 1 for error)
        """
        # Load configuration
        try:
            config = self.load_configuration(argv)
        except ConfigError as e:
            sys.stderr.write(f"{e}\n")
            return 2

        # Create and parse arguments
        parser = self.create_parser(config)
        args = parser.parse_args(argv)

        # Handle help and version
        if len(argv) < 1 or args.help:
            self.print_help(parser)
            return 0

        if args.version:
            sys.stdout.write(f"{self.get_version()}\n")
            return 0

        if not args.files:
            sys.stderr.write("Please provide at least one input file\n")
            return 1

        # Configure formatter
        try:
            self.configure_formatter(args)
        except ValueError as e:
            sys.stderr.write(f"{e}\n")
            return 1

        # Process files
        error = False
        for path in args.files:
            try:
                error |= self.beautify_file(path)
            except (OSError, UnicodeDecodeError) as e:
                logger.error(f"Error processing {path}: {e}")
                sys.stderr.write(f"Error processing {path}: {e}\n")
                error = True

        return 1 if error else 0
