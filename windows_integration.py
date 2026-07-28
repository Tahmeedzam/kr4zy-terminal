"""
windows_integration.py
-----------------------
System tray integration: minimizes to tray on window close instead of
quitting, with a right-click menu to show the window again or quit for
real.

Design decision:
    pystray runs its own event loop on a background thread. It must
    NEVER touch Tkinter widgets directly from that thread - Tkinter is
    not thread-safe. Every action the tray triggers (show window, quit)
    is scheduled back onto the Tkinter main thread via
    `terminal.after(0, ...)`.
"""

from __future__ import annotations

import threading

import pystray

from tray_icon import get_tray_icon_image
from logger import get_logger

logger = get_logger(__name__)


class TrayIntegration:
    """Manages the system tray icon and its menu for a TerminalApp instance."""

    def __init__(self, terminal) -> None:
        """
        Args:
            terminal: The TerminalApp instance to show/hide/quit.
        """
        self.terminal = terminal
        self._icon: pystray.Icon | None = None
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        """
        Build and start the tray icon on a background daemon thread.
        Also rebinds the window's close button to minimize-to-tray
        instead of quitting.
        """
        image = get_tray_icon_image()
        menu = pystray.Menu(
            pystray.MenuItem("Show Kr4zy Terminal", self._on_show, default=True),
            pystray.MenuItem("Quit", self._on_quit),
        )
        self._icon = pystray.Icon("kr4zy_terminal", image, "Kr4zy Terminal", menu)

        self.terminal.protocol("WM_DELETE_WINDOW", self._on_window_close)

        self._thread = threading.Thread(target=self._icon.run, daemon=True)
        self._thread.start()
        logger.info("Tray icon started")

    def stop(self) -> None:
        """Stop the tray icon (called on real quit)."""
        if self._icon is not None:
            self._icon.stop()

    # --- Tray menu callbacks (run on pystray's thread) ----------------------

    def _on_show(self, icon=None, item=None) -> None:
        """Show and focus the window again. Scheduled onto the Tk thread."""
        self.terminal.after(0, self._show_window)

    def _on_quit(self, icon=None, item=None) -> None:
        """Actually quit the app (not just hide it)."""
        self.terminal.after(0, self._quit_app)

    def _on_window_close(self) -> None:
        """Called when the user clicks the window's X button - hide to
        tray instead of closing, per 'minimize to tray' spec requirement."""
        self.terminal.side_panel.stop()
        self.terminal.withdraw()
        logger.info("Window minimized to tray")

    # --- Actions run on the Tk main thread -----------------------------

    def _show_window(self) -> None:
        self.terminal.deiconify()
        self.terminal.lift()
        self.terminal.focus_force()
        self.terminal.input_field.focus_set()
        self.terminal.side_panel.start()

    def _quit_app(self) -> None:
        self.stop()
        self.terminal.destroy()