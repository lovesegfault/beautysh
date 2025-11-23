"""Tests for multiline string handling (issues #82, #65, #66)."""

import pytest

from . import assert_formatting


def test_multiline_string_empty(fixture_dir):
    """Test that empty multiline strings don't cause indent errors."""
    assert_formatting(fixture_dir, "multiline_empty")


def test_multiline_string_trailing_whitespace(fixture_dir):
    """Test that code after multiline strings with trailing whitespace is indented correctly."""
    assert_formatting(fixture_dir, "multiline_trailing_ws")


def test_multiline_string_ending_newline(fixture_dir):
    """Test that code after multiline strings ending with newline is indented correctly."""
    assert_formatting(fixture_dir, "multiline_newline")


def test_multiline_string_content_preserved(fixture_dir):
    """Test that multiline string contents are not indented."""
    assert_formatting(fixture_dir, "multiline_content")


@pytest.mark.skip(reason="Line continuation (backslash-newline) not yet implemented")
def test_multiline_string_in_array(fixture_dir):
    """Test multiline strings inside array assignments."""
    assert_formatting(fixture_dir, "multiline_array")
