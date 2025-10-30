"""Tests for variable style options (issue #126)."""

from . import assert_formatting


def test_variable_style_braces_basic(fixture_dir):
    """Test that --variable-style braces transforms $VAR to ${VAR}."""
    assert_formatting(fixture_dir, "variable_braces_basic", variable_style="braces")


def test_variable_style_braces_in_strings(fixture_dir):
    """Test variable transformation inside strings."""
    assert_formatting(fixture_dir, "variable_braces_strings", variable_style="braces")


def test_variable_style_braces_preserves_existing(fixture_dir):
    """Test that existing ${VAR} syntax is preserved."""
    assert_formatting(fixture_dir, "variable_preserve_existing", variable_style="braces")


def test_variable_style_braces_preserves_expansions(fixture_dir):
    """Test that parameter expansions are not affected."""
    assert_formatting(fixture_dir, "variable_preserve_expansions", variable_style="braces")


def test_variable_style_braces_mixed(fixture_dir):
    """Test mixing simple and complex variables."""
    assert_formatting(fixture_dir, "variable_mixed", variable_style="braces")


def test_variable_style_none(fixture_dir):
    """Test that None (default) doesn't transform variables."""
    assert_formatting(fixture_dir, "variable_none")


def test_variable_style_special_variables(fixture_dir):
    """Test that special variables are left unchanged (Bash convention)."""
    assert_formatting(fixture_dir, "variable_special", variable_style="braces")
