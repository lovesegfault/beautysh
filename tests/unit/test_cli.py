"""Unit tests for beautysh.cli module."""

import io
import sys

import pytest

from beautysh.cli import BeautyshCLI

UNFORMATTED = "if true; then\necho x\nfi\n"
FORMATTED = "if true; then\n    echo x\nfi\n"
# Unbalanced if/fi: formatter will report indent/outdent mismatch
BROKEN = "if true; then\necho x\n"


@pytest.fixture
def unformatted_file(tmp_path, monkeypatch):
    """Unformatted script in clean tmp_path (no pyproject/editorconfig)."""
    monkeypatch.chdir(tmp_path)
    f = tmp_path / "test.sh"
    f.write_text(UNFORMATTED)
    return f


@pytest.fixture
def formatted_file(tmp_path, monkeypatch):
    """Create a tmp_path with an already-formatted script."""
    monkeypatch.chdir(tmp_path)
    f = tmp_path / "test.sh"
    f.write_text(FORMATTED)
    return f


class TestCLIMain:
    """Tests for BeautyshCLI.main()"""

    def test_empty_argv_prints_help(self, capsys, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        exit_code = BeautyshCLI().main([])
        captured = capsys.readouterr()
        assert exit_code == 0
        assert "Bash beautifier" in captured.out
        assert "fnpar" in captured.out
        assert "fnonly" in captured.out
        assert "paronly" in captured.out

    def test_help_flag(self, capsys, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        exit_code = BeautyshCLI().main(["--help"])
        captured = capsys.readouterr()
        assert exit_code == 0
        assert "Bash beautifier" in captured.out

    def test_version_flag(self, capsys, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        exit_code = BeautyshCLI().main(["--version"])
        captured = capsys.readouterr()
        assert exit_code == 0
        assert captured.out.strip() != ""

    def test_no_files_returns_1(self, capsys, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        exit_code = BeautyshCLI().main(["-i", "2"])
        captured = capsys.readouterr()
        assert exit_code == 1
        assert "at least one input file" in captured.err

    def test_formats_file_in_place(self, unformatted_file):
        exit_code = BeautyshCLI().main([str(unformatted_file)])
        assert exit_code == 0
        assert unformatted_file.read_text() == FORMATTED

    def test_check_mode_returns_1_when_unformatted(self, unformatted_file, capsys, monkeypatch):
        monkeypatch.setenv("NO_COLOR", "1")
        exit_code = BeautyshCLI().main(["--check", str(unformatted_file)])
        captured = capsys.readouterr()
        assert exit_code == 1
        # File should NOT be modified in check mode
        assert unformatted_file.read_text() == UNFORMATTED
        # Diff should be printed
        assert "---" in captured.out
        assert "+++" in captured.out

    def test_check_mode_returns_0_when_formatted(self, formatted_file):
        exit_code = BeautyshCLI().main(["--check", str(formatted_file)])
        assert exit_code == 0
        assert formatted_file.read_text() == FORMATTED

    def test_backup_creates_bak_file(self, unformatted_file):
        exit_code = BeautyshCLI().main(["--backup", str(unformatted_file)])
        assert exit_code == 0
        bak = unformatted_file.with_suffix(".sh.bak")
        assert bak.exists()
        assert bak.read_text() == UNFORMATTED
        assert unformatted_file.read_text() == FORMATTED

    def test_invalid_function_style_returns_1(self, unformatted_file, capsys):
        exit_code = BeautyshCLI().main(["-s", "bogus", str(unformatted_file)])
        assert exit_code == 1
        captured = capsys.readouterr()
        assert "Invalid value 'bogus'" in captured.err
        # File should not have been touched
        assert unformatted_file.read_text() == UNFORMATTED

    def test_valid_function_style(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        f = tmp_path / "test.sh"
        f.write_text("function foo() {\necho x\n}\n")
        exit_code = BeautyshCLI().main(["-s", "paronly", str(f)])
        assert exit_code == 0
        assert "foo()" in f.read_text()
        assert "function" not in f.read_text()

    def test_tab_flag(self, unformatted_file):
        exit_code = BeautyshCLI().main(["--tab", str(unformatted_file)])
        assert exit_code == 0
        assert "\techo x" in unformatted_file.read_text()

    def test_stdin_path(self, monkeypatch, capsys, tmp_path):
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(sys, "stdin", io.StringIO(UNFORMATTED))
        exit_code = BeautyshCLI().main(["-"])
        captured = capsys.readouterr()
        assert exit_code == 0
        assert captured.out == FORMATTED

    def test_missing_file_returns_1(self, capsys, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        exit_code = BeautyshCLI().main(["/nonexistent/path/to/file.sh"])
        captured = capsys.readouterr()
        assert exit_code == 1
        assert "Error processing" in captured.err

    def test_formatter_error_does_not_write_file(self, tmp_path, monkeypatch, capsys):
        monkeypatch.chdir(tmp_path)
        f = tmp_path / "broken.sh"
        f.write_text(BROKEN)
        exit_code = BeautyshCLI().main([str(f)])
        captured = capsys.readouterr()
        assert exit_code == 1
        assert f.read_text() == BROKEN
        assert "Not writing" in captured.err
        assert "use --force" in captured.err

    def test_force_writes_despite_formatter_error(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        f = tmp_path / "broken.sh"
        f.write_text(BROKEN)
        exit_code = BeautyshCLI().main(["--force", str(f)])
        assert exit_code == 1
        # File was rewritten with best-effort output (body indented, no fi)
        assert f.read_text() != BROKEN
        assert "    echo x" in f.read_text()

    def test_malformed_pyproject_exits_2(self, tmp_path, monkeypatch, capsys):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "pyproject.toml").write_text("invalid [[[")
        (tmp_path / "test.sh").write_text(FORMATTED)
        exit_code = BeautyshCLI().main([str(tmp_path / "test.sh")])
        captured = capsys.readouterr()
        assert exit_code == 2
        assert "Could not parse pyproject.toml" in captured.err

    def test_multi_file_error_isolated(self, tmp_path, monkeypatch):
        """One broken file doesn't prevent other files from being formatted."""
        monkeypatch.chdir(tmp_path)
        good1 = tmp_path / "good1.sh"
        good1.write_text(UNFORMATTED)
        bad = tmp_path / "bad.sh"
        bad.write_text(BROKEN)
        good2 = tmp_path / "good2.sh"
        good2.write_text(UNFORMATTED)

        exit_code = BeautyshCLI().main([str(good1), str(bad), str(good2)])

        assert exit_code == 1
        assert good1.read_text() == FORMATTED
        assert bad.read_text() == BROKEN  # not overwritten
        assert good2.read_text() == FORMATTED


class TestCLIInternals:
    """Tests for internal CLI helpers."""

    def test_version_fallback(self, monkeypatch):
        from importlib.metadata import PackageNotFoundError

        def fake_version(name):
            raise PackageNotFoundError(name)

        monkeypatch.setattr("beautysh.cli.version", fake_version)
        cli = BeautyshCLI()
        assert cli.get_version() == "Not Available"

    def test_beautify_file_unconfigured_raises(self):
        cli = BeautyshCLI()
        with pytest.raises(RuntimeError, match="Formatter not configured"):
            cli.beautify_file("-")


def test_module_main(monkeypatch, capsys, tmp_path):
    """Smoke test for __main__.main()."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["beautysh", "--version"])
    from beautysh.__main__ import main

    with pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert captured.out.strip() != ""
