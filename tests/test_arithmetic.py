"""Tests for arithmetic expressions with << operator (issue #107)."""

from beautysh import Beautify


def test_arithmetic_left_shift():
    """Test that << in arithmetic expressions doesn't trigger here-doc detection."""
    source = """#!/bin/bash
max=$((1<<63))
"""

    result, error = Beautify().beautify_string(source)

    # Should not report an error
    assert not error, "Should not report indent/outdent mismatch for arithmetic <<"
    assert "max=$((1<<63))" in result


def test_arithmetic_in_if():
    """Test arithmetic << inside conditional."""
    source = """#!/bin/bash
if true; then
val=$((2<<5))
echo $val
fi
"""

    result, error = Beautify().beautify_string(source)

    assert not error
    assert "    val=$((2<<5))" in result
    assert "    echo $val" in result


def test_arithmetic_multiple_shifts():
    """Test multiple shift operations."""
    source = """#!/bin/bash
a=$((1<<10))
b=$((x<<y))
c=$((value << 3))
"""

    result, error = Beautify().beautify_string(source)

    assert not error
    assert "a=$((1<<10))" in result
    assert "b=$((x<<y))" in result
    assert "c=$((value << 3))" in result


def test_arithmetic_vs_heredoc():
    """Test that we can distinguish arithmetic << from here-docs."""
    source = """#!/bin/bash
# Arithmetic shift
val=$((1<<5))

# Here-doc
cat <<EOF
text
EOF

# More arithmetic
result=$((n<<2))
"""

    result, error = Beautify().beautify_string(source)

    assert not error
    # Arithmetic should be treated normally
    assert "val=$((1<<5))" in result
    assert "result=$((n<<2))" in result
    # Here-doc should still work
    assert "<<EOF" in result
    assert "text" in result
