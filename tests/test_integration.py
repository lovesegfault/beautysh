import pytest

from beautysh import Beautify

from . import BeautyshTest


@pytest.fixture
def beautysh_test(fixture_dir):
    return BeautyshTest(fixture_dir)


@pytest.mark.xfail(strict=True)
def test_sanity(beautysh_test):
    beautysh_test.assert_formatting("sanity")


def test_basic(beautysh_test):
    beautysh_test.assert_formatting("basic")


def test_complex(beautysh_test):
    beautysh_test.assert_formatting("complex")


def test_heredoc_basic(beautysh_test):
    beautysh_test.assert_formatting("heredoc_basic")


def test_heredoc_complex(beautysh_test):
    beautysh_test.assert_formatting("heredoc_complex")


def test_if_condition_basic(beautysh_test):
    beautysh_test.assert_formatting("if_condition_basic")


def test_if_condition_for_loop(beautysh_test):
    beautysh_test.assert_formatting("if_condition_for_loop")


def test_if_condition_function(beautysh_test):
    beautysh_test.assert_formatting("if_condition_function")


def test_if_condition_multiline(beautysh_test):
    beautysh_test.assert_formatting("if_condition_multiline")


def test_no_formatter_basic(beautysh_test):
    beautysh_test.assert_formatting("no_formatter_basic")


def test_no_formatter_function(beautysh_test):
    beautysh_test.assert_formatting("no_formatter_function")


def test_indent_basic(beautysh_test):
    beautysh_test.assert_formatting("indent_basic")


def test_indent_string_with_brackets(beautysh_test):
    beautysh_test.assert_formatting("indent_string_with_brackets")


def test_indent_quote_escapes(beautysh_test):
    beautysh_test.assert_formatting("indent_quote_escapes")


def test_indent_mixed(beautysh_test):
    beautysh_test.assert_formatting("indent_mixed")


def test_getopts(beautysh_test):
    beautysh_test.assert_formatting("getopts")


def test_function_styles(beautysh_test):
    raw = beautysh_test.read_file(beautysh_test.fixture_dir / "function_styles_raw.sh")
    for style in range(0, 3):
        formatted = beautysh_test.read_file(
            beautysh_test.fixture_dir / "function_styles_{}.sh".format(style)
        )

        formatter = Beautify()
        formatter.apply_function_style = style

        test, error = formatter.beautify_string(raw)
        assert not error
        beautysh_test.assert_equal_multiline_strings(test, formatted)
