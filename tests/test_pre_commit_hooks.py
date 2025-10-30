"""Tests for pre-commit hook configuration."""

from pathlib import Path

import yaml  # type: ignore[import-untyped]


def test_pre_commit_hooks_yaml_exists():
    """Ensure .pre-commit-hooks.yaml exists for pre-commit integration.

    This file is required for users to use beautysh as a pre-commit hook
    in their own projects. It was accidentally deleted in v6.3.0 (issue #259).
    """
    hooks_file = Path(__file__).parent.parent / ".pre-commit-hooks.yaml"
    assert hooks_file.exists(), (
        ".pre-commit-hooks.yaml is missing! "
        "This file is required for pre-commit integration. "
        "See issue #259"
    )


def test_pre_commit_hooks_yaml_valid():
    """Verify .pre-commit-hooks.yaml is valid YAML with required fields."""
    hooks_file = Path(__file__).parent.parent / ".pre-commit-hooks.yaml"

    with open(hooks_file) as f:
        hooks = yaml.safe_load(f)

    # Should be a list of hooks
    assert isinstance(hooks, list), ".pre-commit-hooks.yaml must be a list"
    assert len(hooks) > 0, ".pre-commit-hooks.yaml must have at least one hook"

    # Check beautysh hook
    beautysh_hook = hooks[0]
    assert beautysh_hook["id"] == "beautysh", "First hook should be 'beautysh'"
    assert "name" in beautysh_hook, "Hook must have 'name' field"
    assert "entry" in beautysh_hook, "Hook must have 'entry' field"
    assert beautysh_hook["entry"] == "beautysh", "Entry should be 'beautysh'"
    assert beautysh_hook["language"] == "python", "Language should be 'python'"
    assert "types" in beautysh_hook, "Hook must have 'types' field"
    assert "shell" in beautysh_hook["types"], "Should run on shell files"
