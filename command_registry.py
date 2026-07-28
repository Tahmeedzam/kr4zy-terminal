"""
command_registry.py
--------------------
Defines the `Command` base class and the registry that maps command
names (and aliases) to Command instances.

Design decision (the core architectural requirement of this project):
    We must NEVER grow a giant if/elif chain like:

        if cmd == "help": ...
        elif cmd == "clear": ...
        elif cmd == "flutter": ...

    Instead, every command is its own class in its own file under
    commands/, decorated with `@register_command`. Importing that file
    (which `command_manager.py` will do automatically by scanning the
    commands/ folder) is enough to make the command available — no
    other file ever needs to change.

    Architecture flow (per spec):
        User types command
            -> Terminal (UI)
            -> CommandManager (parses input, finds command)
            -> CommandRegistry (name -> Command instance lookup)
            -> Command.execute() (this specific command's logic)
            -> Launcher (if it needs to open/run something)
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from logger import get_logger

logger = get_logger(__name__)


class Command(ABC):
    """
    Base class every command must inherit from.

    Subclasses must define:
        name        - the primary string the user types to invoke it.
        description - a short help string shown by the `help` command.
        aliases     - optional list of alternate names (e.g. ["ls"] for
                      a "list" command).

    And implement:
        execute(args, context) - the command's actual behavior.
    """

    name: str = ""
    description: str = ""
    aliases: list[str] = []

    @abstractmethod
    def execute(self, args: list[str], context: "CommandContext") -> None:
        """
        Run the command.

        Args:
            args: The tokens typed after the command name, e.g. typing
                "workspace flutter" gives args=["flutter"].
            context: A CommandContext bundling everything a command
                might need (terminal output, launcher, config), so
                Command subclasses don't need half a dozen constructor
                parameters.
        """
        raise NotImplementedError


class CommandContext:
    """
    Bundle of shared services passed into every Command.execute() call.

    Keeping this as one object (instead of passing terminal, launcher,
    config, etc. as separate params to every command) means adding a
    new shared service later doesn't require touching every command
    file's method signature.
    """

    def __init__(self, terminal, launcher, config) -> None:
        """
        Args:
            terminal: The TerminalApp (or compatible) instance, used by
                commands to print output via terminal.print_*() methods.
            launcher: The shared Launcher instance for opening things.
            config: The shared Config instance for reading settings.
        """
        self.terminal = terminal
        self.launcher = launcher
        self.config = config


class CommandRegistry:
    """
    Holds the mapping of command name/alias -> Command instance.

    This is a singleton in practice (one instance created in
    command_manager.py), but the class itself has no global state,
    which keeps it easy to test in isolation.
    """

    def __init__(self) -> None:
        self._commands: dict[str, Command] = {}

    def register(self, command: Command) -> None:
        """
        Register a command instance under its name and all aliases.

        Args:
            command: An instantiated Command subclass.

        Raises:
            ValueError: if the command's name or an alias is already
                registered, since silently overwriting a command would
                be a confusing, hard-to-debug failure mode.
        """
        keys = [command.name, *command.aliases]
        for key in keys:
            normalized = key.lower().strip()
            if normalized in self._commands:
                raise ValueError(
                    f"Command name/alias '{normalized}' is already registered "
                    f"(conflict while registering '{command.name}')."
                )
            self._commands[normalized] = command

        logger.info(f"Registered command: {command.name} (aliases: {command.aliases})")

    def get(self, name: str) -> Optional[Command]:
        """Look up a command by name or alias, case-insensitively."""
        return self._commands.get(name.lower().strip())

    def all_commands(self) -> list[Command]:
        """
        Return every uniquely-registered Command instance (deduplicated,
        since a command with aliases appears multiple times in the
        internal dict but should only be listed once by `help`).
        """
        seen: set[int] = set()
        unique: list[Command] = []
        for command in self._commands.values():
            if id(command) not in seen:
                seen.add(id(command))
                unique.append(command)
        return unique

    def names(self) -> list[str]:
        """Return every registered name/alias, used by autocomplete."""
        return list(self._commands.keys())


# --- Registration decorator -------------------------------------------------
# A module-level registry that command files register themselves into
# simply by being imported. command_manager.py owns creating the "real"
# registry used at runtime and importing every file in commands/; this
# global exists so the @register_command decorator has somewhere to put
# instances at import time, decoupled from any particular app instance.
_pending_commands: list[Command] = []


def register_command(cls: type[Command]) -> type[Command]:
    """
    Class decorator: instantiate a Command subclass and queue it for
    registration.

    Usage (in commands/help.py):
        @register_command
        class HelpCommand(Command):
            name = "help"
            ...

    Returns:
        The class unchanged, so it can still be imported/tested directly.
    """
    instance = cls()
    _pending_commands.append(instance)
    return cls


def drain_pending_commands() -> list[Command]:
    """
    Return and clear all commands queued by @register_command so far.

    command_manager.py calls this once, after importing every file in
    commands/, to populate the real CommandRegistry.
    """
    global _pending_commands
    pending = _pending_commands
    _pending_commands = []
    return pending