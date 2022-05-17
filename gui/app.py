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


from functools import partial
from logging import getLogger
import sys
import os.path
from os import environ

import wx

import gui.maingui
import gui.infodialog
from gui.utils import file_path, show_history
from gui.send_frame import SendModal

from cryptolib.HDwallet import bip39_is_checksum_valid


logger = getLogger(__name__)


ICON_FILE = "gui/uniblow.ico"
BAD_ADDRESS = "Wrong destination account address checksum or wrong format."


class InfoBox(gui.infodialog.InfoDialog):
    def __init__(self, message, title, style, parent, block_modal=False):
        super().__init__(parent)
        self.is_modal = block_modal
        self.message = message
        self.SetTitle(title)
        HAND_CURSOR = wx.Cursor(wx.CURSOR_HAND)
        self.m_button_cpy.SetCursor(HAND_CURSOR)
        self.m_button_ok.SetCursor(HAND_CURSOR)
        self.m_textCtrl.SetBackgroundColour(self.GetBackgroundColour())
        self.m_textCtrl.SetValue(self.message)
        self.m_textCtrl.SelectNone()
        if self.is_modal:
            self.ShowModal()
        else:
            self.Show()

    def copy_text_dialog(self, event):
        event.Skip()
        if wx.TheClipboard.Open():
            wx.TheClipboard.Clear()
            wx.TheClipboard.SetData(wx.TextDataObject(self.message))
            wx.TheClipboard.Flush()
            wx.TheClipboard.Close()
        # else silent : no Access

    def close_info(self, event):
        if self.is_modal:
            self.EndModal(0)
        self.Destroy()


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


class HDsetting_panel(gui.maingui.HDPanel):
    def __init__(self, arg):
        super().__init__(arg)
        HAND_CURSOR = wx.Cursor(wx.CURSOR_HAND)
        self.m_butOK.SetCursor(HAND_CURSOR)
        self.m_butcancel.SetCursor(HAND_CURSOR)

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
        self.GetParent().EndModal(wx.ID_OK)

    def hd_cancel(self, event):
        event.Skip()
        self.GetParent().EndModal(wx.ID_CANCEL)


class app_option_panel(gui.maingui.OptionPanel):
    def __init__(self, arg):
        super().__init__(arg)
        HAND_CURSOR = wx.Cursor(wx.CURSOR_HAND)
        self.known_choice.SetCursor(HAND_CURSOR)
        self.m_but_paste.SetCursor(HAND_CURSOR)
        self.m_but_ok.SetCursor(HAND_CURSOR)
        self.m_but_cancel.SetCursor(HAND_CURSOR)

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
        self.GetParent().EndModal(wx.ID_OK)

    def pasteValue(self, event):
        """Paste the clipboard value in new_choice input field."""
        event.Skip()
        text_data = wx.TextDataObject()
        if wx.TheClipboard.Open():
            success = wx.TheClipboard.GetData(text_data)
            wx.TheClipboard.Close()
        if success:
            self.new_choice.SetValue(text_data.GetText())

    def cancelOption(self, event):
        event.Skip()
        self.GetParent().EndModal(wx.ID_CANCEL)

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


class UniblowApp(wx.App):
    def __init__(self, version):
        self.version = version
        super().__init__(redirect=False)
        self.Bind(wx.EVT_ACTIVATE_APP, self.OnActivate)
        self.dev_selected = None
        self.coin_selected = None
        self.current_chain = None

    def OnInit(self):
        self.HAND_CURSOR = wx.Cursor(wx.CURSOR_HAND)
        icon_path = file_path(ICON_FILE)
        wicon = wx.IconBundle(icon_path)
        self.gui_frame = gui.maingui.UniblowFrame(None)
        self.gui_frame.Bind(wx.EVT_CLOSE, self.OnClose)
        # if sys.platform.startswith("darwin"):
        # self.gui_frame.SetSize((996, 418))
        self.dev_panel = gui.maingui.DevicesPanel(self.gui_frame)
        self.gui_frame.SetIcons(wicon)

        self.dev_panel.d_btn01.SetBitmap(
            wx.Bitmap(file_path("gui/images/btns/dev_sw.png"), wx.BITMAP_TYPE_PNG)
        )
        self.dev_panel.d_btn02.SetBitmap(
            wx.Bitmap(file_path("gui/images/btns/dev_local.png"), wx.BITMAP_TYPE_PNG)
        )
        self.dev_panel.d_btn03.SetBitmap(
            wx.Bitmap(file_path("gui/images/btns/dev_ledger.png"), wx.BITMAP_TYPE_PNG)
        )
        self.dev_panel.d_btn04.SetBitmap(
            wx.Bitmap(file_path("gui/images/btns/dev_cryptnox.png"), wx.BITMAP_TYPE_PNG)
        )
        self.dev_panel.d_btn05.SetBitmap(
            wx.Bitmap(file_path("gui/images/btns/dev_pgp.png"), wx.BITMAP_TYPE_PNG)
        )

        self.dev_panel.d_btn01.Bind(wx.EVT_BUTTON, self.load_device)
        self.dev_panel.d_btn02.Bind(wx.EVT_BUTTON, self.load_device)
        self.dev_panel.d_btn03.Bind(wx.EVT_BUTTON, self.load_device)
        self.dev_panel.d_btn04.Bind(wx.EVT_BUTTON, self.load_device)
        self.dev_panel.d_btn05.Bind(wx.EVT_BUTTON, self.load_device)

        self.dev_panel.d_btn01.SetCursor(self.HAND_CURSOR)
        self.dev_panel.d_btn02.SetCursor(self.HAND_CURSOR)
        self.dev_panel.d_btn03.SetCursor(self.HAND_CURSOR)
        self.dev_panel.d_btn04.SetCursor(self.HAND_CURSOR)
        self.dev_panel.d_btn05.SetCursor(self.HAND_CURSOR)

        self.SetTopWindow(self.gui_frame)
        return True

    def start_wallet_panel(self):
        """Kill devices choice panel and start the wallet panel."""
        self.dev_panel.Destroy()
        self.gui_frame.SetSize((720, 420))
        self.gui_frame.Layout()
        self.gui_panel = gui.maingui.WalletPanel(self.gui_frame)
        self.gui_panel.copy_button.SetBitmap(
            wx.Bitmap(file_path("gui/images/btns/copy.png"), wx.BITMAP_TYPE_PNG)
        )
        self.gui_panel.hist_button.SetBitmap(
            wx.Bitmap(file_path("gui/images/btns/history.png"), wx.BITMAP_TYPE_PNG)
        )
        self.gui_panel.hist_button.SetCursor(self.HAND_CURSOR)
        self.gui_panel.copy_button.SetCursor(self.HAND_CURSOR)
        self.gui_panel.hist_button.Bind(wx.EVT_BUTTON, self.disp_history)
        self.gui_panel.copy_button.Bind(wx.EVT_BUTTON, self.copy_account)
        self.gui_panel.btn_send.SetBitmap(
            wx.Bitmap(file_path("gui/images/btns/send.png"), wx.BITMAP_TYPE_PNG)
        )
        self.gui_panel.network_choice.SetCursor(self.HAND_CURSOR)
        self.gui_panel.wallopt_choice.SetCursor(self.HAND_CURSOR)
        self.gui_panel.btn_send.SetCursor(self.HAND_CURSOR)
        self.gui_panel.btn_send.Bind(wx.EVT_BUTTON, self.open_send)
        self.gui_panel.btn_send.Hide()
        self.gui_panel.btn_chkaddr.SetBitmap(
            wx.Bitmap(file_path("gui/images/btns/addrchk.png"), wx.BITMAP_TYPE_PNG)
        )
        self.gui_panel.btn_chkaddr.SetCursor(self.HAND_CURSOR)
        self.gui_panel.btn_chkaddr.Bind(wx.EVT_BUTTON, self.check_wallet)

    def gowallet(self, sdevice):
        dev_info = self.dev_selected(sdevice)
        if isinstance(dev_info, list):
            self.start_wallet_panel()
            self.load_coins_list(dev_info)
            self.erase_info(True, True)
            if sdevice == 3:
                self.gui_panel.btn_chkaddr.Show()

    def load_device(self, evt):
        """Called from the device panel choice click."""
        if evt.GetEventObject() is self.dev_panel.d_btn01:
            # SeedWatcher
            sel_dev = 0
        elif evt.GetEventObject() is self.dev_panel.d_btn02:
            # LocalFiles
            sel_dev = 1
        elif evt.GetEventObject() is self.dev_panel.d_btn03:
            # Ledger
            sel_dev = 3
        elif evt.GetEventObject() is self.dev_panel.d_btn04:
            # Cryptnox
            sel_dev = 4
        elif evt.GetEventObject() is self.dev_panel.d_btn05:
            # OpenPGP
            sel_dev = 2
        else:
            raise Exception("Bad device button object")
        wx.CallAfter(self.gowallet, sel_dev)

    def load_coin(self, evt):
        """Called from the chain panel choice click."""
        sel_coinbtn = evt.GetEventObject()
        coinsbtn = sel_coinbtn.GetParent().GetChildren()
        for pos in range(len(coinsbtn)):
            if coinsbtn[pos] is sel_coinbtn:
                coin_name = self.coins_list[pos]
                if coin_name != self.current_chain:
                    sel_coinbtn.SetBackgroundColour(wx.Colour(0x57, 0x46, 0xCC))
                    self.gui_panel.scrolled_coins.Disable()
                    self.current_chain = coin_name
                    wx.CallAfter(self.coin_selected, coin_name)
            else:
                coinsbtn[pos].SetBackgroundColour(wx.Colour(248, 250, 252))

    def deactivate_option_buttons(self):
        self.gui_panel.but_evt1.SetBitmap(wx.NullBitmap)
        self.gui_panel.but_evt2.SetBitmap(wx.NullBitmap)
        self.gui_panel.but_evt1.Unbind(wx.EVT_BUTTON)
        self.gui_panel.but_evt2.Unbind(wx.EVT_BUTTON)
        self.gui_panel.Layout()

    def activate_option_buttons(self):
        self.gui_panel.but_evt1.SetBitmap(
            wx.Bitmap(file_path("gui/images/btns/tokens.png"), wx.BITMAP_TYPE_PNG)
        )
        self.gui_panel.but_evt2.SetBitmap(
            wx.Bitmap(file_path("gui/images/btns/wc.png"), wx.BITMAP_TYPE_PNG)
        )
        self.gui_panel.but_evt1.SetCursor(self.HAND_CURSOR)
        self.gui_panel.but_evt2.SetCursor(self.HAND_CURSOR)
        self.gui_panel.Layout()

    def disable_send(self, msg=""):
        self.gui_panel.btn_send.Hide()
        self.gui_panel.alt_text.SetLabel(msg)
        self.gui_panel.alt_text.Show()
        self.gui_panel.Layout()

    def enable_send(self):
        self.gui_panel.alt_text.Hide()
        self.gui_panel.alt_text.SetLabel("")
        self.gui_panel.btn_send.Show()
        self.gui_panel.Layout()

    def BringWindowToFront(self):
        try:
            self.GetTopWindow().Raise()
        except Exception:
            pass

    def OnActivate(self, event):
        if event.GetActive() and sys.platform != "linux":
            self.BringWindowToFront()
        event.Skip()

    def OnClose(self, event):
        if hasattr(self, "device"):
            del self.device
        if hasattr(self, "wallet"):
            del self.wallet
        event.Skip()

    def MacReopenApp(self):
        self.BringWindowToFront()

    def erase_info(self, reset=False, first_time=False):
        if hasattr(self, "balance_timer"):
            self.balance_timer.Stop()
        if hasattr(self, "wallet") and hasattr(self.wallet, "wc_timer"):
            self.wallet.wc_client.close()
            self.wallet.wc_timer.Stop()
            delattr(self.wallet, "wc_timer")
        self.gui_panel.hist_button.Disable()
        self.gui_panel.copy_button.Disable()
        self.disable_send()
        self.gui_panel.wallopt_label.Disable()
        self.gui_panel.wallopt_choice.Disable()
        self.gui_panel.balance_info.SetLabel("")
        if first_time:
            self.gui_panel.balance_info.SetLabel("👈  Select a chain")
        if reset:
            self.gui_panel.wallopt_choice.SetSelection(0)
        self.gui_panel.qrimg.SetBitmap(wx.Bitmap())
        if hasattr(self, "wallet"):
            del self.wallet
        self.gui_panel.account_addr.SetLabel("")
        self.gui_frame.Refresh()

    def clear_coin_selected(self):
        coin_btns = self.gui_panel.scrolled_coins.GetChildren()
        for btn in coin_btns:
            btn.SetBackgroundColour(wx.Colour(255, 255, 255, 0))

    def load_coins_list(self, coins_list):
        sizer = wx.BoxSizer(wx.VERTICAL)
        for coin in coins_list:
            coin_button = wx.BitmapButton(
                self.gui_panel.scrolled_coins,
                wx.ID_ANY,
                wx.NullBitmap,
                wx.DefaultPosition,
                wx.DefaultSize,
                wx.BU_AUTODRAW | wx.BORDER_NONE,
            )
            img = (
                wx.Image(file_path(f"gui/images/icons/{coin.lower()}.png"), wx.BITMAP_TYPE_PNG)
                .Rescale(32, 32)
                .Resize(wx.Size(42, 36), wx.Point(5, 2), red=-1, green=-1, blue=-1)
            )
            bmp = wx.Bitmap(img)
            coin_button.SetBackgroundColour(wx.Colour(248, 250, 252))
            coin_button.SetBitmap(bmp)
            coin_button.SetCursor(self.HAND_CURSOR)
            coin_button.Bind(wx.EVT_BUTTON, self.load_coin)
            sizer.Add(coin_button, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.BOTTOM | wx.TOP, 3)
        self.coins_list = coins_list
        self.gui_panel.scrolled_coins.SetSizer(sizer)
        self.gui_panel.scrolled_coins.Layout()
        self.gui_panel.Layout()
        self.gui_frame.Layout()

    def callback_send(self, status, address, amount_str, sel_fee=1):
        self.gui_panel.Enable()
        if status != "OK":
            self.send_dialog.Destroy()
            return
        if not self.gui_panel.btn_send.IsShown():
            self.send_dialog.Destroy()
            return
        if not hasattr(self, "wallet"):
            self.send_dialog.Destroy()
            return
        self.gui_panel.Disable()
        if not self.wallet.check_address(address):
            self.warn_modal(BAD_ADDRESS, parent=self.send_dialog)
            return
        if len(amount_str) <= 0:
            self.warn_modal("Input an amount value to transfer.", parent=self.send_dialog)
            return
        if amount_str[0] == "-":
            self.warn_modal("Amount input must be positive or null.", parent=self.send_dialog)
            return
        try:
            if amount_str != "ALL":
                float(amount_str)
        except ValueError:
            self.warn_modal("Unvalid amount input", parent=self.send_dialog)
            return
        self.send_dialog.Destroy()
        self.transfer(address, amount_str, sel_fee)

    def open_send(self, evt):
        self.send_dialog = SendModal(self.gui_panel, self.wallet, self.callback_send)
        self.gui_panel.Disable()
        self.send_dialog.Show()

    def copy_result(self, restxt):
        self.gui_panel.copy_status.SetLabel(restxt)
        if restxt != "":
            wx.CallLater(1800, self.copy_result, "")

    def copy_account(self, ev):
        if not hasattr(self, "wallet"):
            self.copy_result("No wallet")
            return
        try:
            if wx.TheClipboard.IsOpened() or wx.TheClipboard.Open():
                wx.TheClipboard.Clear()
                addr = self.gui_panel.account_addr.GetLabel()
                wx.TheClipboard.SetData(wx.TextDataObject(addr))
                wx.TheClipboard.Flush()
                wx.TheClipboard.Close()
                self.copy_result("Copied")
            else:
                self.copy_result("No Access")
        except Exception:
            self.copy_result("Error")

    def disp_history(self, ev):
        hist_url = self.wallet.history()
        if hist_url:
            show_history(hist_url)

    def warn_modal(self, warning_text, modal=False, parent=None):
        if parent is None:
            parent = self.gui_frame
        InfoBox(warning_text, "Error", wx.OK | wx.ICON_WARNING, parent, block_modal=modal)

    def info_modal(self, title, info_text):
        InfoBox(info_text, title, wx.OK | wx.ICON_INFORMATION, self.gui_frame)

    def get_password(self, device_nam, input_message):
        pwd_dialog = wx.PasswordEntryDialog(
            self.gui_frame,
            input_message,
            caption=f"{device_nam} wallet PIN/password",
            defaultValue="",
            pos=wx.DefaultPosition,
            parent=self.gui_frame,
        )
        if pwd_dialog.ShowModal() == wx.ID_OK:
            passval = pwd_dialog.GetValue()
            return passval

    def get_option(self, network_id, input_value, preset_values):
        option_dialog = gui.maingui.OptionDialog(self.gui_frame)
        option_panel = app_option_panel(option_dialog)
        option_panel.SetTitle(f"Wallet settings : {input_value} selection")
        option_panel.SetPresetLabel(f"preset {input_value}")
        option_panel.SetCustomLabel(f"input a {input_value}")
        if preset_values:
            option_panel.SetPresetValues(preset_values[network_id])
        else:
            option_panel.HidePreset()
        if option_dialog.ShowModal() == wx.ID_OK:
            optval = option_panel.GetValue()
            return optval

    def add_wallet_types(self, wallets_types):
        self.gui_panel.wallopt_choice.Clear()
        for wtype in wallets_types:
            if wtype not in ["ERC20", "WalletConnect"]:
                self.gui_panel.wallopt_choice.Append(wtype)

    def hd_setup(self, proposal):
        """Call the HD device option window."""
        self.gui_hdframe = gui.maingui.HDDialog(self.gui_frame)
        self.gui_hdpanel = HDsetting_panel(self.gui_hdframe)
        if proposal:
            # LocalFile wallet init setup
            self.gui_hdpanel.GOOD_BMP = wx.Bitmap(file_path("gui/images/good.bmp"))
            self.gui_hdpanel.BAD_BMP = wx.Bitmap(file_path("gui/images/bad.bmp"))
            self.gui_hdpanel.m_bitmapHDwl.SetBitmap(self.gui_hdpanel.BAD_BMP)
            self.gui_hdpanel.m_bitmapHDcs.SetBitmap(self.gui_hdpanel.BAD_BMP)
            self.gui_hdpanel.m_checkBox_secboost.SetCursor(self.HAND_CURSOR)
            self.gui_hdpanel.m_textCtrl_mnemo.SetValue(proposal)
            self.gui_hdpanel.m_usertxt.SetLabel(
                "Validate this first proposal,\n"
                "or insert your mnemonic and settings to import\n"
                "an existing HD wallet."
            )
        else:
            # hardware wallet options
            self.gui_hdframe.SetTitle("Open hardware wallet options")
            self.gui_hdpanel.title_text.SetLabel("Hardware wallet account options")
            self.gui_hdpanel.m_textwl.Destroy()
            self.gui_hdpanel.m_textcs.Destroy()
            self.gui_hdpanel.m_textCtrl_mnemo.Destroy()
            self.gui_hdpanel.m_bwptxt.Destroy()
            self.gui_hdpanel.m_textCtrl_pwd.Destroy()
            self.gui_hdpanel.m_checkBox_secboost.Destroy()
            self.gui_hdpanel.m_usertxt.SetLabel("Choose account and index for the key to use.")
            self.gui_hdframe.SetSize(480, 320)
        self.gui_hdpanel.m_butOK.SetCursor(self.HAND_CURSOR)
        self.gui_hdpanel.m_butcancel.SetCursor(self.HAND_CURSOR)
        ret = self.gui_hdframe.ShowModal()
        if ret == wx.ID_OK:
            wallet_settings = self.gui_hdpanel.hd_wallet_settings
            # Removal of stored settings
            self.gui_hdframe.DestroyChildren()
            self.gui_hdframe.Destroy()
            del self.gui_hdframe
            return wallet_settings
        else:
            return None

    def end_checkwallet(self, modal, result):
        wx.MilliSleep(200)
        modal.Update(100, "done")
        wx.MilliSleep(200)
        if not result:
            self.warn_modal("The address verification was rejected on the Ledger.")

    def check_device_address(self, pm):
        try:
            self.device.get_public_key(partial(self.end_checkwallet, pm))
        except Exception as exc:
            pm.Update(100, "failure")
            wx.MilliSleep(200)
            wx.CallAfter(self.device_error, exc)

    def check_wallet(self, evt):
        evt.Skip()
        if not hasattr(self, "wallet"):
            return
        progress_modal = wx.ProgressDialog(
            "",
            "",
            style=wx.PD_APP_MODAL | wx.PD_AUTO_HIDE | wx.PD_SMOOTH,
            parent=self.gui_frame,
        )
        wx.MilliSleep(250)
        wait_msg = "Verify the address on the Ledger screen.\n"
        wait_msg += self.wallet.get_account()
        progress_modal.Update(50, wait_msg)
        wx.MilliSleep(250)
        wx.CallAfter(self.check_device_address, progress_modal)

    def device_error(self, exc):
        # app.gui_panel.coins_choice.Disable()
        # app.gui_panel.coins_choice.SetSelection(0)
        # app.gui_panel.network_choice.Clear()
        # app.gui_panel.network_choice.Disable()
        # app.gui_panel.wallopt_choice.Clear()
        # app.gui_panel.wallopt_choice.Disable()
        # # app.gui_panel.devices_choice.SetSelection(0)
        # # app.gui_panel.btn_chkaddr.Hide()

        # What can we do? Back to device panel ?
        # self.erase_info(True)
        logger.error("Error with device : %s", str(exc), exc_info=exc, stack_info=True)
        self.warn_modal(str(exc))
        return
