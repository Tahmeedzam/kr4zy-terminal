"""
utils.py
--------
Small, shared helper functions used across the app.

Design decision:
    Anything that would otherwise get copy-pasted into multiple files
    (path resolution, timestamp formatting, safe string handling) lives
    here instead. In particular, path resolution is the trickiest part
    of this app to get right because it must work in TWO very different
    run modes:

    1. Running from source:      python main.py
    2. Running as a PyInstaller executable: Kr4zyTerminal.exe

    In mode 2, `__file__`-relative paths break because PyInstaller
    unpacks bundled data into a temporary folder referenced by
    `sys._MEIPASS`. `resource_path()` below is the standard, documented
    workaround and MUST be used by any module that needs to find a
    bundled asset (icons, default config, etc.) at runtime.

    App-writable files (logs, history.json, user-edited config.json)
    should NOT use resource_path() — those should live next to the
    executable / source, not inside the read-only PyInstaller bundle.
    Use `app_root()` for those instead.
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path


def app_root() -> Path:
    """
    Return the directory where user-writable app files should live
    (config.json, history.json, logs/).

    When frozen by PyInstaller, this is the directory containing the
    .exe (not the temp extraction folder), so settings and logs persist
    across runs instead of vanishing when the temp folder is cleaned up.
    """
    if getattr(sys, "frozen", False):
        # Running as a PyInstaller-built executable.
        return Path(sys.executable).resolve().parent
    # Running from source.
    return Path(__file__).resolve().parent


def resource_path(relative_path: str) -> Path:
    """
    Resolve the absolute path to a bundled, READ-ONLY resource
    (e.g. an icon under assets/), working both from source and when
    frozen into a single-file PyInstaller executable.

    Args:
        relative_path: Path relative to the project root, e.g.
            "assets/icon.ico".

    Returns:
        Absolute Path to the resource.
    """
    base = getattr(sys, "_MEIPASS", None)
    if base:
        # PyInstaller one-file mode extracts bundled data here at runtime.
        return Path(base) / relative_path
    return Path(__file__).resolve().parent / relative_path


def timestamp(fmt: str = "%H:%M:%S") -> str:
    """
    Return the current time formatted as a short string, used to prefix
    terminal output lines (e.g. "[10:15:02] Command executed").

    Args:
        fmt: strftime-compatible format string.
    """
    return datetime.now().strftime(fmt)


def safe_str(value: object, max_length: int = 500) -> str:
    """
    Convert any value to a display-safe, length-capped string.

    Used when printing command output or error messages to the terminal
    so a huge stack trace or subprocess output can never freeze the UI
    by dumping thousands of characters into the Textbox at once.

    Args:
        value: Any value (exception, string, object) to stringify.
        max_length: Maximum characters before truncation.
    """
    text = str(value)
    if len(text) > max_length:
        return text[:max_length].rstrip() + " … [truncated]"
    return text


def ensure_directory(path: Path) -> Path:
    """
    Ensure a directory exists, creating parents as needed, and return it.

    Centralizing this (instead of scattering `.mkdir(parents=True,
    exist_ok=True)` everywhere) keeps intent explicit at each call site.
    """
    path.mkdir(parents=True, exist_ok=True)
    return path