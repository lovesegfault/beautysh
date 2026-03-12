"""Unit tests for beautysh.transformers module."""

from beautysh.function_styles import FunctionStyle
from beautysh.transformers import StyleTransformer

FNPAR = FunctionStyle.FNPAR
FNONLY = FunctionStyle.FNONLY
PARONLY = FunctionStyle.PARONLY


class TestChangeFunctionStyle:
    """Tests for StyleTransformer.change_function_style()"""

    def test_fnpar_to_fnonly(self):
        result = StyleTransformer.change_function_style("function foo() {", FNPAR, FNONLY)
        assert result == "function foo {"

    def test_fnpar_to_paronly(self):
        result = StyleTransformer.change_function_style("function foo() {", FNPAR, PARONLY)
        assert result == "foo() {"

    def test_fnonly_to_fnpar(self):
        result = StyleTransformer.change_function_style("function bar {", FNONLY, FNPAR)
        assert result == "function bar() {"

    def test_fnonly_to_paronly(self):
        result = StyleTransformer.change_function_style("function bar {", FNONLY, PARONLY)
        assert result == "bar() {"

    def test_paronly_to_fnpar(self):
        result = StyleTransformer.change_function_style("baz() {", PARONLY, FNPAR)
        assert result == "function baz() {"

    def test_paronly_to_fnonly(self):
        result = StyleTransformer.change_function_style("baz() {", PARONLY, FNONLY)
        assert result == "function baz {"

    def test_no_change_when_none_target(self):
        result = StyleTransformer.change_function_style("function foo() {", FNPAR, None)
        assert result == "function foo() {"

    def test_no_change_when_no_function(self):
        result = StyleTransformer.change_function_style("echo test", None, FNPAR)
        assert result == "echo test"

    def test_same_style_unchanged(self):
        result = StyleTransformer.change_function_style("function foo() {", FNPAR, FNPAR)
        assert result == "function foo() {"


class TestApplyVariableStyle:
    """Tests for StyleTransformer.apply_variable_style()"""

    def test_braces_style_simple_variable(self):
        result = StyleTransformer.apply_variable_style("echo $HOME", "braces")
        assert result == "echo ${HOME}"

    def test_braces_style_multiple_variables(self):
        result = StyleTransformer.apply_variable_style("echo $HOME $USER", "braces")
        assert result == "echo ${HOME} ${USER}"

    def test_braces_style_already_braced(self):
        result = StyleTransformer.apply_variable_style("echo ${HOME}", "braces")
        assert result == "echo ${HOME}"

    def test_braces_style_mixed(self):
        result = StyleTransformer.apply_variable_style("echo $HOME ${USER}", "braces")
        assert result == "echo ${HOME} ${USER}"

    def test_braces_style_with_underscore(self):
        result = StyleTransformer.apply_variable_style("echo $MY_VAR", "braces")
        assert result == "echo ${MY_VAR}"

    def test_braces_style_with_numbers(self):
        result = StyleTransformer.apply_variable_style("echo $VAR1 $VAR2", "braces")
        assert result == "echo ${VAR1} ${VAR2}"

    def test_none_style_no_change(self):
        result = StyleTransformer.apply_variable_style("echo $HOME", None)
        assert result == "echo $HOME"

    def test_braces_preserves_special_variables(self):
        # Should still work with special variables like $1, $@, etc
        result = StyleTransformer.apply_variable_style("echo $1 $@", "braces")
        # Note: regex only matches [a-zA-Z_][a-zA-Z0-9_]*
        # Special variables like $1, $@ won't be matched
        assert "$1" in result  # Should remain unchanged


class TestEnsureSpaceBeforeDoubleSemicolon:
    """Tests for StyleTransformer.ensure_space_before_double_semicolon()"""

    def test_adds_space_when_needed(self):
        result = StyleTransformer.ensure_space_before_double_semicolon("foo;;")
        assert result == "foo ;;"

    def test_preserves_existing_space(self):
        result = StyleTransformer.ensure_space_before_double_semicolon("foo ;;")
        assert result == "foo ;;"

    def test_handles_multiple_semicolons(self):
        result = StyleTransformer.ensure_space_before_double_semicolon("foo;;bar;;")
        assert result == "foo ;;bar ;;"
