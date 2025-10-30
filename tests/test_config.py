"""Tests for configuration file support."""

import os
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Optional

from beautysh import Beautify


@contextmanager
def beautysh_test_env(
    test_script: str,
    filename: str = "test.sh",
    pyproject_config: Optional[str] = None,
    editorconfig: Optional[str] = None,
):
    """Test harness for beautysh configuration tests.

    Args:
        test_script: The bash script to format
        filename: Name of the test file
        pyproject_config: Optional pyproject.toml [tool.beautysh] content
        editorconfig: Optional .editorconfig file content

    Yields:
        Tuple of (run_beautysh, get_formatted):
            run_beautysh: Function to run beautysh with given args
            get_formatted: Function to get the formatted file content
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create config files if provided
        if pyproject_config:
            pyproject = tmppath / "pyproject.toml"
            pyproject.write_text(f"[tool.beautysh]\n{pyproject_config}\n")

        if editorconfig:
            editor_cfg = tmppath / ".editorconfig"
            editor_cfg.write_text(editorconfig)

        # Create test script
        test_file = tmppath / filename
        test_file.write_text(test_script)

        def run_beautysh(args=None):
            """Run beautysh with given args (default: just the filename)."""
            original_dir = os.getcwd()
            try:
                os.chdir(tmppath)
                beautifier = Beautify()
                exit_code = beautifier.main(args or [str(test_file)])
                assert exit_code == 0, f"beautysh exited with code {exit_code}"
            finally:
                os.chdir(original_dir)

        def get_formatted():
            """Get the formatted file content."""
            return test_file.read_text()

        yield run_beautysh, get_formatted


def test_config_from_pyproject_toml():
    """Test loading configuration from pyproject.toml."""
    test_script = """function test-func() {
if true; then
echo "test"
fi
}
"""

    with beautysh_test_env(test_script, pyproject_config="indent_size = 2") as (
        run,
        get_formatted,
    ):
        run()
        formatted = get_formatted()

        # Should use 2 spaces from config
        assert "  if true; then" in formatted
        assert "    echo" in formatted
        assert "      echo" not in formatted  # No 4-space indentation


def test_cli_overrides_config():
    """Test that CLI arguments override config file settings."""
    test_script = """function test() {
if true; then
echo "test"
fi
}
"""

    with beautysh_test_env(test_script, pyproject_config="indent_size = 2") as (
        run,
        get_formatted,
    ):
        run(["--indent-size", "8", "test.sh"])
        formatted = get_formatted()

        # Should use 8 spaces from CLI, not 2 from config
        assert "        if true; then" in formatted
        assert "                echo" in formatted


def test_editorconfig_support():
    """Test loading configuration from .editorconfig."""
    test_script = """function test() {
if true; then
echo "test"
fi
}
"""

    editor_config = """root = true

[*.sh]
indent_style = space
indent_size = 2
"""

    with beautysh_test_env(test_script, editorconfig=editor_config) as (run, get_formatted):
        run()
        formatted = get_formatted()

        # Should use 2 spaces from EditorConfig
        assert "  if true; then" in formatted
        assert "    echo" in formatted


def test_editorconfig_tab_style():
    """Test EditorConfig with tab indentation."""
    test_script = """function test() {
if true; then
echo "test"
fi
}
"""

    editor_config = """root = true

[*.sh]
indent_style = tab
"""

    with beautysh_test_env(test_script, editorconfig=editor_config) as (run, get_formatted):
        run()
        formatted = get_formatted()

        # Should use tabs from EditorConfig
        assert "\tif true; then" in formatted
        assert "\t\techo" in formatted


def test_pyproject_overrides_editorconfig():
    """Test that pyproject.toml overrides EditorConfig."""
    test_script = """function test() {
if true; then
echo "test"
fi
}
"""

    editor_config = """root = true

[*.sh]
indent_style = space
indent_size = 2
"""

    with beautysh_test_env(
        test_script, pyproject_config="indent_size = 6", editorconfig=editor_config
    ) as (run, get_formatted):
        run()
        formatted = get_formatted()

        # Should use 6 spaces from pyproject.toml, not 2 from EditorConfig
        assert "      if true; then" in formatted
        assert "            echo" in formatted


def test_editorconfig_bash_extension():
    """Test EditorConfig works with .bash files."""
    test_script = """function test() {
if true; then
echo "test"
fi
}
"""

    editor_config = """root = true

[*.bash]
indent_style = space
indent_size = 3
"""

    with beautysh_test_env(test_script, filename="test.bash", editorconfig=editor_config) as (
        run,
        get_formatted,
    ):
        run()
        formatted = get_formatted()

        # Should use 3 spaces from EditorConfig for .bash files
        assert "   if true; then" in formatted
        assert "      echo" in formatted
