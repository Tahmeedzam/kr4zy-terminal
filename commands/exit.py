"""commands/exit.py - closes Kr4zy Terminal."""

from command_registry import Command, register_command, CommandContext


@register_command
class ExitCommand(Command):
    name = "exit"
    description = "Close Kr4zy Terminal"
    aliases = ["quit", "q"]

    def execute(self, args: list[str], context: CommandContext) -> None:
        context.terminal.print_output("Goodbye!")
        if getattr(context.terminal, "tray", None) is not None:
            context.terminal.tray.stop()
        context.terminal.after(300, context.terminal.destroy)