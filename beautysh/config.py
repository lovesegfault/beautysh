"""Configuration management for beautysh."""

import logging
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Optional, TypedDict

if sys.version_info >= (3, 11):  # novermin
    import tomllib
else:  # pragma: no cover
    import tomli as tomllib  # type: ignore[import-not-found]

from editorconfig import EditorConfigError, get_properties

logger = logging.getLogger(__name__)


class ConfigError(Exception):
    """Raised when a configuration source is present but malformed."""


class BeautyshConfig(TypedDict, total=False):
    """Schema for [tool.beautysh] and editorconfig-derived settings.

    total=False: every key is optional.
    """

    indent_size: int
    tab: bool
    force_function_style: str
    variable_style: str
    backup: bool
    check: bool
    force: bool


_EXPECTED_TYPES: dict[str, type] = {
    "indent_size": int,
    "tab": bool,
    "force_function_style": str,
    "variable_style": str,
    "backup": bool,
    "check": bool,
    "force": bool,
}


def _validate_pyproject_config(raw: dict[str, Any]) -> BeautyshConfig:
    """Drop unknown keys and wrongly-typed values from a pyproject config.

    bool is rejected where int is expected (since bool is a subclass of int,
    a bare `indent_size = true` would otherwise silently mean indent=1).
    """
    validated: BeautyshConfig = {}
    for key, value in raw.items():
        expected = _EXPECTED_TYPES.get(key)
        if expected is None:
            logger.warning(f"Unknown [tool.beautysh] key {key!r}, ignoring")
            continue
        if expected is int and isinstance(value, bool):
            logger.warning(f"[tool.beautysh] {key} expects int, got bool; ignoring")
            continue
        if not isinstance(value, expected):
            logger.warning(
                f"[tool.beautysh] {key} expects {expected.__name__}, "
                f"got {type(value).__name__}; ignoring"
            )
            continue
        validated[key] = value  # type: ignore[literal-required]
    return validated


def load_config_from_pyproject() -> BeautyshConfig:
    """Load beautysh configuration from pyproject.toml if it exists.

    Looks for configuration in the [tool.beautysh] section of pyproject.toml
    in the current working directory. Unknown keys and wrongly-typed values
    are logged and dropped.

    Returns:
        Validated configuration. Empty if no file or no [tool.beautysh] section.

    Raises:
        ConfigError: if the file exists but can't be read or parsed.

    Example:
        # pyproject.toml
        [tool.beautysh]
        indent_size = 2
        tab = false
        force_function_style = "fnpar"
    """
    pyproject_path = Path.cwd() / "pyproject.toml"

    if not pyproject_path.exists():
        logger.debug("No pyproject.toml found in current directory")
        return {}

    try:
        with open(pyproject_path, "rb") as f:
            data = tomllib.load(f)
        raw: dict[str, Any] = data.get("tool", {}).get("beautysh", {})
        if raw:
            logger.debug(f"Loaded configuration from pyproject.toml: {raw}")
        return _validate_pyproject_config(raw)
    except OSError as e:
        raise ConfigError(f"Could not read pyproject.toml: {e}") from e
    except tomllib.TOMLDecodeError as e:
        raise ConfigError(f"Could not parse pyproject.toml: {e}") from e


def load_config_from_editorconfig(filepath: str) -> dict[str, Any]:
    """Load configuration from .editorconfig for the given file.

    Maps EditorConfig properties to beautysh configuration:
    - indent_style (tab/space) → tab (bool)
    - indent_size (integer) → indent_size (int)

    Args:
        filepath: Path to the file being formatted (used to find relevant .editorconfig)

    Returns:
        Dictionary with beautysh-compatible configuration keys.

    Example:
        # .editorconfig
        [*.sh]
        indent_style = space
        indent_size = 2
    """
    try:
        props = get_properties(str(filepath))
        config: dict[str, Any] = {}

        # Map EditorConfig indent_style to beautysh tab setting
        if "indent_style" in props:
            if props["indent_style"] == "tab":
                config["tab"] = True
                logger.debug(f"EditorConfig: using tab indentation for {filepath}")
            elif props["indent_style"] == "space":
                config["tab"] = False
                logger.debug(f"EditorConfig: using space indentation for {filepath}")

        # Map EditorConfig indent_size to beautysh indent_size.
        # The spec allows `indent_size = tab` (meaning "use tab_width"); skip it
        # rather than emitting a spurious warning.
        if "indent_size" in props and props["indent_size"] != "tab":
            try:
                indent_size = int(props["indent_size"])
                config["indent_size"] = indent_size
                logger.debug(f"EditorConfig: indent_size={indent_size} for {filepath}")
            except (ValueError, TypeError) as e:
                logger.warning(f"Invalid indent_size in EditorConfig: {e}")

        return config
    except EditorConfigError as e:
        logger.warning(f"EditorConfig parsing failed for {filepath}: {e}")
        return {}


def merge_configs(
    editorconfig: Mapping[str, Any],
    pyproject: Mapping[str, Any],
    cli_args: Optional[Mapping[str, Any]] = None,
) -> dict[str, Any]:
    """Merge configuration from multiple sources with proper priority.

    Priority order (highest to lowest):
    1. CLI arguments
    2. pyproject.toml [tool.beautysh]
    3. EditorConfig

    Args:
        editorconfig: Configuration from .editorconfig
        pyproject: Configuration from pyproject.toml
        cli_args: Configuration from CLI arguments (optional)

    Returns:
        Merged configuration dictionary

    Example:
        >>> editorconfig = {"indent_size": 2}
        >>> pyproject = {"indent_size": 4, "tab": False}
        >>> cli = {"indent_size": 8}
        >>> merge_configs(editorconfig, pyproject, cli)
        {'indent_size': 8, 'tab': False}
    """
    merged: dict[str, Any] = {}
    merged.update(editorconfig)
    merged.update(pyproject)
    if cli_args:
        # Filter out None values from CLI args
        merged.update({k: v for k, v in cli_args.items() if v is not None})

    logger.debug(f"Merged configuration: {merged}")
    return merged
