"""Tests for variable style options (issue #126)."""

from beautysh import Beautify


def test_variable_style_braces_basic():
    """Test that --variable-style braces transforms $VAR to ${VAR}."""
    source = """#!/bin/bash
echo "$VAR"
echo "$FOO_BAR"
"""

    beautifier = Beautify()
    beautifier.variable_style = "braces"
    result, error = beautifier.beautify_string(source)

    assert not error
    assert 'echo "${VAR}"' in result
    assert 'echo "${FOO_BAR}"' in result


def test_variable_style_braces_in_strings():
    """Test variable transformation inside strings."""
    source = """#!/bin/bash
msg="Hello $USER, your home is $HOME"
"""

    beautifier = Beautify()
    beautifier.variable_style = "braces"
    result, error = beautifier.beautify_string(source)

    assert not error
    assert 'msg="Hello ${USER}, your home is ${HOME}"' in result


def test_variable_style_braces_preserves_existing():
    """Test that existing ${VAR} syntax is preserved."""
    source = """#!/bin/bash
echo "${ALREADY_BRACED}"
echo "$SIMPLE"
"""

    beautifier = Beautify()
    beautifier.variable_style = "braces"
    result, error = beautifier.beautify_string(source)

    assert not error
    assert 'echo "${ALREADY_BRACED}"' in result
    assert 'echo "${SIMPLE}"' in result


def test_variable_style_braces_preserves_expansions():
    """Test that parameter expansions are not affected."""
    source = """#!/bin/bash
echo "${VAR:-default}"
echo "${VAR#prefix}"
echo "${arr[1]}"
echo "${!VAR}"
echo "${#VAR}"
"""

    beautifier = Beautify()
    beautifier.variable_style = "braces"
    result, error = beautifier.beautify_string(source)

    assert not error
    # These should all remain unchanged as they're already using braces
    assert "${VAR:-default}" in result
    assert "${VAR#prefix}" in result
    assert "${arr[1]}" in result
    assert "${!VAR}" in result
    assert "${#VAR}" in result


def test_variable_style_braces_mixed():
    """Test mixing simple and complex variables."""
    source = """#!/bin/bash
result="${PREFIX}_${MIDDLE}_${SUFFIX}"
path="$HOME/.config"
default="${CONFIG:-/etc/config}"
simple="$VAR"
"""

    beautifier = Beautify()
    beautifier.variable_style = "braces"
    result, error = beautifier.beautify_string(source)

    assert not error
    # Already braced variables stay as-is
    assert 'result="${PREFIX}_${MIDDLE}_${SUFFIX}"' in result
    assert 'default="${CONFIG:-/etc/config}"' in result
    # Simple variables get transformed
    assert 'path="${HOME}/.config"' in result
    assert 'simple="${VAR}"' in result


def test_variable_style_none():
    """Test that None (default) doesn't transform variables."""
    source = """#!/bin/bash
echo "$VAR"
echo "${BRACED}"
"""

    beautifier = Beautify()
    # variable_style is None by default
    result, error = beautifier.beautify_string(source)

    assert not error
    # Both should remain as-is
    assert 'echo "$VAR"' in result
    assert 'echo "${BRACED}"' in result


def test_variable_style_special_variables():
    """Test that special variables are left unchanged (Bash convention)."""
    source = """#!/bin/bash
echo "$?"
echo "$1"
echo "$@"
echo "$*"
echo "$$"
"""

    beautifier = Beautify()
    beautifier.variable_style = "braces"
    result, error = beautifier.beautify_string(source)

    assert not error
    # Special variables remain unchanged by convention
    assert 'echo "$?"' in result
    assert 'echo "$1"' in result
    assert 'echo "$@"' in result
    assert 'echo "$*"' in result
    assert 'echo "$$"' in result
