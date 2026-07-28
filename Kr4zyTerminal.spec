# Kr4zyTerminal.spec
# ------------------
# PyInstaller build spec for Kr4zy Terminal.
#
# Why a .spec file instead of a plain `pyinstaller main.py` command:
#   - config.json and assets/ are DATA files, not code. PyInstaller
#     won't bundle them automatically - they must be listed explicitly
#     via `datas`, or the packaged .exe will crash looking for
#     config.json next to a temp folder that doesn't have it.
#   - commands/*.py are discovered dynamically at runtime via
#     pkgutil.iter_modules(), not via a static `import commands.help`
#     anywhere in the code. PyInstaller's static analysis can't see
#     those imports, so every command module must be listed as a
#     hiddenimport or it'll be silently left out of the build.
#
# Build with:
#     pyinstaller Kr4zyTerminal.spec
#
# Output: dist/KrazyTerminal/KrazyTerminal.exe (one-folder build,
# recommended over one-file for this app since config.json/history.json/
# logs/ need to live in a real, persistent folder next to the exe -
# see utils.app_root()).


import glob
import os
from PyInstaller.utils.hooks import collect_data_files

ctk_datas = collect_data_files("customtkinter")

block_cipher = None

# Auto-discover every commands/*.py module so hiddenimports never goes
# stale when a new command file is added - matches the same "just add
# a file" philosophy as command_manager.py's runtime discovery.
command_modules = [
    f"commands.{os.path.splitext(os.path.basename(f))[0]}"
    for f in glob.glob("commands/*.py")
    if not os.path.basename(f).startswith("_")
]

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=[],
    datas=[
        ("config.json", "."),
        ("assets", "assets"),
        *ctk_datas,
    ],
    hiddenimports=command_modules,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="KrazyTerminal",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # no console window behind the CustomTkinter UI
    icon="assets/icon.ico" if os.path.exists("assets/icon.ico") else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="KrazyTerminal",
)
