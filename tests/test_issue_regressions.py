"""Regression tests for specific GitHub issues that have been fixed."""

from . import assert_formatting


def test_issue53_multiline_strings_not_indented(fixture_dir):
    """Test that multiline string contents are preserved (issue #53)."""
    # This is already covered by test_multiline_strings.py
    # but keeping reference here for documentation
    assert_formatting(fixture_dir, "multiline_content")


def test_issue58_markdown_link_with_backticks(fixture_dir):
    """Test that multiline MD link with backticks doesn't cause parse error (issue #58)."""
    assert_formatting(fixture_dir, "issue58_md_link")


def test_issue81_shift_operator(fixture_dir):
    """Test that << shift operator in arithmetic doesn't cause indent mismatch (issue #81)."""
    # This is already covered by test_arithmetic.py
    # but keeping reference here for documentation
    assert_formatting(fixture_dir, "arithmetic_shift")


def test_issue101_multiline_subcommand_indentation(fixture_dir):
    """Test that multiline command substitutions maintain proper indentation (issue #101)."""
    assert_formatting(fixture_dir, "issue101_multiline_subcommand")


def test_issue78_multiline_array_in_case(fixture_dir):
    """Test multiline array in case statement doesn't cause indent mismatch (issue #78)."""
    assert_formatting(fixture_dir, "issue78_multiline_array_case")


def test_issue64_do_case_same_line(fixture_dir):
    """Test that 'do case' on the same line doesn't cause indent/outdent mismatch (issue #64)."""
    assert_formatting(fixture_dir, "issue64_do_case")


def test_issue265_heredoc_in_function(fixture_dir):
    """Test heredoc terminators at column 0 inside functions (issue #265)."""
    assert_formatting(fixture_dir, "issue265_heredoc_function")


def test_issue265_quoted_empty_case_patterns(fixture_dir):
    """Test empty quoted case patterns like "" or '' (issue #265)."""
    assert_formatting(fixture_dir, "issue265_quoted_case")


def test_issue267_formatter_off_with_variable_style(fixture_dir):
    """Test that @formatter:off/on directives respect variable style option (issue #267)."""
    assert_formatting(fixture_dir, "issue267_formatter_variable", variable_style="braces")


def test_issue268_variable_style_single_quotes(fixture_dir):
    """Test that variables inside single quotes are not transformed (issue #268)."""
    assert_formatting(fixture_dir, "issue268_single_quotes", variable_style="braces")


def test_issue268_variable_style_heredoc_quotes(fixture_dir):
    """Test that variables in heredocs with quoted terminators are not transformed (issue #268)."""
    assert_formatting(fixture_dir, "issue268_heredoc_quotes", variable_style="braces")


def test_issue270_escaped_case_patterns(fixture_dir):
    r"""Test case patterns that begin with escaped chars like \?) (issue #270).

    ESCAPED_CHAR stripping reduces `\?)` to `)`, which the CASE_CHOICE_PATTERN
    (which requires content before the paren to avoid issue #78 false positives)
    cannot match. Detect this by noting that the original line had content
    before the `)` that get_test_record removed.
    """
    assert_formatting(fixture_dir, "issue270_escaped_case")


def test_issue272_backslash_continuation_in_quoted_string(fixture_dir):
    """Test backslash continuation inside a quoted string in an if condition (issue #272).

    When a line like `if foo="$(echo \\` continues onto the next line, keywords
    appearing after the closing quote on the continuation line (like `then`)
    must still be counted for indentation tracking.
    """
    assert_formatting(fixture_dir, "issue272_split_lines")


def test_keyword_as_command_argument(fixture_dir):
    """Keywords used as command arguments (echo done, printf then) must not affect indent.

    Previously 'echo done' matched INDENT_DECREASE_KEYWORDS because the regex
    prefix (\\s|\\A|;) matched the single space between 'echo' and 'done'.
    """
    assert_formatting(fixture_dir, "keyword_as_argument")
