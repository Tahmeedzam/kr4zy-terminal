@echo off
REM build.bat - builds Kr4zy Terminal into a distributable .exe
REM
REM Usage: just double-click this file, or run `build.bat` from a
REM terminal in the project folder.

echo Generating app icon...
python build_icon.py
if errorlevel 1 (
    echo Icon generation failed - aborting build.
    exit /b 1
)

echo.
echo Building with PyInstaller...
pyinstaller Kr4zyTerminal.spec --noconfirm

echo.
echo Done. Your app is in: dist\KrazyTerminal\KrazyTerminal.exe
echo Copy the whole dist\KrazyTerminal\ folder wherever you want to run it from -
echo config.json, history.json, and logs\ will all live next to the .exe.
pause