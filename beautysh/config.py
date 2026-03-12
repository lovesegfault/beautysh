"""Configuration management for beautysh."""

import logging
from pathlib import Path
from typing import Any, Optional

try:
    import tomllib  # novermin
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib  # type: ignore[import-not-found,no-redef]

from editorconfig import EditorConfigError, get_properties

logger = logging.getLogger(__name__)


class ConfigError(Exception):
    """Raised when a configuration source is present but malformed."""


def load_config_from_pyproject() -> dict[str, Any]:
    """Load beautysh configuration from pyproject.toml if it exists.

    Looks for configuration in the [tool.beautysh] section of pyproject.toml
    in the current working directory.

    Returns:
        Dictionary with configuration values, or empty dict if file not found.

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
        config: dict[str, Any] = data.get("tool", {}).get("beautysh", {})
        if config:
            logger.debug(f"Loaded configuration from pyproject.toml: {config}")
        return config
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
    editorconfig: dict[str, Any],
    pyproject: dict[str, Any],
    cli_args: Optional[dict[str, Any]] = None,
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
    merged = {}
    merged.update(editorconfig)
    merged.update(pyproject)
    if cli_args:
        # Filter out None values from CLI args
        merged.update({k: v for k, v in cli_args.items() if v is not None})

    logger.debug(f"Merged configuration: {merged}")
    return merged
