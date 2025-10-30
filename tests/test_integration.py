"""Integration tests for beautysh beautifier."""

from pathlib import Path

import pytest

from beautysh import Beautify

from . import assert_equal_multiline_strings, assert_formatting, read_file


@pytest.fixture
def fixture_dir():
    """Return the path to test fixtures directory."""
    return Path(__file__).parent.absolute() / "fixtures"


@pytest.mark.xfail(strict=True)
def test_sanity(fixture_dir):
    assert_formatting(fixture_dir, "sanity")


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


def test_function_styles(fixture_dir):
    """Test all three function style formatting options."""
    raw = read_file(fixture_dir / "function_styles_raw.sh")

    for style in range(3):
        formatted = read_file(fixture_dir / f"function_styles_{style}.sh")

        formatter = Beautify()
        formatter.apply_function_style = style

        actual, error = formatter.beautify_string(raw)

        assert not error, f"Beautifier reported an error for function style {style}"
        assert_equal_multiline_strings(actual, formatted)
