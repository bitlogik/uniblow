#!/bin/sh

# Build the uniblow MacOS binary package release

# Requires Xcode developer tools
# Python 3.10
# If needed, python3 -m venv unibenv should trigger the dev tools installation


rm -Rf build
rm -Rf dist

echo Initializing venv ...
python3 -m venv unibenv
source unibenv/bin/activate

echo Installing pip dependencies ...
python -m pip install -U pip
python -m pip install -U swig
python -m pip install OpenPGPpy --no-deps
python -m pip install pyscard==2.0.10
python -m pip install wxPython>=4.2.0
python -m pip install "cryptography>=3.3" "safe-pysha3==1.0.4" "qrcode==6.1" "PyNaCl==1.5.0" "pyweb3==0.1.7" "hidapi==0.14.0" "pyWalletConnect==1.6.2",

python -m pip install -U certifi
python -m pip install pyinstaller==5.13.2

echo Building package ...
python -OO -m PyInstaller package/uniblow.spec
deactivate

rm -Rf dist/uniblow-bundle
chmod +x dist/uniblow.app/Contents/MacOS/uniblow
setopt +o nomatch
rm -Rf dist/uniblow.app/Contents/MacOS/*-info
rm -Rf dist/uniblow.app/Contents/Resources/*-info
setopt -o nomatch
rm -Rf dist/uniblow.app/Contents/Frameworks/numpy/.dylibs
rm -Rf dist/uniblow.app/Contents/Frameworks/PIL/.dylibs

echo Compilation done.
echo Binary result is in the dist folder.

echo Now need : code sign, notarization, dmg bundling, and notarization of the bundle.
echo DMG building requires biplist and dmgbuild.
