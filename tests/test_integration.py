from pathlib import Path

import pytest

from beautysh import Beautify

from . import BeautyshTest


class IntegrationTest(BeautyshTest):
    def __init__(self, method_name: str):
        fixture_dir = Path(__file__).parent.absolute() / "fixtures"
        BeautyshTest.__init__(self, method_name, fixture_dir)

    @pytest.mark.xfail(strict=True)
    def test_sanity(self):
        self.assert_formatting("sanity")

    def test_basic(self):
        self.assert_formatting("basic")

    def test_complex(self):
        self.assert_formatting("complex")

    def test_heredoc_basic(self):
        self.assert_formatting("heredoc_basic")

    def test_heredoc_complex(self):
        self.assert_formatting("heredoc_complex")

    def test_if_condition_basic(self):
        self.assert_formatting("if_condition_basic")

    def test_if_condition_for_loop(self):
        self.assert_formatting("if_condition_for_loop")

    def test_if_condition_function(self):
        self.assert_formatting("if_condition_function")

    def test_if_condition_multiline(self):
        self.assert_formatting("if_condition_multiline")

    def test_no_formatter_basic(self):
        self.assert_formatting("no_formatter_basic")

    def test_no_formatter_function(self):
        self.assert_formatting("no_formatter_function")

    def test_indent_basic(self):
        self.assert_formatting("indent_basic")

    def test_indent_string_with_brackets(self):
        self.assert_formatting("indent_string_with_brackets")

    def test_indent_quote_escapes(self):
        self.assert_formatting("indent_quote_escapes")

    def test_indent_mixed(self):
        self.assert_formatting("indent_mixed")

    def test_getopts(self):
        self.assert_formatting("getopts")

    def test_function_styles(self):
        raw = self.read_file(self.fixture_dir / "function_styles_raw.sh")
        for style in range(0, 3):
            formatted = self.read_file(self.fixture_dir / "function_styles_{}.sh".format(style))

            formatter = Beautify()
            formatter.apply_function_style = style

            test, error = formatter.beautify_string(raw)
            self.assertFalse(error)
            self.assert_equal_multiline_strings(test, formatted)
