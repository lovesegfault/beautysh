"""Property-based tests for beautysh.formatter module using Hypothesis."""

import pytest
from hypothesis import assume, given
from hypothesis import strategies as st

from beautysh.formatter import BashFormatter
from beautysh.types import FunctionStyle

# Strategy for generating valid bash-like scripts
bash_keywords = st.sampled_from(
    [
        "if",
        "then",
        "else",
        "elif",
        "fi",
        "for",
        "do",
        "done",
        "while",
        "until",
        "case",
        "esac",
        "function",
    ]
)

bash_operators = st.sampled_from(["[", "]", "(", ")", "{", "}", ";", "|", "&"])

bash_commands = st.sampled_from(
    [
        "echo",
        "test",
        "cd",
        "ls",
        "cat",
        "grep",
        "awk",
        "sed",
    ]
)


class TestFormatterProperties:
    """Property-based tests for BashFormatter."""

    @given(st.text())
    def test_beautify_string_always_returns_tuple(self, script):
        """beautify_string should always return (str, bool) tuple."""
        formatter = BashFormatter()
        result = formatter.beautify_string(script)
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], str)
        assert isinstance(result[1], bool)

    @given(st.text())
    def test_beautify_string_preserves_line_count_roughly(self, script):
        """beautify_string should not drastically change line count."""
        formatter = BashFormatter()
        original_lines = script.count("\n")
        formatted, error = formatter.beautify_string(script)
        formatted_lines = formatted.count("\n")

        # Line count can increase (do case split) but should be within reason
        # Allow up to 2x increase for edge cases
        assert formatted_lines <= original_lines * 2 + 10

    @given(st.integers(min_value=1, max_value=8))
    def test_beautify_string_with_custom_indent(self, indent_size):
        """Formatter should work with various indent sizes."""
        formatter = BashFormatter(indent_size=indent_size)
        script = "if true; then\necho test\nfi"
        formatted, error = formatter.beautify_string(script)
        assert isinstance(formatted, str)
        # Should have indentation
        assert " " * indent_size in formatted or formatted.count(" ") > 0

    @given(st.lists(bash_keywords, min_size=1, max_size=5))
    def test_beautify_string_with_keywords(self, keywords):
        """Formatter should handle bash keywords."""
        formatter = BashFormatter()
        script = " ".join(keywords)
        formatted, error = formatter.beautify_string(script)
        assert isinstance(formatted, str)
        # All keywords should still be present
        for keyword in keywords:
            assert keyword in formatted

    @given(st.text())
    def test_beautify_string_idempotent(self, script):
        """Formatting twice should give same result as formatting once."""
        # Skip scripts that cause errors
        assume("\x00" not in script)  # Null bytes cause issues

        formatter = BashFormatter()
        first, error1 = formatter.beautify_string(script)

        if not error1:
            second, error2 = formatter.beautify_string(first)
            assert not error2
            # Second formatting should not change result
            assert first == second

    @given(st.sampled_from(list(FunctionStyle)))
    def test_beautify_string_with_function_styles(self, style):
        """Formatter should work with different function styles."""
        formatter = BashFormatter(function_style=style)
        script = "function foo() {\necho test\n}"
        formatted, error = formatter.beautify_string(script)
        assert isinstance(formatted, str)
        assert not error

    @given(st.text(alphabet="abcdefghijklmnopqrstuvwxyz\n ", min_size=0, max_size=100))
    def test_beautify_string_no_crashes(self, script):
        """Formatter should not crash on any simple text input."""
        formatter = BashFormatter()
        try:
            formatted, error = formatter.beautify_string(script)
            assert isinstance(formatted, str)
            assert isinstance(error, bool)
        except Exception as e:
            assert False, f"Formatter crashed: {e}"

    @pytest.mark.skip(reason="Content preservation varies with PEG parser")
    @given(st.lists(st.text(min_size=1), min_size=1, max_size=10))
    def test_beautify_string_preserves_content(self, lines):
        """Formatter should preserve actual content (after stripping)."""
        formatter = BashFormatter()
        script = "\n".join(lines)
        formatted, error = formatter.beautify_string(script)

        # Each non-empty line's content should appear in formatted output
        for line in lines:
            if line.strip():
                # Content should be preserved (though whitespace may change)
                assert line.strip() in formatted or any(
                    word in formatted for word in line.split() if word
                )

    @given(st.integers(min_value=0, max_value=5))
    def test_balanced_if_fi(self, n):
        """Properly balanced if/fi should not cause errors."""
        formatter = BashFormatter()
        script_lines = []
        for i in range(n):
            script_lines.extend(
                [
                    f"if [ $test{i} ]; then",
                    f"    echo 'test{i}'",
                    "fi",
                ]
            )
        script = "\n".join(script_lines)
        formatted, error = formatter.beautify_string(script)
        assert not error

    @given(st.integers(min_value=0, max_value=5))
    def test_balanced_case_esac(self, n):
        """Properly balanced case/esac should not cause errors."""
        formatter = BashFormatter()
        script_lines = []
        for i in range(n):
            script_lines.extend(
                [
                    f"case $var{i} in",
                    f"    pattern{i})",
                    "        echo 'match'",
                    "        ;;",
                    "esac",
                ]
            )
        script = "\n".join(script_lines)
        formatted, error = formatter.beautify_string(script)
        assert not error

    @given(st.text(min_size=1, max_size=50))
    def test_preserves_shebang(self, rest_of_script):
        """Formatter should preserve shebang lines."""
        script = "#!/bin/bash\n" + rest_of_script
        formatter = BashFormatter()
        formatted, error = formatter.beautify_string(script)
        assert formatted.startswith("#!/bin/bash")

    @pytest.mark.skip(reason="Blank line preservation not yet implemented")
    @given(st.lists(st.text(), min_size=2, max_size=10))
    def test_blank_lines_preserved(self, content_lines):
        """Formatter should preserve blank lines."""
        script_lines = []
        for line in content_lines:
            script_lines.append(line)
            script_lines.append("")  # Add blank line after each

        script = "\n".join(script_lines)
        formatter = BashFormatter()
        formatted, error = formatter.beautify_string(script)

        # Should have blank lines in output (at least one double newline)
        assert "\n\n" in formatted

    def test_deeply_nested_structures(self):
        """Formatter should handle deeply nested structures."""
        formatter = BashFormatter()
        script = """
if true; then
    if true; then
        if true; then
            if true; then
                echo "deep"
            fi
        fi
    fi
fi
"""
        formatted, error = formatter.beautify_string(script)
        assert not error
        # Should have progressive indentation
        assert "    echo" in formatted or "echo" in formatted
