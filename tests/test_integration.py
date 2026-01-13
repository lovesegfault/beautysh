"""Integration tests for beautysh beautifier."""

import pytest

from beautysh import BashFormatter

from . import assert_equal_multiline_strings, assert_formatting, read_file


@pytest.mark.xfail(strict=True)
def test_sanity(fixture_dir):
    """Test sanity check with a basic script."""
    assert_formatting(fixture_dir, "sanity")


def test_basic(fixture_dir):
    """Test basic formatting capabilities."""
    assert_formatting(fixture_dir, "basic")


def test_complex(fixture_dir):
    """Test formatting of complex script structures."""
    assert_formatting(fixture_dir, "complex")


def test_heredoc_basic(fixture_dir):
    """Test basic heredoc formatting."""
    assert_formatting(fixture_dir, "heredoc_basic")


def test_heredoc_complex(fixture_dir):
    """Test complex heredoc formatting."""
    assert_formatting(fixture_dir, "heredoc_complex")


def test_if_condition_basic(fixture_dir):
    """Test basic if condition formatting."""
    assert_formatting(fixture_dir, "if_condition_basic")


def test_if_condition_for_loop(fixture_dir):
    """Test if condition containing a for loop."""
    assert_formatting(fixture_dir, "if_condition_for_loop")


def test_if_condition_function(fixture_dir):
    """Test if condition containing a function."""
    assert_formatting(fixture_dir, "if_condition_function")


def test_if_condition_multiline(fixture_dir):
    """Test multiline if condition formatting."""
    assert_formatting(fixture_dir, "if_condition_multiline")


def test_no_formatter_basic(fixture_dir):
    """Test basic script with formatter disabled."""
    assert_formatting(fixture_dir, "no_formatter_basic")


def test_no_formatter_function(fixture_dir):
    """Test function with formatter disabled."""
    assert_formatting(fixture_dir, "no_formatter_function")


def test_indent_basic(fixture_dir):
    """Test basic indentation."""
    assert_formatting(fixture_dir, "indent_basic")


def test_indent_string_with_brackets(fixture_dir):
    """Test indentation with strings containing brackets."""
    assert_formatting(fixture_dir, "indent_string_with_brackets")


def test_indent_quote_escapes(fixture_dir):
    """Test indentation with escaped quotes."""
    assert_formatting(fixture_dir, "indent_quote_escapes")


def test_indent_mixed(fixture_dir):
    """Test mixed indentation styles."""
    assert_formatting(fixture_dir, "indent_mixed")


def test_getopts(fixture_dir):
    """Test formatting of getopts loops."""
    assert_formatting(fixture_dir, "getopts")


def test_function_hyphen(fixture_dir):
    """Test function names with special characters (-, :, @)."""
    assert_formatting(fixture_dir, "function_hyphen")


def test_function_styles(fixture_dir):
    """Test all three function style formatting options."""
    raw = read_file(fixture_dir / "function_styles_raw.sh")

    for style in range(3):
        formatted = read_file(fixture_dir / f"function_styles_{style}.sh")

        formatter = BashFormatter(apply_function_style=style)

        actual, error = formatter.beautify_string(raw)

        assert not error, f"Beautifier reported an error for function style {style}"
        assert_equal_multiline_strings(actual, formatted)