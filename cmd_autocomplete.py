"""
autocomplete.py
----------------
Fuzzy, case-insensitive matching of a partial command name against all
registered command names/aliases.

Design decision:
    This logic is deliberately separated from terminal.py (the Tab key
    handler just calls into this). That means the matching algorithm
    can be fully unit-tested without a display/Tkinter, and the popup
    UI can change later without touching the matching logic.

Matching strategy (in priority order, most useful first):
    1. Exact "starts with" matches (typing "he" -> "help") - this is
       what most terminals do and what people expect from Tab.
    2. Substring matches anywhere in the name (typing "isto" -> "history")
       - only used if no prefix match exists.
    3. Fuzzy/typo-tolerant matches via difflib - only used as a last
       resort, so "wrkspace" can still suggest "workspace".
"""

from __future__ import annotations

import difflib
from typing import Callable


class Autocompleter:
    """
    Suggests and cycles through command name completions for a given
    partial input, given a callable that returns the current list of
    registered command names (kept as a callable, not a snapshot list,
    so newly-registered commands are always reflected without needing
    to recreate the Autocompleter).
    """

    def __init__(self, get_names: Callable[[], list[str]]) -> None:
        """
        Args:
            get_names: Zero-arg callable returning all currently
                registered command names/aliases, e.g.
                `registry.names`.
        """
        self._get_names = get_names
        self._last_prefix: str | None = None
        self._matches: list[str] = []
        self._cycle_index: int = 0

    def suggest(self, prefix: str) -> list[str]:
        """
        Return all matches for `prefix`, ranked by the strategy above.

        Args:
            prefix: The partial command text typed so far (case-insensitive).

        Returns:
            A deduplicated, sorted list of matching command names.
            Empty list if nothing matches at all.
        """
        prefix = prefix.lower().strip()
        if not prefix:
            return []

        names = sorted(set(self._get_names()))

        starts_with = [n for n in names if n.startswith(prefix)]
        if starts_with:
            return starts_with

        contains = [n for n in names if prefix in n]
        if contains:
            return contains

        fuzzy = difflib.get_close_matches(prefix, names, n=5, cutoff=0.6)
        return fuzzy

    def next_completion(self, prefix: str) -> str | None:
        """
        Stateful helper for repeated Tab presses: cycles through the
        match list for the given prefix each time it's called with the
        same prefix, and resets the cycle when the prefix changes.

        Args:
            prefix: Current partial input text.

        Returns:
            The next completion to insert, or None if there are no
            matches at all.
        """
        if prefix != self._last_prefix:
            self._last_prefix = prefix
            self._matches = self.suggest(prefix)
            self._cycle_index = 0

        if not self._matches:
            return None

        completion = self._matches[self._cycle_index % len(self._matches)]
        self._cycle_index += 1
        return completion

    def reset(self) -> None:
        """Clear cycling state, e.g. called whenever the user types anything
        other than pressing Tab, so the next Tab press starts fresh."""
        self._last_prefix = None
        self._matches = []
        self._cycle_index = 0