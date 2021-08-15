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
from webbrowser import open as wopen

from wx import (
    IconBundle,
    TextDataObject,
    TheClipboard,
    Bitmap,
    ID_OK,
    ID_CANCEL,
    Cursor,
    CURSOR_HAND,
    BITMAP_TYPE_PNG,
    ID_CANCEL,
    ID_OK,
)

import gui.window
import gui.infodialog

from cryptolib.HDwallet import bip39_is_checksum_valid

ICON_FILE = "gui/uniblow.ico"


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
    wopen(history_url, new=1, autoraise=True)


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
    HAND_CURSOR = Cursor(CURSOR_HAND)
    app.gui_hdpanel.m_checkBox_secboost.SetCursor(HAND_CURSOR)
    app.gui_hdpanel.m_butOK.SetCursor(HAND_CURSOR)
    app.gui_hdpanel.m_butcancel.SetCursor(HAND_CURSOR)
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


class app_option_panel(gui.window.OptionPanel):
    def valid_custom(self, event):
        self.okOption(event)

    def okOption(self, event):
        event.Skip()
        option_value = self.new_choice.GetValue()
        # Option value filled by user, or not preset displayed
        if option_value or not hasattr(self, "preset_values"):
            self.option_value = option_value
        else:
            preset_choice = self.known_choice.GetStringSelection()
            self.option_value = self.preset_values.get(preset_choice, "NotSelected")
        self.GetParent().EndModal(ID_OK)

    def cancelOption(self, event):
        event.Skip()
        self.GetParent().EndModal(ID_CANCEL)

    def GetValue(self):
        return self.option_value

    def HidePreset(self):
        self.preset_text.Hide()
        self.known_choice.Hide()
        self.m_staticTextor.Hide()

    def SetPresetLabel(self, text):
        self.preset_label = text
        self.preset_text.SetLabelText(self.preset_label)

    def SetPresetValues(self, values):
        self.known_choice.Clear()
        self.known_choice.Append(f"Select a {self.preset_label}")
        self.preset_values = values
        for preset_txt in values.keys():
            self.known_choice.Append(preset_txt)
        self.known_choice.SetSelection(0)

    def SetCustomLabel(self, text):
        self.custom_text.SetLabelText(text)

    def SetTitle(self, title):
        self.GetParent().SetTitle(title)


def start_app(app, version, coins_list, devices_list):
    icon_path = file_path(ICON_FILE)
    if not os.path.isfile(icon_path):
        print("Icon not found. Run uniblow from its directory.")
        return "ERR"
    wicon = IconBundle(icon_path)
    HAND_CURSOR = Cursor(CURSOR_HAND)
    app.gui_frame = gui.window.TopFrame(None)
    app.gui_panel = gui.window.TopPanel(app.gui_frame)
    app.gui_frame.SetIcons(wicon)
    app.gui_frame.SetTitle(f"  Uniblow  -  {version}")
    load_coins_list(app, coins_list)
    load_devices(app, devices_list)

    app.gui_panel.hist_button.SetBitmap(Bitmap(file_path("gui/histo.png"), BITMAP_TYPE_PNG))
    app.gui_panel.hist_button.SetBitmapPressed(
        Bitmap(file_path("gui/histodn.png"), BITMAP_TYPE_PNG)
    )
    app.gui_panel.copy_button.SetBitmap(Bitmap(file_path("gui/copy.png"), BITMAP_TYPE_PNG))
    app.gui_panel.copy_button.SetBitmapPressed(Bitmap(file_path("gui/copydn.png"), BITMAP_TYPE_PNG))
    app.gui_panel.send_button.SetBitmap(Bitmap(file_path("gui/send.png"), BITMAP_TYPE_PNG))
    app.gui_panel.send_button.SetBitmapPressed(Bitmap(file_path("gui/senddn.png"), BITMAP_TYPE_PNG))
    app.gui_panel.send_all.SetBitmap(Bitmap(file_path("gui/swipe.png"), BITMAP_TYPE_PNG))
    app.gui_panel.send_all.SetBitmapPressed(Bitmap(file_path("gui/swipedn.png"), BITMAP_TYPE_PNG))

    app.gui_panel.devices_choice.SetCursor(HAND_CURSOR)
    app.gui_panel.coins_choice.SetCursor(HAND_CURSOR)
    app.gui_panel.network_choice.SetCursor(HAND_CURSOR)
    app.gui_panel.wallopt_choice.SetCursor(HAND_CURSOR)
    app.gui_panel.hist_button.SetCursor(HAND_CURSOR)
    app.gui_panel.copy_button.SetCursor(HAND_CURSOR)
    app.gui_panel.send_button.SetCursor(HAND_CURSOR)
    app.gui_panel.send_all.SetCursor(HAND_CURSOR)

    app.gui_frame.Show()
