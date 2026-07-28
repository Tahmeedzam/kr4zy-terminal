"""
history.py
----------
Command history: persistent storage + in-memory up/down navigation.

Design decision:
    The terminal UI (terminal.py) needs two related but distinct
    behaviors that are easy to tangle together if not separated:

    1. PERSISTENCE — remembering commands across app restarts, saved to
       a JSON file (history.json) next to the executable.
    2. NAVIGATION — a "cursor" that moves up/down through history while
       the user presses the Up/Down arrow keys, without permanently
       mutating the stored list until a new command is actually run.

    Keeping this in its own class (`CommandHistory`) means terminal.py
    only has to call `.add()`, `.previous()`, `.next()` — it never
    touches the file system or list-indexing logic directly.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from config import get_config
from logger import get_logger
from utils import app_root

logger = get_logger(__name__)


class CommandHistory:
    """
    Manages persistent command history and up/down navigation state.

    Example:
        history = CommandHistory()
        history.add("flutter")
        history.add("clear")

        history.previous()  # -> "clear"
        history.previous()  # -> "flutter"
        history.next()      # -> "clear"
    """

    def __init__(self) -> None:
        """Load existing history from disk (if any) and reset the cursor."""
        config = get_config()
        history_filename = config.get("history.file", default="history.json")
        self.max_entries: int = config.get("history.max_entries", default=200)

        self._file_path: Path = app_root() / history_filename
        self._entries: list[str] = []
        self._cursor: Optional[int] = None  # None = not currently navigating

        self._load()

    def _load(self) -> None:
        """Load history entries from disk, tolerating a missing/corrupt file."""
        if not self._file_path.exists():
            self._entries = []
            return

        try:
            with self._file_path.open("r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                self._entries = [str(item) for item in data]
            else:
                logger.warning("history.json did not contain a list; resetting.")
                self._entries = []
        except (json.JSONDecodeError, OSError) as exc:
            logger.error(f"Failed to load history.json: {exc}")
            self._entries = []

    def _save(self) -> None:
        """Persist current history entries to disk."""
        try:
            with self._file_path.open("w", encoding="utf-8") as f:
                json.dump(self._entries, f, indent=2)
        except OSError as exc:
            logger.error(f"Failed to save history.json: {exc}")

    def add(self, command: str) -> None:
        """
        Record a newly executed command, trimming to max_entries and
        resetting navigation state (a fresh command always ends browsing
        history, matching the behavior of real shells).

        Args:
            command: The raw command text the user submitted.
        """
        command = command.strip()
        if not command:
            return

        # Avoid storing immediate duplicates back-to-back (e.g. hitting
        # Enter on "clear" twice in a row shouldn't bloat history).
        if self._entries and self._entries[-1] == command:
            self._cursor = None
            return

        self._entries.append(command)
        if len(self._entries) > self.max_entries:
            self._entries = self._entries[-self.max_entries :]

        self._cursor = None
        self._save()

    def previous(self) -> Optional[str]:
        """
        Move the navigation cursor one step further into the past and
        return that entry, or None if history is empty / at the oldest
        entry already.
        """
        if not self._entries:
            return None

        if self._cursor is None:
            self._cursor = len(self._entries) - 1
        elif self._cursor > 0:
            self._cursor -= 1

        return self._entries[self._cursor]

    def next(self) -> Optional[str]:
        """
        Move the navigation cursor one step toward the present.

        Returns:
            The next (more recent) entry, an empty string if the user
            has navigated past the newest entry (matching typical shell
            behavior of clearing the input), or None if not currently
            navigating history at all.
        """
        if self._cursor is None:
            return None

        if self._cursor < len(self._entries) - 1:
            self._cursor += 1
            return self._entries[self._cursor]

        # Past the newest entry: stop navigating, clear the input line.
        self._cursor = None
        return ""

    def reset_cursor(self) -> None:
        """Reset navigation state, e.g. after the input field loses focus."""
        self._cursor = None

    def all(self) -> list[str]:
        """Return a copy of all stored history entries, oldest first."""
        return list(self._entries)