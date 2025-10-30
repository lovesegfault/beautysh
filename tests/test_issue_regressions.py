"""Regression tests for specific GitHub issues that have been fixed."""

from . import assert_formatting


def test_issue53_multiline_strings_not_indented(fixture_dir):
    """Test that multiline string contents are preserved (issue #53)."""
    # This is already covered by test_multiline_strings.py
    # but keeping reference here for documentation
    assert_formatting(fixture_dir, "multiline_content")


def test_issue58_markdown_link_with_backticks(fixture_dir):
    """Test that multiline MD link with backticks doesn't cause parse error (issue #58)."""
    assert_formatting(fixture_dir, "issue58_md_link")


def test_issue81_shift_operator(fixture_dir):
    """Test that << shift operator in arithmetic doesn't cause indent mismatch (issue #81)."""
    # This is already covered by test_arithmetic.py
    # but keeping reference here for documentation
    assert_formatting(fixture_dir, "arithmetic_shift")


def test_issue101_multiline_subcommand_indentation(fixture_dir):
    """Test that multiline command substitutions maintain proper indentation (issue #101)."""
    assert_formatting(fixture_dir, "issue101_multiline_subcommand")


def test_issue78_multiline_array_in_case(fixture_dir):
    """Test multiline array in case statement doesn't cause indent mismatch (issue #78)."""
    assert_formatting(fixture_dir, "issue78_multiline_array_case")
