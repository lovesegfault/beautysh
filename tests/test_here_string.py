"""Tests for here-string (<<<) handling (issue #11)."""

from . import assert_formatting


def test_here_string_basic(fixture_dir):
    """Test that here-strings (<<<) are handled correctly."""
    assert_formatting(fixture_dir, "herestring_basic")


def test_here_string_in_if(fixture_dir):
    """Test here-string inside conditional."""
    assert_formatting(fixture_dir, "herestring_if")


def test_here_string_with_variable(fixture_dir):
    """Test here-string with variables."""
    assert_formatting(fixture_dir, "herestring_variable")


def test_here_doc_still_works(fixture_dir):
    """Ensure regular here-docs still work after fixing here-strings."""
    assert_formatting(fixture_dir, "herestring_vs_heredoc")
