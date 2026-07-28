"""
main.py
-------
Entry point for Kr4zy Terminal. Keeps startup logic minimal: create the
TerminalApp window and start the CustomTkinter event loop. All real
logic lives in terminal.py / command_manager.py / config.py.
"""

from __future__ import annotations

from terminal import TerminalApp
from logger import get_logger

logger = get_logger(__name__)


def main() -> None:
    """Start Kr4zy Terminal."""
    try:
        app = TerminalApp()
        app.mainloop()
    except Exception as exc:
        # Last-resort catch: log the crash so it's not silently lost,
        # matching the spec's "never crash" / friendly-error philosophy
        # even for startup-level failures.
        logger.error(f"Fatal error during startup: {exc}")
        raise


if __name__ == "__main__":
    main()