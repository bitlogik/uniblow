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


import importlib
import sys
from io import BytesIO

import wx
import qrcode
import gui.app
from version import VERSION

SUPPORTED_COINS = [
    "BTC",
    "ETH",
    "LTC",
    "DOGE",
    "EOS",
    "XTZ",
]

DEVICES_LIST = [
    "BasicFile",
    "OpenPGP",
]

FEES_PRORITY_TEXT = [
    "Economic fee",
    "Normal fee",
    "Faster fee",
]

DEFAULT_PASSWORD = "NoPasswd"

GREEN_COLOR = wx.Colour(73, 172, 73)
RED_COLOR = wx.Colour(198, 60, 60)

wallets = {}
for coin_lib in SUPPORTED_COINS:
    wallets[f"{coin_lib}wallet"] = importlib.import_module(f"wallets.{coin_lib}wallet")


def get_coin_class(coin_name):
    return getattr(wallets[f"{coin_name}wallet"], f"{coin_name}_wallet")


devices = {}
for device_name in DEVICES_LIST:
    devices[device_name] = importlib.import_module(f"devices.{device_name}")


def get_device_class(device_name):
    global pwdException, NotinitException
    device_class = getattr(devices[device_name], device_name)
    if device_class.has_password:
        pwdException = getattr(devices[device_name], "pwdException")
    NotinitException = getattr(devices[device_name], "NotinitException")
    return device_class


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
    app.gui_panel.copy_button.Enable()
    bal_str = balance.split(" ")[0]
    if bal_str not in ("0", "0.0") and not bal_str.startswith("Register"):
        app.gui_panel.send_button.Enable()
        app.gui_panel.send_all.Enable()


def erase_info():
    if hasattr(app, "balance_timer"):
        app.balance_timer.Stop()
    paint_toaddr(wx.NullColour)
    app.gui_panel.copy_button.Disable()
    app.gui_panel.send_all.Disable()
    app.gui_panel.send_button.Disable()
    app.gui_panel.network_choice.Disable()
    app.gui_panel.wallopt_choice.Disable()
    app.gui_panel.qrimg.SetBitmap(wx.Bitmap())
    if hasattr(app, "wallet"):
        delattr(app, "wallet")
    app.gui_panel.balance_info.SetLabel("")
    app.gui_panel.account_addr.SetLabel("")
    app.gui_frame.Refresh()


class display_timer(wx.Timer):
    def __init__(self):
        wx.Timer.__init__(self)

    def Notify(self):
        display_balance()


def warn_modal(warning_text):
    gui.app.InfoBox(warning_text, "Error", wx.OK | wx.ICON_WARNING, app.gui_frame)


def info_modal(title, info_text):
    gui.app.InfoBox(info_text, title, wx.OK | wx.ICON_INFORMATION, app.gui_frame)


def get_password(device_name, input_message):
    pwd_dialog = wx.PasswordEntryDialog(
        app.gui_frame,
        input_message,
        caption=f"{device_name} wallet PIN/password",
        defaultValue="",
        pos=wx.DefaultPosition,
    )
    if pwd_dialog.ShowModal() == wx.ID_OK:
        passval = pwd_dialog.GetValue()
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
    info_modal("Transaction sent", message)


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
            wx.TheClipboard.Clear()
            account_id = app.wallet.get_account()
            wx.TheClipboard.SetData(wx.TextDataObject(account_id))
            wx.TheClipboard.Close()
            wx.TheClipboard.Flush()
            copy_result("Copied")
        else:
            copy_result("No Access")
    except Exception:
        copy_result("Error")


def close_device():
    if hasattr(app, "device"):
        del app.device


def device_selected(device):
    global DEFAULT_PASSWORD
    close_device()
    app.gui_panel.coins_choice.Disable()
    app.gui_panel.coins_choice.SetSelection(0)
    app.gui_panel.network_choice.Clear()
    app.gui_panel.wallopt_choice.Clear()
    erase_info()
    sel_device = device.GetInt()
    device_sel_name = DEVICES_LIST[sel_device - 1]
    if sel_device > 0:
        password_default = DEFAULT_PASSWORD
        the_device = get_device_class(device_sel_name)
        try:
            device_loaded = the_device()
        except Exception as exc:
            warn_modal(str(exc))
            app.gui_panel.devices_choice.SetSelection(0)
            if not getattr(sys, "frozen", False):
                # output the exception when dev environment
                raise exc
            return
        while True:
            try:
                pwdPIN = "password"
                if device_sel_name == "OpenPGP":
                    pwdPIN = "PIN1"
                if the_device.has_password:
                    device_loaded.open_account(password_default)
                else:
                    device_loaded.open_account()
                break
            except NotinitException as exc:
                if the_device.has_admin_password:
                    set_admin_message = f"Choose your admin PIN3 for the {device_sel_name} device\n"
                    set_admin_message += "If blank, a default admin PIN will be used."
                    admin_password = get_password(device_sel_name, set_admin_message)
                    if admin_password is None:
                        app.gui_panel.devices_choice.SetSelection(0)
                        return
                    if admin_password == "":
                        admin_password = DEFAULT_PASSWORD
                    if len(admin_password) < 8:
                        warn_modal("Admin password shall be at least 8 chars.")
                        app.gui_panel.devices_choice.SetSelection(0)
                        return
                if the_device.has_password:
                    inp_message = f"Choose your {pwdPIN} for the {device_sel_name} wallet\n"
                    inp_message += "If blank, a default PIN/password will be used."
                    password = get_password(device_sel_name, inp_message)
                    if password is None:
                        app.gui_panel.devices_choice.SetSelection(0)
                        return
                    if password == "":
                        password = DEFAULT_PASSWORD
                try:
                    if len(password) < 6:
                        raise Exception("PIN password shall be at least 6 chars.")
                    if the_device.has_admin_password:
                        device_loaded.set_admin(admin_password)
                    if the_device.has_password:
                        device_loaded.initialize_device(password)
                    else:
                        device_loaded.initialize_device()
                    break
                except Exception as exc:
                    warn_modal(str(exc))
                    app.gui_panel.devices_choice.SetSelection(0)
                    if not getattr(sys, "frozen", False):
                        # output the exception when dev environment
                        raise exc
                    return
            except pwdException as exc:
                inp_message = f"Input your {device_sel_name} wallet {pwdPIN}\n"
                password_default = get_password(device_sel_name, inp_message)
                if password_default is None:
                    app.gui_panel.devices_choice.SetSelection(0)
                    return
            except Exception as exc:
                warn_modal(str(exc))
                app.gui_panel.devices_choice.SetSelection(0)
                if not getattr(sys, "frozen", False):
                    # output the exception when dev environment
                    raise exc
                return
        wx.MilliSleep(100)
        app.device = device_loaded
        if app.device.created:
            info_modal(
                "Device created",
                f"A new {device_sel_name} device was successfully created.",
            )
        app.gui_panel.coins_choice.Enable()
        app.gui_panel.coins_choice.Hide()
        app.gui_panel.coins_choice.ShowWithEffect(wx.SHOW_EFFECT_ROLL_TO_RIGHT, 750)
        app.gui_panel.coins_choice.SetFocus()
    else:
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
        erase_info()
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
    app.balance_timer.Start(8000)
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


def paint_toaddr(color):
    app.gui_panel.addr_panel.SetBackgroundColour(color)


def check_addr(ev):
    ev.Skip()
    paint_toaddr(wx.NullColour)
    if not hasattr(app, "wallet"):
        return
    addr = ev.GetString()
    if len(addr) < 10:
        app.gui_frame.Refresh()
        return
    if app.wallet.check_address(addr):
        paint_toaddr(GREEN_COLOR)
    else:
        paint_toaddr(RED_COLOR)
    app.gui_frame.Refresh()


def transfer(to, amount):
    conf = confirm(to, amount)
    if conf == wx.ID_YES:
        fee_opt = app.gui_panel.fee_slider.GetValue()
        try:
            progress_modal = wx.ProgressDialog(
                "Processing transaction",
                "",
                style=wx.PD_APP_MODAL | wx.PD_AUTO_HIDE | wx.PD_SMOOTH,
            )
            wx.MilliSleep(50)
            wait_msg = "Buiding and signing the transaction"
            if app.device.has_hardware_button:
                wait_msg += "\nPress the button on the physical device to confirm."
            progress_modal.Update(50, wait_msg)
            wx.MilliSleep(250)
            if amount == "ALL":
                tx_info = app.wallet.transfer_all(to, fee_opt)
            else:
                tx_info = app.wallet.transfer(amount, to, fee_opt)
            progress_modal.Update(100, "done")
            wx.MilliSleep(250)
            tx_success(tx_info)
        except Exception as exc:
            progress_modal.Update(100)
            wx.MilliSleep(100)
            progress_modal.Destroy()
            wx.MilliSleep(100)
            if str(exc) == "Error status : 0x6600":
                warn_modal("User button on PGP device timeout")
            else:
                warn_modal(str(exc))
            wx.MilliSleep(250)
            if not getattr(sys, "frozen", False):
                # output the exception when dev environment
                raise exc
            return


def send(ev):
    ev.Skip()
    if not app.gui_panel.send_button.IsEnabled():
        return
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
    transfer(to, amount)


def send_all(ev):
    ev.Skip()
    if not hasattr(app, "wallet"):
        return
    to = app.gui_panel.dest_addr.GetValue()
    if not app.wallet.check_address(to):
        warn_modal("Wrong destination account address format")
        return
    transfer(to, "ALL")


if __name__ == "__main__":
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(True)
    except Exception:
        pass
    app = wx.App()

    gui.app.start_app(app, VERSION, SUPPORTED_COINS, DEVICES_LIST)

    app.gui_panel.devices_choice.Bind(wx.EVT_CHOICE, device_selected)
    app.gui_panel.coins_choice.Bind(wx.EVT_CHOICE, coin_selected)
    app.gui_panel.network_choice.Bind(wx.EVT_CHOICE, net_selected)
    app.gui_panel.wallopt_choice.Bind(wx.EVT_CHOICE, wtype_selected)
    app.gui_panel.send_button.Bind(wx.EVT_BUTTON, send)
    app.gui_panel.send_all.Bind(wx.EVT_BUTTON, send_all)
    app.gui_panel.dest_addr.Bind(wx.EVT_TEXT, check_addr)
    app.gui_panel.amount.Bind(wx.EVT_TEXT_ENTER, send)
    app.gui_panel.copy_button.Bind(wx.EVT_BUTTON, copy_account)
    app.gui_panel.fee_slider.Bind(wx.EVT_SCROLL_CHANGED, fee_changed)

    app.MainLoop()
