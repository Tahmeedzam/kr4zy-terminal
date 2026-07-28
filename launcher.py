"""
launcher.py
-----------
Launches external things on behalf of commands: executables, folders,
websites, and CMD/PowerShell commands.

Design decision:
    This is the ONLY module in the app allowed to call `subprocess`,
    `os.startfile`, or `webbrowser.open`. Every command file (help.py,
    flutter.py, workspace.py, ...) goes through `Launcher`, never
    through subprocess directly. That gives us one place to:

    - Run everything in background threads (spec requirement: "Run
      tasks asynchronously so the UI never freezes").
    - Log every launch attempt/result consistently.
    - Handle "file not found" / "app missing" errors the same way
      everywhere, instead of each command file reinventing error
      handling.

    Every public method here is fire-and-forget from the caller's
    perspective: it kicks off a background thread and returns
    immediately. Callers pass an `on_result` callback if they want to
    know the outcome (e.g. to print success/failure to the terminal),
    rather than blocking on a return value.
"""

from __future__ import annotations

import subprocess
import threading
import webbrowser
from pathlib import Path
from typing import Callable, Optional

from logger import get_logger
from utils import safe_str

logger = get_logger(__name__)

# Callback signature: (success: bool, message: str) -> None
ResultCallback = Optional[Callable[[bool, str], None]]


class Launcher:
    """
    Handles launching external applications, folders, websites, and
    shell commands, always off the main UI thread.
    """

    def open_app(self, path: str, args: Optional[list[str]] = None, on_result: ResultCallback = None) -> None:
        """
        Launch an executable file.

        Args:
            path: Absolute path to the .exe (or any executable) file.
            args: Optional list of command-line arguments.
            on_result: Optional callback invoked with (success, message)
                once the launch attempt completes.
        """
        self._run_in_thread(self._open_app_task, path, args or [], on_result)

    def open_folder(self, path: str, on_result: ResultCallback = None) -> None:
        """
        Open a folder in the system file explorer.

        Args:
            path: Absolute path to the folder.
            on_result: Optional result callback.
        """
        self._run_in_thread(self._open_folder_task, path, on_result)

    def open_website(self, url: str, on_result: ResultCallback = None) -> None:
        """
        Open a URL in the default web browser.

        Args:
            url: Full URL, e.g. "https://docs.flutter.dev".
            on_result: Optional result callback.
        """
        self._run_in_thread(self._open_website_task, url, on_result)

    def run_command(self, command: str, shell: str = "cmd", on_result: ResultCallback = None) -> None:
        """
        Run a shell command (CMD or PowerShell) as a subprocess.

        Args:
            command: The full command string to execute, e.g.
                "flutter doctor" or "git status".
            shell: Either "cmd" or "powershell".
            on_result: Optional callback invoked with (success, output)
                once the command finishes.
        """
        self._run_in_thread(self._run_command_task, command, shell, on_result)

    # --- Internal thread-wrapped implementations ----------------------------

    def _run_in_thread(self, target: Callable, *args) -> None:
        """
        Start `target(*args)` on a daemon background thread.

        `daemon=True` ensures a stuck/long-running launch never prevents
        the whole app from closing when the user exits.
        """
        thread = threading.Thread(target=target, args=args, daemon=True)
        thread.start()

    def _open_app_task(self, path: str, args: list[str], on_result: ResultCallback) -> None:
        exe_path = Path(path)
        if not exe_path.exists():
            message = f"Application not found: {path}"
            logger.error(message)
            self._notify(on_result, False, message)
            return

        try:
            subprocess.Popen([str(exe_path), *args])
            message = f"Launched: {exe_path.name}"
            logger.info(message)
            self._notify(on_result, True, message)
        except OSError as exc:
            message = f"Failed to launch {exe_path.name}: {safe_str(exc)}"
            logger.error(message)
            self._notify(on_result, False, message)

    def _open_folder_task(self, path: str, on_result: ResultCallback) -> None:
        folder_path = Path(path)
        if not folder_path.exists():
            message = f"Folder not found: {path}"
            logger.error(message)
            self._notify(on_result, False, message)
            return

        try:
            # os.startfile is Windows-only, which matches this app's target
            # platform (Windows desktop, per the project spec).
            import os

            os.startfile(str(folder_path))  # type: ignore[attr-defined]
            message = f"Opened folder: {folder_path}"
            logger.info(message)
            self._notify(on_result, True, message)
        except OSError as exc:
            message = f"Failed to open folder {path}: {safe_str(exc)}"
            logger.error(message)
            self._notify(on_result, False, message)

    def _open_website_task(self, url: str, on_result: ResultCallback) -> None:
        try:
            webbrowser.open_new_tab(url)
            message = f"Opened website: {url}"
            logger.info(message)
            self._notify(on_result, True, message)
        except Exception as exc:  # webbrowser rarely raises, but stay safe
            message = f"Failed to open website {url}: {safe_str(exc)}"
            logger.error(message)
            self._notify(on_result, False, message)

    def _run_command_task(self, command: str, shell: str, on_result: ResultCallback) -> None:
        shell_args = ["powershell", "-Command", command] if shell == "powershell" else ["cmd", "/c", command]

        try:
            result = subprocess.run(
                shell_args,
                capture_output=True,
                text=True,
                timeout=60,
            )
            output = (result.stdout or result.stderr or "(no output)").strip()
            success = result.returncode == 0
            logger.info(f"Ran command '{command}' (shell={shell}), exit={result.returncode}")
            self._notify(on_result, success, safe_str(output, max_length=2000))
        except subprocess.TimeoutExpired:
            message = f"Command timed out: {command}"
            logger.error(message)
            self._notify(on_result, False, message)
        except OSError as exc:
            message = f"Failed to run command '{command}': {safe_str(exc)}"
            logger.error(message)
            self._notify(on_result, False, message)

    def _notify(self, on_result: ResultCallback, success: bool, message: str) -> None:
        """Safely invoke the caller's result callback, if provided."""
        if on_result is not None:
            try:
                on_result(success, message)
            except Exception as exc:  # A broken callback must never crash the thread
                logger.error(f"on_result callback raised: {safe_str(exc)}")