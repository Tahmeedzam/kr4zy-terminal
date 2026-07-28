"""commands/version.py - prints the current app version."""

from command_registry import Command, register_command, CommandContext


@register_command
class VersionCommand(Command):
    name = "version"
    description = "Show the current app version"
    aliases = ["ver"]

    def execute(self, args: list[str], context: CommandContext) -> None:
        name = context.config.get("app.name", default="Kr4zy Terminal")
        version = context.config.get("app.version", default="0.1.0")
        context.terminal.print_output(f"{name} v{version}")