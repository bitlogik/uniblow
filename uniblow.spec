# -*- mode: python ; coding: utf-8 -*-

import os
import sys
import platform

current_path = os.path.dirname(os.path.abspath("uniblow.spec"))
sys.path.append(current_path)
from uniblow import SUPPORTED_COINS, DEVICES_LIST
from version import VERSION

ICON = "gui/uniblow.ico"


os_system = platform.system()
if os_system == "Windows":
    os_platform = "win"
if os_system == "Linux":
    os_platform = "nux"
if os_system == "Darwin":
    os_platform = "mac"
plt_arch = platform.machine().lower()
BIN_PKG_NAME = f"Uniblow-{os_platform}-{plt_arch}-{VERSION}"

additional_imports = [f"wallets.{coinpkg}wallet" for coinpkg in SUPPORTED_COINS]
additional_imports += [f"devices.{device}" for device in DEVICES_LIST]

pkgs_remove = ["sqlite3", "tcl85", "tk85", "_sqlite3", "_tkinter", "libopenblas", "libdgamln"]

a = Analysis(
    ["uniblow.py"],
    pathex=[current_path],
    binaries=[],
    datas=[
        (ICON, "gui/"),
        ("cryptolib/wordslist/english.txt", "cryptolib/wordslist/"),
        ("gui/good.bmp", "gui/"),
        ("gui/bad.bmp", "gui/"),
    ],
    hiddenimports=additional_imports,
    hookspath=[],
    runtime_hooks=[],
    excludes=[
        "_gtkagg",
        "_tkagg",
        "curses",
        "pywin.debugger",
        "pywin.debugger.dbgcon",
        "pywin.dialogs",
        "tcl",
        "Tkconstants",
        "Tkinter",
        "libopenblas",
        "libdgamln",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

for pkg in pkgs_remove:
    a.binaries = [x for x in a.binaries if not x[0].startswith(pkg)]

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name=BIN_PKG_NAME,
    icon=ICON,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
)
