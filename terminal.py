"""
terminal.py
-----------
The main CustomTkinter UI: title, scrollable output, ">" prompt, input
field, and status bar. Wires user input to CommandManager and command
history to Up/Down arrow keys.
"""

from __future__ import annotations

import customtkinter as ctk

from command_manager import CommandManager
from history import CommandHistory
from cmd_autocomplete import Autocompleter
from windows_integration import TrayIntegration
from sidepanel import SidePanel
from config import get_config
from logger import get_logger
from utils import timestamp, app_root

logger = get_logger(__name__)


class TerminalApp(ctk.CTk):
    """Main application window for Kr4zy Terminal."""

    def __init__(self) -> None:
        super().__init__()

        self.config = get_config()
        self.history = CommandHistory()
        # command_manager needs `self` (the terminal) to print output,
        # so it's created after basic attributes exist but before the
        # widgets that might immediately want to print (e.g. a startup
        # banner further down).
        self.command_manager = CommandManager(self)
        self.autocompleter = Autocompleter(self.command_manager.registry.names)

        self._configure_window()
        self._build_widgets()
        self._bind_keys()
        self._print_welcome_banner()
        self.side_panel.start()

        if self.config.get("app.minimize_to_tray", default=False):
            self.tray = TrayIntegration(self)
            self.tray.start()
        else:
            self.tray = None

    # --- Setup ---------------------------------------------------------

    def _configure_window(self) -> None:
        """Apply theme + window size from config.json."""
        ctk.set_appearance_mode(self.config.get("theme.mode", default="dark"))
        ctk.set_default_color_theme("blue")

        width = self.config.get("app.window_width", default=900)
        height = self.config.get("app.window_height", default=600)
        title = self.config.get("app.name", default="Kr4zy Terminal")

        self.title(title)
        self.geometry(f"{width}x{height}")
        self.configure(fg_color=self.config.get("theme.background_color", default="#1E1E1E"))
        self._apply_window_icon()

    def _apply_window_icon(self) -> None:
        """
        Set the window/taskbar icon to the generated K logo, generating
        assets/icon.ico on first run if it doesn't exist yet.

        Wrapped in try/except because iconbitmap's .ico support is
        Windows-specific; on other platforms it can raise, and a
        missing icon should never prevent the app from starting.
        """
        icon_path = app_root() / "assets" / "icon.ico"
        try:
            self.iconbitmap(str(icon_path))
        except Exception as exc:
            logger.warning(f"Could not set window icon: {exc}")

    def _build_widgets(self) -> None:
        """Build the side panel + title bar, output pane, prompt row, and status bar."""
        font_family = self.config.get("theme.font_family", default="Consolas")
        font_size = self.config.get("theme.font_size", default=14)
        mono_font = ctk.CTkFont(family=font_family, size=font_size)

        # Outer horizontal split: side panel (fixed width, left) + main
        # content column (expands, right). Everything below that used
        # to be packed into `self` directly is now packed into
        # `main_frame` instead, so the spinner has room alongside it.
        outer = ctk.CTkFrame(self, fg_color="transparent")
        outer.pack(fill="both", expand=True)

        self.side_panel = SidePanel(outer, width=140)
        self.side_panel.pack(side="left", fill="y", padx=(8, 0), pady=8)

        main_frame = ctk.CTkFrame(outer, fg_color="transparent")
        main_frame.pack(side="left", fill="both", expand=True)

        # Title label
        self.title_label = ctk.CTkLabel(
            main_frame,
            text=self.config.get("app.name", default="Kr4zy Terminal"),
            font=ctk.CTkFont(family=font_family, size=font_size + 4, weight="bold"),
        )
        self.title_label.pack(padx=12, pady=(10, 4), anchor="w")

        # Scrollable, read-only output pane
        self.output_box = ctk.CTkTextbox(
            main_frame,
            fg_color=self.config.get("theme.output_bg_color", default="#141414"),
            text_color=self.config.get("theme.text_color", default="#D4D4D4"),
            font=mono_font,
            wrap="word",
            state="disabled",
        )
        self.output_box.pack(padx=12, pady=4, fill="both", expand=True)

        # CTkTextbox wraps a plain tkinter Text widget internally. We
        # configure color tags on it directly so success/error/warning
        # lines render in distinct colors (spec: "Colored messages").
        text_widget = self.output_box._textbox
        text_widget.tag_config("success", foreground=self.config.get("theme.success_color", default="#4CD964"))
        text_widget.tag_config("error", foreground=self.config.get("theme.error_color", default="#F14C4C"))
        text_widget.tag_config("warning", foreground=self.config.get("theme.warning_color", default="#E5C07B"))
        text_widget.tag_config("loading", foreground=self.config.get("theme.accent_color", default="#3B8ED0"))
        text_widget.tag_config("command", foreground=self.config.get("theme.warning_color", default="#DEC446"))


        # Bottom command bar: static ">" + input field
        self.input_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        self.input_frame.pack(padx=12, pady=(0, 4), fill="x")

        self.prompt_label = ctk.CTkLabel(
            self.input_frame,
            text=">",
            font=mono_font,
            text_color=self.config.get("theme.accent_color", default="#DEC446"),
        )
        self.prompt_label.pack(side="left", padx=(0, 6))

        self.input_field = ctk.CTkEntry(
            self.input_frame,
            font=mono_font,
            placeholder_text="Type a command... (try 'help')",
        )
        self.input_field.pack(side="left", fill="x", expand=True)
        self.input_field.focus_set()

        # Status bar
        self.status_bar = ctk.CTkLabel(
            main_frame,
            text="Ready",
            font=ctk.CTkFont(family=font_family, size=font_size - 2),
            anchor="w",
        )
        self.status_bar.pack(padx=12, pady=(0, 8), fill="x")

    def _bind_keys(self) -> None:
        """Wire Enter, Up/Down history navigation, and auto-refocus."""
        self.input_field.bind("<Return>", self._on_submit)
        self.input_field.bind("<Up>", self._on_history_up)
        self.input_field.bind("<Down>", self._on_history_down)
        self.input_field.bind("<Tab>", self._on_tab_complete)
        self.input_field.bind("<Key>", self._on_any_key)
        # Clicking anywhere in the window refocuses the input field, per
        # the spec's "Focus input automatically" requirement.
        self.bind("<Button-1>", lambda event: self.input_field.focus_set())

    def _print_welcome_banner(self) -> None:
        name = self.config.get("app.name", default="Kr4zy Terminal")
        version = self.config.get("app.version", default="0.1.0")
        self.print_output(f"{name} v{version}")
        self.print_output("Type 'help' to see available commands.")
        self.print_output("")

    # --- Event handlers --------------------------------------------------

    def _on_submit(self, event=None) -> None:
        """Handle Enter key: echo input, run command, record history."""
        raw_input = self.input_field.get()
        if not raw_input.strip():
            return

        self.print_command(raw_input)
        self.history.add(raw_input)
        self.input_field.delete(0, "end")

        self.set_status(f"Running: {raw_input.split()[0]}")
        handled = self.command_manager.execute(raw_input)
        if not handled:
            self.print_error(f"Unknown command: '{raw_input.split()[0]}'. Type 'help' for a list.")
        self.set_status("Ready")

    def _on_history_up(self, event=None) -> str:
        previous = self.history.previous()
        if previous is not None:
            self._set_input_text(previous)
        return "break"  # prevent default cursor-move behavior

    def _on_history_down(self, event=None) -> str:
        nxt = self.history.next()
        if nxt is not None:
            self._set_input_text(nxt)
        return "break"

    def _on_tab_complete(self, event=None) -> str:
        """Handle Tab: cycle through matching command names for the
        first word typed so far. Only the command name (first word) is
        completed - arguments after it are left untouched."""
        current_text = self.input_field.get()
        parts = current_text.split(" ", 1)
        first_word = parts[0]
        rest = f" {parts[1]}" if len(parts) > 1 else ""

        completion = self.autocompleter.next_completion(first_word)
        if completion is None:
            return "break"  # no matches - do nothing, don't insert a literal tab

        self._set_input_text(completion + rest)
        # Move cursor to end so the user can keep typing arguments.
        self.input_field.icursor("end")
        return "break"

    def _on_any_key(self, event=None) -> None:
        """Reset autocomplete cycling on any key that isn't part of the
        completion/history flow, so a fresh keystroke starts a fresh
        suggestion search instead of continuing an old cycle."""
        if event is not None and event.keysym in ("Tab", "Up", "Down", "Return"):
            return
        self.autocompleter.reset()

    def _set_input_text(self, text: str) -> None:
        self.input_field.delete(0, "end")
        self.input_field.insert(0, text)

    # --- Output helpers (called by commands via CommandContext) ---------
    
    def print_command(self, text: str) -> None:
        """Echo the user's typed command, with a yellow '>' prompt."""
        self._append_line(f"> {text}", tag="command")

    def print_output(self, text: str) -> None:
        """Print a plain output line to the terminal pane."""
        self._append_line(text)

    def print_success(self, text: str) -> None:
        """Print a success-styled (green) line."""
        self._append_line(f"[OK] {text}", tag="success")

    def print_error(self, text: str) -> None:
        """Print an error-styled (red) line."""
        self._append_line(f"[ERROR] {text}", tag="error")
        logger.error(text)

    def print_warning(self, text: str) -> None:
        """Print a warning-styled (yellow) line."""
        self._append_line(f"[WARN] {text}", tag="warning")

    def print_loading(self, text: str) -> None:
        """Print a loading/in-progress (accent-colored) line."""
        self._append_line(f"[...] {text}", tag="loading")

    def clear_output(self) -> None:
        """Clear all text from the output pane (used by `clear` command)."""
        self.output_box.configure(state="normal")
        self.output_box.delete("1.0", "end")
        self.output_box.configure(state="disabled")

    def set_status(self, text: str) -> None:
        """Update the status bar text."""
        self.status_bar.configure(text=f"[{timestamp()}] {text}")

    def _append_line(self, text: str, tag: str | None = None) -> None:
        """Append a line to the read-only output box and auto-scroll."""
        self.output_box.configure(state="normal")
        start_index = self.output_box.index("end-1c")
        self.output_box.insert("end", text + "\n")
        if tag:
            self.output_box._textbox.tag_add(tag, start_index, "end-1c")
        self.output_box.configure(state="disabled")
        self.output_box.see("end")