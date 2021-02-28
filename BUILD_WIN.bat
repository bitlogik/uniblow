REM Build Uniblow exe for Windows
@echo off

RMDIR /S /Q dist
RMDIR /S /Q build

"%UserProfile%\AppData\Local\Programs\Python\Python36\Scripts\pyinstaller.exe" .\uniblow.spec

PAUSE
