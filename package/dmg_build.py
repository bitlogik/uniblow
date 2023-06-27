#!/usr/bin/python3
# -*- coding: utf8 -*-

# Uniblow DMG builder
# Copyright (C) 2021-2023 BitLogiK

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3 of the License.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>


import plistlib
import os.path

exec(open("version.py", encoding="utf8").read())

# Use : dmgbuild -s packages/dmg_build.py

application = defines.get("app", "dist/uniblow.app")
appname = os.path.basename(application)


def icon_from_app(app_path):
    plist_path = os.path.join(app_path, "Contents", "Info.plist")
    with open(plist_path, "rb") as plistf:
        plist = plistlib.load(plistf)
    icon_name = plist["CFBundleIconFile"]
    icon_root, icon_ext = os.path.splitext(icon_name)
    if not icon_ext:
        icon_ext = ".icns"
    icon_name = icon_root + icon_ext
    return os.path.join(app_path, "Contents", "Resources", icon_name)


filename = f"dist/Uniblow-mac-{VERSION}.dmg"
volume_name = f"uniblow {VERSION} install disk image"
format = defines.get("format", "UDBZ")
compression_level = 9
size = defines.get("size", None)
files = [application]
symlinks = {"Applications": "/Applications"}

# icon = '/path/to/icon.icns'
badge_icon = icon_from_app(application)

icon_locations = {appname: (120, 100), "Applications": (470, 100)}

background = "package/backgroundDMG.png"

show_status_bar = False
show_tab_view = False
show_toolbar = False
show_pathbar = False
show_sidebar = False
sidebar_width = 180

window_rect = ((100, 100), (590, 275))

default_view = "icon-view"

show_icon_preview = False
include_icon_view_settings = "auto"
include_list_view_settings = "auto"

arrange_by = None
grid_offset = (0, 0)
grid_spacing = 100
scroll_position = (0, 0)
label_pos = "bottom"
text_size = 14
icon_size = 128
list_icon_size = 16
list_text_size = 12
list_scroll_position = (0, 0)
list_sort_by = "name"
list_use_relative_dates = True
list_calculate_all_sizes = (False,)
list_columns = ("name", "date-modified", "size", "kind", "date-added")
list_column_widths = {
    "name": 300,
    "date-modified": 181,
    "date-created": 181,
    "date-added": 181,
    "date-last-opened": 181,
    "size": 97,
    "kind": 115,
    "label": 100,
    "version": 75,
    "comments": 300,
}
list_column_sort_directions = {
    "name": "ascending",
    "date-modified": "descending",
    "date-created": "descending",
    "date-added": "descending",
    "date-last-opened": "descending",
    "size": "descending",
    "kind": "ascending",
    "label": "ascending",
    "version": "ascending",
    "comments": "ascending",
}
