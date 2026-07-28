"""commands/clear.py - clears the terminal output pane."""

from command_registry import Command, register_command, CommandContext


@register_command
class ClearCommand(Command):
    name = "clear"
    description = "Clear the terminal output"
    aliases = ["cls"]

    def execute(self, args: list[str], context: CommandContext) -> None:
        context.terminal.clear_output()