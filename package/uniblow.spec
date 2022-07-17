# -*- mode: python ; coding: utf-8 -*-

import os
import sys
import platform
from package.build_win_verinfo import fill_version_info

from uniblow import SUPPORTED_COINS, DEVICES_LIST
from version import VERSION


current_path = os.path.dirname(os.path.abspath("uniblow.spec"))
sys.path.append(current_path)

ICON = "../gui/uniblow.ico"
FILE_DESCRIPTION = "uniblow application executable"
COMMENTS = "universal blockchain wallet for cryptos"


os_system = platform.system()
if os_system == "Windows":
    os_platform = "win"
elif os_system == "Linux":
    os_platform = "linux"
elif os_system == "Darwin":
    os_platform = "mac"
else:
    raise Exception("Unknown platform target")
plt_arch = platform.machine().lower()
BIN_PKG_NAME = f"Uniblow-{os_platform}-{plt_arch}-{VERSION}"

additional_imports = [f"wallets.{coinpkg}wallet" for coinpkg in SUPPORTED_COINS]
additional_imports += [f"devices.{device}" for device in DEVICES_LIST]

if os_platform == "mac":
    additional_imports.append("certifi")

pkgs_remove = [
    "sqlite3",
    "tcl85",
    "tk85",
    "_sqlite3",
    "_tkinter",
    "libopenblas",
    "libdgamln",
    "libdbus",
]

datai = [
    (ICON, "gui/"),
    ("../cryptolib/wordslist/english.txt", "cryptolib/wordslist/"),
    ("../gui/images/logo.png", "gui/images/"),
    ("../gui/images/good.png", "gui/images/"),
    ("../gui/images/bad.png", "gui/images/"),
    ("../gui/images/btns/GenSeed.png", "gui/images/btns/"),
    ("../gui/images/btns/cancel.png", "gui/images/btns/"),
    ("../gui/images/btns/chdev.png", "gui/images/btns/"),
    ("../gui/images/btns/close.png", "gui/images/btns/"),
    ("../gui/images/btns/proceed.png", "gui/images/btns/"),
    ("../gui/images/btns/paste.png", "gui/images/btns/"),
    ("../gui/images/btns/ok.png", "gui/images/btns/"),
    ("../gui/images/btns/quit.png", "gui/images/btns/"),
    ("../gui/images/btns/copy.png", "gui/images/btns/"),
    ("../gui/images/btns/history.png", "gui/images/btns/"),
    ("../gui/images/btns/SeekAssets.png", "gui/images/btns/"),
    ("../gui/images/btns/send.png", "gui/images/btns/"),
    ("../gui/images/btns/dev_seedwatcher.png", "gui/images/btns/"),
    ("../gui/images/btns/dev_local.png", "gui/images/btns/"),
    ("../gui/images/btns/dev_ledger.png", "gui/images/btns/"),
    ("../gui/images/btns/dev_cryptnox.png", "gui/images/btns/"),
    ("../gui/images/btns/dev_pgp.png", "gui/images/btns/"),
    ("../gui/images/btns/addrchk.png", "gui/images/btns/"),
    ("../gui/images/btns/tokens.png", "gui/images/btns/"),
    ("../gui/images/btns/wc.png", "gui/images/btns/"),
    ("../gui/images/btns/endwc.png", "gui/images/btns/"),
]
datai += [
    (f"../gui/images/icons/{coin.lower()}.png", "gui/images/icons/") for coin in SUPPORTED_COINS
]

a = Analysis(
    ["../uniblow.py"],
    pathex=[current_path],
    binaries=[],
    datas=datai,
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

if os_platform == "win":
    fill_version_info(BIN_PKG_NAME, VERSION, FILE_DESCRIPTION, COMMENTS)
    version_info_file = "version_info"
else:
    version_info_file = None

exe_options = [a.scripts]

if os_platform == "mac":
    bins_apart = True
    BIN_PKG_NAME = "uniblow"
else:
    bins_apart = False
    exe_options += [a.binaries, a.zipfiles, a.datas]

exe = EXE(
    pyz,
    *exe_options,
    [],
    exclude_binaries=bins_apart,
    name=BIN_PKG_NAME,
    icon=ICON,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    version=version_info_file,
)

if os_platform == "mac":
    coll = COLLECT(
        exe,
        a.binaries,
        a.zipfiles,
        a.datas,
        strip=False,
        upx=True,
        upx_exclude=[],
        name="uniblow-bundle",
    )

    app = BUNDLE(
        coll,
        name="uniblow.app",
        icon=ICON,
        bundle_identifier="fr.bitlogik.uniblow",
        version=VERSION,
        info_plist={
            "NSPrincipalClass": "NSApplication",
            "NSHighResolutionCapable": True,
            "NSAppleScriptEnabled": False,
            "CFBundleIdentifier": "fr.bitlogik.uniblow",
            "CFBundleName": "uniblow",
            "CFBundleDisplayName": "uniblow",
            "CFBundleVersion": VERSION,
            "CFBundleShortVersionString": VERSION,
            "LSEnvironment": {
                "LANG": "en_US.UTF-8",
                "LC_CTYPE": "en_US.UTF-8",
            },
            "NSHumanReadableCopyright": "Copyright (C) 2021-2022 BitLogiK",
        },
    )
