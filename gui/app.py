# -*- coding: utf8 -*-

# UNIBLOW app
# Copyright (C) 2021-2022 BitLogiK

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
from os import environ
from webbrowser import open as wopen

from wx import (
    App,
    IconBundle,
    TextDataObject,
    TheClipboard,
    Bitmap,
    ID_OK,
    ID_CANCEL,
    Cursor,
    CURSOR_HAND,
    BITMAP_TYPE_PNG,
    EVT_ACTIVATE_APP,
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
        self.Show()

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


def show_history(history_url):
    wopen(history_url, new=1, autoraise=True)


if sys.platform.startswith("darwin"):
    # On MacOS, the set_default_verify_paths method of the Python OpenSSL lib,
    # used in the context method load_default_certs, mostly fails to find any
    # root Certificates Authorities for the SSLContext class.
    # This helps the Python OpenSSL to find the location for the context,
    # at which CA certificates for verification purposes is located.
    # On Mac, Uniblow is bundled with the certifi package, which uses
    # the Mozilla CA certificates list, in the 'cacert' PEM file.
    # https://wiki.mozilla.org/CA/Included_Certificates
    cert_file_path = os.path.abspath(os.path.join(__file__, "../../certifi/cacert.pem"))
    # The certifi CA file exists at this path when in the Mac app bundle
    if os.path.exists(cert_file_path):
        # Setting the environment variable SSL_CERT_FILE for libssl
        environ["SSL_CERT_FILE"] = cert_file_path


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
        account = str(self.m_spinCtrl_account.GetValue())
        index = str(self.m_spinCtrl_index.GetValue())
        legacy = self.m_altderiv.IsChecked()
        self.hd_wallet_settings = {
            "account": account,
            "index": index,
            "legacy_path": legacy,
        }
        if self.m_checkBox_secboost:
            # Case software HD
            if self.m_checkBox_secboost.IsChecked():
                derivation = "SCRYPT"
            else:
                derivation = "PBKDF2-2048-HMAC-SHA512"
            mnemo_txt = self.m_textCtrl_mnemo.GetValue()
            password = self.m_textCtrl_pwd.GetValue()

            # Attach object to frame, so the modal inputs are synchroneous
            self.hd_wallet_settings.update(
                {
                    "mnemonic": mnemo_txt,
                    "HD_password": password,
                    "seed_gen": derivation,
                }
            )
        self.GetParent().EndModal(ID_OK)

    def hd_cancel(self, event):
        event.Skip()
        self.GetParent().EndModal(ID_CANCEL)


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

    def pasteValue(self, event):
        """Paste the clipboard value in new_choice input field."""
        event.Skip()
        text_data = TextDataObject()
        if TheClipboard.Open():
            success = TheClipboard.GetData(text_data)
            TheClipboard.Close()
        if success:
            self.new_choice.SetValue(text_data.GetText())

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


class UniblowApp(App):
    def __init__(self, version):
        self.version = version
        App.__init__(self)
        self.Bind(EVT_ACTIVATE_APP, self.OnActivate)

    def OnInit(self):
        icon_path = file_path(ICON_FILE)
        wicon = IconBundle(icon_path)
        HAND_CURSOR = Cursor(CURSOR_HAND)
        self.gui_frame = gui.window.TopFrame(None)
        self.SetTopWindow(self.gui_frame)
        if sys.platform.startswith("darwin"):
            self.gui_frame.SetSize((996, 418))
        self.gui_panel = gui.window.TopPanel(self.gui_frame)
        self.gui_frame.SetIcons(wicon)
        self.gui_frame.SetTitle(f"  Uniblow  -  {self.version}")
        self.gui_panel.hist_button.SetBitmap(Bitmap(file_path("gui/histo.png"), BITMAP_TYPE_PNG))
        self.gui_panel.hist_button.SetBitmapPressed(
            Bitmap(file_path("gui/histodn.png"), BITMAP_TYPE_PNG)
        )
        self.gui_panel.copy_button.SetBitmap(Bitmap(file_path("gui/copy.png"), BITMAP_TYPE_PNG))
        self.gui_panel.copy_button.SetBitmapPressed(
            Bitmap(file_path("gui/copydn.png"), BITMAP_TYPE_PNG)
        )
        self.gui_panel.send_button.SetBitmap(Bitmap(file_path("gui/send.png"), BITMAP_TYPE_PNG))
        self.gui_panel.send_button.SetBitmapPressed(
            Bitmap(file_path("gui/senddn.png"), BITMAP_TYPE_PNG)
        )
        self.gui_panel.send_all.SetBitmap(Bitmap(file_path("gui/swipe.png"), BITMAP_TYPE_PNG))
        self.gui_panel.send_all.SetBitmapPressed(
            Bitmap(file_path("gui/swipedn.png"), BITMAP_TYPE_PNG)
        )
        self.gui_panel.devices_choice.SetCursor(HAND_CURSOR)
        self.gui_panel.coins_choice.SetCursor(HAND_CURSOR)
        self.gui_panel.network_choice.SetCursor(HAND_CURSOR)
        self.gui_panel.wallopt_choice.SetCursor(HAND_CURSOR)
        self.gui_panel.hist_button.SetCursor(HAND_CURSOR)
        self.gui_panel.copy_button.SetCursor(HAND_CURSOR)
        self.gui_panel.send_button.SetCursor(HAND_CURSOR)
        self.gui_panel.send_all.SetCursor(HAND_CURSOR)
        self.gui_panel.btn_chkaddr.SetCursor(HAND_CURSOR)
        return True

    def BringWindowToFront(self):
        try:
            self.GetTopWindow().Raise()
        except Exception:
            pass

    def OnActivate(self, event):
        if event.GetActive() and sys.platform != "linux":
            self.BringWindowToFront()
        event.Skip()

    def MacReopenApp(self):
        self.BringWindowToFront()

    def load_devices(self, devices_list):
        self.gui_panel.devices_choice.Append("Choose your device")
        for device in devices_list:
            self.gui_panel.devices_choice.Append(device)
        self.gui_panel.devices_choice.SetSelection(0)

    def load_coins_list(self, coins_list):
        self.gui_panel.coins_choice.Clear()
        self.gui_panel.coins_choice.Append("Select blockchain")
        for coin in coins_list:
            self.gui_panel.coins_choice.Append(coin)
        self.gui_panel.coins_choice.SetSelection(0)

    def hd_setup(self, proposal):
        """Call the HD device option window."""
        self.gui_hdframe = gui.window.HDDialog(self.gui_frame)
        self.gui_hdpanel = HDsetting_panel(self.gui_hdframe)
        HAND_CURSOR = Cursor(CURSOR_HAND)
        if proposal:
            self.gui_hdpanel.GOOD_BMP = Bitmap(file_path("gui/good.bmp"))
            self.gui_hdpanel.BAD_BMP = Bitmap(file_path("gui/bad.bmp"))
            self.gui_hdpanel.m_bitmapHDwl.SetBitmap(self.gui_hdpanel.BAD_BMP)
            self.gui_hdpanel.m_bitmapHDcs.SetBitmap(self.gui_hdpanel.BAD_BMP)
            self.gui_hdpanel.m_checkBox_secboost.SetCursor(HAND_CURSOR)
            self.gui_hdpanel.m_textCtrl_mnemo.SetValue(proposal)
            self.gui_hdpanel.m_usertxt.SetLabel(
                "Validate this first proposal,\n"
                "or insert your mnemonic and settings to import\n"
                "an existing HD wallet."
            )
        else:
            self.gui_hdpanel.title_text.SetLabel("Hardware wallet account options")
            self.gui_hdpanel.m_textwl.Destroy()
            self.gui_hdpanel.m_textcs.Destroy()
            self.gui_hdpanel.m_textCtrl_mnemo.Destroy()
            self.gui_hdpanel.m_bwptxt.Destroy()
            self.gui_hdpanel.m_textCtrl_pwd.Destroy()
            self.gui_hdpanel.m_checkBox_secboost.Destroy()
            self.gui_hdpanel.m_usertxt.SetLabel("Choose account and index for the key to use.")
            self.gui_hdframe.SetSize(470, 290)
        self.gui_hdpanel.m_butOK.SetCursor(HAND_CURSOR)
        self.gui_hdpanel.m_butcancel.SetCursor(HAND_CURSOR)
        ret = self.gui_hdframe.ShowModal()
        if ret == ID_OK:
            wallet_settings = self.gui_hdpanel.hd_wallet_settings
            # Removal of stored settings
            self.gui_hdframe.DestroyChildren()
            self.gui_hdframe.Destroy()
            del self.gui_hdframe
            return wallet_settings
        else:
            return None
