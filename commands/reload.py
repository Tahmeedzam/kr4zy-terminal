"""commands/reload.py - reloads config.json from disk without restarting."""

from command_registry import Command, register_command, CommandContext


@register_command
class ReloadCommand(Command):
    name = "reload"
    description = "Reload config.json without restarting the app"
    aliases = []

    def execute(self, args: list[str], context: CommandContext) -> None:
        try:
            context.config.reload()
            context.terminal.print_success("Config reloaded from config.json")
        except Exception as exc:
            context.terminal.print_error(f"Failed to reload config: {exc}")