REM Build uniblow Windows binary package release

@echo off

PUSHD .

CD ..

RMDIR /S /Q dist
RMDIR /S /Q build

"%UserProfile%\AppData\Local\Programs\Python\Python38\python38.exe" -O -m PyInstaller .\package\uniblow.spec

POPD

PAUSE
