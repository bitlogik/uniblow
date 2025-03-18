# -*- coding: utf8 -*-

# UNIBLOW app
# Copyright (C) 2021-2024 BitLogiK

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
from locale import setlocale, LC_ALL
from logging import getLogger
import sys
import os.path
from os import environ

import wx

import gui.maingui
import gui.infodialog
from gui.utils import file_path, show_history, icon_file
from gui.send_frame import SendModal
from gui.qrframe import QRFrame
from gui.fiat_price import PriceAPI
from version import VERSION

from cryptolib.HDwallet import bip39_is_checksum_valid


logger = getLogger(__name__)


BAD_ADDRESS = (
    "Wrong destination account address checksum, "
    "wrong format, or non-registered domain. "
    "Check the destination input."
)
BLANK_ADDR = " " * 65


def attach_tt(elt, txt):
    if elt.GetToolTip() is None:
        ttc = wx.ToolTip(txt)
        ttc.SetDelay(0)
        elt.SetToolTip(ttc)

        def remove_tt():
            ttc.SetTip("")
            elt.UnsetToolTip()

        wx.CallLater(1200, remove_tt)


def isBitmapButton(elt):
    return isinstance(elt, wx.BitmapButton)


def scaleSize(frame, sz):
    """Scale frame size depending of scaling factor."""
    if not hasattr(frame, "GetDPIScaleFactor"):
        return sz
    scal_fact = 1
    if frame.GetDPIScaleFactor() > 1.25:
        scal_fact = 1.1
    if frame.GetDPIScaleFactor() > 1.5:
        scal_fact = 1.25
    return (int(sz[0] * scal_fact), int(sz[1] * scal_fact))


def resize(frame, new_size):
    scaled_sz = scaleSize(frame, new_size)
    frame.SetMinSize(scaled_sz)
    frame.SetSize(scaled_sz)


class InfoBox(gui.infodialog.InfoDialog):
    def __init__(self, message, title, style, parent, block_modal=False):
        super().__init__(parent)
        self.is_modal = block_modal
        self.message = message
        self.SetTitle(title)
        self.panel = gui.infodialog.InfoPanel(self)
        HAND_CURSOR = wx.Cursor(wx.CURSOR_HAND)
        self.panel.m_button_cpy.SetCursor(HAND_CURSOR)
        self.panel.m_button_ok.SetCursor(HAND_CURSOR)
        self.panel.m_button_ok.Bind(wx.EVT_BUTTON, self.close_info)
        self.panel.m_button_cpy.Bind(wx.EVT_BUTTON, self.copy_text_dialog)
        self.panel.m_textCtrl.SetBackgroundColour(self.GetBackgroundColour())
        self.panel.m_textCtrl.SetValue(self.message)
        self.panel.m_textCtrl.SelectNone()
        if self.is_modal:
            self.Layout()
            self.ShowModal()
        else:
            self.Show()
            self.Layout()

    def copy_text_dialog(self, event):
        event.Skip()
        if wx.TheClipboard.IsOpened() or wx.TheClipboard.Open():
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
        self.m_butCancel.SetCursor(HAND_CURSOR)
        self.m_butOK.SetBitmap(wx.Bitmap(file_path("gui/images/btns/ok.png"), wx.BITMAP_TYPE_PNG))
        self.m_butCancel.SetBitmap(
            wx.Bitmap(file_path("gui/images/btns/cancel.png"), wx.BITMAP_TYPE_PNG)
        )

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
        self.m_but_paste.SetBitmap(
            wx.Bitmap(file_path("gui/images/btns/paste.png"), wx.BITMAP_TYPE_PNG)
        )
        self.m_but_ok.SetBitmap(wx.Bitmap(file_path("gui/images/btns/ok.png"), wx.BITMAP_TYPE_PNG))
        self.m_but_cancel.SetBitmap(
            wx.Bitmap(file_path("gui/images/btns/cancel.png"), wx.BITMAP_TYPE_PNG)
        )
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

    def onSearch(self, event):
        event.Skip()
        search = str(self.search_preset.GetValue())
        if search:
            self.search_preset.ShowCancelButton(True)
            filt_values = dict(
                filter(lambda val: search.lower() in val[0].lower(), self.full_options.items())
            )
            self.known_choice.Clear()
            self.known_choice.Append(f"> Select preset filtered with {search}")
            self.preset_values = filt_values
            for preset_txt in filt_values.keys():
                self.known_choice.Append(preset_txt)
            if len(filt_values) == 1:
                self.known_choice.SetSelection(1)
            elif len(filt_values) == 0:
                self.known_choice.Clear()
                self.known_choice.Append(f"No preset found for {search}")
                self.known_choice.SetSelection(0)
            else:
                self.known_choice.SetSelection(0)
        else:
            self.search_preset.ShowCancelButton(False)
            self.SetPresetValues(self.full_options)

    def pasteValue(self, event):
        """Paste the clipboard value in new_choice input field."""
        event.Skip()
        text_data = wx.TextDataObject()
        if wx.TheClipboard.IsOpened() or wx.TheClipboard.Open():
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
        self.search_preset.Hide()
        self.search_preset.ShowCancelButton(False)
        self.preset_text.Hide()
        self.known_choice.Hide()
        self.m_staticTextor.Hide()

    def SetPresetLabel(self, text):
        self.preset_label = text
        self.preset_text.SetLabelText(self.preset_label)

    def SetPresetValues(self, values):
        self.full_options = values
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
    def __init__(self, devices, coinclasses):
        self.devices = devices
        self.open_devices_sz = None
        super().__init__(redirect=False)
        self.Bind(wx.EVT_ACTIVATE_APP, self.OnActivate)
        self.coin_classes = coinclasses
        self.dev_selected = None
        self.coin_selected = None
        self.current_chain = ""

    def OnInit(self):
        self.HAND_CURSOR = wx.Cursor(wx.CURSOR_HAND)
        wicon = wx.IconBundle(icon_file)
        self.gui_frame = gui.maingui.UniblowFrame(None)
        self.gui_frame.swrun = False
        self.gui_frame.Bind(wx.EVT_CLOSE, self.OnClose)
        self.gui_frame.SetIcons(wicon)
        self.open_devices_panel()
        self.SetTopWindow(self.gui_frame)
        self.gui_frame.SetLabel(f"  Uniblow  -  {VERSION}")
        self.gui_frame.Show()
        return True

    def InitLocale(self):
        if sys.platform.startswith("win") and sys.version_info > (3, 8):
            setlocale(LC_ALL, "C")

    def open_devices_panel(self):
        self.gui_frame.swrun = False
        self.dev_panel = gui.maingui.DevicesPanel(self.gui_frame)
        logo = wx.Image(file_path("gui/images/logo.png"), wx.BITMAP_TYPE_PNG)
        logo.Rescale(64, 64)
        self.dev_panel.Layout()
        self.dev_panel.bmp_logo.SetBitmap(logo.ConvertToBitmap())
        for dev_idx, device in enumerate(self.devices, start=1):
            dbtn = getattr(self.dev_panel, f"d_btn{dev_idx:02d}")
            dbtn.SetBitmap(
                wx.Bitmap(
                    file_path(f"gui/images/btns/dev_{device.lower()}.png"), wx.BITMAP_TYPE_PNG
                )
            )
            dbtn.Bind(wx.EVT_BUTTON, self.load_device)
            dbtn.SetCursor(self.HAND_CURSOR)
        if sys.platform.startswith("darwin"):
            self.dev_panel.m_staticText1.SetFont(wx.Font(wx.FontInfo(26)))
        self.dev_panel.Layout()
        resize(self.gui_frame, (500, 468))
        self.gui_frame.Layout()

    def start_wallet_panel(self):
        """Kill devices choice panel and start the wallet panel."""
        self.dev_panel.Destroy()
        resize(self.gui_frame, (820, 475))
        self.gui_frame.Layout()
        self.gui_panel = gui.maingui.WalletPanel(self.gui_frame)
        self.gui_panel.copy_button.SetBitmap(
            wx.Bitmap(file_path("gui/images/btns/copy.png"), wx.BITMAP_TYPE_PNG)
        )
        self.gui_panel.qr_button.SetBitmap(
            wx.Bitmap(file_path("gui/images/btns/qr.png"), wx.BITMAP_TYPE_PNG)
        )
        self.gui_panel.hist_button.SetBitmap(
            wx.Bitmap(file_path("gui/images/btns/history.png"), wx.BITMAP_TYPE_PNG)
        )
        tt_hist = wx.ToolTip("Open in a block explorer")
        tt_hist.SetDelay(400)
        self.gui_panel.hist_button.SetToolTip(tt_hist)
        self.gui_panel.m_but_changedevice.SetBitmap(
            wx.Bitmap(file_path("gui/images/btns/chdev.png"), wx.BITMAP_TYPE_PNG)
        )
        self.gui_panel.hist_button.SetCursor(self.HAND_CURSOR)
        self.gui_panel.copy_button.SetCursor(self.HAND_CURSOR)
        self.gui_panel.qr_button.SetCursor(self.HAND_CURSOR)
        self.gui_panel.m_but_changedevice.SetCursor(self.HAND_CURSOR)
        self.gui_panel.hist_button.Bind(wx.EVT_BUTTON, self.disp_history)
        self.gui_panel.qr_button.Bind(wx.EVT_BUTTON, self.qr_open)
        self.gui_panel.copy_button.Bind(wx.EVT_BUTTON, self.copy_account)
        self.gui_panel.m_but_changedevice.Bind(wx.EVT_BUTTON, self.change_device)
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
        self.gui_panel.wallopt_label.Disable()
        self.gui_panel.wallopt_choice.Disable()
        self.gui_panel.network_choice.Disable()
        if sys.platform.startswith("darwin"):
            self.gui_panel.balance_info.SetFont(wx.Font(wx.FontInfo(24)))
            self.gui_panel.balance_small.SetFont(wx.Font(wx.FontInfo(15)))
            self.gui_panel.balance_unit.SetFont(wx.Font(wx.FontInfo(24)))
            self.gui_panel.txt_fiat.SetFont(wx.Font(wx.FontInfo(15)))
            self.gui_panel.account_addr.SetFont(wx.Font(wx.FontInfo(18)))
        self.gui_panel.account_addr.SetLabel(BLANK_ADDR)
        self.gui_frame.Layout()

    def gowallet(self, sdevice):
        dev_info = self.dev_selected(sdevice)
        if isinstance(dev_info, list):
            self.start_wallet_panel()
            self.load_coins_list(dev_info)
            self.erase_info(True, True)
            if sdevice == 2:  # Ledger
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
            sel_dev = 2
        elif evt.GetEventObject() is self.dev_panel.d_btn04:
            # Cryptnox
            sel_dev = 3
        elif evt.GetEventObject() is self.dev_panel.d_btn05:
            # OpenPGP
            sel_dev = 4
        elif evt.GetEventObject() is self.dev_panel.d_btn06:
            # Satochip
            sel_dev = 5
        else:
            raise Exception("Bad device button object")
        wx.CallAfter(self.gowallet, sel_dev)

    def change_device(self, evt):
        if hasattr(self, "balance_timer"):
            self.balance_timer.Stop()
        if hasattr(self, "device"):
            if hasattr(self.device, "disconnect"):
                self.device.disconnect()
            del self.device
        self.gui_panel.Destroy()
        self.current_chain = ""
        del self.gui_panel
        self.open_devices_panel()

    def load_coin(self, evt):
        """Called from the chain panel choice click."""
        sel_coinbtn = evt.GetEventObject()
        siblings = sel_coinbtn.GetParent().GetChildren()
        coinsbtn = list(filter(isBitmapButton, siblings))
        for pos in range(len(coinsbtn)):
            if coinsbtn[pos] is sel_coinbtn:
                coin_name = self.coins_list[pos]
                if coin_name != self.current_chain:
                    sel_coinbtn.SetBackgroundColour(wx.Colour(113, 110, 234))
                    self.gui_panel.scrolled_coins.Disable()
                    self.current_chain = coin_name
                    wx.CallAfter(self.coin_selected, coin_name)
            else:
                coinsbtn[pos].SetBackgroundColour(wx.Colour(248, 250, 252))

    def deactivate_option_buttons(self):
        self.gui_panel.but_opt_tok.SetBitmap(
            wx.Bitmap(file_path("gui/images/btns/blankopt.png"), wx.BITMAP_TYPE_PNG)
        )
        self.gui_panel.but_opt_tok.SetCursor(wx.NullCursor)
        self.gui_panel.but_opt_nft.SetCursor(wx.NullCursor)
        self.gui_panel.but_opt_nft.Hide()
        self.gui_panel.but_opt_wc.Hide()
        self.gui_panel.but_opt_tok.Unbind(wx.EVT_BUTTON)
        self.gui_panel.but_opt_nft.Unbind(wx.EVT_BUTTON)
        self.gui_panel.but_opt_wc.Unbind(wx.EVT_BUTTON)
        self.gui_panel.Layout()

    def activate_option_buttons(self):
        self.gui_panel.but_opt_tok.SetBitmap(
            wx.Bitmap(file_path("gui/images/btns/tokens.png"), wx.BITMAP_TYPE_PNG)
        )
        self.gui_panel.but_opt_nft.SetBitmap(
            wx.Bitmap(file_path("gui/images/btns/nfts.png"), wx.BITMAP_TYPE_PNG)
        )
        self.gui_panel.but_opt_wc.SetBitmap(
            wx.Bitmap(file_path("gui/images/btns/wc.png"), wx.BITMAP_TYPE_PNG)
        )
        self.gui_panel.but_opt_nft.Show()
        self.gui_panel.but_opt_wc.Show()
        self.gui_panel.but_opt_tok.SetCursor(self.HAND_CURSOR)
        self.gui_panel.but_opt_nft.SetCursor(self.HAND_CURSOR)
        self.gui_panel.but_opt_wc.SetCursor(self.HAND_CURSOR)
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
            if self.gui_frame.swrun:
                self.sw_frame.Raise()
            else:
                self.GetTopWindow().Raise()
        except Exception:
            pass

    def OnActivate(self, event):
        if event.GetActive() and sys.platform != "linux":
            self.BringWindowToFront()
        event.Skip()

    def OnClose(self, event):
        if hasattr(self, "balance_timer"):
            self.balance_timer.Stop()
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
        self.gui_panel.balance_small.SetLabel("")
        self.gui_panel.balance_unit.SetLabel("")
        self.gui_panel.txt_fiat.SetLabel("$ 0")
        self.gui_panel.fiat_panel.Hide()
        if hasattr(self.gui_panel, "fiat_price"):
            del self.gui_panel.fiat_price
        if first_time:
            self.gui_panel.img_arrsel.Show()
            self.gui_panel.img_arrsel.SetBitmap(
                wx.Bitmap(file_path("gui/images/arrsel.png"), wx.BITMAP_TYPE_PNG)
            )
            self.gui_panel.balance_info.SetLabel("Select a chain")
        else:
            self.gui_panel.img_arrsel.Hide()
        if reset:
            self.gui_panel.wallopt_choice.SetSelection(0)
        self.gui_panel.qr_button.Disable()
        if hasattr(self, "wallet"):
            del self.wallet
        self.gui_panel.account_addr.SetLabel(BLANK_ADDR)
        self.gui_frame.Refresh()
        self.gui_frame.Layout()

    def clear_coin_selected(self):
        self.current_chain = ""
        coin_btns = self.gui_panel.scrolled_coins.GetChildren()
        for btn in coin_btns:
            btn.SetBackgroundColour(wx.Colour(248, 250, 252))
        self.erase_info(False, True)

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
            img = wx.Image(file_path(f"gui/images/icons/{coin.lower()}.png"), wx.BITMAP_TYPE_PNG)
            img.Rescale(48, 48, wx.IMAGE_QUALITY_BILINEAR)
            img.Resize(wx.Size(58, 56), wx.Point(5, 4), red=-1, green=-1, blue=-1)
            coin_button.SetBackgroundColour(wx.Colour(248, 250, 252))
            coin_button.SetBitmap(wx.Bitmap(img))
            coin_button.SetCursor(self.HAND_CURSOR)
            coin_button.Bind(wx.EVT_BUTTON, self.load_coin)
            sizer.Add(coin_button, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.BOTTOM | wx.TOP, 3)
        self.coins_list = coins_list
        self.gui_panel.scrolled_coins.SetSizer(sizer)
        self.gui_panel.scrolled_coins.Layout()
        self.gui_panel.Layout()
        self.gui_frame.Layout()

    def confirm_tx(self, to_addr, amount, domain):
        if domain:
            to_addr += f" ({domain})"
        conf_txt = "Confirm this transaction ?\n" f"{amount} {self.wallet.coin} to {to_addr}"
        confirm_tx_modal = wx.MessageDialog(
            self.gui_frame,
            conf_txt,
            "Confirmation",
            wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION | wx.STAY_ON_TOP | wx.CENTER,
            wx.DefaultPosition,
        )
        return confirm_tx_modal.ShowModal()

    def callback_send(self, status, address, amount_str, sel_fee=1, domain=""):
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
                if float(amount_str) <= 0:
                    self.warn_modal("Input a positive amount value.", parent=self.send_dialog)
                    return
        except ValueError:
            self.warn_modal("Unvalid amount input", parent=self.send_dialog)
            return
        self.send_dialog.Disable()
        conf = self.confirm_tx(address, amount_str, domain)
        if conf == wx.ID_YES:
            self.gui_panel.Enable()
            self.send_dialog.Destroy()
            self.transfer(address, amount_str, sel_fee)
            return
        self.send_dialog.Enable()

    def open_send(self, evt):
        cansend_all = True
        if not (
            (
                hasattr(self.wallet, "eth")
                and self.wallet.eth.contract
                and self.wallet.eth.is_fungible
            )
            or (self.current_chain == "TRX" and self.wallet.contract)
        ):
            # Native : disable SendAll for layer2 chains
            cansend_all = not getattr(self.wallet, "sendall_notallowed", False)

        self.send_dialog = SendModal(
            self.gui_panel,
            self.wallet.coin,
            self.wallet.check_address,
            cansend_all,
            self.callback_send,
        )
        resize(self.send_dialog, (520, 432))
        self.gui_panel.Disable()
        self.send_dialog.Show()

    def qr_open(self, evt):
        addr = self.wallet.get_account()
        self.gui_panel.qr_button.Disable()
        QRFrame(self.gui_frame, self.wallet.coin, addr, self.gui_panel.qr_button)

    def copy_account(self, ev):
        if not hasattr(self, "wallet"):
            attach_tt(self.gui_panel.copy_button, "No wallet")
            return
        try:
            if wx.TheClipboard.IsOpened() or wx.TheClipboard.Open():
                wx.TheClipboard.Clear()
                addr = self.gui_panel.account_addr.GetLabel()
                wx.TheClipboard.SetData(wx.TextDataObject(addr))
                wx.TheClipboard.Flush()
                wx.TheClipboard.Close()
                attach_tt(self.gui_panel.copy_button, "Address copied")
            else:
                attach_tt(self.gui_panel.copy_button, "No Access")
        except Exception:
            attach_tt(self.gui_panel.copy_button, "Error")

    def disp_history(self, ev):
        hist_url = self.wallet.history()
        if hist_url:
            show_history(hist_url)

    def warn_modal(self, warning_text, modal=True, parent=None):
        if parent is None:
            parent = self.gui_frame
        InfoBox(warning_text, "Error", wx.OK | wx.ICON_WARNING, parent, block_modal=modal)

    def info_modal(self, title, info_text):
        InfoBox(info_text, title, wx.OK | wx.ICON_INFORMATION, self.gui_frame, True)

    def get_password(self, device_nam, input_message):
        pwd_dialog = wx.PasswordEntryDialog(
            self.gui_frame,
            input_message,
            caption=f"{device_nam} wallet PIN/password",
            defaultValue="",
            pos=wx.DefaultPosition,
        )
        if pwd_dialog.ShowModal() == wx.ID_OK:
            passval = pwd_dialog.GetValue()
            return passval

    def get_option(self, network_id, input_value, preset_values):
        option_dialog = gui.maingui.OptionDialog(self.gui_frame)
        resize(option_dialog, (455, 400))
        option_panel = app_option_panel(option_dialog)
        option_panel.SetTitle(f"Wallet settings : {input_value} selection")
        option_panel.SetPresetLabel(f"preset {input_value}")
        inp_txt = ("an " if input_value.lower().startswith("e") else "a ") + input_value
        option_panel.SetCustomLabel(f"Input {inp_txt}")
        if preset_values and len(preset_values[network_id]) > 0:
            option_panel.SetPresetValues(preset_values[network_id])
        else:
            option_panel.HidePreset()
        if option_dialog.ShowModal() == wx.ID_OK:
            optval = option_panel.GetValue()
            return optval

    def add_wallet_types(self, wallets_types):
        self.gui_panel.wallopt_choice.Clear()
        for wtype in wallets_types:
            if wtype not in ["ERC20", "WalletConnect", "NFT"]:
                self.gui_panel.wallopt_choice.Append(wtype)

    def hd_setup(self, proposal):
        """Call the HD device option window."""
        self.gui_hdframe = gui.maingui.HDDialog(self.gui_frame)
        self.gui_hdpanel = HDsetting_panel(self.gui_hdframe)
        if proposal:
            # LocalFile wallet init setup
            self.gui_hdpanel.GOOD_BMP = wx.Bitmap(file_path("gui/images/good.png"))
            self.gui_hdpanel.BAD_BMP = wx.Bitmap(file_path("gui/images/bad.png"))
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
            resize(self.gui_hdframe, (580, 380))
        self.gui_hdpanel.m_butOK.SetCursor(self.HAND_CURSOR)
        self.gui_hdpanel.m_butCancel.SetCursor(self.HAND_CURSOR)
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

    def display_fiat(self, chain, net, balance, fiat_price):
        if not self.check_coin_consistency(chain, net):
            # User changed the coin or network the time of the get price
            return
        self.gui_panel.fiat_price = fiat_price
        self.gui_panel.fiat_panel.Show()
        self.gui_panel.txt_fiat.SetLabel(f"$ {balance * fiat_price:.2f}")
        self.gui_panel.Layout()

    def display_balance(self):
        logger.debug("Checking for wallet balance")
        if not hasattr(self, "wallet"):
            self.erase_info()
            return
        if not hasattr(self, "gui_panel"):
            # When device disconnected
            # and there's still a balance call pending
            return
        coinw = type(self.wallet)
        wall_net = self.gui_panel.network_choice.GetSelection()
        try:
            balance = self.wallet.get_balance()
        except Exception as exc:
            if hasattr(self, "balance_timer"):
                self.balance_timer.Stop()
            if hasattr(self, "wallet") and hasattr(self.wallet, "wc_timer"):
                self.wallet.wc_client.close()
                self.wallet.wc_timer.Stop()
                delattr(self.wallet, "wc_timer")
            self.gui_panel.hist_button.Disable()
            self.disable_send()
            self.deactivate_option_buttons()
            self.gui_panel.wallopt_label.Disable()
            self.gui_panel.balance_info.SetLabel(" -  offline  -")
            self.gui_panel.balance_small.SetLabel("")
            self.gui_panel.balance_unit.SetLabel("")
            self.gui_panel.txt_fiat.SetLabel("$ 0")
            self.gui_panel.fiat_panel.Hide()
            if hasattr(self.gui_panel, "fiat_price"):
                del self.gui_panel.fiat_price
            self.gui_frame.Refresh()
            self.gui_frame.Layout()
            err_msg = (
                f"Error when getting account balance.\nCheck your Internet connection.\n{str(exc)}"
            )
            logger.error("Error in display_balance : %s", err_msg, exc_info=exc, stack_info=True)
            self.warn_modal(err_msg)
            return
        if not self.check_coin_consistency(coinw, wall_net):
            # User changed the coin or network the time of the get balance
            return
        if not hasattr(self, "wallet"):
            return
        # special case for EOS
        if balance.startswith("No pubkey"):
            balance_num, balance_coin = balance, ""
        else:
            balance_num, balance_coin = balance.split(" ")[:2]
        if "." in balance_num:
            balance_int, balance_float = balance_num.split(".")
            balance_int += "."
        else:
            balance_int = balance_num
            balance_float = ""
        self.gui_panel.balance_info.SetLabel(f"{balance_int}{balance_float[:2]}")
        self.gui_panel.balance_small.SetLabel(f"{balance_float[2:]}")
        self.gui_panel.balance_unit.SetLabel(balance_coin)
        if (
            # No fund in the wallet
            balance_num not in ("0", "0.0")
            # EOS when register pubkey mode : disable sending
            and not balance_num.startswith("No pubkey")
            # WalletConnect : disable sending
            and not hasattr(self.wallet, "wc_timer")
        ):
            self.enable_send()
            cb_fiat = partial(self.display_fiat, coinw, wall_net, float(balance_num))
            # Read the coin price
            # if not testnet
            if self.gui_panel.network_choice.GetSelection() == 0 or (
                self.gui_panel.network_choice.GetSelection() == 1
                and (self.wallet.__class__.coin == "GLMR" or self.wallet.__class__.coin == "FTM")
            ):
                if hasattr(self.wallet, "eth"):
                    if self.wallet.eth.contract and self.wallet.eth.is_fungible:
                        PriceAPI(cb_fiat, self.wallet.eth.contract, self.current_chain)
                    if not self.wallet.eth.contract:
                        PriceAPI(cb_fiat, self.wallet.coin)
                elif self.current_chain == "TRX" and self.wallet.contract:
                    PriceAPI(cb_fiat, self.wallet.contract, self.current_chain)
                else:
                    PriceAPI(cb_fiat, self.wallet.coin)
        else:
            self.gui_panel.fiat_panel.Hide()
            self.disable_send()
        if hasattr(self, "wallet") and hasattr(self.wallet, "wc_timer"):
            # WalletConnect active
            self.disable_send("Use the connected dapp to transact")
        self.gui_panel.Refresh()
        self.gui_panel.Update()
        self.gui_panel.Layout()

    def device_error(self, exc):
        self.current_chain = ""
        if hasattr(self, "device"):
            del self.device
        if hasattr(self, "gui_panel"):
            # Back to device panel
            self.gui_panel.Destroy()
            del self.gui_panel
            self.open_devices_panel()
        logger.error("Error with device : %s", str(exc), exc_info=exc, stack_info=True)
        self.warn_modal(str(exc))
        return

    def check_coin_consistency(self, current_wallet=None, network_num=None):
        """Check if selected coin is the same as the current wallet class used."""
        # Designed to fix a race condition when the async data of a wallet
        # are displayed : address and balance.
        # Changing the coin selected could mix crypto info. So this terminates some
        # process path that are no longer valid.
        if hasattr(self, "wallet") and self.current_chain:
            if current_wallet is None:
                current_wallet = type(self.wallet)
            coin_class = self.coin_classes(self.current_chain)
            if coin_class is not current_wallet:
                return False
        if network_num is not None:
            if self.gui_panel.network_choice.IsEmpty():
                return
            net_sel = self.gui_panel.network_choice.GetSelection()
            if net_sel < 0:
                return False
            return net_sel == network_num
        return True

    def token_started(self):
        self.gui_panel.but_opt_tok.Unbind(wx.EVT_BUTTON)
        self.gui_panel.but_opt_nft.Unbind(wx.EVT_BUTTON)
        self.gui_panel.but_opt_tok.SetBitmap(
            wx.Bitmap(file_path("gui/images/btns/quit.png"), wx.BITMAP_TYPE_PNG)
        )
        self.gui_panel.but_opt_nft.Disable()
        self.gui_panel.but_opt_wc.Disable()
        return self.gui_panel.but_opt_tok

    def wc_started(self):
        self.gui_panel.but_opt_wc.Unbind(wx.EVT_BUTTON)
        self.gui_panel.but_opt_nft.Unbind(wx.EVT_BUTTON)
        self.gui_panel.but_opt_wc.SetBitmap(
            wx.Bitmap(file_path("gui/images/btns/endwc.png"), wx.BITMAP_TYPE_PNG)
        )
        self.gui_panel.but_opt_tok.Disable()
        self.gui_panel.but_opt_nft.Disable()
        self.gui_panel.but_opt_nft.Hide()
        return self.gui_panel.but_opt_wc
