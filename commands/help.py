"""commands/help.py - lists all available commands and descriptions."""

from command_registry import Command, register_command, CommandContext


@register_command
class HelpCommand(Command):
    name = "help"
    description = "List all available commands"
    aliases = ["?"]

    def execute(self, args: list[str], context: CommandContext) -> None:
        context.terminal.print_output("Available commands:")
        for command in sorted(context.terminal.command_manager.registry.all_commands(), key=lambda c: c.name):
            alias_text = f" (aliases: {', '.join(command.aliases)})" if command.aliases else ""
            context.terminal.print_output(f"  {command.name:<12} - {command.description}{alias_text}")