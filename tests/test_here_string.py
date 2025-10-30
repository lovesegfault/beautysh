"""Tests for here-string (<<<) handling (issue #11)."""

from beautysh import Beautify


def test_here_string_basic():
    """Test that here-strings (<<<) are handled correctly."""
    source = """#!/bin/bash

function get_resource {
    IFS="$DELIMITER" read -r -a ARR <<< "$temp"
}
"""

    result, error = Beautify().beautify_string(source)

    # Should not report an error
    assert not error, "Should not report indent/outdent mismatch for here-string"

    # Function body should be indented
    assert '    IFS="$DELIMITER" read -r -a ARR <<< "$temp"' in result


def test_here_string_in_if():
    """Test here-string inside conditional."""
    source = """#!/bin/bash
if true; then
read var <<< "hello world"
fi
"""

    result, error = Beautify().beautify_string(source)

    assert not error
    # The read line should be indented
    assert '    read var <<< "hello world"' in result


def test_here_string_with_variable():
    """Test here-string with variables."""
    source = """#!/bin/bash
while IFS= read -r line; do
echo "$line"
done <<< "$variable"
"""

    result, error = Beautify().beautify_string(source)

    assert not error
    # Proper indentation maintained
    assert "    echo" in result
    assert '<<< "$variable"' in result


def test_here_doc_still_works():
    """Ensure regular here-docs still work after fixing here-strings."""
    source = """#!/bin/bash
cat <<EOF
line 1
line 2
EOF
"""

    result, error = Beautify().beautify_string(source)

    assert not error
    # Here-doc content preserved
    assert "line 1" in result
    assert "line 2" in result
    assert "EOF" in result
