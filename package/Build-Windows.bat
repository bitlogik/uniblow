REM Build uniblow Windows binary package release

@echo off

PUSHD .

CD ..

RMDIR /S /Q dist

SET python_bin="%UserProfile%\AppData\Local\Programs\Python\Python38\python.exe"
SET python_env="unibenv\Scripts\python"

%python_bin% -m venv unibenv

%python_env% -m pip install -U pip
%python_env% -m pip install wxPython==4.1.1
%python_env% setup.py install

%python_env% -m pip install PyInstaller==4.4
%python_env% -O -m PyInstaller .\package\uniblow.spec

POPD

echo Compilation done.
echo Binary result is in the dist folder.

PAUSE
