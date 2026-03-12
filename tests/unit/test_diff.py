"""Unit tests for beautysh.diff module."""

from colorama import Fore

from beautysh.diff import DiffFormatter


class TestColorDiff:
    """Tests for DiffFormatter.color_diff()"""

    def test_added_line_green(self):
        formatter = DiffFormatter(use_color=True)
        result = list(formatter.color_diff(iter(["+added"])))
        assert result == [Fore.GREEN + "+added" + Fore.RESET]

    def test_removed_line_red(self):
        formatter = DiffFormatter(use_color=True)
        result = list(formatter.color_diff(iter(["-removed"])))
        assert result == [Fore.RED + "-removed" + Fore.RESET]

    def test_caret_line_blue(self):
        formatter = DiffFormatter(use_color=True)
        result = list(formatter.color_diff(iter(["^changed"])))
        assert result == [Fore.BLUE + "^changed" + Fore.RESET]

    def test_context_line_unchanged(self):
        formatter = DiffFormatter(use_color=True)
        result = list(formatter.color_diff(iter([" context"])))
        assert result == [" context"]


class TestPrintDiff:
    """Tests for DiffFormatter.print_diff()"""

    def test_prints_unified_diff(self, capsys):
        formatter = DiffFormatter(use_color=False)
        formatter.print_diff("a\nb", "a\nc")
        captured = capsys.readouterr()
        assert "--- original" in captured.out
        assert "+++ formatted" in captured.out
        assert "@@" in captured.out
        assert "-b" in captured.out
        assert "+c" in captured.out

    def test_identical_prints_nothing(self, capsys):
        formatter = DiffFormatter(use_color=False)
        formatter.print_diff("same\n", "same\n")
        captured = capsys.readouterr()
        assert captured.out == ""

    def test_no_color_skips_coloring(self, capsys):
        formatter = DiffFormatter(use_color=False)
        formatter.print_diff("a", "b")
        captured = capsys.readouterr()
        assert Fore.GREEN not in captured.out
        assert Fore.RED not in captured.out

    def test_color_applies_ansi_codes(self, capsys):
        formatter = DiffFormatter(use_color=True)
        formatter.print_diff("a", "b")
        captured = capsys.readouterr()
        assert Fore.GREEN in captured.out
        assert Fore.RED in captured.out
