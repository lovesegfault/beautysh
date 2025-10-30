"""Tests for $$ handling (issue #86)."""

from . import assert_formatting


def test_double_dollar_in_string(fixture_dir):
    """Test that $$ in strings doesn't cause indent/outdent mismatch.

    This was the original issue #86 where --ignore-case was incorrectly
    matching the 'case' keyword pattern.
    """
    assert_formatting(fixture_dir, "dollar_dollar_string")


def test_double_dollar_in_if(fixture_dir):
    """Test $$ in conditional."""
    assert_formatting(fixture_dir, "dollar_dollar_if")


def test_pid_variable(fixture_dir):
    """Test that $$ as PID variable works."""
    assert_formatting(fixture_dir, "dollar_dollar_pid")
