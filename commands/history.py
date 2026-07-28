"""commands/history.py - lists previously executed commands."""

from command_registry import Command, register_command, CommandContext


@register_command
class HistoryCommand(Command):
    name = "history"
    description = "Show previously executed commands"
    aliases = ["hist"]

    def execute(self, args: list[str], context: CommandContext) -> None:
        entries = context.terminal.history.all()
        if not entries:
            context.terminal.print_output("No command history yet.")
            return

        for index, entry in enumerate(entries, start=1):
            context.terminal.print_output(f"  {index:>3}  {entry}")