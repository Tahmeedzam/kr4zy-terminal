"""
commands/settings.py
---------------------
View and edit config.json values without leaving the terminal.

Usage:
    settings                          - show common settings
    settings get theme.accent_color   - read one value
    settings set theme.accent_color "#FF0000"   - set + persist a value
"""

from command_registry import Command, register_command, CommandContext


@register_command
class SettingsCommand(Command):
    name = "settings"
    description = "View or edit settings (get/set dot-path values)"
    aliases = []

    def execute(self, args: list[str], context: CommandContext) -> None:
        if not args:
            self._show_overview(context)
            return

        action = args[0].lower()

        if action == "get" and len(args) >= 2:
            value = context.config.get(args[1], default="(not set)")
            context.terminal.print_output(f"{args[1]} = {value}")
            return

        if action == "set" and len(args) >= 3:
            key = args[1]
            value = " ".join(args[2:])
            context.config.set(key, value, persist=True)
            context.terminal.print_success(f"Set {key} = {value}")
            return

        context.terminal.print_error("Usage: settings | settings get <key> | settings set <key> <value>")

    def _show_overview(self, context: CommandContext) -> None:
        context.terminal.print_output(f"App name:      {context.config.get('app.name')}")
        context.terminal.print_output(f"Version:       {context.config.get('app.version')}")
        context.terminal.print_output(f"Theme mode:    {context.config.get('theme.mode')}")
        context.terminal.print_output(f"Accent color:  {context.config.get('theme.accent_color')}")
        context.terminal.print_output(f"Window size:   {context.config.get('app.window_width')}x{context.config.get('app.window_height')}")
        context.terminal.print_output("Use 'settings get <key>' / 'settings set <key> <value>' to edit.")