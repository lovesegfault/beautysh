"""Command-line interface for beautysh."""

import argparse
import logging
import os
import sys
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any, Dict, List, Optional

from .config import (
    load_config_from_beautyshrc,
    load_config_from_editorconfig,
    load_config_from_file,
    load_config_from_pyproject,
    merge_configs,
)
from .constants import DEFAULT_TAB_SIZE, TAB_CHARACTER
from .diff import DiffFormatter
from .formatter import BashFormatter
from .transformers import FunctionStyleParser

logger = logging.getLogger(__name__)


class BeautyshCLI:
    """Command-line interface handler for beautysh."""

    def __init__(self):
        """Initialize CLI handler."""
        self.formatter: Optional[BashFormatter] = None
        self.diff_formatter: Optional[DiffFormatter] = None
        self.backup = False
        self.check_only = False
        self.config_file: Optional[str] = None

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
        sys.stdout.write(
            "  fnpar: function keyword, open/closed parentheses, e.g.      function foo()\n"
        )
        sys.stdout.write(
            "  fnonly: function keyword, no open/closed parentheses, e.g.  function foo\n"
        )
        sys.stdout.write("  paronly: no function keyword, open/closed parentheses, e.g. foo()\n")
        sys.stdout.write("\n")

    def create_parser(self, config: Dict[str, Any]) -> argparse.ArgumentParser:
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
            "--config",
            type=str,
            default=config.get("config"),
            help="Path to a specific configuration file (e.g., .beautyshrc). "
            "Overrides auto-discovered config files.",
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

    def load_configuration(self, argv: List[str]) -> Dict[str, Any]:
        """Load configuration from all sources.

        Priority: EditorConfig < pyproject.toml < .beautyshrc < --config file < CLI args

        Args:
            argv: Command-line arguments

        Returns:
            Merged configuration dictionary
        """
        editorconfig_settings: Dict[str, Any] = {}
        explicit_config_settings: Dict[str, Any] = {}

        config_file_path = None
        for i, arg in enumerate(argv):
            if arg == "--config":
                if i + 1 < len(argv):
                    config_file_path = argv[i + 1]
                break
            if arg.startswith("--config="):
                config_file_path = arg.split("=", 1)[1]
                break

        if config_file_path:
            self.config_file = config_file_path  # Store for later use
            explicit_config_settings = load_config_from_file(Path(config_file_path))

        # Load EditorConfig if processing a file
        if argv and argv[0] not in ["-h", "--help", "-v", "--version"]:
            for arg in argv:
                if not arg.startswith("-") and arg != "-":
                    editorconfig_settings = load_config_from_editorconfig(arg)
                    break

        # Load pyproject.toml config
        pyproject_config = load_config_from_pyproject()

        # Load .beautyshrc config
        beautyshrc_config = load_config_from_beautyshrc()

        # Merge configs
        return merge_configs(
            editorconfig_settings,
            pyproject_config,
            beautyshrc_config,
            explicit_config_settings,
        )

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

        if args.config:
            self.config_file = args.config

        apply_function_style = None
        if args.force_function_style is not None:
            apply_function_style = FunctionStyleParser.parse_function_style(
                args.force_function_style
            )
            if apply_function_style is None:
                sys.stdout.write("Invalid value for the function style. See --help for details.\n")
                sys.exit(1)

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

        logger.debug(
            f"Configured formatter: indent_size={indent_size}, "
            f"tab_str={repr(tab_str)}, function_style={apply_function_style}"
        )

    def read_file(self, filepath: str) -> str:
        """Read file content.

        Args:
            filepath: Path to file

        Returns:
            File content as string
        """
        with open(filepath) as f:
            return f.read()

    def write_file(self, filepath: str, content: str) -> None:
        """Write content to file.

        Args:
            filepath: Path to file
            content: Content to write
        """
        with open(filepath, "w", newline="\n") as f:
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

        error = False

        if path == "-":
            # Read from stdin, write to stdout
            data = sys.stdin.read()
            result, error = self.formatter.beautify_string(data, "(stdin)")
            sys.stdout.write(result)
        else:
            # Process named file
            data = self.read_file(path)
            result, error = self.formatter.beautify_string(data, path)

            if data != result:
                if self.check_only:
                    # Check mode: show diff and return error if different
                    if not error:
                        error = result != data
                        if error and self.diff_formatter:
                            self.diff_formatter.print_diff(data, result)
                else:
                    # Format mode: write changes
                    if self.backup:
                        self.write_file(path + ".bak", data)
                        logger.info(f"Created backup: {path}.bak")

                    self.write_file(path, result)
                    logger.info(f"Formatted: {path}")

        return error

    def main(self, argv: List[str]) -> int:
        """Main entry point for CLI.

        Args:
            argv: Command-line arguments (excluding program name)

        Returns:
            Exit code (0 for success, 1 for error)
        """
        # Load configuration
        config = self.load_configuration(argv)

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
            sys.stdout.write("Please provide at least one input file\n")
            return 1

        # Configure formatter
        self.configure_formatter(args)

        # Process files
        error = False
        for path in args.files:
            try:
                error |= self.beautify_file(path)
            except Exception as e:
                logger.error(f"Error processing {path}: {e}")
                sys.stderr.write(f"Error processing {path}: {e}\n")
                error = True

        return 1 if error else 0
