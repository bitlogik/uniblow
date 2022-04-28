#!/usr/bin/python3
# -*- coding: utf8 -*-

# UNIBLOW  : a UNIversal BLOckchain Wallet
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


try:
    from ctypes import windll
except ImportError:
    # Not Windows, anyway
    pass

if "windll" in globals():
    windll.shcore.SetProcessDpiAwareness(2)

from copy import copy as ccopy
from functools import partial
from importlib import import_module
from logging import basicConfig, DEBUG, getLogger
from io import BytesIO
from sys import argv

import wx
import qrcode
import gui.app
from devices.SeedWatcher import start_seedwatcher
from devices.SingleKey import SKdevice
from wallets.wallets_utils import InvalidOption, NotEnoughTokens
from version import VERSION

SUPPORTED_COINS = [
    "BTC",
    "ETH",
    "BSC",
    "MATIC",
    "FTM",
    "METIS",
    "CELO",
    "MOVR",
    "ARB",
    "AVAX",
    "LTC",
    "DOGE",
    "EOS",
    "XTZ",
    "SOL",
]

DEVICES_LIST = [
    "SeedWatcher",
    "LocalFile",
    "OpenPGP",
    "Ledger",
    "Cryptnox",
]

FEES_PRORITY_TEXT = [
    "Economic fee",
    "Normal fee",
    "Faster fee",
]

DEFAULT_PASSWORD = "NoPasswd"

GREEN_COLOR = wx.Colour(73, 172, 73)
RED_COLOR = wx.Colour(198, 60, 60)


BAD_ADDRESS = "Wrong destination account address checksum or wrong format."


logger = getLogger(__name__)


wallets = {}
for coin_lib in SUPPORTED_COINS:
    wallets[f"{coin_lib}wallet"] = import_module(f"wallets.{coin_lib}wallet")


def get_coin_class(coin_name):
    cname = coin_name
    if coin_name == "ARB/ETH":
        cname = "ARB"
    return getattr(wallets[f"{cname}wallet"], f"{cname}_wallet")


devices = {}
for device_name in DEVICES_LIST:
    devices[device_name] = import_module(f"devices.{device_name}")


def get_device_class(device_str):
    global pwdException, NotinitException
    device_class = getattr(devices[device_str], device_str)
    pwdException = ValueError  # Fake value to filter out
    if device_class.has_password:
        pwdException = getattr(devices[device_str], "pwdException")
    NotinitException = getattr(devices[device_str], "NotinitException")
    return device_class


def check_coin_consistency(current_wallet=None, network_num=None):
    """Check if selected coin is the same as the current wallet class used."""
    # Designed to fix a race condition when the async data of a wallet
    # are displayed : address and balance.
    # Changing the coin selector could mix crypto info. So this terminates some
    # process path that are no longer valid.
    if not app.gui_panel.coins_choice.IsEnabled():
        # Can be seedwatcher
        return True
    coin_sel = app.gui_panel.coins_choice.GetSelection()
    if coin_sel <= 0:
        return False
    coin_name = app.gui_panel.coins_choice.GetString(coin_sel)
    coin_class = get_coin_class(coin_name)
    if current_wallet is None:
        current_wallet = type(app.wallet)
    if coin_class is not current_wallet:
        return False
    if network_num is not None:
        net_sel = app.gui_panel.network_choice.GetSelection()
        if net_sel < 0:
            return False
        return net_sel == network_num
    return True


def display_balance():
    logger.debug("Checking for wallet balance")
    if not hasattr(app, "wallet"):
        erase_info()
        return
    if not check_coin_consistency():
        return
    try:
        balance = app.wallet.get_balance()
    except Exception as exc:
        erase_info()
        err_msg = (
            f"Error when getting account balance.\nCheck your Internet connection.\n{str(exc)}"
        )
        logger.error("Error in display_balance : %s", err_msg, exc_info=exc, stack_info=True)
        warn_modal(err_msg)
        return
    app.gui_panel.balance_info.SetLabel(balance)
    app.gui_panel.hist_button.Enable()
    app.gui_panel.copy_button.Enable()
    app.gui_panel.account_label.Enable()
    app.gui_panel.balance_label.Enable()
    bal_str = balance.split(" ")[0]
    if (
        # No fund in the wallet
        bal_str not in ("0", "0.0")
        # EOS when register pubkey mode : disable sending
        and not bal_str.startswith("Register")
        # WalletConnect : disable sending
        and not hasattr(app.wallet, "wc_timer")
    ):
        app.gui_panel.dest_addr.Enable()
        app.gui_panel.amount.Enable()
        app.gui_panel.dest_label.Enable()
        app.gui_panel.amount_label.Enable()
        app.gui_panel.fee_slider.Enable()
        app.gui_panel.fee_setting.Enable()
        app.gui_panel.send_button.Enable()
        app.gui_panel.send_all.Enable()
    else:
        app.gui_panel.dest_addr.Clear()
        app.gui_panel.amount.Clear()
        app.gui_panel.dest_label.Disable()
        app.gui_panel.amount_label.Disable()
        app.gui_panel.fee_slider.Disable()
        app.gui_panel.fee_setting.Disable()
        app.gui_panel.dest_addr.Disable()
        app.gui_panel.amount.Disable()
        app.gui_panel.send_button.Disable()
        app.gui_panel.send_all.Disable()
    if hasattr(app.wallet, "wc_timer"):
        # WalletConnect active
        app.gui_panel.dest_addr.ChangeValue("   Use the connected dapp to transact")


def erase_info(reset=False):
    if hasattr(app, "balance_timer"):
        app.balance_timer.Stop()
    if hasattr(app, "wallet") and hasattr(app.wallet, "wc_timer"):
        app.wallet.wc_client.close()
        app.wallet.wc_timer.Stop()
        delattr(app.wallet, "wc_timer")
    paint_toaddr(wx.NullColour)
    app.gui_panel.hist_button.Disable()
    app.gui_panel.copy_button.Disable()
    app.gui_panel.dest_addr.Clear()
    app.gui_panel.dest_addr.Disable()
    app.gui_panel.amount.Clear()
    app.gui_panel.amount.Disable()
    app.gui_panel.send_all.Disable()
    app.gui_panel.send_button.Disable()
    app.gui_panel.wallopt_label.Disable()
    app.gui_panel.wallopt_choice.Disable()
    app.gui_panel.account_label.Disable()
    app.gui_panel.balance_label.Disable()
    app.gui_panel.dest_label.Disable()
    app.gui_panel.amount_label.Disable()
    app.gui_panel.fee_slider.Disable()
    app.gui_panel.fee_setting.Disable()
    app.gui_panel.btn_chkaddr.Hide()
    if reset:
        app.gui_panel.network_choice.SetSelection(0)
        app.gui_panel.wallopt_choice.SetSelection(0)
        app.gui_panel.fee_setting.SetLabel("")
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


def warn_modal(warning_text, modal=False):
    gui.app.InfoBox(
        warning_text, "Error", wx.OK | wx.ICON_WARNING, app.gui_frame, block_modal=modal
    )


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
    returns True if the user approves the request.
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
        if wx.TheClipboard.IsOpened() or wx.TheClipboard.Open():
            wx.TheClipboard.Clear()
            addr = app.gui_panel.account_addr.GetValue()
            wx.TheClipboard.SetData(wx.TextDataObject(addr))
            wx.TheClipboard.Flush()
            wx.TheClipboard.Close()
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
    """Watch for messages received.
    For some wallet types such as WalletConnect.
    """
    try:
        app.wallet.get_messages()
    except NotEnoughTokens as exc:
        warn_modal(str(exc))
    except Exception as exc:
        if str(exc).startswith("You rejected the"):
            warn_modal(str(exc))
            return
        wallet_error(exc, "fromwatch")


def close_device():
    if hasattr(app, "device"):
        del app.device


def cb_open_wallet(wallet_obj, pkey, waltype, sw_frame, pubkey_cpr):
    """Process the opening of the wallet from SeedWatcher."""
    key_device = SKdevice()
    key_device.load_key(pkey)
    app.device = key_device
    if pubkey_cpr:
        app.wallet = wallet_obj(key_device)
    else:
        # Special case for Bitcoin Electrum old
        app.wallet = wallet_obj(key_device, pubkey_cpr)
    sw_frame.Close()
    app.gui_panel.btn_chkaddr.Hide()
    app.gui_panel.devices_choice.SetSelection(1)
    app.gui_panel.coins_choice.Clear()
    app.gui_panel.coins_choice.Append(app.wallet.coin)
    app.gui_panel.coins_choice.SetSelection(0)
    app.gui_panel.coins_choice.Disable()
    app.gui_panel.network_choice.Clear()
    app.gui_panel.wallopt_choice.Clear()
    app.gui_panel.network_choice.Enable()
    app.gui_panel.network_label.Enable()
    if app.wallet.coin not in ["BTC", "XTZ"]:
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
    close_device()
    app.gui_panel.btn_chkaddr.Hide()
    app.gui_panel.coins_choice.Disable()
    app.gui_panel.coins_choice.SetSelection(0)
    app.gui_panel.network_choice.Clear()
    app.gui_panel.network_choice.Disable()
    app.gui_panel.wallopt_choice.Clear()
    erase_info(True)
    sel_device = device.GetInt()
    device_sel_name = DEVICES_LIST[sel_device - 1]
    coins_list = ccopy(SUPPORTED_COINS)
    if device_sel_name == "Ledger":
        coins_list = [
            "ETH",
            "BSC",
            "MATIC",
            "FTM",
            "CELO",
            "MOVR",
            "ARB",
            "AVAX",
        ]
    if device_sel_name == "OpenPGP":
        coins_list.remove("SOL")
    if device_sel_name == "Cryptnox":
        coins_list.remove("SOL")
    app.load_coins_list(coins_list)
    if sel_device == 1:
        # Seed Watcher
        start_seedwatcher(app, cb_open_wallet)
    if sel_device > 1:
        # Real keys device
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
        pin_left = -1
        password_default = device_loaded.default_password
        while True:
            try:
                pwd_pin = the_device.password_name
                if the_device.has_password:
                    if (
                        not the_device.password_retries_inf
                        and pin_left == -1
                        and device_loaded.is_init()
                    ):
                        # Goto password exception to ask for user PIN
                        pin_left = device_loaded.get_pw_left()
                        if the_device.is_HD:
                            HDwallet_settings = app.hd_setup("")
                            if HDwallet_settings is None:
                                app.gui_panel.devices_choice.SetSelection(0)
                                return
                        raise pwdException
                    # Can raise notinit
                    device_loaded.open_account(password_default)
                else:
                    device_loaded.open_account()
                break
            except NotinitException:
                if the_device.is_HD:
                    mnemonic = ""
                    if not the_device.internally_gen_keys:
                        # Mnemonic generated by the software wallet
                        mnemonic = device_loaded.generate_mnemonic()  # mnemonic proposal
                    # Get settings from the user
                    HDwallet_settings = app.hd_setup(mnemonic)
                    if HDwallet_settings is None:
                        app.gui_panel.devices_choice.SetSelection(0)
                        return
                if the_device.has_admin_password:
                    set_admin_message = (
                        f"Choose the {the_device.admin_pass_name} to init "
                        f"the {device_sel_name} device.\n"
                    )
                    set_admin_message += "\nFor demo, quick insecure setup, it can be left blank,\n"
                    set_admin_message += (
                        f"and a default {the_device.admin_pass_name} will be used.\n\n"
                    )
                    lenmsg = (
                        str(device_loaded.admin_pwd_minlen)
                        if device_loaded.admin_pwd_minlen == device_loaded.admin_pwd_maxlen
                        else f"between {device_loaded.admin_pwd_minlen} and {device_loaded.admin_pwd_maxlen}"
                    )
                    set_admin_message += (
                        f"The chosen {the_device.admin_pass_name} must be\n{lenmsg} chars long."
                    )
                    while True:
                        admin_password = get_password(device_sel_name, set_admin_message)
                        if admin_password is None:
                            app.gui_panel.devices_choice.SetSelection(0)
                            return
                        if admin_password == "":
                            admin_password = device_loaded.default_admin_password
                        if (
                            len(admin_password) >= device_loaded.admin_pwd_minlen
                            and len(admin_password) <= device_loaded.admin_pwd_maxlen
                        ):
                            break
                        warn_modal(
                            f"{the_device.admin_pass_name} shall be {lenmsg} chars long.",
                            True,
                        )
                if the_device.has_password:
                    inp_message = f"Choose your {pwd_pin} to setup the {device_sel_name} wallet.\n"
                    inp_message += "\nFor demo, quick insecure setup, it can be left blank,\n"
                    inp_message += f"and a default {pwd_pin} will be used.\n\n"
                    lenmsg = (
                        str(device_loaded.password_min_len)
                        if device_loaded.password_min_len == device_loaded.password_max_len
                        else f"between {device_loaded.password_min_len} and {device_loaded.password_max_len}"
                    )
                    pintype = "chars"
                    if device_loaded.is_pin_numeric:
                        pintype = "digits"
                    inp_message += f"The chosen {pwd_pin} must be\n{lenmsg} {pintype} long."
                    while True:
                        password = get_password(device_sel_name, inp_message)
                        if password is None:
                            app.gui_panel.devices_choice.SetSelection(0)
                            return
                        if password == "":
                            password = device_loaded.default_password
                        if (
                            len(password) >= device_loaded.password_min_len
                            and len(password) <= device_loaded.password_max_len
                            and (not device_loaded.is_pin_numeric or password.isdigit())
                        ):
                            break
                        wmsg = f"Device {pwd_pin} shall be {lenmsg} {pintype} long."
                        if device_loaded.is_pin_numeric:
                            wmsg += f"\n\nThe {pwd_pin} must be {pintype} (0-9) only."
                        warn_modal(
                            wmsg,
                            True,
                        )
                try:
                    if the_device.has_admin_password:
                        device_loaded.set_admin(admin_password)
                    if the_device.is_HD:
                        if the_device.has_password:
                            HDwallet_settings["file_password"] = password
                        device_loaded.initialize_device(HDwallet_settings)
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
            except pwdException as excp:
                if not device_loaded.password_retries_inf:
                    try:
                        pin_left = device_loaded.get_pw_left()
                    except Exception as exc:
                        device_error(exc)
                        return
                    if pin_left == 0:
                        warn_modal(f"Device {pwd_pin} is locked.")
                        return
                    if (
                        the_device.password_softlock > 0
                        and pin_left == the_device.password_softlock
                        and str(excp) == "0"
                    ):
                        warn_modal(f"Device {pwd_pin} is soft locked. Restart it to try again.")
                        return
                while True:
                    inp_message = f"Input your {device_sel_name} wallet {pwd_pin}.\n"
                    if not the_device.password_retries_inf:
                        inp_message += (
                            f"{pin_left} {pwd_pin} tr{'ies' if pin_left >=2 else 'y'}"
                            " left on this device.\n"
                        )
                    lenmsg = (
                        str(device_loaded.password_min_len)
                        if device_loaded.password_min_len == device_loaded.password_max_len
                        else f"between {device_loaded.password_min_len} and {device_loaded.password_max_len}"
                    )
                    pintype = "chars"
                    if device_loaded.is_pin_numeric:
                        pintype = "digits"
                    inp_message += f"\nThe {pwd_pin} to provide\nis {lenmsg} {pintype} long."
                    password_default = get_password(device_sel_name, inp_message)
                    if password_default is None:
                        app.gui_panel.devices_choice.SetSelection(0)
                        return
                    if (
                        len(password_default) >= device_loaded.password_min_len
                        and len(password_default) <= device_loaded.password_max_len
                        and (not device_loaded.is_pin_numeric or password_default.isdigit())
                    ):
                        break
                    wmsg = f"Device {pwd_pin} shall be {lenmsg} {pintype} long."
                    if device_loaded.is_pin_numeric:
                        wmsg += f"\n\nThe {pwd_pin} must be {pintype} (0-9) only."
                    warn_modal(
                        wmsg,
                        True,
                    )
            except Exception as exc:
                return device_error(exc)
        wx.MilliSleep(100)
        if the_device.has_password and the_device.is_HD and not the_device.password_retries_inf:
            # Kind of special for Cryptnox for now
            device_loaded.set_path(HDwallet_settings)
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
        erase_info(True)


def wallet_fallback():
    """Called when a user option failed"""
    # Reset the wallet to the first type
    wallet_type_fallback = 0
    # If Tezos, which have 2 different key types, must stick on the previous keytype
    if app.gui_panel.coins_choice.GetStringSelection() == "XTZ" and hasattr(
        app.device, "get_key_type"
    ):
        device_key_type = app.device.get_key_type()
        if device_key_type:
            # Inverse of XTZ get_key_type to set back the type selector
            if device_key_type == "ED":
                # tz1 first choice
                wallet_type_fallback = 0
            elif device_key_type == "K1":
                # tz2 second choice
                wallet_type_fallback = 1
    app.gui_panel.wallopt_choice.SetSelection(wallet_type_fallback)
    # Act like the user selected back the first wallet type
    coin_sel = app.gui_panel.coins_choice.GetStringSelection()
    net_sel = app.gui_panel.network_choice.GetSelection()
    wx.CallLater(180, process_coin_select, coin_sel, net_sel, wallet_type_fallback)


def device_error(exc):
    app.gui_panel.coins_choice.Disable()
    app.gui_panel.coins_choice.SetSelection(0)
    app.gui_panel.network_choice.Clear()
    app.gui_panel.network_choice.Disable()
    app.gui_panel.wallopt_choice.Clear()
    app.gui_panel.wallopt_choice.Disable()
    app.gui_panel.devices_choice.SetSelection(0)
    app.gui_panel.btn_chkaddr.Hide()
    erase_info(True)
    logger.error("Error with device : %s", str(exc), exc_info=exc, stack_info=True)
    warn_modal(str(exc))
    return


def wallet_error(exc, level="hard"):
    """Process wallet exception"""
    if level == "hard":
        app.gui_panel.network_choice.Clear()
        app.gui_panel.coins_choice.SetSelection(0)
        app.gui_panel.wallopt_choice.Clear()
        app.gui_panel.wallopt_choice.Disable()
    if hasattr(app, "wallet"):
        erase_option = app.wallet.coin != "BTC"
    else:
        erase_option = False
    erase_info(erase_option)
    logger.error("Error in the wallet : %s", str(exc), exc_info=exc, stack_info=True)
    if level == "fromwatch":
        exc = str(exc) + "\nYou can reconnect by selecting the network option."
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
                    wx.CallAfter(wallet_fallback)
                    return
        key_type = get_coin_class(coin).get_key_type(wallet_type)
        if not check_coin_consistency(get_coin_class(coin), network):
            return
        if app.device.is_HD:
            current_path = (
                get_coin_class(coin)
                .get_path(network, wallet_type, app.device.legacy_derive)
                .format(app.device.get_account(), app.device.get_address_index())
            )
            app.device.derive_key(current_path, key_type)
        else:
            app.device.set_key_type(key_type)
        if option_info is not None:
            option_arg = {
                option_info["option_name"]: option_value,
                "confirm_callback": confirm_request,
            }
        app.wallet = get_coin_class(coin)(network, wallet_type, app.device, **option_arg)
        if not check_coin_consistency(network_num=network):
            return
        account_id = app.wallet.get_account()
        if not check_coin_consistency(network_num=network):
            return
        if option_info is not None and option_info.get("use_get_messages", False):
            app.wallet.wc_timer = wx.Timer()
            app.wallet.wc_timer.Notify = watch_messages
    except InvalidOption as exc:
        warn_modal(str(exc))
        wx.CallAfter(wallet_fallback)
        return
    except Exception as exc:
        if str(exc).endswith("disconnected."):
            device_error(exc)
        else:
            wallet_error(exc)
        return
    if not check_coin_consistency(network_num=network):
        return
    if app.device.has_screen:
        app.gui_panel.btn_chkaddr.Show()
    display_coin(account_id)


def display_coin(account_addr):
    imgbuf = BytesIO()
    imgqr = qrcode.make(
        account_addr,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=4,
        border=3,
    )
    imgqr.save(imgbuf, "PNG")
    if not check_coin_consistency():
        return
    app.gui_panel.account_addr.SetValue(account_addr)
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
    erase_info(True)
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
                "Error during the transaction processing : %s",
                str(exc),
                exc_info=exc,
                stack_info=True,
            )
            if str(exc).endswith("disconnected."):
                device_error(exc)
            elif str(exc) == "Error status : 0x6600":
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
        warn_modal(BAD_ADDRESS)
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
        warn_modal(BAD_ADDRESS)
        return
    transfer(to, "ALL")


def end_checkwallet(modal, result):
    wx.MilliSleep(200)
    modal.Update(100, "done")
    wx.MilliSleep(200)
    if not result:
        warn_modal("The address verification was rejected on the Ledger.")


def check_wallet(evt):
    progress_modal = wx.ProgressDialog(
        "",
        "",
        style=wx.PD_APP_MODAL | wx.PD_AUTO_HIDE | wx.PD_SMOOTH,
    )
    wx.MilliSleep(200)
    wait_msg = "Verify the address on the Ledger screen."
    progress_modal.Update(50, wait_msg)
    wx.MilliSleep(250)
    try:
        app.device.get_public_key(partial(end_checkwallet, progress_modal))
    except Exception as exc:
        progress_modal.Update(100, "failure")
        wx.MilliSleep(200)
        wx.CallAfter(device_error, exc)


def start_main_app():
    app.load_devices(DEVICES_LIST)
    app.load_coins_list(SUPPORTED_COINS)
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
    app.gui_panel.btn_chkaddr.Bind(wx.EVT_BUTTON, check_wallet)
    app.gui_panel.btn_chkaddr.Hide()
    erase_info(True)
    app.gui_frame.SetLabel(f"Uniblow  -  {VERSION}")
    app.gui_frame.Show()


app = gui.app.UniblowApp(VERSION)


if __name__ == "__main__":

    if "-v" in argv[1:]:
        basicConfig(level=DEBUG)

    start_main_app()
    app.MainLoop()
