"""Unit tests for beautysh.parser module."""

from beautysh import parser
from beautysh.function_styles import FunctionStyle


class TestGetTestRecord:
    """Tests for parser.get_test_record()"""

    def test_removes_single_quoted_strings(self):
        result = parser.get_test_record("echo 'hello world'")
        assert result == "echo "

    def test_removes_double_quoted_strings(self):
        result = parser.get_test_record('echo "hello world"')
        assert result == "echo "

    def test_removes_backtick_strings(self):
        result = parser.get_test_record("echo `date`")
        assert result == "echo "

    def test_removes_comments(self):
        result = parser.get_test_record('echo "test"  # this is a comment')
        assert result == "echo  "  # Two spaces before comment location

    def test_removes_escaped_quotes(self):
        result = parser.get_test_record(r"echo \"test\"")
        assert '"' not in result

    def test_preserves_keywords(self):
        result = parser.get_test_record('if [ "$x" = "y" ]; then')
        assert "if" in result
        assert "then" in result

    def test_preserves_brackets(self):
        result = parser.get_test_record('if [ "$x" = "y" ]; then')
        assert "[" in result
        assert "]" in result

    def test_complex_line(self):
        line = 'if [ "$HOME" = "/root" ]; then  # check home'
        result = parser.get_test_record(line)
        assert "if" in result
        assert "then" in result
        assert "/root" not in result
        assert "check home" not in result


class TestDetectUnclosedQuote:
    """Tests for parser.detect_unclosed_quote()"""

    def test_no_unclosed_quotes(self):
        assert parser.detect_unclosed_quote("echo test") is None

    def test_unclosed_double_quote(self):
        assert parser.detect_unclosed_quote('echo "') == '"'

    def test_unclosed_single_quote(self):
        assert parser.detect_unclosed_quote("echo '") == "'"

    def test_multiple_unclosed_double_quotes_odd(self):
        assert parser.detect_unclosed_quote('echo " test " more "') == '"'

    def test_multiple_quotes_even(self):
        assert parser.detect_unclosed_quote('echo " test " more " end "') is None

    def test_double_takes_precedence_over_single(self):
        # Matches the old tuple order: double was checked first.
        assert parser.detect_unclosed_quote("echo \" '") == '"'


class TestFunctionStyleDetect:
    """Tests for FunctionStyle.detect() (formerly parser.detect_function_style)."""

    def test_fnpar_style(self):
        assert FunctionStyle.detect("function foo() {") is FunctionStyle.FNPAR

    def test_fnonly_style(self):
        assert FunctionStyle.detect("function bar {") is FunctionStyle.FNONLY

    def test_paronly_style(self):
        assert FunctionStyle.detect("baz() {") is FunctionStyle.PARONLY

    def test_no_function(self):
        assert FunctionStyle.detect('echo "hello world"') is None

    def test_function_with_hyphens(self):
        assert FunctionStyle.detect("function test-func() {") is FunctionStyle.FNPAR

    def test_function_with_colons(self):
        assert FunctionStyle.detect("function namespace:func() {") is FunctionStyle.FNPAR

    def test_function_with_at_sign(self):
        assert FunctionStyle.detect("function @special() {") is FunctionStyle.FNPAR


class TestNormalizeDocaseLines:
    """Tests for parser.normalize_do_case_lines()"""

    def test_splits_do_case(self):
        script = "while true; do case $x in"
        result = parser.normalize_do_case_lines(script)
        lines = result.split("\n")
        assert len(lines) == 2
        assert "do" in lines[0]
        assert "case" in lines[1]

    def test_splits_then_case(self):
        script = "if true; then case $x in"
        result = parser.normalize_do_case_lines(script)
        lines = result.split("\n")
        assert len(lines) == 2
        assert "then" in lines[0]
        assert "case" in lines[1]

    def test_preserves_normal_lines(self):
        script = "if true; then\n    case $x in"
        result = parser.normalize_do_case_lines(script)
        lines = result.split("\n")
        assert len(lines) == 2

    def test_handles_multiline(self):
        script = 'echo "test"\nwhile true; do case $x in\necho "more"'
        result = parser.normalize_do_case_lines(script)
        lines = result.split("\n")
        assert len(lines) == 4

    def test_quoted_content_creates_false_do_case_no_split(self):
        # After quote stripping, test_record sees 'do case', but in the
        # original there is no whitespace before 'case' (it's ""case).
        # CASE_SPLIT_PATTERN can't match, so the line must be preserved as-is.
        script = 'do ""case x in'
        result = parser.normalize_do_case_lines(script)
        assert result == script

    def test_does_not_split_echo_do_case(self):
        # 'do' and 'case' here are command arguments, not keywords.
        script = "echo do case stuff"
        result = parser.normalize_do_case_lines(script)
        assert result == script


class TestDetectHeredoc:
    """Tests for parser.detect_heredoc()"""

    def test_basic_heredoc(self):
        assert parser.detect_heredoc("cat <<EOF", "cat <<EOF") == "EOF"

    def test_heredoc_with_dash(self):
        assert parser.detect_heredoc("cat <<-END", "cat <<-END") == "END"

    def test_heredoc_with_quotes(self):
        assert parser.detect_heredoc('cat <<"EOF"', 'cat <<"EOF"') == "EOF"

    def test_not_herestring(self):
        assert parser.detect_heredoc("cat <<<$var", "cat <<<$var") is None

    def test_not_arithmetic_shift(self):
        assert parser.detect_heredoc("$(( x << 2 ))", "$(( x << 2 ))") is None

    def test_unmatched_delimiter_not_heredoc(self):
        # Dot is not a word character, so HEREDOC_TERMINATOR won't match.
        # Previously re.sub() returned the input unchanged, setting the
        # entire line as the terminator and breaking the rest of the file.
        assert parser.detect_heredoc("cat << .", "cat << .") is None

    def test_arithmetic_command_not_heredoc(self):
        # (( )) without $ is a bash arithmetic command; << is bit-shift.
        # Previously only $((...)) was excluded, so this entered heredoc mode
        # with terminator '2' and corrupted the rest of the file.
        line = "((x = 1 << 2))"
        assert parser.detect_heredoc(line, line) is None

    def test_let_shift_not_heredoc(self):
        line = "let x=1<<2"
        assert parser.detect_heredoc(line, line) is None

    def test_heredoc_with_pipeline(self):
        # cat <<EOF|grep is valid bash: EOF is the terminator, |grep is a pipeline.
        # Previously the regex had | as a literal inside [_|\w] and matched 'EOF|grep'.
        line = "cat <<EOF|grep foo"
        assert parser.detect_heredoc(line, line) == "EOF"

    def test_arithmetic_command_with_dollar_var(self):
        # $shift prevents \w+ from matching at that position; previously
        # this set the whole line as terminator.
        line = "(( result = x << $shift ))"
        assert parser.detect_heredoc(line, line) is None


class TestIsLineContinuation:
    """Tests for parser.is_line_continuation()"""

    def test_line_with_backslash(self):
        assert parser.is_line_continuation('echo "test" \\')

    def test_line_without_backslash(self):
        assert not parser.is_line_continuation('echo "test"')

    def test_empty_line(self):
        assert not parser.is_line_continuation("")

    def test_backslash_in_middle(self):
        # Backslash in middle doesn't count
        assert not parser.is_line_continuation('echo "test\\nmore"')


class TestIsHeredocQuoted:
    """Tests for parser.is_heredoc_quoted()"""

    def test_single_quoted_terminator(self):
        assert parser.is_heredoc_quoted("cat <<'EOF'")

    def test_double_quoted_terminator(self):
        assert parser.is_heredoc_quoted('cat <<"EOF"')

    def test_backslash_escaped_terminator(self):
        assert parser.is_heredoc_quoted(r"cat <<\EOF")

    def test_unquoted_terminator(self):
        assert not parser.is_heredoc_quoted("cat <<EOF")

    def test_dash_heredoc_single_quoted(self):
        assert parser.is_heredoc_quoted("cat <<-'END'")

    def test_dash_heredoc_double_quoted(self):
        assert parser.is_heredoc_quoted('cat <<-"END"')

    def test_dash_heredoc_backslash(self):
        assert parser.is_heredoc_quoted(r"cat <<-\END")

    def test_dash_heredoc_unquoted(self):
        assert not parser.is_heredoc_quoted("cat <<-EOF")

    def test_with_spaces_before_quotes(self):
        assert parser.is_heredoc_quoted("cat << 'EOF'")

    def test_with_redirect(self):
        assert parser.is_heredoc_quoted("cat <<'EOF' > file")

    def test_quotes_in_command_not_heredoc(self):
        # Command has quotes, but terminator doesn't
        assert not parser.is_heredoc_quoted('echo "test" <<EOF')

    def test_partial_backslash_escape(self):
        # Any backslash after << means quoted
        assert parser.is_heredoc_quoted(r"cat <<E\OF")

    def test_not_a_heredoc(self):
        # Should handle gracefully
        assert not parser.is_heredoc_quoted("echo hello")
