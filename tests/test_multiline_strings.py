"""Tests for multiline string handling (issues #82, #65, #66)."""

from beautysh import Beautify


def test_multiline_string_empty():
    """Test that empty multiline strings don't cause indent errors."""
    source = """#!/bin/bash
if true; then
    x="
    "
fi
"""

    result, error = Beautify().beautify_string(source)

    # Should not report an error
    assert not error, "Should not report indent/outdent mismatch"


def test_multiline_string_trailing_whitespace():
    """Test that code after multiline strings with trailing whitespace is indented correctly."""
    source = """#!/bin/bash
VAR="
text "

if true; then
echo should be indented
fi
"""

    result, error = Beautify().beautify_string(source)

    assert not error
    # The echo line should be indented
    assert "    echo should be indented" in result


def test_multiline_string_ending_newline():
    """Test that code after multiline strings ending with newline is indented correctly."""
    source = """#!/bin/bash
VAR="
"

if true; then
echo should be indented
fi
"""

    result, error = Beautify().beautify_string(source)

    assert not error
    # The echo line should be indented
    assert "    echo should be indented" in result


def test_multiline_string_content_preserved():
    """Test that multiline string contents are not indented."""
    source = """#!/bin/bash
if true; then
VAR="
value"
fi
"""

    result, error = Beautify().beautify_string(source)

    assert not error
    # The string content should NOT be indented - it should remain as "value" not "    value"
    # The VAR line itself should be indented, but not the content of the string
    assert 'VAR="\nvalue"' in result or 'VAR="\n    value"' not in result.replace(
        " " * 4 + "VAR", "VAR"
    )


def test_multiline_string_in_array():
    """Test multiline strings inside array assignments."""
    source = """#!/bin/bash
here_launch=(--tab -e "sh -c 'sleep 4; roslaunch launch_scripts here.launch \\
   run_minimal:=${run_minimal} --wait; $SHELL -i'")
"""

    result, error = Beautify().beautify_string(source)

    # Should not report an error
    assert not error, "Should not report indent/outdent mismatch"
