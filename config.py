"""
config.py
---------
Centralized configuration management for Kr4zy Terminal.

Design decision:
    Every other module (launcher, commands, terminal UI, themes) needs
    read access to configuration values, but NOTHING outside this file
    should know or care where those values physically live (a JSON file
    on disk). That means:

    - No module should ever call `open("config.json")` directly.
    - No module should hardcode a default value if it isn't found here.
    - Reloading config (the `reload` command) should not require
      restarting the app or re-importing modules.

This module exposes a single `Config` class, instantiated once and
shared as a singleton (`get_config()`), so every part of the app reads
from the same in-memory state without repeatedly hitting disk.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional


# The directory this file lives in. Using __file__ instead of a hardcoded
# absolute path means the app works correctly whether run from source
# or packaged with PyInstaller (relative to the executable's temp dir).
BASE_DIR = Path(__file__).resolve().parent
DEFAULT_CONFIG_PATH = BASE_DIR / "config.json"


class ConfigError(Exception):
    """Raised when the configuration file is missing or malformed."""


class Config:
    """
    Loads and provides typed, dot-path access to config.json.

    Example:
        config = Config()
        accent = config.get("theme.accent_color", default="#3B8ED0")
        workspaces = config.get("workspaces", default={})
    """

    def __init__(self, config_path: Optional[Path] = None) -> None:
        """
        Initialize the config object and load data from disk immediately.

        Args:
            config_path: Optional override path, useful for testing.
        """
        self.config_path: Path = config_path or DEFAULT_CONFIG_PATH
        self._data: dict[str, Any] = {}
        self.load()

    def load(self) -> None:
        """
        Load (or reload) configuration from disk into memory.

        Raises:
            ConfigError: if the file is missing or contains invalid JSON.
                We raise instead of silently continuing because a broken
                config could otherwise cause confusing downstream errors
                (e.g. a workspace silently doing nothing).
        """
        if not self.config_path.exists():
            raise ConfigError(
                f"Config file not found at: {self.config_path}. "
                "Kr4zy Terminal cannot start without it."
            )

        try:
            with self.config_path.open("r", encoding="utf-8") as f:
                self._data = json.load(f)
        except json.JSONDecodeError as exc:
            raise ConfigError(
                f"Config file at {self.config_path} contains invalid JSON: {exc}"
            ) from exc

    def reload(self) -> None:
        """Re-read config.json from disk. Used by the `reload` command."""
        self.load()

    def get(self, dot_path: str, default: Any = None) -> Any:
        """
        Retrieve a value using dot-separated path notation.

        Example:
            config.get("theme.accent_color")
            config.get("workspaces.flutter.apps")

        Args:
            dot_path: Dot-separated key path into the config dict.
            default: Value returned if the path does not exist.

        Returns:
            The resolved value, or `default` if any part of the path
            is missing.
        """
        node: Any = self._data
        for part in dot_path.split("."):
            if isinstance(node, dict) and part in node:
                node = node[part]
            else:
                return default
        return node

    def set(self, dot_path: str, value: Any, persist: bool = False) -> None:
        """
        Set a value in memory, optionally persisting it back to disk.

        Args:
            dot_path: Dot-separated key path to set.
            value: New value to assign.
            persist: If True, immediately write the full config back to
                config.json. Kept optional so callers can batch several
                in-memory changes before a single disk write.
        """
        parts = dot_path.split(".")
        node = self._data
        for part in parts[:-1]:
            node = node.setdefault(part, {})
        node[parts[-1]] = value

        if persist:
            self.save()

    def save(self) -> None:
        """Persist the current in-memory config back to config.json."""
        with self.config_path.open("w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2)

    @property
    def raw(self) -> dict[str, Any]:
        """Return the full underlying config dict (read-only convention)."""
        return self._data


# --- Singleton accessor -----------------------------------------------------
# Rather than importing a bare module-level instance (which makes testing
# and reloading awkward), we expose a getter that lazily creates one shared
# instance. This keeps a single source of truth without import-order bugs.
_config_instance: Optional[Config] = None


def get_config() -> Config:
    """Return the shared Config singleton, creating it on first use."""
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance