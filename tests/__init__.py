"""Test utilities and helpers for beautysh tests."""

from pathlib import Path
from typing import Optional

from beautysh import Beautify


def read_file(file: Path) -> str:
    """Read file into string."""
    with open(file) as f:
        return f.read()


def highlight_string(string: str) -> str:
    """Highlight whitespace in strings for debugging test failures."""
    if len(string) == 0:
        return string

    output = ""
    idx = 0
    while idx < len(string) and (string[idx] == " " or string[idx] == "\t"):
        if string[idx] == " ":
            output += "."
        elif string[idx] == "\t":
            output += "T"
        idx += 1
    if idx < len(string):
        output += string[idx:]
    return output


def assert_equal_multiline_strings(actual: str, expected: str):
    """Assert two multiline strings are equal with helpful error messages."""
    actual_lines = actual.split("\n")
    expected_lines = expected.split("\n")

    assert len(actual_lines) == len(
        expected_lines
    ), f"Mismatched line counts: expected {len(expected_lines)}, got {len(actual_lines)}"

    for idx in range(len(expected_lines)):
        assert expected_lines[idx] == actual_lines[idx], (
            f"Mismatch on line {idx + 1}:\n"
            f"Expected: {highlight_string(expected_lines[idx])}\n"
            f"Got:      {highlight_string(actual_lines[idx])}"
        )


def assert_formatting(
    fixture_dir: Path, test_name: str, apply_function_style: Optional[int] = None
):
    """Assert that beautifying a raw file produces the expected formatted output."""
    raw_file = fixture_dir / f"{test_name}_raw.sh"
    formatted_file = fixture_dir / f"{test_name}_formatted.sh"

    raw = read_file(raw_file)
    expected = read_file(formatted_file)

    formatter = Beautify()
    if apply_function_style is not None:
        formatter.apply_function_style = apply_function_style

    actual, error = formatter.beautify_string(raw)

    assert not error, f"Beautifier reported an error for {test_name}"
    assert_equal_multiline_strings(actual, expected)
