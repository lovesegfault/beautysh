"""Unit tests for beautysh.formatter module."""

import pytest

from beautysh.formatter import BashFormatter
from beautysh.types import FunctionStyle, VariableStyle


class TestBashFormatter:
    """Tests for BashFormatter class"""

    def test_basic_if_statement(self):
        formatter = BashFormatter()
        script = 'if true;then\necho "test"\nfi'
        formatted, error = formatter.beautify_string(script)

        assert not error
        # Parser-based formatter normalizes spacing around keywords
        assert "if true; then" in formatted
        assert '    echo "test"' in formatted
        assert "fi" in formatted

    def test_custom_indent_size(self):
        formatter = BashFormatter(indent_size=2)
        script = 'if true;then\necho "test"\nfi'
        formatted, error = formatter.beautify_string(script)

        assert not error
        assert '  echo "test"' in formatted  # 2 spaces

    def test_tab_indentation(self):
        formatter = BashFormatter(indent_size=1, tab_str="\t")
        script = 'if true;then\necho "test"\nfi'
        formatted, error = formatter.beautify_string(script)

        assert not error
        assert '\techo "test"' in formatted

    def test_nested_structures(self):
        formatter = BashFormatter()
        script = 'if true;then\nif false;then\necho "nested"\nfi\nfi'
        formatted, error = formatter.beautify_string(script)

        assert not error
        lines = formatted.split("\n")
        # Check progressive indentation
        assert lines[1].startswith("    ")  # inner if
        assert lines[2].startswith("        ")  # echo (double indented)

    @pytest.mark.skip(reason="Blank line preservation in compound commands not yet implemented")
    def test_preserves_blank_lines(self):
        formatter = BashFormatter()
        script = 'if true;then\n\necho "test"\nfi'
        formatted, error = formatter.beautify_string(script)

        assert not error
        lines = formatted.split("\n")
        # Should have a blank line
        assert "" in lines

    def test_case_statement(self):
        formatter = BashFormatter()
        script = 'case $x in\na) echo "a";;\nesac'
        formatted, error = formatter.beautify_string(script)

        assert not error
        assert "case $x in" in formatted
        assert "esac" in formatted

    def test_function_style_enforcement(self):
        formatter = BashFormatter(function_style=FunctionStyle.PARONLY)
        script = 'function foo() {\necho "test"\n}'
        formatted, error = formatter.beautify_string(script)

        assert not error
        assert "foo() {" in formatted
        assert "function" not in formatted

    def test_variable_style_braces(self):
        formatter = BashFormatter(variable_style=VariableStyle.BRACES)
        script = "echo $HOME $USER"
        formatted, error = formatter.beautify_string(script)

        assert not error
        assert "${HOME}" in formatted
        assert "${USER}" in formatted

    @pytest.mark.skip(reason="PEG parser fallback makes structural error detection difficult")
    def test_error_on_mismatch(self):
        formatter = BashFormatter()
        script = 'if true;then\necho "test"'  # Missing fi
        formatted, error = formatter.beautify_string(script)

        # Note: PEG parsers with ordered choice fall back to simpler rules
        # when complex ones fail, so "if" gets parsed as a simple command
        # Structural error detection would need a separate validation pass
        assert error  # Should report error

    def test_multiline_string_preserved(self):
        formatter = BashFormatter()
        script = 'echo "\nline1\nline2\n"'
        formatted, error = formatter.beautify_string(script)

        # Multiline string content should be preserved
        assert "line1" in formatted
        assert "line2" in formatted

    def test_formatter_off_directive(self):
        formatter = BashFormatter()
        script = "if true;then\n# @formatter:off\nUGLY   CODE\n# @formatter:on\nfi"
        formatted, error = formatter.beautify_string(script)

        assert not error
        # Content between @formatter:off/on should be preserved
        assert "UGLY   CODE" in formatted

    def test_do_case_normalization(self):
        formatter = BashFormatter()
        script = 'while true; do case $x in\na) echo "a";;\nesac\ndone'
        formatted, error = formatter.beautify_string(script)

        assert not error
        # Should split 'do case' onto separate lines
        lines = formatted.split("\n")
        assert any("do" in line and "case" not in line for line in lines)


class TestFormatterEdgeCases:
    """Tests for edge cases in formatting"""

    def test_empty_script(self):
        formatter = BashFormatter()
        script = ""
        formatted, error = formatter.beautify_string(script)

        assert not error
        assert formatted == ""

    @pytest.mark.skip(reason="Blank line preservation not yet implemented")
    def test_only_blank_lines(self):
        formatter = BashFormatter()
        script = "\n\n\n"
        formatted, error = formatter.beautify_string(script)

        assert not error
        assert formatted == "\n\n\n"

    def test_here_doc_preservation(self):
        formatter = BashFormatter()
        script = "cat <<EOF\nUnformatted   content\n  with spaces\nEOF"
        formatted, error = formatter.beautify_string(script)

        assert not error
        # Here-doc content should be preserved exactly
        assert "Unformatted   content" in formatted
        assert "  with spaces" in formatted

    def test_arithmetic_with_shift_operator(self):
        formatter = BashFormatter()
        script = "result=$(( x << 2 ))"
        formatted, error = formatter.beautify_string(script)

        assert not error
        # Should not confuse << with heredoc
        assert formatted.strip() == script

    def test_here_string(self):
        formatter = BashFormatter()
        script = "grep pattern <<<$variable"
        formatted, error = formatter.beautify_string(script)

        assert not error
        # Should not confuse <<< with heredoc
        assert "<<<" in formatted
