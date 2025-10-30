"""Tests for configuration file support."""

import os
import tempfile
from pathlib import Path

from beautysh import Beautify


def test_config_from_pyproject_toml():
    """Test loading configuration from pyproject.toml."""
    test_script = """function test-func() {
if true; then
echo "test"
fi
}
"""

    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create a pyproject.toml with beautysh config (indent_size = 2)
        pyproject = tmppath / "pyproject.toml"
        pyproject.write_text(
            """[tool.beautysh]
indent_size = 2
"""
        )

        # Create test script
        test_file = tmppath / "test.sh"
        test_file.write_text(test_script)

        # Change to temp directory and run beautysh
        original_dir = os.getcwd()
        try:
            os.chdir(tmppath)

            # Run beautysh main which should pick up the config
            beautifier = Beautify()
            exit_code = beautifier.main([str(test_file)])
            assert exit_code == 0, f"beautysh exited with code {exit_code}"

        finally:
            os.chdir(original_dir)

        # Read the formatted file
        formatted = test_file.read_text()

        # The indentation should be 2 spaces (from config), not 4 (default)
        assert "  if true; then" in formatted
        assert "    echo" in formatted
        # Check there's no 6-space indentation (which would happen with indent_size=4)
        assert "      echo" not in formatted


def test_cli_overrides_config():
    """Test that CLI arguments override config file settings."""
    test_script = """function test() {
if true; then
echo "test"
fi
}
"""

    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create config with indent_size = 2
        pyproject = tmppath / "pyproject.toml"
        pyproject.write_text(
            """[tool.beautysh]
indent_size = 2
"""
        )

        # Create test script
        test_file = tmppath / "test.sh"
        test_file.write_text(test_script)

        # Change to temp directory and run beautysh with override
        original_dir = os.getcwd()
        try:
            os.chdir(tmppath)

            # Run beautysh with explicit --indent-size 8 (should override config)
            beautifier = Beautify()
            exit_code = beautifier.main(["--indent-size", "8", str(test_file)])
            assert exit_code == 0, f"beautysh exited with code {exit_code}"

        finally:
            os.chdir(original_dir)

        # Read the formatted file
        formatted = test_file.read_text()

        # Should use 8 spaces (from CLI override), not 2 (from config)
        assert "        if true; then" in formatted
        assert "                echo" in formatted
