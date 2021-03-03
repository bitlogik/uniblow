#!/usr/bin/python3
# -*- coding: utf8 -*-

# UNIBLOW  : a UNIversal BLOckchain Wallet
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
from io import BytesIO

import wx
import qrcode
import gui.app
from devices.BasicFile import BasicFile, pwdException
from version import VERSION

SUPPORTED_COINS = [
    "BTC",
    "ETH",
    # "EOS",
]

DEVICES = [
    "BasicFile",
]

FEES_PRORITY_TEXT = [
    "Economic fee",
    "Normal fee",
    "Faster fee",
]

DEFAULT_PASSWORD = "NoPasswd"

import wallets.BTCwallet
import wallets.ETHwallet


def get_coin_class(coin_name):
    return getattr(getattr(wallets, f"{coin_name}wallet"), f"{coin_name}_wallet")


class wallet:
    def __init__(self, coin, *options):
        self.coin = coin
        self.coin_wallet = get_coin_class(coin)(*options)

    def get_networks(self):
        return self.coin_wallet.get_networks()

    def get_account_types(self):
        return self.coin_wallet.get_account_types()

    def get_account(self):
        # Read address to fund the wallet
        return self.coin_wallet.get_account()

    def get_balance(self):
        # Get balance as string
        return self.coin_wallet.get_balance()

    def check_address(self, addr_str):
        # Check if address is valid
        return self.coin_wallet.check_address(addr_str)

    def history(self):
        # Get history as tx list
        return self.coin_wallet.history()

    def transfer(self, amount, to_account, fee_priority):
        # Transfer to pay x coin unit to an external account
        return self.coin_wallet.transfer(amount, to_account, fee_priority)

    def transfer_all(self, to_account, fee_priority):
        # Transfer all teh wallet amount to an external account
        return self.coin_wallet.transfer_all(to_account, fee_priority)


def display_balance():
    try:
        balance = app.wallet.get_balance()
    except IOError as exc:
        erase_info()
        err_msg = f"Network error when getting info.\nCheck your Internet connection.\n{str(exc)}"
        warn_modal(err_msg)
        if not getattr(sys, "frozen", False):
            # output the exception when dev environment
            raise exc
        return
    app.gui_panel.balance_info.SetLabel(balance)
    bal_str = balance.split(" ")[0]
    if bal_str != "0" and bal_str != "0.0":
        app.gui_panel.send_button.Enable()
        app.gui_panel.send_all.Enable()


def erase_info():
    if hasattr(app, "balance_timer"):
        app.balance_timer.Stop()
    app.gui_panel.send_all.Disable()
    app.gui_panel.send_button.Disable()
    app.gui_panel.network_choice.Disable()
    app.gui_panel.wallopt_choice.Disable()
    app.gui_panel.qrimg.SetBitmap(wx.Bitmap())
    if hasattr(app, "wallet"):
        delattr(app, "wallet")
    app.gui_panel.balance_info.SetLabel("")
    app.gui_panel.account_addr.SetLabel("")


class display_timer(wx.Timer):
    def __init__(self):
        wx.Timer.__init__(self)

    def Notify(self):
        display_balance()


def warn_modal(warning_text):
    wx.MessageBox(warning_text, "Error", wx.OK | wx.ICON_WARNING, app.gui_frame)


def get_password(newp="BadPass"):
    input_message = "Input BasicFile wallet password\n"
    if newp == "NewPass":
        input_message += "If blank a default password will be used."
    pwd_dialog = wx.PasswordEntryDialog(
        app.gui_frame,
        input_message,
        caption="BasicFile wallet password",
        defaultValue="",
        pos=wx.DefaultPosition,
    )
    if pwd_dialog.ShowModal() == wx.ID_OK:
        passval = pwd_dialog.GetValue()
        if passval == "":
            return DEFAULT_PASSWORD
        return passval


def confirm(to_addr, amount):
    conf_txt = f"Confirm this transaction ?\n{amount} {app.wallet.coin} to {to_addr}"
    confirm_modal = wx.MessageDialog(
        app.gui_frame,
        conf_txt,
        "Confirmation",
        wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION | wx.STAY_ON_TOP | wx.CENTER,
        wx.DefaultPosition,
    )
    return confirm_modal.ShowModal()


def tx_success(message):
    wx.MessageBox(message, "Transaction sent", wx.OK | wx.ICON_INFORMATION, app.gui_frame)


def copy_result(restxt):
    app.gui_panel.copy_status.SetLabel(restxt)
    if restxt != "":
        wx.CallLater(1800, copy_result, "")


def copy_account(ev):
    if not hasattr(app, "wallet"):
        copy_result("No wallet")
        return
    try:
        if wx.TheClipboard.Open():
            account_id = app.wallet.get_account()
            wx.TheClipboard.SetData(wx.TextDataObject(account_id))
            wx.TheClipboard.Close()
            copy_result("Copied")
        else:
            copy_result("No Access")
    except:
        copy_result("Error")


def device_selected(device):
    sel_device = device.GetInt()
    if sel_device > 0:
        # For now, only BasicFile device
        password_BasicFile = DEFAULT_PASSWORD
        i = 0
        while True:
            i += 1
            try:
                device_loaded = BasicFile(password_BasicFile, i)
                break
            except pwdException as exc:
                password_BasicFile = get_password(str(exc))
                if password_BasicFile is None:
                    app.gui_panel.devices_choice.SetSelection(0)
                    app.gui_panel.coins_choice.Disable()
                    return
            except Exception as exc:
                warn_modal(str(exc))
                if not getattr(sys, "frozen", False):
                    # output the exception when dev environment
                    raise exc
                app.gui_panel.devices_choice.SetSelection(0)
                app.gui_panel.coins_choice.Disable()
                return
        app.device = device_loaded
        if app.device.created:
            warn_modal(f"New {DEVICES[sel_device-1]} was successfully created.")
        app.gui_panel.coins_choice.Enable()
        app.gui_panel.coins_choice.Hide()
        app.gui_panel.coins_choice.ShowWithEffect(wx.SHOW_EFFECT_ROLL_TO_RIGHT, 750)
        app.gui_panel.coins_choice.SetFocus()
    else:
        app.gui_panel.devices_choice.SetSelection(0)
        app.gui_panel.coins_choice.SetSelection(0)
        app.gui_panel.coins_choice.Disable()
        app.gui_panel.network_choice.Clear()
        app.gui_panel.wallopt_choice.Clear()
        erase_info()


def set_coin(coin, network, wallet_type):
    fee_opt_sel = app.gui_panel.fee_slider.GetValue()
    app.gui_panel.fee_setting.SetLabel(FEES_PRORITY_TEXT[fee_opt_sel])
    try:
        app.wallet = wallet(coin, network, wallet_type, app.device)
        account_id = app.wallet.get_account()
    except Exception as exc:
        warn_modal(str(exc))
        if not getattr(sys, "frozen", False):
            # output the exception when dev environment
            raise exc
        return
    app.gui_panel.account_addr.SetValue(account_id)
    imgbuf = BytesIO()
    imgqr = qrcode.make(
        account_id,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=4,
        border=3,
    )
    imgqr.save(imgbuf, "PNG")
    imgbuf.seek(0)
    wxi = wx.Image(imgbuf, type=wx.BITMAP_TYPE_PNG)
    app.gui_panel.qrimg.SetScaleMode(wx.StaticBitmap.ScaleMode.Scale_None)  # or Scale_AspectFit
    app.gui_panel.qrimg.SetBitmap(wx.Bitmap(wxi))
    app.balance_timer = display_timer()
    display_balance()
    app.balance_timer.Start(5000)
    app.gui_frame.Refresh()
    app.gui_frame.Update()


def process_coin_select(coin, sel_network, sel_wallettype):
    app.gui_panel.network_choice.Enable()
    app.gui_panel.wallopt_choice.Enable()
    set_coin(coin, sel_network, sel_wallettype)


def coin_selected(coin_sel):
    app.gui_panel.network_choice.Clear()
    app.gui_panel.wallopt_choice.Clear()
    erase_info()
    if coin_sel.GetInt() > 0:
        coin_name = coin_sel.GetString()
        networks = get_coin_class(coin_name).get_networks()
        acc_types = get_coin_class(coin_name).get_account_types()
        for netw in networks:
            app.gui_panel.network_choice.Append(netw)
        for wtype in acc_types:
            app.gui_panel.wallopt_choice.Append(wtype)
        sele_network = 0
        sele_wttype = 0
        app.gui_panel.network_choice.SetSelection(sele_network)
        app.gui_panel.wallopt_choice.SetSelection(sele_wttype)
        wx.CallLater(180, process_coin_select, coin_name, sele_network, sele_wttype)


def net_selected(net_sel):
    erase_info()
    coin_sel = app.gui_panel.coins_choice.GetStringSelection()
    wtype_sel = app.gui_panel.wallopt_choice.GetSelection()
    wx.CallLater(180, process_coin_select, coin_sel, net_sel.GetInt(), wtype_sel)


def wtype_selected(wtype_sel):
    erase_info()
    coin_sel = app.gui_panel.coins_choice.GetStringSelection()
    net_sel = app.gui_panel.network_choice.GetSelection()
    wx.CallLater(180, process_coin_select, coin_sel, net_sel, wtype_sel.GetInt())


def fee_changed(feesel):
    app.gui_panel.fee_setting.SetLabel(FEES_PRORITY_TEXT[feesel.GetSelection()])


def send(ev):
    if not hasattr(app, "wallet"):
        return
    to = app.gui_panel.dest_addr.GetValue()
    if not app.wallet.check_address(to):
        warn_modal("Wrong destination account address format")
        return
    try:
        amount = float(app.gui_panel.amount.GetValue())
    except ValueError:
        warn_modal("Unvalid amount input")
        return
    conf = confirm(to, amount)
    if conf == wx.ID_YES:
        fee_opt = app.gui_panel.fee_slider.GetValue()
        try:
            tx_info = app.wallet.transfer(amount, to, fee_opt)
            tx_success(tx_info)
        except Exception as exc:
            warn_modal(str(exc))
            if not getattr(sys, "frozen", False):
                # output the exception when dev environment
                raise exc


def send_all(ev):
    if not hasattr(app, "wallet"):
        return
    to = app.gui_panel.dest_addr.GetValue()
    if not app.wallet.check_address(to):
        warn_modal("Wrong destination account address format")
        return
    conf = confirm(to, "ALL")
    if conf == wx.ID_YES:
        fee_opt = app.gui_panel.fee_slider.GetValue()
        try:
            tx_info = app.wallet.transfer_all(to, fee_opt)
            tx_success(tx_info)
        except Exception as exc:
            warn_modal(str(exc))
            if not getattr(sys, "frozen", False):
                # output the exception when dev environment
                raise exc


if __name__ == "__main__":
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(True)
    except:
        pass
    app = wx.App()

    gui.app.start_app(app, VERSION, SUPPORTED_COINS, DEVICES)

    app.gui_panel.devices_choice.Bind(wx.EVT_CHOICE, device_selected)
    app.gui_panel.coins_choice.Bind(wx.EVT_CHOICE, coin_selected)
    app.gui_panel.network_choice.Bind(wx.EVT_CHOICE, net_selected)
    app.gui_panel.wallopt_choice.Bind(wx.EVT_CHOICE, wtype_selected)
    app.gui_panel.send_button.Bind(wx.EVT_BUTTON, send)
    app.gui_panel.send_all.Bind(wx.EVT_BUTTON, send_all)
    app.gui_panel.amount.Bind(wx.EVT_TEXT_ENTER, send)
    app.gui_panel.copy_button.Bind(wx.EVT_BUTTON, copy_account)
    app.gui_panel.fee_slider.Bind(wx.EVT_SCROLL_CHANGED, fee_changed)

    app.MainLoop()
