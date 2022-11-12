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

    windll.shcore.SetProcessDpiAwareness(1)
except ImportError:
    # Not Windows, anyway
    pass


from copy import copy as ccopy
from importlib import import_module
from logging import basicConfig, DEBUG, getLogger
from sys import argv

import wx
import gui.app
from gui.utils import file_path
from gui.galleryapp import Gallery
from devices.SeedWatcher import start_seedwatcher
from devices.SingleKey import SKdevice
from wallets.wallets_utils import InvalidOption, NotEnoughTokens
from wallets.NFTwallet import NFTWallet
from version import VERSION

SUPPORTED_COINS = [
    "BTC",
    "ETH",
    "BSC",
    "MATIC",
    "FTM",
    "OP",
    "METIS",
    "CELO",
    "GLMR",
    "ARB",
    "AVAX",
    "LTC",
    "DOGE",
    "EOS",
    "XTZ",
    "SOL",
]

EVM_LIST = [
    "ETH",
    "BSC",
    "MATIC",
    "FTM",
    "OP",
    "METIS",
    "CELO",
    "GLMR",
    "ARB",
    "AVAX",
]

NFT_LIST = [
    "ETH",
    "MATIC",
    "OP",
    "ARB",
    "AVAX",
]

DEVICES_LIST = [
    "SeedWatcher",
    "LocalFile",
    "Ledger",
    "Cryptnox",
    "OpenPGP",
]

DEFAULT_PASSWORD = "NoPasswd"


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


class DisplayTimer(wx.Timer):
    def __init__(self):
        wx.Timer.__init__(self)

    def Notify(self):
        wx.CallAfter(app.display_balance)


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
    app.info_modal("Transaction sent", message)


def watch_messages():
    """Watch for messages received.
    For some wallet types such as WalletConnect.
    """
    try:
        app.wallet.get_messages()
    except NotEnoughTokens as exc:
        app.warn_modal(str(exc))
    except Exception as exc:
        if str(exc).startswith("You rejected the"):
            app.warn_modal(str(exc))
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
    app.start_wallet_panel()
    app.gui_panel.btn_chkaddr.Hide()
    app.gui_panel.network_choice.Clear()
    app.gui_panel.network_choice.Enable()
    if app.wallet.coin not in ["BTC", "XTZ"]:
        app.gui_panel.wallopt_choice.Enable()
        app.gui_panel.wallopt_label.Enable()
    networks = app.wallet.get_networks()
    acc_types = app.wallet.get_account_types()
    for netw in networks:
        app.gui_panel.network_choice.Append(netw)
    app.add_wallet_types(acc_types)
    app.gui_panel.network_choice.SetSelection(0)
    app.gui_panel.wallopt_choice.SetSelection(waltype)
    app.deactivate_option_buttons()
    app.current_chain = app.wallet.coin
    if app.wallet.coin in EVM_LIST:
        app.activate_option_buttons()
        app.gui_panel.but_opt_tok.Bind(
            wx.EVT_BUTTON, lambda x: process_coin_select(app.wallet.coin, 0, 1)
        )
        if app.wallet.coin in NFT_LIST:
            app.gui_panel.but_opt_nft.Bind(
                wx.EVT_BUTTON, lambda x: process_coin_select(app.wallet.coin, 0, 3)
            )
        else:
            app.gui_panel.but_opt_nft.Hide()
        app.gui_panel.but_opt_wc.Bind(
            wx.EVT_BUTTON, lambda x: process_coin_select(app.wallet.coin, 0, 2)
        )
    app.gui_panel.network_choice.Bind(
        wx.EVT_CHOICE, lambda x: net_selected(app.wallet.coin, x.GetInt())
    )
    app.gui_panel.wallopt_choice.Bind(wx.EVT_CHOICE, lambda x: wtype_selected(app.wallet.coin, x))

    coin_button = wx.BitmapButton(
        app.gui_panel.scrolled_coins,
        wx.ID_ANY,
        wx.NullBitmap,
        wx.DefaultPosition,
        wx.DefaultSize,
        wx.BU_AUTODRAW | wx.BORDER_NONE,
    )
    chain_img = "arb" if app.wallet.coin == "ARB/ETH" else app.wallet.coin.lower()
    img = wx.Image(file_path(f"gui/images/icons/{chain_img}.png"), wx.BITMAP_TYPE_PNG)
    img.Rescale(48, 48, wx.IMAGE_QUALITY_BILINEAR)
    img.Resize(wx.Size(58, 56), wx.Point(5, 4), red=-1, green=-1, blue=-1)
    bmp = wx.Bitmap(img)
    coin_button.SetBackgroundColour(wx.Colour(248, 250, 252))
    coin_button.SetBitmap(bmp)
    sizer = wx.BoxSizer(wx.VERTICAL)
    sizer.Add(coin_button, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.BOTTOM | wx.TOP, 6)
    app.gui_panel.scrolled_coins.SetSizer(sizer)
    app.gui_panel.scrolled_coins.Layout()
    app.gui_panel.Layout()
    app.gui_frame.Layout()
    display_coin(app.wallet.get_account())


def device_selected(sel_device):
    close_device()
    device_sel_name = DEVICES_LIST[sel_device]
    coins_list = ccopy(SUPPORTED_COINS)
    if device_sel_name == "Ledger":
        coins_list = EVM_LIST
    if device_sel_name == "OpenPGP":
        coins_list.remove("SOL")
    if device_sel_name == "Cryptnox":
        coins_list.remove("SOL")
    if sel_device == 0:
        # Seed Watcher
        start_seedwatcher(app, cb_open_wallet)
    if sel_device > 0:
        # Real keys device
        the_device = get_device_class(device_sel_name)
        try:
            device_loaded = the_device()
        except Exception as exc:
            # app.gui_panel.devices_choice.SetSelection(0)
            logger.error(
                "Error during device loading : %s", str(exc), exc_info=exc, stack_info=True
            )
            app.warn_modal(str(exc))
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
                                # app.gui_panel.devices_choice.SetSelection(0)
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
                        # app.gui_panel.devices_choice.SetSelection(0)
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
                        admin_password = app.get_password(device_sel_name, set_admin_message)
                        if admin_password is None:
                            # app.gui_panel.devices_choice.SetSelection(0)
                            return
                        if admin_password == "":
                            admin_password = device_loaded.default_admin_password
                        if (
                            len(admin_password) >= device_loaded.admin_pwd_minlen
                            and len(admin_password) <= device_loaded.admin_pwd_maxlen
                        ):
                            break
                        app.warn_modal(
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
                        password = app.get_password(device_sel_name, inp_message)
                        if password is None:
                            # app.gui_panel.devices_choice.SetSelection(0)
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
                        app.warn_modal(
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
                    # app.gui_panel.devices_choice.SetSelection(0)
                    logger.error(
                        "Error during device initialization : %s",
                        {str(exc)},
                        exc_info=exc,
                        stack_info=True,
                    )
                    app.warn_modal(str(exc))
                    return
            except pwdException as excp:
                if not device_loaded.password_retries_inf:
                    try:
                        pin_left = device_loaded.get_pw_left()
                    except Exception as exc:
                        app.device_error(exc)
                        return
                    if pin_left == 0:
                        app.warn_modal(f"Device {pwd_pin} is locked.")
                        return
                    if (
                        the_device.password_softlock > 0
                        and pin_left == the_device.password_softlock
                        and str(excp) == "0"
                    ):
                        app.warn_modal(f"Device {pwd_pin} is soft locked. Restart it to try again.")
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
                    password_default = app.get_password(device_sel_name, inp_message)
                    if password_default is None:
                        # app.gui_panel.devices_choice.SetSelection(0)
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
                    app.warn_modal(
                        wmsg,
                        True,
                    )
            except Exception as exc:
                return app.device_error(exc)
        wx.MilliSleep(100)
        if the_device.has_password and the_device.is_HD and not the_device.password_retries_inf:
            # Kind of special for Cryptnox for now
            device_loaded.set_path(HDwallet_settings)
        app.device = device_loaded
        if app.device.created:
            app.info_modal(
                "Device created",
                f"A new {device_sel_name} device was successfully created.",
            )
        return coins_list


def wallet_fallback():
    """Called when a user option failed"""
    # Reset the wallet to the first type
    wallet_type_fallback = 0
    app.gui_panel.wallopt_choice.SetSelection(wallet_type_fallback)
    app.gui_panel.scrolled_coins.Enable()


def wallet_error(exc, level="hard"):
    """Process wallet exception"""
    if level == "hard":
        app.gui_panel.network_choice.Clear()
        app.clear_coin_selected()
        app.deactivate_option_buttons()
        app.gui_panel.wallopt_choice.Clear()
        app.gui_panel.wallopt_choice.Disable()
        app.gui_panel.btn_chkaddr.Disable()
    if hasattr(app, "wallet"):
        erase_option = app.wallet.coin != "BTC"
    else:
        app.clear_coin_selected()
        app.current_chain = ""
        erase_option = False
    app.erase_info(erase_option)
    logger.error("Error in the wallet : %s", str(exc), exc_info=exc, stack_info=True)
    if level == "fromwatch":
        exc = str(exc) + "\nYou can reconnect by selecting the network option."
        app.deactivate_option_buttons()
    app.gui_panel.scrolled_coins.Enable()
    app.warn_modal(str(exc))


def set_coin(coin, network, wallet_type):
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
                option_value = app.get_option(network, option_info["prompt"], option_preset)
                if option_value is None:
                    wx.CallAfter(wallet_fallback)
                    return
        key_type = get_coin_class(coin).get_key_type(wallet_type)
        if not app.check_coin_consistency(get_coin_class(coin), network):
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
        if not app.check_coin_consistency(network_num=network):
            return
        account_id = app.wallet.get_account()
        if not app.check_coin_consistency(network_num=network):
            return
        app.gui_panel.btn_chkaddr.Enable()
        if option_info is not None and option_info.get("use_get_messages", False):
            app.wallet.wc_timer = wx.Timer()
            app.wallet.wc_timer.Notify = watch_messages
    except InvalidOption as exc:
        app.warn_modal(str(exc))
        wx.CallAfter(wallet_fallback)
        return
    except Exception as exc:
        if str(exc).endswith("disconnected."):
            app.device_error(exc)
        else:
            wallet_error(exc)
        return
    if not app.check_coin_consistency(network_num=network):
        return
    if app.gui_panel.network_choice.GetSelection() > 0 and app.current_chain != "GLMR":
        # Testnet
        app.wallet.coin = "t" + app.wallet.coin
    app.gui_panel.scrolled_coins.Enable()
    app.gui_panel.txt_fiat.SetLabel("$ 0")

    app.gui_panel.but_opt_tok.Enable()
    app.gui_panel.but_opt_nft.Enable()
    app.gui_panel.but_opt_wc.Enable()

    # Detect is token or wallet connect
    if coin in EVM_LIST:
        call_return = lambda x: process_coin_select(coin, network, 0)
        if wallet_type == 1:
            btn = app.token_started()
            btn.Bind(wx.EVT_BUTTON, call_return)
        if wallet_type == 2:
            btn = app.wc_started()
            btn.Bind(wx.EVT_BUTTON, call_return)
        if wallet_type == 3:
            # NFT
            app.gui_panel.fiat_panel.Hide()
            if hasattr(app.gui_panel, "fiat_price"):
                del app.gui_panel.fiat_price
            nft_wallet = NFTWallet(app.wallet)
            app.gui_frame.Hide()
            Gallery(app.gui_frame, nft_wallet, call_return)
            return
    app.gui_panel.fiat_panel.Hide()
    if hasattr(app.gui_panel, "fiat_price"):
        del app.gui_panel.fiat_price
    display_coin(account_id)


def display_coin(account_addr):
    if not app.check_coin_consistency():
        return
    app.gui_panel.account_addr.SetLabel(account_addr)
    app.gui_panel.qr_button.Enable()
    app.gui_panel.copy_button.Enable()
    app.gui_panel.hist_button.Enable()
    app.gui_panel.balance_info.SetLabel(f"  ...  ")
    app.gui_panel.account_addr.Layout()
    if hasattr(app, "balance_timer"):
        app.balance_timer.Stop()
    app.balance_timer = DisplayTimer()
    app.balance_timer.Start(12000)
    if hasattr(app.wallet, "wc_timer"):
        app.wallet.wc_timer.Start(2500, oneShot=wx.TIMER_CONTINUOUS)
    app.gui_frame.Refresh()
    app.gui_frame.Update()
    app.gui_frame.Layout()
    wx.CallAfter(app.display_balance)


def process_coin_select(coin, sel_network, sel_wallettype):
    app.gui_panel.network_choice.Enable()
    if len(app.gui_panel.scrolled_coins.GetChildren()) > 1 or app.current_chain != "BTC":
        # Because BTC wallet types are different path/wallet from SeedWatcher
        app.gui_panel.wallopt_choice.Enable()
        app.gui_panel.wallopt_label.Enable()
    app.deactivate_option_buttons()
    app.gui_panel.btn_chkaddr.Disable()
    if coin in EVM_LIST:
        app.activate_option_buttons()
        app.gui_panel.but_opt_tok.Bind(
            wx.EVT_BUTTON, lambda x: process_coin_select(coin, sel_network, 1)
        )
        if coin in NFT_LIST:
            app.gui_panel.but_opt_nft.Bind(
                wx.EVT_BUTTON, lambda x: process_coin_select(coin, sel_network, 3)
            )
        else:
            app.gui_panel.but_opt_nft.Hide()
        app.gui_panel.but_opt_wc.Bind(
            wx.EVT_BUTTON, lambda x: process_coin_select(coin, sel_network, 2)
        )
        app.gui_panel.wallopt_choice.Disable()
        app.gui_panel.m_panel1.Layout()
    app.gui_panel.network_choice.Bind(wx.EVT_CHOICE, lambda x: net_selected(coin, x.GetInt()))
    app.gui_panel.wallopt_choice.Bind(wx.EVT_CHOICE, lambda x: wtype_selected(coin, x))
    set_coin(coin, sel_network, sel_wallettype)


def coin_selected(coin_name):
    app.gui_panel.network_choice.Clear()
    app.erase_info(True)
    networks = get_coin_class(coin_name).get_networks()
    acc_types = get_coin_class(coin_name).get_account_types()
    for netw in networks:
        app.gui_panel.network_choice.Append(netw)
    app.add_wallet_types(acc_types)
    sele_network = 0
    sele_wttype = 0
    app.gui_panel.network_choice.SetSelection(sele_network)
    app.gui_panel.wallopt_choice.SetSelection(sele_wttype)
    app.gui_panel.btn_chkaddr.Disable()
    wx.CallLater(180, process_coin_select, coin_name, sele_network, sele_wttype)


def net_selected(coin_sel, net_sel):
    app.erase_info()
    app.gui_panel.btn_chkaddr.Disable()
    wtype_sel = app.gui_panel.wallopt_choice.GetSelection()
    wx.CallLater(180, process_coin_select, coin_sel, net_sel, wtype_sel)


def wtype_selected(coin_sel, wtype_sel):
    app.erase_info()
    app.gui_panel.btn_chkaddr.Disable()
    net_sel = app.gui_panel.network_choice.GetSelection()
    wx.CallLater(180, process_coin_select, coin_sel, net_sel, wtype_sel.GetInt())


def perform_transfer(to, amnt, fees, status_modal):
    try:
        if amnt == "ALL":
            tx_info = app.wallet.transfer_all(to, fees)
        else:
            tx_info = app.wallet.transfer(amnt, to, fees)
        status_modal.Update(100, "done")
        status_modal.Fit()
        tx_success(tx_info)
    except Exception as exc:
        status_modal.Update(100)
        wx.MilliSleep(100)
        status_modal.Destroy()
        wx.MilliSleep(100)
        logger.error(
            "Error during the transaction processing : %s",
            str(exc),
            exc_info=exc,
            stack_info=True,
        )
        if str(exc).endswith("disconnected."):
            app.device_error(exc)
        elif str(exc) == "Error status : 0x6600":
            app.warn_modal("User button on PGP device timeout")
        else:
            app.warn_modal(str(exc))
        wx.MilliSleep(250)


def transfer(to, amount, fee_opt=1):
    progress_modal = wx.ProgressDialog(
        "Processing transaction",
        "",
        style=wx.PD_APP_MODAL | wx.PD_AUTO_HIDE | wx.PD_SMOOTH,
        parent=app.gui_frame,
    )
    wait_msg = "Buiding and signing the transaction"
    if app.wallet.current_device.has_hardware_button:
        wait_msg += "\nPress the button on the physical device to confirm."
    progress_modal.Update(50, wait_msg)
    progress_modal.Fit()
    wx.CallLater(250, perform_transfer, to, amount, fee_opt, progress_modal)


def start_main_app():
    app.gui_frame.SetLabel(f"  Uniblow  -  {VERSION}")
    app.gui_frame.Show()


if __name__ == "__main__":

    app = gui.app.UniblowApp(DEVICES_LIST, get_coin_class)
    app.dev_selected = device_selected
    app.coin_selected = coin_selected
    app.transfer = transfer

    if "-v" in argv[1:]:
        basicConfig(level=DEBUG)

    start_main_app()
    app.MainLoop()
