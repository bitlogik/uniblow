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

from wx import IconBundle, TextDataObject, TheClipboard, Bitmap, EVT_TEXT, ID_OK, ID_CANCEL

import gui.window
import gui.infodialog

from cryptolib.HDwallet import bip39_is_checksum_valid


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


class HDsetting_panel(gui.window.HDPanel):
    def hdmnemo_changed(self, evt):
        evt.Skip()
        self.m_bitmapHDwl.SetBitmap(self.BAD_BMP)
        self.m_bitmapHDcs.SetBitmap(self.BAD_BMP)
        cs, wl = bip39_is_checksum_valid(self.m_textCtrl_mnemo.GetValue())
        if wl:
            self.m_bitmapHDwl.SetBitmap(self.GOOD_BMP)
        if cs:
            self.m_bitmapHDcs.SetBitmap(self.GOOD_BMP)

    def hd_ok(self, event):
        event.Skip()
        if self.m_checkBox_secboost.IsChecked():
            derivation = "SCRYPT"
        else:
            derivation = "PBKDF2-2048-HMAC-SHA512"
        mnemo_txt = self.m_textCtrl_mnemo.GetValue()
        password = self.m_textCtrl_pwd.GetValue()
        account_idx = str(self.m_spinCtrl_accountidx.GetValue())
        # Attach object to frame, so the modal inputs are synchroneous
        self.hd_wallet_settings = {
            "mnemonic": mnemo_txt,
            "account_index": account_idx,
            "HD_password": password,
            "seed_gen": derivation,
        }
        self.GetParent().EndModal(ID_OK)

    def hd_cancel(self, event):
        event.Skip()
        self.GetParent().EndModal(ID_CANCEL)


def set_mnemonic(app, proposal):
    app.gui_hdframe = gui.window.HDDialog(app.gui_frame)
    app.gui_hdpanel = HDsetting_panel(app.gui_hdframe)
    app.gui_hdpanel.GOOD_BMP = Bitmap(file_path("gui/good.bmp"))
    app.gui_hdpanel.BAD_BMP = Bitmap(file_path("gui/bad.bmp"))
    app.gui_hdpanel.m_bitmapHDwl.SetBitmap(app.gui_hdpanel.BAD_BMP)
    app.gui_hdpanel.m_bitmapHDcs.SetBitmap(app.gui_hdpanel.BAD_BMP)
    app.gui_hdpanel.m_textCtrl_mnemo.SetValue(proposal)
    ret = app.gui_hdframe.ShowModal()
    if ret == ID_OK:
        wallet_settings = app.gui_hdpanel.hd_wallet_settings
        # Removal of stored settings
        app.gui_hdframe.DestroyChildren()
        app.gui_hdframe.Destroy()
        del app.gui_hdframe
        return wallet_settings
    else:
        return None


def start_app(app, version, coins_list, devices_list):
    app.gui_frame = gui.window.TopFrame(None)
    app.gui_panel = gui.window.TopPanel(app.gui_frame)
    app.gui_frame.SetIcons(IconBundle(file_path("gui/uniblow.ico")))
    app.gui_frame.SetTitle(f"  Uniblow  -  {version}")
    load_coins_list(app, coins_list)
    load_devices(app, devices_list)
    app.gui_frame.Show()
