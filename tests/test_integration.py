"""Integration tests for beautysh beautifier."""

import shutil
import subprocess
from pathlib import Path

import pytest

from beautysh import BashFormatter, FunctionStyle

from . import assert_equal_multiline_strings, assert_formatting, read_file

_FIXTURE_DIR = Path(__file__).parent / "fixtures"

# All *_formatted.sh fixtures, excluding the sanity self-test (deliberately
# wrong) and function_styles_N.sh (require a non-default function style to
# reproduce).
_FORMATTED_FIXTURES = sorted(
    p.name for p in _FIXTURE_DIR.glob("*_formatted.sh") if p.stem not in {"sanity_formatted"}
)


# Inverted self-test: sanity_raw.sh == sanity_formatted.sh, both deliberately
# wrong. assert_formatting therefore fails, which xfail(strict=True) turns into
# a pass. If the formatter ever stops formatting entirely, raw would match the
# expected-wrong output, the inner assert would pass, and strict=True would
# flip that into an error.
@pytest.mark.xfail(strict=True)
def test_sanity(fixture_dir):
    assert_formatting(fixture_dir, "sanity")


@pytest.mark.parametrize("fixture_name", _FORMATTED_FIXTURES)
def test_formatted_fixtures_are_fixpoints(fixture_dir, fixture_name):
    """format(formatted) == formatted for every golden output.

    This is the primary idempotency check. The hypothesis-based test in
    test_formatter_properties.py uses random text and almost never hits the
    success path; this uses the curated corpus we already maintain.
    """
    content = read_file(fixture_dir / fixture_name)
    out, err = BashFormatter().beautify_string(content)
    assert not err
    assert_equal_multiline_strings(out, content)


# Fixtures that are deliberately not valid bash: they exercise beautysh's
# handling of syntax that *looks* like something else. Skip from bash -n only.
_NOT_VALID_BASH = {
    # `let y=1<<3` without quotes is a heredoc redirect, not a shift.
    "arithmetic_command_shift_formatted.sh",
}


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash not on PATH")
@pytest.mark.parametrize(
    "fixture_name", [f for f in _FORMATTED_FIXTURES if f not in _NOT_VALID_BASH]
)
def test_formatted_fixtures_are_valid_bash(fixture_dir, fixture_name):
    """bash -n accepts every golden output.

    Guards against the formatter producing syntactically invalid bash
    (e.g. a mid-string line split, a corrupted ;;).
    """
    content = read_file(fixture_dir / fixture_name)
    result = subprocess.run(
        ["bash", "-n", "-"],
        input=content,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"bash -n rejected {fixture_name}:\n{result.stderr}"


def test_basic(fixture_dir):
    assert_formatting(fixture_dir, "basic")


def test_complex(fixture_dir):
    assert_formatting(fixture_dir, "complex")


def test_heredoc_basic(fixture_dir):
    assert_formatting(fixture_dir, "heredoc_basic")


def test_heredoc_complex(fixture_dir):
    assert_formatting(fixture_dir, "heredoc_complex")


def test_if_condition_basic(fixture_dir):
    assert_formatting(fixture_dir, "if_condition_basic")


def test_if_condition_for_loop(fixture_dir):
    assert_formatting(fixture_dir, "if_condition_for_loop")


def test_if_condition_function(fixture_dir):
    assert_formatting(fixture_dir, "if_condition_function")


def test_if_condition_multiline(fixture_dir):
    assert_formatting(fixture_dir, "if_condition_multiline")


def test_no_formatter_basic(fixture_dir):
    assert_formatting(fixture_dir, "no_formatter_basic")


def test_no_formatter_function(fixture_dir):
    assert_formatting(fixture_dir, "no_formatter_function")


def test_indent_basic(fixture_dir):
    assert_formatting(fixture_dir, "indent_basic")


def test_indent_string_with_brackets(fixture_dir):
    assert_formatting(fixture_dir, "indent_string_with_brackets")


def test_indent_quote_escapes(fixture_dir):
    assert_formatting(fixture_dir, "indent_quote_escapes")


def test_indent_mixed(fixture_dir):
    assert_formatting(fixture_dir, "indent_mixed")


def test_getopts(fixture_dir):
    assert_formatting(fixture_dir, "getopts")


def test_function_hyphen(fixture_dir):
    """Test function names with special characters (-, :, @)."""
    assert_formatting(fixture_dir, "function_hyphen")


@pytest.mark.parametrize("idx,style", enumerate(FunctionStyle))
def test_function_styles(fixture_dir, idx, style):
    """Test all three function style formatting options."""
    raw = read_file(fixture_dir / "function_styles_raw.sh")
    formatted = read_file(fixture_dir / f"function_styles_{idx}.sh")

    formatter = BashFormatter(apply_function_style=style)
    actual, error = formatter.beautify_string(raw)

    assert not error, f"Beautifier reported an error for function style {style}"
    assert_equal_multiline_strings(actual, formatted)
