"""Unit tests for beautysh.transformers module."""

from beautysh.transformers import (
    FunctionStyleParser,
    StyleTransformer,
)


class TestChangeFunctionStyle:
    """Tests for StyleTransformer.change_function_style()"""

    def test_fnpar_to_fnonly(self):
        result = StyleTransformer.change_function_style("function foo() {", 0, 1)
        assert result == "function foo {"

    def test_fnpar_to_paronly(self):
        result = StyleTransformer.change_function_style("function foo() {", 0, 2)
        assert result == "foo() {"

    def test_fnonly_to_fnpar(self):
        result = StyleTransformer.change_function_style("function bar {", 1, 0)
        assert result == "function bar() {"

    def test_fnonly_to_paronly(self):
        result = StyleTransformer.change_function_style("function bar {", 1, 2)
        assert result == "bar() {"

    def test_paronly_to_fnpar(self):
        result = StyleTransformer.change_function_style("baz() {", 2, 0)
        assert result == "function baz() {"

    def test_paronly_to_fnonly(self):
        result = StyleTransformer.change_function_style("baz() {", 2, 1)
        assert result == "function baz {"

    def test_no_change_when_none_style(self):
        result = StyleTransformer.change_function_style("function foo() {", 0, None)
        assert result == "function foo() {"

    def test_no_change_when_no_function(self):
        result = StyleTransformer.change_function_style("echo test", None, 0)
        assert result == "echo test"

    def test_same_style_unchanged(self):
        result = StyleTransformer.change_function_style("function foo() {", 0, 0)
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
        result = StyleTransformer.ensure_space_before_double_semicolon("foo;;", True)
        assert result == "foo ;;"

    def test_preserves_existing_space(self):
        result = StyleTransformer.ensure_space_before_double_semicolon("foo ;;", True)
        assert result == "foo ;;"

    def test_no_change_when_not_in_case(self):
        result = StyleTransformer.ensure_space_before_double_semicolon("foo;;", False)
        assert result == "foo;;"

    def test_handles_multiple_semicolons(self):
        result = StyleTransformer.ensure_space_before_double_semicolon("foo;;bar;;", True)
        assert result == "foo ;;bar ;;"


class TestFunctionStyleParser:
    """Tests for FunctionStyleParser"""

    def test_parse_fnpar(self):
        result = FunctionStyleParser.parse_function_style("fnpar")
        assert result == 0

    def test_parse_fnonly(self):
        result = FunctionStyleParser.parse_function_style("fnonly")
        assert result == 1

    def test_parse_paronly(self):
        result = FunctionStyleParser.parse_function_style("paronly")
        assert result == 2

    def test_parse_invalid(self):
        result = FunctionStyleParser.parse_function_style("invalid")
        assert result is None

    def test_get_style_names(self):
        names = FunctionStyleParser.get_style_names()
        assert "fnpar" in names
        assert "fnonly" in names
        assert "paronly" in names
        assert len(names) == 3
