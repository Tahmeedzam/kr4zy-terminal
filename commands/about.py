"""commands/about.py - short about/credits blurb."""

from command_registry import Command, register_command, CommandContext


@register_command
class AboutCommand(Command):
    name = "about"
    description = "About Kr4zy Terminal"
    aliases = []

    def execute(self, args: list[str], context: CommandContext) -> None:
        name = context.config.get("app.name", default="Kr4zy Terminal")
        version = context.config.get("app.version", default="0.1.0")
        context.terminal.print_output(f"{name} v{version}")
        context.terminal.print_output("A personal command terminal for launching apps, workspaces, and commands.")
        context.terminal.print_output("Type 'help' to see everything it can do.")