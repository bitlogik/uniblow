REM Build Uniblow exe for Windows
@echo off

RMDIR /S /Q dist
RMDIR /S /Q build

python3 -O -m PyInstaller .\uniblow.spec

PAUSE
