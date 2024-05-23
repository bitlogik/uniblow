#!/bin/sh

# Build the uniblow MacOS binary package release

# Requires Xcode developer tools
# Python 3.9
# If needed, python3 -m venv unibenv should trigger the dev tools installation


rm -Rf build
rm -Rf dist

echo Initializing venv ...
python3 -m venv unibenv
source unibenv/bin/activate

echo Installing pip dependencies ...
python -m pip install pip==21.2.1
python -m pip install wxPython>=4.2.0
python -m pip install .

python -m pip install -U certifi
python -m pip install pyinstaller==4.10

echo Building package ...
python -OO -m PyInstaller package/uniblow.spec
deactivate

rm -Rf dist/uniblow-bundle
chmod +x dist/uniblow.app/Contents/MacOS/uniblow
setopt +o nomatch
rm -Rf dist/uniblow.app/Contents/MacOS/*-info
rm -Rf dist/uniblow.app/Contents/Resources/*-info
setopt -o nomatch

echo Compilation done.
echo Binary result is in the dist folder.

echo Now need : code sign, notarization, dmg bundling, and notarization of the bundle.
echo DMG building requires biplist and dmgbuild.
