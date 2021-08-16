#!/bin/sh

# Build uniblow Debian 10 binary package release

# EXPERIMENTAL

# Requires Xcode developer tools
# Python 3.9
# if needed, python3 -m venv unibenvi should trigger the dev tools installation


echo Initializing venv ...
python3 -m venv unibenv
source unibenv/bin/activate

/Applications/Python\ 3.9/Install\ Certificates.command

echo Installing pip dependencies ...
python -m pip install pip==21.2.1
python -m pip install wxPython==4.1.1 pyscard==2.0.1 pysha3==1.0.2 pynacl==1.4.0 pyWalletConnect==1.0.0
python -m pip install .

python -m pip install pyinstaller==4.4

echo Building package ...
python -OO -m PyInstaller package/uniblow.spec
deactivate

echo Compilation done.
echo Binary result is in the dist folder.
