"""Unit tests for beautysh.config module."""

from beautysh.config import (
    load_config_from_beautyshrc,
    load_config_from_editorconfig,
    load_config_from_file,
    load_config_from_pyproject,
    merge_configs,
)


class TestLoadConfigFromFile:
    """Tests for load_config_from_file()"""

    def test_loads_config_with_tool_section(self, tmp_path):
        config_file = tmp_path / ".beautyshrc"
        config_file.write_text(
            """
[tool.beautysh]
indent_size = 2
"""
        )
        config = load_config_from_file(config_file)
        assert config["indent_size"] == 2

    def test_loads_config_without_tool_section(self, tmp_path):
        config_file = tmp_path / ".beautyshrc"
        config_file.write_text(
            """
indent_size = 3
"""
        )
        config = load_config_from_file(config_file)
        assert config["indent_size"] == 3

    def test_returns_empty_dict_when_no_file(self, tmp_path):
        config = load_config_from_file(tmp_path / "nonexistent.toml")
        assert config == {}

    def test_handles_invalid_toml(self, tmp_path):
        config_file = tmp_path / ".beautyshrc"
        config_file.write_text("invalid toml content [[[")
        config = load_config_from_file(config_file)
        assert config == {}


class TestLoadConfigFromPyproject:
    """Tests for load_config_from_pyproject()"""

    def test_returns_empty_dict_when_no_file(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        config = load_config_from_pyproject()
        assert config == {}

    def test_loads_config_from_tool_section(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            """
[tool.beautysh]
indent_size = 2
tab = false
"""
        )
        config = load_config_from_pyproject()
        assert config["indent_size"] == 2
        assert config["tab"] is False

    def test_returns_empty_dict_when_no_beautysh_section(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            """
[tool.other]
value = 123
"""
        )
        config = load_config_from_pyproject()
        assert config == {}

    def test_handles_invalid_toml(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("invalid toml content [[[")
        config = load_config_from_pyproject()
        assert config == {}


class TestLoadConfigFromBeautyshrc:
    """Tests for load_config_from_beautyshrc()"""

    def test_loads_config_from_beautyshrc_root(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        beautyshrc = tmp_path / ".beautyshrc"
        beautyshrc.write_text(
            """
indent_size = 3
"""
        )
        config = load_config_from_beautyshrc()
        assert config["indent_size"] == 3

    def test_loads_config_from_beautyshrc_tool_section(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        beautyshrc = tmp_path / ".beautyshrc"
        beautyshrc.write_text(
            """
[tool.beautysh]
indent_size = 2
"""
        )
        config = load_config_from_beautyshrc()
        assert config["indent_size"] == 2

    def test_returns_empty_dict_when_no_file(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        config = load_config_from_beautyshrc()
        assert config == {}


class TestLoadConfigFromEditorconfig:
    """Tests for load_config_from_editorconfig()"""

    def test_loads_space_indentation(self, tmp_path):
        editorconfig = tmp_path / ".editorconfig"
        editorconfig.write_text(
            """
[*.sh]
indent_style = space
indent_size = 2
"""
        )
        testfile = tmp_path / "test.sh"
        testfile.write_text("#!/bin/bash\n")

        config = load_config_from_editorconfig(str(testfile))
        assert config["tab"] is False
        assert config["indent_size"] == 2

    def test_loads_tab_indentation(self, tmp_path):
        editorconfig = tmp_path / ".editorconfig"
        editorconfig.write_text(
            """
[*.sh]
indent_style = tab
"""
        )
        testfile = tmp_path / "test.sh"
        testfile.write_text("#!/bin/bash\n")

        config = load_config_from_editorconfig(str(testfile))
        assert config["tab"] is True

    def test_returns_empty_dict_when_no_editorconfig(self, tmp_path):
        testfile = tmp_path / "test.sh"
        testfile.write_text("#!/bin/bash\n")

        config = load_config_from_editorconfig(str(testfile))
        assert config == {}

    def test_handles_invalid_indent_size(self, tmp_path):
        editorconfig = tmp_path / ".editorconfig"
        editorconfig.write_text(
            """
[*.sh]
indent_size = invalid
"""
        )
        testfile = tmp_path / "test.sh"
        testfile.write_text("#!/bin/bash\n")

        config = load_config_from_editorconfig(str(testfile))
        # Should skip invalid indent_size
        assert "indent_size" not in config


class TestMergeConfigs:
    """Tests for merge_configs()"""

    def test_merges_with_correct_priority(self):
        editorconfig = {"indent_size": 2, "tab": True}
        pyproject = {"indent_size": 4}
        beautyshrc = {"indent_size": 3}
        explicit_config = {"indent_size": 6}
        cli = {"indent_size": 8}

        merged = merge_configs(editorconfig, pyproject, beautyshrc, explicit_config, cli)
        assert merged["indent_size"] == 8
        assert merged["tab"] is True  # From lowest priority

    def test_cli_overrides_all(self):
        editorconfig = {"indent_size": 2}
        pyproject = {"indent_size": 4}
        beautyshrc = {"indent_size": 3}
        explicit_config = {"indent_size": 6}
        cli = {"indent_size": 8, "backup": True}

        merged = merge_configs(editorconfig, pyproject, beautyshrc, explicit_config, cli)
        assert merged["indent_size"] == 8
        assert merged["backup"] is True

    def test_explicit_config_overrides_beautyshrc(self):
        editorconfig = {"indent_size": 2}
        pyproject = {"indent_size": 4}
        beautyshrc = {"indent_size": 3}
        explicit_config = {"indent_size": 6}

        merged = merge_configs(editorconfig, pyproject, beautyshrc, explicit_config, {})
        assert merged["indent_size"] == 6

    def test_beautyshrc_overrides_pyproject(self):
        editorconfig = {"indent_size": 2}
        pyproject = {"indent_size": 4}
        beautyshrc = {"indent_size": 3}
        explicit_config = {}

        merged = merge_configs(editorconfig, pyproject, beautyshrc, explicit_config, {})
        assert merged["indent_size"] == 3

    def test_pyproject_overrides_editorconfig(self):
        editorconfig = {"indent_size": 2, "tab": True}
        pyproject = {"indent_size": 4}
        beautyshrc = {}
        explicit_config = {}

        merged = merge_configs(editorconfig, pyproject, beautyshrc, explicit_config, {})
        assert merged["indent_size"] == 4
        assert merged["tab"] is True

    def test_filters_none_values_from_cli(self):
        editorconfig = {"indent_size": 2}
        pyproject = {"indent_size": 4}
        beautyshrc = {"indent_size": 3}
        explicit_config = {"indent_size": 6}
        cli = {"indent_size": None, "backup": True}

        merged = merge_configs(editorconfig, pyproject, beautyshrc, explicit_config, cli)
        # None should be filtered out, so explicit_config value (6) should win
        assert merged["indent_size"] == 6
        assert merged["backup"] is True

    def test_empty_configs(self):
        merged = merge_configs({}, {}, {}, {}, {})
        assert merged == {}
