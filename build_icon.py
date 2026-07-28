"""
build_icon.py
--------------
Standalone script: generates assets/icon.ico before packaging.

The app also generates this lazily on first run (see
terminal.py:_apply_window_icon), but PyInstaller needs the .ico file
to exist BEFORE the build (it's baked into the .exe's own icon), so
this script must be run once ahead of `pyinstaller Kr4zyTerminal.spec`.
Build.bat runs this automatically.
"""

from pathlib import Path

from icon_generator import ensure_ico_file

if __name__ == "__main__":
    icon_path = Path(__file__).resolve().parent / "assets" / "icon.ico"
    ensure_ico_file()
    print(f"Icon ready at: {icon_path}")