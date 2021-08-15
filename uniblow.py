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


from ctypes import windll
from importlib import import_module
from logging import basicConfig, DEBUG, getLogger
from io import BytesIO
from sys import argv

import wx
import qrcode
import gui.app
from devices.SeedWatcher import start_seedwatcher
from devices.SingleKey import SKdevice
from wallets.wallets_utils import InvalidOption
from version import VERSION

SUPPORTED_COINS = [
    "BTC",
    "ETH",
    "BSC",
    "MATIC",
    "LTC",
    "DOGE",
    "EOS",
    "XTZ",
]

DEVICES_LIST = [
    "SeedWatcher",
    "BasicFile",
    "OpenPGP",
    "HDdevice",
]

FEES_PRORITY_TEXT = [
    "Economic fee",
    "Normal fee",
    "Faster fee",
]

DEFAULT_PASSWORD = "NoPasswd"

GREEN_COLOR = wx.Colour(73, 172, 73)
RED_COLOR = wx.Colour(198, 60, 60)


logger = getLogger(__name__)


wallets = {}
for coin_lib in SUPPORTED_COINS:
    wallets[f"{coin_lib}wallet"] = import_module(f"wallets.{coin_lib}wallet")


def get_coin_class(coin_name):
    return getattr(wallets[f"{coin_name}wallet"], f"{coin_name}_wallet")


devices = {}
for device_name in DEVICES_LIST:
    devices[device_name] = import_module(f"devices.{device_name}")


def get_device_class(device_str):
    global pwdException, NotinitException
    device_class = getattr(devices[device_str], device_str)
    if device_class.has_password:
        pwdException = getattr(devices[device_str], "pwdException")
    NotinitException = getattr(devices[device_str], "NotinitException")
    return device_class


def display_balance():
    try:
        balance = app.wallet.get_balance()
    except IOError as exc:
        erase_info()
        err_msg = f"Network error when getting info.\nCheck your Internet connection.\n{str(exc)}"
        logger.error("Error in display_balance : %s", err_msg, exc_info=exc, stack_info=True)
        warn_modal(err_msg)
        return
    app.gui_panel.balance_info.SetLabel(balance)
    app.gui_panel.hist_button.Enable()
    app.gui_panel.copy_button.Enable()
    bal_str = balance.split(" ")[0]
    if (
        bal_str not in ("0", "0.0")
        # EOS when register pubkey mode : disable sending
        and not bal_str.startswith("Register")
        # WalletConnect : disable sending
        and not hasattr(app.wallet, "wc_timer")
    ):
        app.gui_panel.dest_addr.Enable()
        app.gui_panel.amount.Enable()
        app.gui_panel.send_button.Enable()
        app.gui_panel.send_all.Enable()


def erase_info():
    if hasattr(app, "balance_timer"):
        app.balance_timer.Stop()
    if hasattr(app, "wallet") and hasattr(app.wallet, "wc_timer"):
        app.wallet.wc_client.close()
        app.wallet.wc_timer.Stop()
        delattr(app.wallet, "wc_timer")
    paint_toaddr(wx.NullColour)
    app.gui_panel.hist_button.Disable()
    app.gui_panel.copy_button.Disable()
    app.gui_panel.dest_addr.Disable()
    app.gui_panel.amount.Disable()
    app.gui_panel.send_all.Disable()
    app.gui_panel.send_button.Disable()
    app.gui_panel.network_label.Disable()
    app.gui_panel.network_choice.Disable()
    app.gui_panel.wallopt_label.Disable()
    app.gui_panel.wallopt_choice.Disable()
    app.gui_panel.qrimg.SetBitmap(wx.Bitmap())
    if hasattr(app, "wallet"):
        del app.wallet
    app.gui_panel.balance_info.SetLabel("")
    app.gui_panel.account_addr.SetLabel("")
    app.gui_frame.Refresh()


class DisplayTimer(wx.Timer):
    def __init__(self):
        wx.Timer.__init__(self)

    def Notify(self):
        display_balance()


def warn_modal(warning_text):
    gui.app.InfoBox(warning_text, "Error", wx.OK | wx.ICON_WARNING, app.gui_frame)


def info_modal(title, info_text):
    gui.app.InfoBox(info_text, title, wx.OK | wx.ICON_INFORMATION, app.gui_frame)


def get_password(device_nam, input_message):
    pwd_dialog = wx.PasswordEntryDialog(
        app.gui_frame,
        input_message,
        caption=f"{device_nam} wallet PIN/password",
        defaultValue="",
        pos=wx.DefaultPosition,
    )
    if pwd_dialog.ShowModal() == wx.ID_OK:
        passval = pwd_dialog.GetValue()
        return passval


def get_option(network_id, input_value, preset_values):
    option_dialog = gui.window.OptionDialog(app.gui_frame)
    option_panel = gui.app.app_option_panel(option_dialog)
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


def confirm_tx(to_addr, amount):
    conf_txt = f"Confirm this transaction ?\n{amount} {app.wallet.coin} to {to_addr}"
    confirm_tx_modal = wx.MessageDialog(
        app.gui_frame,
        conf_txt,
        "Confirmation",
        wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION | wx.STAY_ON_TOP | wx.CENTER,
        wx.DefaultPosition,
    )
    return confirm_tx_modal.ShowModal()


def confirm_request(request_ui_message):
    """Display a modal to the user.
    callback *args called if the user approves the request.
    """
    confirm_txt = f"Do you approve the following request ?\n\n{request_ui_message}"
    confirm_tx_modal = wx.MessageDialog(
        app.gui_frame,
        confirm_txt,
        "Request",
        wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION | wx.STAY_ON_TOP | wx.CENTER,
        wx.DefaultPosition,
    )
    modal_choice = confirm_tx_modal.ShowModal()
    return modal_choice == wx.ID_YES


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
            addr = app.gui_panel.account_addr.GetValue()
            wx.TheClipboard.SetData(wx.TextDataObject(addr))
            wx.TheClipboard.Close()
            wx.TheClipboard.Flush()
            copy_result("Copied")
        else:
            copy_result("No Access")
    except Exception:
        copy_result("Error")


def disp_history(ev):
    hist_url = app.wallet.history()
    if hist_url:
        gui.app.show_history(hist_url)


def watch_messages():
    """Watch for messages recveives.
    For some wallet types such as WalletConnect.
    """
    try:
        app.wallet.get_messages()
    except Exception as exc:
        wallet_error(exc)


def close_device():
    if hasattr(app, "device"):
        del app.device


def cb_open_wallet(wallet_obj, pkey, waltype, sw_frame):
    """Process the opening of the wallet from SeedWatcher."""
    key_device = SKdevice()
    key_device.load_key(pkey)
    app.device = key_device
    app.wallet = wallet_obj(key_device)
    sw_frame.Close()
    app.gui_panel.devices_choice.SetSelection(1)
    app.gui_panel.coins_choice.Clear()
    app.gui_panel.coins_choice.Append(app.wallet.coin)
    app.gui_panel.coins_choice.SetSelection(0)
    app.gui_panel.coins_choice.Disable()
    app.gui_panel.network_choice.Clear()
    app.gui_panel.wallopt_choice.Clear()
    app.gui_panel.network_choice.Enable()
    app.gui_panel.network_label.Enable()
    if app.wallet.coin != "BTC":
        app.gui_panel.wallopt_choice.Enable()
        app.gui_panel.wallopt_label.Enable()
    networks = app.wallet.get_networks()
    acc_types = app.wallet.get_account_types()
    for netw in networks:
        app.gui_panel.network_choice.Append(netw)
    for wtype in acc_types:
        app.gui_panel.wallopt_choice.Append(wtype)
    app.gui_panel.network_choice.SetSelection(0)
    app.gui_panel.wallopt_choice.SetSelection(waltype)
    display_coin(app.wallet.get_account())


def device_selected(device):
    global DEFAULT_PASSWORD
    close_device()
    app.gui_panel.coins_choice.Disable()
    app.gui_panel.coins_choice.SetSelection(0)
    app.gui_panel.network_choice.Clear()
    app.gui_panel.wallopt_choice.Clear()
    erase_info()
    gui.app.load_coins_list(app, SUPPORTED_COINS)
    sel_device = device.GetInt()
    device_sel_name = DEVICES_LIST[sel_device - 1]
    if sel_device == 1:
        # Seed Watcher
        start_seedwatcher(app, cb_open_wallet)
    if sel_device > 1:
        # Real keys device
        password_default = DEFAULT_PASSWORD
        the_device = get_device_class(device_sel_name)
        try:
            device_loaded = the_device()
        except Exception as exc:
            app.gui_panel.devices_choice.SetSelection(0)
            logger.error(
                "Error during device loading : %s", str(exc), exc_info=exc, stack_info=True
            )
            warn_modal(str(exc))
            return
        while True:
            try:
                pwd_pin = "local user password"
                if device_sel_name == "OpenPGP":
                    pwd_pin = "PIN1"
                if the_device.has_password:
                    device_loaded.open_account(password_default)
                else:
                    device_loaded.open_account()
                break
            except NotinitException:
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
                if the_device.is_HD:
                    # HD means also mnemonic can be imported
                    mnemonic = device_loaded.generate_mnemonic()  # mnemonic proposal
                    # Get settings from the user
                    HDwallet_settings = gui.app.set_mnemonic(app, mnemonic)
                    if HDwallet_settings is None:
                        app.gui_panel.devices_choice.SetSelection(0)
                        return
                if the_device.has_password:
                    inp_message = f"Choose your {pwd_pin} for the {device_sel_name} wallet\n"
                    inp_message += f"If blank, a default {pwd_pin} will be used."
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
                    if the_device.is_HD:
                        HDwallet_settings["file_password"] = password
                        device_loaded.initialize_device(HDwallet_settings)
                    # is_HD has password already
                    #  attribute has_password is false, password set by settings parameters
                    elif the_device.has_password:
                        device_loaded.initialize_device(password)
                    else:
                        device_loaded.initialize_device()
                    break
                except Exception as exc:
                    app.gui_panel.devices_choice.SetSelection(0)
                    logger.error(
                        "Error during device initialization : %s",
                        {str(exc)},
                        exc_info=exc,
                        stack_info=True,
                    )
                    warn_modal(str(exc))
                    return
            except pwdException:
                inp_message = f"Input your {device_sel_name} wallet {pwd_pin}\n"
                password_default = get_password(device_sel_name, inp_message)
                if password_default is None:
                    app.gui_panel.devices_choice.SetSelection(0)
                    return
            except Exception as exc:
                app.gui_panel.devices_choice.SetSelection(0)
                warn_modal(str(exc))
                logger.error(
                    "Error during device PIN/pwd : %s", str(exc), exc_info=exc, stack_info=True
                )
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


def wallet_fallback():
    """Called when a user option failed"""
    # Reset the wallet to the first type
    wallet_type_fallback = 0
    app.gui_panel.wallopt_choice.SetSelection(wallet_type_fallback)
    # Act like the user selected back the first wallet type
    coin_sel = app.gui_panel.coins_choice.GetStringSelection()
    net_sel = app.gui_panel.network_choice.GetSelection()
    wx.CallLater(180, process_coin_select, coin_sel, net_sel, wallet_type_fallback)


def wallet_error(exc):
    """Process wallet exception"""
    app.gui_panel.network_choice.Clear()
    app.gui_panel.wallopt_choice.Clear()
    app.gui_panel.coins_choice.SetSelection(0)
    erase_info()
    logger.error("Error in the wallet : %s", str(exc), exc_info=exc, stack_info=True)
    warn_modal(str(exc))


def set_coin(coin, network, wallet_type):
    fee_opt_sel = app.gui_panel.fee_slider.GetValue()
    app.gui_panel.fee_setting.SetLabel(FEES_PRORITY_TEXT[fee_opt_sel])
    try:
        option_info = None
        option_arg = {}
        if hasattr(get_coin_class(coin), "user_options"):
            coin_class = get_coin_class(coin)
            if wallet_type in coin_class.user_options:
                # This wallet has a user input option
                # ! A wallet cant have its first type option having a user option
                opt_idx = coin_class.user_options.index(wallet_type)
                option_info = coin_class.options_data[opt_idx]
                option_preset = option_info.get("preset")
                option_value = get_option(network, option_info["prompt"], option_preset)
                if option_value is None:
                    wallet_fallback()
                    return
        if app.device.is_HD:
            current_path = (
                get_coin_class(coin).get_path(network, wallet_type) + app.device.get_address_index()
            )
            app.device.derive_key(current_path)
        if option_info is not None:
            option_arg = {
                option_info["option_name"]: option_value,
                "confirm_callback": confirm_request,
            }
        app.wallet = get_coin_class(coin)(network, wallet_type, app.device, **option_arg)
        account_id = app.wallet.get_account()
        if option_info is not None and option_info.get("use_get_messages", False):
            app.wallet.wc_timer = wx.Timer()
            app.wallet.wc_timer.Notify = watch_messages
    except InvalidOption as exc:
        warn_modal(str(exc))
        wallet_fallback()
        return
    except Exception as exc:
        wallet_error(exc)
        return
    display_coin(account_id)


def display_coin(account_addr):
    app.gui_panel.account_addr.SetValue(account_addr)
    imgbuf = BytesIO()
    imgqr = qrcode.make(
        account_addr,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=4,
        border=3,
    )
    imgqr.save(imgbuf, "PNG")
    imgbuf.seek(0)
    wxi = wx.Image(imgbuf, type=wx.BITMAP_TYPE_PNG)
    app.gui_panel.qrimg.SetScaleMode(wx.StaticBitmap.ScaleMode.Scale_None)  # or Scale_AspectFit
    app.gui_panel.qrimg.SetBitmap(wx.Bitmap(wxi))
    app.balance_timer = DisplayTimer()
    wx.CallLater(50, display_balance)
    app.balance_timer.Start(10000)
    if hasattr(app.wallet, "wc_timer"):
        app.wallet.wc_timer.Start(2500, oneShot=wx.TIMER_CONTINUOUS)
    app.gui_frame.Refresh()
    app.gui_frame.Update()


def process_coin_select(coin, sel_network, sel_wallettype):
    app.gui_panel.network_choice.Enable()
    app.gui_panel.network_label.Enable()
    if (
        app.gui_panel.coins_choice.IsEnabled()
        or app.gui_panel.coins_choice.GetStringSelection() != "BTC"
    ):
        # Because BTC wallet types are different path/wallet from SeedWatcher
        app.gui_panel.wallopt_choice.Enable()
        app.gui_panel.wallopt_label.Enable()
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
    if len(addr) < 7:
        app.gui_frame.Refresh()
        return
    if app.wallet.check_address(addr):
        paint_toaddr(GREEN_COLOR)
    else:
        paint_toaddr(RED_COLOR)
    app.gui_frame.Refresh()


def transfer(to, amount):
    conf = confirm_tx(to, amount)
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
            if app.wallet.current_device.has_hardware_button:
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
            logger.error(
                "Error during device selection : %s", str(exc), exc_info=exc, stack_info=True
            )
            if str(exc) == "Error status : 0x6600":
                warn_modal("User button on PGP device timeout")
            else:
                warn_modal(str(exc))
            wx.MilliSleep(250)
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
    sending_value_str = app.gui_panel.amount.GetValue()
    if len(sending_value_str) <= 0:
        warn_modal("Input an amount value to transfer.")
        return
    if sending_value_str[0] == "-":
        warn_modal("Amount input must be positive or null.")
        return
    try:
        float(sending_value_str)
    except ValueError:
        warn_modal("Unvalid amount input")
        return
    transfer(to, sending_value_str)


def send_all(ev):
    ev.Skip()
    if not hasattr(app, "wallet"):
        return
    to = app.gui_panel.dest_addr.GetValue()
    if not app.wallet.check_address(to):
        warn_modal("Wrong destination account address format")
        return
    transfer(to, "ALL")


def start_main_app():
    global app

    app = wx.App()
    ret = gui.app.start_app(app, VERSION, SUPPORTED_COINS, DEVICES_LIST)
    if ret == "ERR":
        return

    app.gui_panel.devices_choice.Bind(wx.EVT_CHOICE, device_selected)
    app.gui_panel.coins_choice.Bind(wx.EVT_CHOICE, coin_selected)
    app.gui_panel.network_choice.Bind(wx.EVT_CHOICE, net_selected)
    app.gui_panel.wallopt_choice.Bind(wx.EVT_CHOICE, wtype_selected)
    app.gui_panel.send_button.Bind(wx.EVT_BUTTON, send)
    app.gui_panel.send_all.Bind(wx.EVT_BUTTON, send_all)
    app.gui_panel.dest_addr.Bind(wx.EVT_TEXT, check_addr)
    app.gui_panel.amount.Bind(wx.EVT_TEXT_ENTER, send)
    app.gui_panel.hist_button.Bind(wx.EVT_BUTTON, disp_history)
    app.gui_panel.copy_button.Bind(wx.EVT_BUTTON, copy_account)
    app.gui_panel.fee_slider.Bind(wx.EVT_SCROLL_CHANGED, fee_changed)

    app.MainLoop()


if __name__ == "__main__":

    if "-v" in argv[1:]:
        basicConfig(level=DEBUG)

    try:
        windll.shcore.SetProcessDpiAwareness(True)
    except Exception:
        pass

    start_main_app()
