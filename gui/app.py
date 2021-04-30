# -*- coding: utf8 -*-

# UNIBLOW app
# Copyright (C) 2021 BitLogiK

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3 of the License.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>


import sys
import os.path
import webbrowser

from wx import Icon
from wx import TextDataObject
from wx import TheClipboard

import gui.window
import gui.infodialog


class InfoBox(gui.infodialog.InfoDialog):
    def __init__(self, message, title, style, parent):
        super().__init__(parent)
        self.message = message
        self.SetTitle(title)
        self.m_textCtrl.SetBackgroundColour(self.GetBackgroundColour())
        self.m_textCtrl.SetValue(self.message)
        self.m_textCtrl.SelectNone()
        self.ShowModal()

    def copy_text_dialog(self, event):
        event.Skip()
        if TheClipboard.Open():
            TheClipboard.Clear()
            TheClipboard.SetData(TextDataObject(self.message))
            TheClipboard.Close()
            TheClipboard.Flush()
        # else silent : no Access

    def close_info(self, event):
        event.Skip()
        self.Destroy()


def file_path(fpath):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, fpath)
    return fpath


def load_devices(app, devices_list):
    app.gui_panel.devices_choice.Append("Choose your device")
    for device in devices_list:
        app.gui_panel.devices_choice.Append(device)
    app.gui_panel.devices_choice.SetSelection(0)


def load_coins_list(app, coins_list):
    app.gui_panel.coins_choice.Clear()
    app.gui_panel.coins_choice.Append("Select blockchain")
    for coin in coins_list:
        app.gui_panel.coins_choice.Append(coin)
    app.gui_panel.coins_choice.SetSelection(0)


def show_history(history_url):
    webbrowser.open(history_url, new=1, autoraise=True)


def start_app(app, version, coins_list, devices_list):
    app.gui_frame = gui.window.TopFrame(None)
    app.gui_panel = gui.window.TopPanel(app.gui_frame)
    app.gui_frame.SetIcon(Icon(file_path("gui/uniblow.ico")))
    app.gui_frame.SetTitle(f"  Uniblow  -  {version}")
    load_coins_list(app, coins_list)
    load_devices(app, devices_list)
    app.gui_frame.Show()
