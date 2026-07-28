"""
command_manager.py
-------------------
Parses raw terminal input and dispatches to the CommandRegistry.
Auto-discovers command files from commands/ so new commands never
require editing this file.
"""

from __future__ import annotations

import importlib
import pkgutil
from pathlib import Path

from command_registry import CommandRegistry, CommandContext, drain_pending_commands
from launcher import Launcher
from config import get_config
from logger import get_logger

logger = get_logger(__name__)


class CommandManager:
    """Owns the CommandRegistry + Launcher, parses input, executes commands."""

    def __init__(self, terminal) -> None:
        """
        Args:
            terminal: The TerminalApp instance, passed into CommandContext
                so commands can print output.
        """
        self.terminal = terminal
        self.config = get_config()
        self.launcher = Launcher()
        self.registry = CommandRegistry()
        self._discover_commands()

    def _discover_commands(self) -> None:
        """Import every module under commands/, then register whatever
        queued itself via @register_command."""
        import commands as commands_pkg

        for _, module_name, _ in pkgutil.iter_modules(commands_pkg.__path__):
            full_name = f"commands.{module_name}"
            try:
                importlib.import_module(full_name)
            except Exception as exc:
                logger.error(f"Failed to load command module '{full_name}': {exc}")

        for command in drain_pending_commands():
            try:
                self.registry.register(command)
            except ValueError as exc:
                logger.error(str(exc))

    def execute(self, raw_input: str) -> bool:
        """
        Parse and run a raw command line.

        Args:
            raw_input: Exact text the user typed.

        Returns:
            True if a matching command was found and executed,
            False if the command name was unrecognized.
        """
        raw_input = raw_input.strip()
        if not raw_input:
            return False

        parts = raw_input.split()
        name, args = parts[0], parts[1:]

        command = self.registry.get(name)
        if command is None:
            return False

        context = CommandContext(
            terminal=self.terminal,
            launcher=self.launcher,
            config=self.config,
        )

        try:
            command.execute(args, context)
        except Exception as exc:
            logger.error(f"Command '{name}' raised an exception: {exc}")
            if hasattr(self.terminal, "print_error"):
                self.terminal.print_error(f"Command '{name}' failed: {exc}")
        return True