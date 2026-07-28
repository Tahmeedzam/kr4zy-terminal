"""
commands/workspace.py
----------------------
Launches every app/website defined for a named workspace in config.json.

Usage: `workspace production`, `workspace flutter`, `workspace` (lists
available workspaces if no name given).

This command never hardcodes a workspace name or app path - it just
reads whatever is under config.json -> workspaces.<name>. Adding a new
workspace (e.g. "production") means editing config.json only, never
this file.
"""

from command_registry import Command, register_command, CommandContext


@register_command
class WorkspaceCommand(Command):
    name = "workspace"
    description = "Launch a workspace's apps and websites (see config.json)"
    aliases = ["ws"]

    def execute(self, args: list[str], context: CommandContext) -> None:
        workspaces = context.config.get("workspaces", default={})

        if not args:
            context.terminal.print_output("Available workspaces:")
            for ws_name, ws_data in workspaces.items():
                description = ws_data.get("description", "") if isinstance(ws_data, dict) else ""
                context.terminal.print_output(f"  {ws_name:<12} - {description}")
            context.terminal.print_output("Usage: workspace <name>")
            return

        ws_name = args[0].lower()
        workspace = workspaces.get(ws_name)

        if workspace is None:
            context.terminal.print_error(
                f"Unknown workspace: '{ws_name}'. Type 'workspace' with no args to see options."
            )
            return

        context.terminal.print_loading(f"Launching workspace: {ws_name}")

        for app in workspace.get("apps", []):
            self._launch_app(app, context)

        for url in workspace.get("websites", []):
            context.launcher.open_website(
                url,
                on_result=lambda success, message: context.terminal.print_success(message)
                if success
                else context.terminal.print_error(message),
            )

    def _launch_app(self, app: dict, context: CommandContext) -> None:
        """Dispatch a single app entry to the right Launcher method based on its 'type'."""
        app_type = app.get("type")

        def report(success: bool, message: str) -> None:
            if success:
                context.terminal.print_success(message)
            else:
                context.terminal.print_error(message)

        if app_type == "exe":
            context.launcher.open_app(app.get("path", ""), app.get("args", []), on_result=report)
        elif app_type == "folder":
            context.launcher.open_folder(app.get("path", ""), on_result=report)
        elif app_type == "cmd":
            context.launcher.run_command(app.get("command", ""), shell="cmd", on_result=report)
        elif app_type == "powershell":
            context.launcher.run_command(app.get("command", ""), shell="powershell", on_result=report)
        else:
            context.terminal.print_error(f"Unknown app type in config: '{app_type}'")