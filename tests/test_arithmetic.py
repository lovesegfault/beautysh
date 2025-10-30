"""Tests for arithmetic expressions with << operator (issue #107)."""

from . import assert_formatting


def test_arithmetic_left_shift(fixture_dir):
    """Test that << in arithmetic expressions doesn't trigger here-doc detection."""
    assert_formatting(fixture_dir, "arithmetic_shift")


def test_arithmetic_in_if(fixture_dir):
    """Test arithmetic << inside conditional."""
    assert_formatting(fixture_dir, "arithmetic_if")


def test_arithmetic_multiple_shifts(fixture_dir):
    """Test multiple shift operations."""
    assert_formatting(fixture_dir, "arithmetic_multiple")


def test_arithmetic_vs_heredoc(fixture_dir):
    """Test that we can distinguish arithmetic << from here-docs."""
    assert_formatting(fixture_dir, "arithmetic_vs_heredoc")
