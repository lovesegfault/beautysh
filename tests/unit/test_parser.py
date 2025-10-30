"""Unit tests for beautysh.parser module."""

from beautysh.parser import BashParser


class TestGetTestRecord:
    """Tests for BashParser.get_test_record()"""

    def test_removes_single_quoted_strings(self):
        result = BashParser.get_test_record("echo 'hello world'")
        assert result == "echo "

    def test_removes_double_quoted_strings(self):
        result = BashParser.get_test_record('echo "hello world"')
        assert result == "echo "

    def test_removes_backtick_strings(self):
        result = BashParser.get_test_record("echo `date`")
        assert result == "echo "

    def test_removes_comments(self):
        result = BashParser.get_test_record('echo "test"  # this is a comment')
        assert result == "echo  "  # Two spaces before comment location

    def test_removes_escaped_quotes(self):
        result = BashParser.get_test_record(r"echo \"test\"")
        assert '"' not in result

    def test_preserves_keywords(self):
        result = BashParser.get_test_record('if [ "$x" = "y" ]; then')
        assert "if" in result
        assert "then" in result

    def test_preserves_brackets(self):
        result = BashParser.get_test_record('if [ "$x" = "y" ]; then')
        assert "[" in result
        assert "]" in result

    def test_complex_line(self):
        line = 'if [ "$HOME" = "/root" ]; then  # check home'
        result = BashParser.get_test_record(line)
        assert "if" in result
        assert "then" in result
        assert "/root" not in result
        assert "check home" not in result


class TestDetectUnclosedQuote:
    """Tests for BashParser.detect_unclosed_quote()"""

    def test_no_unclosed_quotes(self):
        test_record = "echo test"
        unclosed_double, unclosed_single = BashParser.detect_unclosed_quote(test_record)
        assert not unclosed_double
        assert not unclosed_single

    def test_unclosed_double_quote(self):
        test_record = 'echo "'
        unclosed_double, unclosed_single = BashParser.detect_unclosed_quote(test_record)
        assert unclosed_double
        assert not unclosed_single

    def test_unclosed_single_quote(self):
        test_record = "echo '"
        unclosed_double, unclosed_single = BashParser.detect_unclosed_quote(test_record)
        assert not unclosed_double
        assert unclosed_single

    def test_multiple_unclosed_double_quotes_odd(self):
        test_record = 'echo " test " more "'
        unclosed_double, unclosed_single = BashParser.detect_unclosed_quote(test_record)
        assert unclosed_double

    def test_multiple_quotes_even(self):
        test_record = 'echo " test " more " end "'
        unclosed_double, unclosed_single = BashParser.detect_unclosed_quote(test_record)
        assert not unclosed_double


class TestDetectFunctionStyle:
    """Tests for BashParser.detect_function_style()"""

    def test_fnpar_style(self):
        result = BashParser.detect_function_style("function foo() {")
        assert result == 0

    def test_fnonly_style(self):
        result = BashParser.detect_function_style("function bar {")
        assert result == 1

    def test_paronly_style(self):
        result = BashParser.detect_function_style("baz() {")
        assert result == 2

    def test_no_function(self):
        # foo() is actually a valid function declaration, so use a different example
        result = BashParser.detect_function_style('echo "hello world"')
        assert result is None

    def test_function_with_hyphens(self):
        result = BashParser.detect_function_style("function test-func() {")
        assert result == 0

    def test_function_with_colons(self):
        result = BashParser.detect_function_style("function namespace:func() {")
        assert result == 0

    def test_function_with_at_sign(self):
        result = BashParser.detect_function_style("function @special() {")
        assert result == 0


class TestNormalizeDocaseLines:
    """Tests for BashParser.normalize_do_case_lines()"""

    def test_splits_do_case(self):
        script = "while true; do case $x in"
        result = BashParser.normalize_do_case_lines(script)
        lines = result.split("\n")
        assert len(lines) == 2
        assert "do" in lines[0]
        assert "case" in lines[1]

    def test_splits_then_case(self):
        script = "if true; then case $x in"
        result = BashParser.normalize_do_case_lines(script)
        lines = result.split("\n")
        assert len(lines) == 2
        assert "then" in lines[0]
        assert "case" in lines[1]

    def test_preserves_normal_lines(self):
        script = "if true; then\n    case $x in"
        result = BashParser.normalize_do_case_lines(script)
        lines = result.split("\n")
        assert len(lines) == 2

    def test_handles_multiline(self):
        script = 'echo "test"\nwhile true; do case $x in\necho "more"'
        result = BashParser.normalize_do_case_lines(script)
        lines = result.split("\n")
        assert len(lines) == 4


class TestDetectHeredoc:
    """Tests for BashParser.detect_heredoc()"""

    def test_basic_heredoc(self):
        test_record = "cat <<EOF"
        stripped = "cat <<EOF"
        is_heredoc, terminator = BashParser.detect_heredoc(test_record, stripped)
        assert is_heredoc
        assert terminator == "EOF"

    def test_heredoc_with_dash(self):
        test_record = "cat <<-END"
        stripped = "cat <<-END"
        is_heredoc, terminator = BashParser.detect_heredoc(test_record, stripped)
        assert is_heredoc
        assert terminator == "END"

    def test_heredoc_with_quotes(self):
        test_record = 'cat <<"EOF"'
        stripped = 'cat <<"EOF"'
        is_heredoc, terminator = BashParser.detect_heredoc(test_record, stripped)
        assert is_heredoc
        assert terminator == "EOF"

    def test_not_herestring(self):
        test_record = "cat <<<$var"
        stripped = "cat <<<$var"
        is_heredoc, terminator = BashParser.detect_heredoc(test_record, stripped)
        assert not is_heredoc

    def test_not_arithmetic_shift(self):
        test_record = "$(( x << 2 ))"
        stripped = "$(( x << 2 ))"
        is_heredoc, terminator = BashParser.detect_heredoc(test_record, stripped)
        assert not is_heredoc


class TestIsLineContinuation:
    """Tests for BashParser.is_line_continuation()"""

    def test_line_with_backslash(self):
        assert BashParser.is_line_continuation('echo "test" \\')

    def test_line_without_backslash(self):
        assert not BashParser.is_line_continuation('echo "test"')

    def test_empty_line(self):
        assert not BashParser.is_line_continuation("")

    def test_backslash_in_middle(self):
        # Backslash in middle doesn't count
        assert not BashParser.is_line_continuation('echo "test\\nmore"')
