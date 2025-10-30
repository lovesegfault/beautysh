#!/usr/bin/env python3
"""A beautifier for Bash shell scripts written in Python."""
import argparse
import difflib
import os
import re
import sys
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib  # type: ignore[import-not-found,no-redef]

from colorama import Fore
from editorconfig import EditorConfigError, get_properties

# correct function style detection is obtained only if following regex are
# tested in sequence.  styles are listed as follows:
# 0) function keyword, open/closed parentheses, e.g.      function foo()
# 1) function keyword, NO open/closed parentheses, e.g.   function foo
# 2) NO function keyword, open/closed parentheses, e.g.   foo()
FUNCTION_STYLE_REGEX = [
    r"\bfunction\s+([\w:@-]+)\s*\(\s*\)\s*",
    r"\bfunction\s+([\w:@-]+)\s*",
    r"\b\s*([\w:@-]+)\s*\(\s*\)\s*",
]

FUNCTION_STYLE_REPLACEMENT = [r"function \g<1>() ", r"function \g<1> ", r"\g<1>() "]


def load_config_from_pyproject():
    """Load beautysh configuration from pyproject.toml if it exists."""
    pyproject_path = Path.cwd() / "pyproject.toml"

    if not pyproject_path.exists():
        return {}

    try:
        with open(pyproject_path, "rb") as f:
            data = tomllib.load(f)
        return data.get("tool", {}).get("beautysh", {})
    except Exception:
        # If we can't read the config, just return empty dict
        return {}


def load_config_from_editorconfig(filepath):
    """Load configuration from .editorconfig for the given file.

    Args:
        filepath: Path to the file being formatted (used to find relevant .editorconfig)

    Returns:
        dict: Configuration dictionary with beautysh-compatible keys
    """
    try:
        props = get_properties(str(filepath))
        config = {}

        # Map EditorConfig indent_style to beautysh tab setting
        if "indent_style" in props:
            if props["indent_style"] == "tab":
                config["tab"] = True
            elif props["indent_style"] == "space":
                config["tab"] = False

        # Map EditorConfig indent_size to beautysh indent_size
        if "indent_size" in props:
            try:
                config["indent_size"] = int(props["indent_size"])
            except (ValueError, TypeError):
                pass  # Invalid indent_size, ignore it

        return config
    except EditorConfigError:
        # If EditorConfig parsing fails, return empty config
        return {}


class Beautify:
    """Class to handle both module and non-module calls."""

    def __init__(self):
        """Set tab as space and it's value to 4."""
        self.tab_str = " "
        self.tab_size = 4
        self.backup = False
        self.check_only = False
        self.apply_function_style = None  # default is no change based on function style
        self.variable_style = None  # Options: 'braces' (force ${VAR}), None (no change)
        self.color = True

    def read_file(self, fp):
        """Read input file."""
        with open(fp) as f:
            return f.read()

    def write_file(self, fp, data):
        """Write output to a file."""
        with open(fp, "w", newline="\n") as f:
            f.write(data)

    def detect_function_style(self, test_record):
        """Returns the index for the function declaration style detected in the given string
        or None if no function declarations are detected."""
        index = 0
        # IMPORTANT: apply regex sequentially and stop on the first match:
        for regex in FUNCTION_STYLE_REGEX:
            if re.search(regex, test_record):
                return index
            index += 1
        return None

    def change_function_style(self, stripped_record, func_decl_style):
        """Converts a function definition syntax from the 'func_decl_style' to
        the one that has been set in self.apply_function_style and returns the
        string with the converted syntax."""
        if func_decl_style is None:
            return stripped_record
        if self.apply_function_style is None:
            # user does not want to enforce any specific function style
            return stripped_record
        regex = FUNCTION_STYLE_REGEX[func_decl_style]
        replacement = FUNCTION_STYLE_REPLACEMENT[self.apply_function_style]
        changed_record = re.sub(regex, replacement, stripped_record)
        return changed_record.strip()

    def get_test_record(self, source_line):
        """Takes the given Bash source code line and simplifies it by removing stuff that is not
        useful for the purpose of indentation level calculation"""
        # first of all, get rid of escaped special characters like single/double quotes
        # that may impact later "collapse" attempts
        test_record = source_line.replace("\\'", "")
        test_record = test_record.replace('\\"', "")

        # collapse multiple quotes between ' ... '
        test_record = re.sub(r"\'.*?\'", "", test_record)
        # collapse multiple quotes between " ... "
        test_record = re.sub(r'".*?"', "", test_record)
        # collapse multiple quotes between ` ... `
        test_record = re.sub(r"`.*?`", "", test_record)
        # collapse multiple quotes between \` ... ' (weird case)
        test_record = re.sub(r"\\`.*?\'", "", test_record)
        # strip out any escaped single characters
        test_record = re.sub(r"\\.", "", test_record)
        # remove '#' comments
        test_record = re.sub(r"(\A|\s)(#.*)", "", test_record, 1)
        return test_record

    def detect_unclosed_quote(self, test_record):
        """Detect if test_record has an unclosed quote after collapsing same-line quotes.

        After get_test_record() has collapsed all properly closed quotes on the same line,
        any remaining quotes indicate an unclosed multiline string.

        Returns:
            tuple: (has_unclosed_double_quote, has_unclosed_single_quote)
        """
        unclosed_double = test_record.count('"') % 2 == 1
        unclosed_single = test_record.count("'") % 2 == 1
        return (unclosed_double, unclosed_single)

    def normalize_do_case_lines(self, data):
        """Split lines where 'do case' or 'then case' appear together.

        This normalizes bash code like:
            while x; do case $y in
        Into:
            while x; do
            case $y in

        This makes indentation handling more straightforward.
        """
        lines = []
        for line in data.split("\n"):
            # Check if line contains both 'do' and 'case' or 'then' and 'case'
            test_line = self.get_test_record(line)

            # Look for patterns like 'do case' or 'then case'
            match = re.search(r"(\s|\A|;)(do|then)(\s+)(case\s)", test_line)
            if match:
                # Find the position in the original line
                # We need to preserve any content before 'case'
                case_match = re.search(r"(\s+)(case\s)", line)
                if case_match:
                    split_pos = case_match.start(2)  # Position of 'case'
                    before = line[:split_pos].rstrip()
                    after = line[split_pos:]
                    lines.append(before)
                    lines.append(after)
                else:
                    lines.append(line)
            else:
                lines.append(line)

        return "\n".join(lines)

    def beautify_string(self, data, path=""):
        """Beautify string (file part)."""
        # Preprocess: split 'do case' and 'then case' onto separate lines
        data = self.normalize_do_case_lines(data)

        tab = 0
        case_level = 0
        prev_line_had_continue = False
        continue_line = False
        started_multiline_quoted_string = False
        ended_multiline_quoted_string = False
        open_brackets = 0
        in_here_doc = False
        # New: track unclosed multiline strings (without backslash continuation)
        in_multiline_string = False
        multiline_string_quote_char = None
        here_string = ""
        output = []
        line = 1
        formatter = True
        for record in re.split("\n", data):
            record = record.rstrip()
            stripped_record = record.strip()

            # preserve blank lines
            if not stripped_record:
                output.append(stripped_record)
                continue

            # ensure space before ;; terminators in case statements
            if case_level:
                stripped_record = re.sub(r"(\S);;", r"\1 ;;", stripped_record)

            test_record = self.get_test_record(stripped_record)

            # Handle multiline strings (without backslash continuation)
            # Check if we're currently inside a multiline string
            if in_multiline_string:
                # Check if this line closes the string
                if multiline_string_quote_char in stripped_record:
                    # Count occurrences of the quote character
                    quote_count = stripped_record.count(multiline_string_quote_char)
                    if quote_count % 2 == 1:  # Odd number = closing quote
                        in_multiline_string = False
                        multiline_string_quote_char = None
                # Pass through unchanged to preserve string content
                output.append(record)
                line += 1
                continue

            # Check if a new multiline string starts on this line
            unclosed_double, unclosed_single = self.detect_unclosed_quote(test_record)
            if unclosed_double or unclosed_single:
                in_multiline_string = True
                multiline_string_quote_char = '"' if unclosed_double else "'"
                # Apply current indentation to the line that starts the string
                output.append((self.tab_str * self.tab_size * tab) + stripped_record)
                line += 1
                continue

            # detect whether this line ends with line continuation character:
            prev_line_had_continue = continue_line
            continue_line = True if (re.search(r"\\$", stripped_record) is not None) else False
            inside_multiline_quoted_string = (
                prev_line_had_continue and continue_line and started_multiline_quoted_string
            )

            if not continue_line and prev_line_had_continue and started_multiline_quoted_string:
                # remove contents of strings initiated on previous lines and
                # that are ending on this line:
                [test_record, num_subs] = re.subn(r'^[^"]*"', "", test_record)
                ended_multiline_quoted_string = True if num_subs > 0 else False
            else:
                ended_multiline_quoted_string = False

            if (
                (in_here_doc)
                or (inside_multiline_quoted_string)
                or (ended_multiline_quoted_string)
            ):  # pass on with no changes
                output.append(record)
                # now test for here-doc termination string
                if re.search(here_string, test_record) and not re.search(r"<<", test_record):
                    in_here_doc = False
            else:  # not in here doc or inside multiline-quoted

                if continue_line:
                    if prev_line_had_continue:
                        # this line is not STARTING a multiline-quoted string...
                        # we may be in the middle of such a multiline string
                        # though
                        started_multiline_quoted_string = False
                    else:
                        # remove contents of strings initiated on current line
                        # but that continue on next line (in particular we need
                        # to ignore brackets they may contain!)
                        [test_record, num_subs] = re.subn(r'"[^"]*?\\$', "", test_record)
                        started_multiline_quoted_string = True if num_subs > 0 else False
                else:
                    # this line is not STARTING a multiline-quoted string
                    started_multiline_quoted_string = False

                # Detect here-docs, but exclude here-strings (<<<) and arithmetic ($((<<)))
                has_heredoc = re.search(r"<<-?", test_record)
                is_herestring = re.search(r".*<<<", test_record)
                is_arithmetic = re.search(r"\$\(\(.*<<.*\)\)", test_record)

                if has_heredoc and not is_herestring and not is_arithmetic:
                    here_string = re.sub(
                        r'.*<<-?\s*[\'|"]?([_|\w]+)[\'|"]?.*', r"\1", stripped_record, 1
                    )
                    in_here_doc = len(here_string) > 0

                # Handle @formatter:off/on directives
                if not formatter:
                    # pass on unchanged
                    output.append(record)
                    if re.search(r"#\s*@formatter:on", stripped_record):
                        formatter = True
                        continue
                else:
                    if re.search(r"#\s*@formatter:off", stripped_record):
                        formatter = False
                        output.append(record)
                        continue

                    # multi-line conditions are often meticulously formatted
                    if open_brackets:
                        output.append(record)
                    else:
                        inc = len(re.findall(r"(\s|\A|;)(case|then|do)(;|\Z|\s)", test_record))
                        inc += len(re.findall(r"(\{|\(|\[)", test_record))
                        outc = len(
                            re.findall(
                                r"(\s|\A|;)(esac|fi|done|elif)(;|\)|\||\Z|\s)",
                                test_record,
                            )
                        )
                        outc += len(re.findall(r"(\}|\)|\])", test_record))
                        if re.search(r"\besac\b", test_record):
                            if case_level == 0:
                                sys.stderr.write(
                                    'File %s: error: "esac" before "case" in '
                                    "line %d.\n" % (path, line)
                                )
                            else:
                                outc += 1
                                case_level -= 1

                        # special handling for bad syntax within case ... esac
                        if re.search(r"(\s|\A|;)case\s", test_record):
                            inc += 1
                            case_level += 1

                        choice_case = 0
                        if case_level:
                            if re.search(r"\A[^(]+\)", test_record):
                                inc += 1
                                choice_case = -1

                        # detect functions
                        func_decl_style = self.detect_function_style(test_record)
                        if func_decl_style is not None:
                            stripped_record = self.change_function_style(
                                stripped_record, func_decl_style
                            )

                        # an ad-hoc solution for the "else" or "elif ... then" keywords
                        else_case = (0, -1)[
                            re.search(r"^(else|elif\s.*?;\s+?then)", test_record) is not None
                        ]

                        net = inc - outc
                        tab += min(net, 0)

                        # while 'tab' is preserved across multiple lines,
                        # 'extab' is not and is used for some adjustments:
                        extab = tab + else_case + choice_case
                        if (
                            prev_line_had_continue
                            and not open_brackets
                            and not ended_multiline_quoted_string
                        ):
                            extab += 1
                        extab = max(0, extab)
                        output.append((self.tab_str * self.tab_size * extab) + stripped_record)
                        tab += max(net, 0)

                # count open brackets for line continuation
                open_brackets += len(re.findall(r"\[", test_record))
                open_brackets -= len(re.findall(r"\]", test_record))
            line += 1
        error = tab != 0
        if error:
            sys.stderr.write("File %s: error: indent/outdent mismatch: %d.\n" % (path, tab))

        # Apply variable style transformation if requested
        if self.variable_style is not None:
            output = [self.apply_variable_style(line) for line in output]

        return "\n".join(output), error

    def beautify_file(self, path):
        """Beautify bash script file."""
        error = False
        if path == "-":
            data = sys.stdin.read()
            result, error = self.beautify_string(data, "(stdin)")
            sys.stdout.write(result)
        else:  # named file
            data = self.read_file(path)
            result, error = self.beautify_string(data, path)
            if data != result:
                if self.check_only:
                    if not error:
                        # we want to return 0 (success) only if the given file is already
                        # well formatted:
                        error = result != data
                        if error:
                            self.print_diff(data, result)
                else:
                    if self.backup:
                        self.write_file(path + ".bak", data)
                    self.write_file(path, result)
        return error

    def color_diff(self, diff):
        for line in diff:
            if line.startswith("+"):
                yield Fore.GREEN + line + Fore.RESET
            elif line.startswith("-"):
                yield Fore.RED + line + Fore.RESET
            elif line.startswith("^"):
                yield Fore.BLUE + line + Fore.RESET
            else:
                yield line

    def print_diff(self, original: str, formatted: str):
        original_lines = original.splitlines()
        formatted_lines = formatted.splitlines()

        delta = difflib.unified_diff(
            original_lines, formatted_lines, "original", "formatted", lineterm=""
        )
        if self.color:
            delta = self.color_diff(delta)

        print("\n".join(delta))

    def print_help(self, parser):
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

    def parse_function_style(self, style_name):
        # map the user-provided function style to our range 0-2
        if style_name == "fnpar":
            return 0
        elif style_name == "fnonly":
            return 1
        elif style_name == "paronly":
            return 2
        return None

    def apply_variable_style(self, line):
        """Apply variable style transformation to a line.

        Args:
            line: The line to transform

        Returns:
            Transformed line with variable style applied
        """
        if self.variable_style == "braces":
            # Transform $VAR to ${VAR}, but only for simple variables
            # Pattern: $ followed by alphanumeric/underscore, but not already in braces
            # Negative lookbehind (?<!{) ensures we don't match ${VAR}
            # \b word boundary ensures we get complete variable names
            line = re.sub(r"\$(?!{)([a-zA-Z_][a-zA-Z0-9_]*)\b", r"${\1}", line)
        return line

    def get_version(self):
        try:
            return version("beautysh")
        except PackageNotFoundError:
            return "Not Available"

    def main(self, argv):
        """Main beautifying function.

        Args:
            argv: List of command-line arguments (excluding program name).
        """
        error = False

        # Build merged config with priority: EditorConfig < pyproject.toml < CLI args
        # First, try to load EditorConfig if we're processing a file
        editorconfig_settings = {}
        if argv and argv[0] not in ["-h", "--help", "-v", "--version"]:
            # Find first file argument (skip flags)
            for arg in argv:
                if not arg.startswith("-") and arg != "-":
                    editorconfig_settings = load_config_from_editorconfig(arg)
                    break

        # Load pyproject.toml config (overrides EditorConfig)
        pyproject_config = load_config_from_pyproject()

        # Merge configs: EditorConfig < pyproject.toml
        config = {**editorconfig_settings, **pyproject_config}

        parser = argparse.ArgumentParser(
            description="A Bash beautifier for the masses, version {}".format(self.get_version()),
            add_help=False,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        )
        parser.add_argument(
            "--indent-size",
            "-i",
            type=int,
            default=config.get("indent_size", 4),
            help="Sets the number of spaces to be used in indentation.",
        )
        parser.add_argument(
            "--backup",
            "-b",
            action="store_true",
            default=config.get("backup", False),
            help="Beautysh will create a backup file in the " "same path as the original.",
        )
        parser.add_argument(
            "--check",
            "-c",
            action="store_true",
            default=config.get("check", False),
            help="Beautysh will just check the files without doing " "any in-place beautify.",
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
            "--version", "-v", action="store_true", help="Prints the version and exits."
        )
        parser.add_argument("--help", "-h", action="store_true", help="Print this help message.")
        parser.add_argument(
            "files",
            metavar="FILE",
            nargs="*",
            help="Files to be beautified. This is mandatory. "
            "If - is provided as filename, then beautysh reads "
            "from stdin and writes on stdout.",
        )
        args = parser.parse_args(argv)
        if (len(argv) < 1) or args.help:
            self.print_help(parser)
            return 0
        if args.version:
            sys.stdout.write("%s\n" % self.get_version())
            return 0
        if not args.files:
            sys.stdout.write("Please provide at least one input file\n")
            return 1
        self.tab_size = args.indent_size
        self.backup = args.backup
        self.check_only = args.check
        if args.tab:
            self.tab_size = 1
            self.tab_str = "\t"
        if args.force_function_style is not None:
            provided_style = self.parse_function_style(args.force_function_style)
            if provided_style is None:
                sys.stdout.write("Invalid value for the function style. See --help for details.\n")
                return 1
            self.apply_function_style = provided_style
        if args.variable_style is not None:
            self.variable_style = args.variable_style
        if "NO_COLOR" in os.environ:
            self.color = False
        for path in args.files:
            error |= self.beautify_file(path)
        return 1 if error else 0
