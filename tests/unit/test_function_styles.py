"""Unit tests for beautysh.function_styles module."""

from beautysh.function_styles import FunctionStyle


class TestFromName:
    def test_fnpar(self):
        assert FunctionStyle.from_name("fnpar") is FunctionStyle.FNPAR

    def test_fnonly(self):
        assert FunctionStyle.from_name("fnonly") is FunctionStyle.FNONLY

    def test_paronly(self):
        assert FunctionStyle.from_name("paronly") is FunctionStyle.PARONLY

    def test_invalid(self):
        assert FunctionStyle.from_name("invalid") is None


class TestAllNames:
    def test_returns_all_three(self):
        names = FunctionStyle.all_names()
        assert names == ["fnpar", "fnonly", "paronly"]


class TestDetect:
    def test_fnpar(self):
        assert FunctionStyle.detect("function foo() {") is FunctionStyle.FNPAR

    def test_fnonly(self):
        assert FunctionStyle.detect("function bar {") is FunctionStyle.FNONLY

    def test_paronly(self):
        assert FunctionStyle.detect("baz() {") is FunctionStyle.PARONLY

    def test_no_function(self):
        assert FunctionStyle.detect("echo hello") is None


class TestTransformTo:
    def test_fnpar_to_paronly(self):
        result = FunctionStyle.FNPAR.transform_to("function foo() {", FunctionStyle.PARONLY)
        assert result == "foo() {"

    def test_paronly_to_fnonly(self):
        result = FunctionStyle.PARONLY.transform_to("foo() {", FunctionStyle.FNONLY)
        assert result == "function foo {"
