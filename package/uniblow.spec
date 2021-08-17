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


def is_debian():
    OS_REL_FILE = "/etc/os-release"
    if os.path.isfile(OS_REL_FILE):
        with open(OS_REL_FILE, "r") as osrel_fid:
            for line_str in osrel_fid.readlines():
                if line_str[6:12] == "Debian":
                    # NAME="Debian
                    return True
    return False


os_system = platform.system()
if os_system == "Windows":
    os_platform = "win"
elif os_system == "Linux":
    os_platform = "nux"
    if is_debian():
        os_platform = "deb"
elif os_system == "Darwin":
    os_platform = "mac"
else:
    raise Exception("Unknown platform target")
plt_arch = platform.machine().lower()
BIN_PKG_NAME = f"Uniblow-{os_platform}-{plt_arch}-{VERSION}"

additional_imports = [f"wallets.{coinpkg}wallet" for coinpkg in SUPPORTED_COINS]
additional_imports += [f"devices.{device}" for device in DEVICES_LIST]

pkgs_remove = ["sqlite3", "tcl85", "tk85", "_sqlite3", "_tkinter", "libopenblas", "libdgamln"]

a = Analysis(
    ["../uniblow.py"],
    pathex=[current_path],
    binaries=[],
    datas=[
        (ICON, "gui/"),
        ("../cryptolib/wordslist/english.txt", "cryptolib/wordslist/"),
        ("../gui/good.bmp", "gui/"),
        ("../gui/bad.bmp", "gui/"),
        ("../gui/GenSeed.png", "gui/"),
        ("../gui/GenSeeddn.png", "gui/"),
        ("../gui/copy.png", "gui/"),
        ("../gui/copydn.png", "gui/"),
        ("../gui/histo.png", "gui/"),
        ("../gui/histodn.png", "gui/"),
        ("../gui/SeekAssets.png", "gui/"),
        ("../gui/SeekAssetsdn.png", "gui/"),
        ("../gui/send.png", "gui/"),
        ("../gui/senddn.png", "gui/"),
        ("../gui/swipe.png", "gui/"),
        ("../gui/swipedn.png", "gui/"),
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

if os_platform == "win":
    fill_version_info(BIN_PKG_NAME, VERSION, FILE_DESCRIPTION, COMMENTS)
    version_info_file = "version_info"
else:
    version_info_file = None

exe_options = [a.scripts]

if os_platform == "mac":
    BIN_PKG_NAME = "uniblow"
else:
    exe_options += [a.binaries, a.zipfiles, a.datas]

exe = EXE(
    pyz,
    *exe_options,
    [],
    exclude_binaries=True,
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
        exe, a.binaries, a.zipfiles, a.datas, strip=False, upx=True, upx_exclude=[], name="uniblow"
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
            "CFBundleShortVersionString": VERSION,
        },
    )
