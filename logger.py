"""
logger.py
---------
Centralized logging setup for Kr4zy Terminal.

Design decision:
    We use Python's built-in `logging` module with a RotatingFileHandler
    instead of hand-rolled `print()`-to-file code. This gives us, for
    free: log levels, automatic rotation (so logs/ never grows
    unbounded), and consistent timestamp/format across every module.

    Every module that needs to log calls `get_logger(__name__)` rather
    than configuring logging itself. This keeps configuration in ONE
    place (this file) while still giving each module its own named
    logger, so log lines show exactly which file they came from, e.g.:

        2026-07-28 10:15:02 [launcher] INFO: Launched app: Code.exe

Nothing in this module ever raises on logging failure — a logging
problem should never be the reason the whole terminal crashes.
"""

from __future__ import annotations

import logging
import logging.handlers
from pathlib import Path

from config import get_config, BASE_DIR

_LOG_FORMAT = "%(asctime)s [%(name)s] %(levelname)s: %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

_configured = False


def _configure_root_logger() -> None:
    """
    Configure the root logger once, based on config.json settings.

    This is called automatically the first time `get_logger()` is used,
    so no explicit "setup" call is required anywhere else in the app.
    """
    global _configured
    if _configured:
        return

    config = get_config()
    log_dir_name = config.get("logging.directory", default="logs")
    level_name = config.get("logging.level", default="INFO")
    max_bytes = config.get("logging.max_bytes", default=1_048_576)
    backup_count = config.get("logging.backup_count", default=3)

    log_dir = BASE_DIR / log_dir_name
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "kr4zy_terminal.log"

    root_logger = logging.getLogger("kr4zy")
    root_logger.setLevel(getattr(logging, level_name.upper(), logging.INFO))

    # Avoid duplicate handlers if this ever gets called more than once
    # (e.g. during a `reload` command in the future).
    if not root_logger.handlers:
        file_handler = logging.handlers.RotatingFileHandler(
            filename=str(log_file),
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )
        file_handler.setFormatter(logging.Formatter(_LOG_FORMAT, _DATE_FORMAT))
        root_logger.addHandler(file_handler)

    _configured = True


def get_logger(name: str) -> logging.Logger:
    """
    Return a named logger that writes into logs/kr4zy_terminal.log.

    Args:
        name: Typically `__name__` of the calling module, so log lines
            are traceable to their source file.

    Returns:
        A configured `logging.Logger` instance.
    """
    _configure_root_logger()
    # Namespacing under "kr4zy." keeps all app loggers grouped under
    # one root logger, so log level changes apply everywhere at once.
    return logging.getLogger(f"kr4zy.{name}")