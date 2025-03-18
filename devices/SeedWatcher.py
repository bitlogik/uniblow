#!/usr/bin/python3
# -*- coding: utf8 -*-

# UNIBLOW Seed Watcher keys device
# Copyright (C) 2021-2023 BitLogiK

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
from threading import Thread
import webbrowser
from wx import (
    CallAfter,
    Menu,
    MenuItem,
    EVT_MENU,
    Bitmap,
    dataview,
    TheClipboard,
    NOT_FOUND,
    MessageDialog,
    STAY_ON_TOP,
    CENTER,
    DefaultPosition,
    IconBundle,
    Cursor,
    CURSOR_HAND,
    BITMAP_TYPE_PNG,
    TextDataObject,
    Font,
    FontInfo,
)
import gui.swgui
from gui.app import file_path, scaleSize
from cryptolib.HDwallet import (
    HD_Wallet,
    generate_mnemonic,
    bip39_is_checksum_valid,
    ElectrumOldWallet,
)
from cryptolib.slip39 import slip39_is_checksum_valid


from wallets.BTCwallet import BTC_wallet
from wallets.ETHwallet import ETH_wallet
from wallets.BSCwallet import BSC_wallet
from wallets.MATICwallet import MATIC_wallet
from wallets.TRXwallet import TRX_wallet
from wallets.GNOwallet import GNO_wallet
from wallets.FTMwallet import FTM_wallet
from wallets.OPwallet import OP_wallet
from wallets.BASEwallet import BASE_wallet
from wallets.METISwallet import METIS_wallet
from wallets.CELOwallet import CELO_wallet
from wallets.GLMRwallet import GLMR_wallet
from wallets.AVAXwallet import AVAX_wallet
from wallets.ARBwallet import ARB_wallet
from wallets.LTCwallet import LTC_wallet
from wallets.DOGEwallet import DOGE_wallet
from wallets.EOSwallet import EOS_wallet
from wallets.XTZwallet import XTZ_wallet
from wallets.SOLwallet import SOL_wallet

coins_list = [
    {"name": "Bitcoin Legacy", "path": "m/44'/0'/{}'/{}/{}", "wallet_lib": BTC_wallet, "type": 0},
    {"name": "Bitcoin P2WSH", "path": "m/49'/ 0'/{}'/{}/{}", "wallet_lib": BTC_wallet, "type": 1},
    {"name": "Bitcoin SegWit", "path": "m/84'/ 0'/{}'/{}/{}", "wallet_lib": BTC_wallet, "type": 2},
    {"name": "Ethereum", "path": "m/44'/60'/{}'/{}/{}", "wallet_lib": ETH_wallet},
    {"name": "Eth (alt. deriv1)", "path": "m/44'/60'/{0}'/{2}", "wallet_lib": ETH_wallet},
    {"name": "Eth (alt. deriv2)", "path": "m/44'/60'/{0}/{2}", "wallet_lib": ETH_wallet},
    {"name": "BSC", "path": "m/44'/60'/{}'/{}/{}", "wallet_lib": BSC_wallet},
    {"name": "Polygon PoS", "path": "m/44'/60'/{}'/{}/{}", "wallet_lib": MATIC_wallet},
    {"name": "TRON", "path": "m/44'/195'/{}'/{}/{}", "wallet_lib": TRX_wallet},
    {"name": "TRON (alt. deriv)", "path": "m/44'/195'/{2}'", "wallet_lib": TRX_wallet},
    {"name": "Gnosis", "path": "m/44'/60'/{}'/{}/{}", "wallet_lib": GNO_wallet},
    {"name": "Fantom", "path": "m/44'/60'/{}'/{}/{}", "wallet_lib": FTM_wallet},
    {"name": "Sonic", "path": "m/44'/60'/{}'/{}/{}", "wallet_lib": FTM_wallet, "network": 1},
    {"name": "OP", "path": "m/44'/60'/{}'/{}/{}", "wallet_lib": OP_wallet},
    {"name": "Base", "path": "m/44'/60'/{}'/{}/{}", "wallet_lib": BASE_wallet},
    {"name": "METIS", "path": "m/44'/60'/{}'/{}/{}", "wallet_lib": METIS_wallet},
    {"name": "CELO", "path": "m/44'/60'/{}'/{}/{}", "wallet_lib": CELO_wallet},
    {"name": "GLMR", "path": "m/44'/60'/{}'/{}/{}", "wallet_lib": GLMR_wallet, "network": 0},
    {"name": "MOVR", "path": "m/44'/60'/{}'/{}/{}", "wallet_lib": GLMR_wallet, "network": 1},
    {"name": "ARB", "path": "m/44'/60'/{}'/{}/{}", "wallet_lib": ARB_wallet},
    {"name": "AVAX", "path": "m/44'/60'/{}'/{}/{}", "wallet_lib": AVAX_wallet},
    {"name": "Litecoin", "path": "m/44'/2'/{}'/{}/{}", "wallet_lib": LTC_wallet},
    {"name": "Dogecoin", "path": "m/44'/3'/{}'/{}/{}", "wallet_lib": DOGE_wallet},
    {"name": "EOSio", "path": "m/44'/194'/{}'/{}/{}", "wallet_lib": EOS_wallet},
    {"name": "Tezos tz1", "path": "m/44'/1729'/{0}'/{2}", "wallet_lib": XTZ_wallet, "type": 1},
    {"name": "Tezos tz2", "path": "m/44'/1729'/{}'/{}/{}", "wallet_lib": XTZ_wallet, "type": 0},
    {"name": "Solana", "path": "m/44'/501'/{0}'/{2}", "wallet_lib": SOL_wallet},
    {"name": "Solana (alt. deriv)", "path": "m/44'/501'/{2}", "wallet_lib": SOL_wallet},
]

WORDSLEN_LIST = ["12 words", "15 words", "18 words", "21 words", "24 words"]


logger = getLogger(__name__)


def open_explorer(explorer_url):
    webbrowser.open(explorer_url, new=1, autoraise=True)


class SeedDevice:
    def __init__(self, ecpair):
        self.ecpair = ecpair

    def get_public_key(self):
        return self.ecpair.get_public_key()


class blockchainWallet:
    def __init__(self, coin_data, device, deriv_type):
        self.name = coin_data["name"]
        wallet_netw = coin_data.get("network", 0)
        wallet_type = coin_data.get("type", 0)
        if self.name == "Bitcoin Legacy" and deriv_type == 2:
            # This is Electrum Old derivation wallet, set public key as uncompressed
            self.wallet = coin_data["wallet_lib"](wallet_netw, wallet_type, device, False)
        else:
            self.wallet = coin_data["wallet_lib"](wallet_netw, wallet_type, device)


class ContextOptionsMenu(Menu):
    def __init__(self, parent):
        Menu.__init__(self)
        self.parent = parent

        men1 = MenuItem(self, 1, "Copy address")
        self.Append(men1)
        self.Bind(EVT_MENU, self.parent.copy_account, men1)

        men2 = MenuItem(self, 2, "Open block explorer")
        self.Append(men2)
        self.Bind(EVT_MENU, self.parent.open_explorer, men2)

        men3 = MenuItem(self, 3, "Open in wallet")
        self.Append(men3)
        self.Bind(EVT_MENU, self.parent.open_wallet, men3)


class SeedWatcherFrame(gui.swgui.MainFrame):
    def closesw(self, event):
        event.Skip()
        gui_frm = self.GetParent()
        gui_frm.swrun = False
        gui_frm.Show()


class SeedWatcherPanel(gui.swgui.MainPanel):
    def mnemo_changed(self, event):
        event.Skip()
        mneno = self.m_typechoice.GetSelection()
        if mneno > 1:
            self.m_staticText5.Hide()
            self.m_staticText6.Hide()
            self.m_bitmap_wl.Hide()
            self.m_bitmap_cs.Hide()
        else:
            self.m_staticText5.Show()
            self.m_staticText6.Show()
            self.m_bitmap_wl.Show()
            self.m_bitmap_cs.Show()
            self.m_bitmap_wl.SetBitmap(self.BAD_BMP)
            self.m_bitmap_cs.SetBitmap(self.BAD_BMP)
        self.m_dataViewListCtrl1.DeleteAllItems()
        self.m_staticTextcopy.Disable()
        self.check_mnemonic(mneno)

    def gen_new_mnemonic(self, event):
        event.Skip()
        seli = self.m_choice_nwords.GetSelection()
        selnw = int(WORDSLEN_LIST[seli][:2])
        self.generate_mnemonic(selnw)

    def initialize(self, cb_wallet):
        self.GOOD_BMP = Bitmap(file_path("gui/images/good.png"))
        self.BAD_BMP = Bitmap(file_path("gui/images/bad.png"))
        self.m_choice_nwords.Set(WORDSLEN_LIST)
        self.m_choice_nwords.SetSelection(0)
        ctab = self.m_dataViewListCtrl1
        dv1 = dataview.DataViewColumn("Name", dataview.DataViewTextRenderer(), 0)
        dv1.SetWidth(125)
        ctab.AppendColumn(dv1)
        dv2 = dataview.DataViewColumn("Account", dataview.DataViewTextRenderer(), 1)
        dv2.SetWidth(372)
        ctab.AppendColumn(dv2)
        dv3 = dataview.DataViewColumn("Balance", dataview.DataViewTextRenderer(), 2)
        dv3.SetWidth(86)
        ctab.AppendColumn(dv3)
        self.m_bitmap_wl.SetBitmap(self.BAD_BMP)
        self.m_bitmap_cs.SetBitmap(self.BAD_BMP)
        self.cb_wallet = cb_wallet

    def generate_mnemonic(self, n_words):
        self.m_typechoice.SetSelection(0)
        mnemonic = generate_mnemonic(n_words)
        # Trigger wallet table computations
        self.fill_mnemonic(mnemonic)

    def fill_mnemonic(self, mnemo):
        self.m_textCtrl_mnemo.SetValue(mnemo)

    def display_coin(self, coin):
        try:
            coin_balance = coin.wallet.get_balance()
            if coin_balance.startswith("Register"):
                coin_balance = "No account"
            coin_info = [coin.name, coin.wallet.get_account(), coin_balance]
        except Exception as exc:
            logger.error("Error when reading info for %s (skipped) : ", coin.name, exc_info=exc)
            raise
        else:
            if self.__nonzero__():
                self.m_dataViewListCtrl1.AppendItem(coin_info)
                self.m_dataViewListCtrl1.SetRowHeight(28)

    def get_coin_info(self, coin_idx, seed):
        coin = coins_list[coin_idx]
        cpath = coin["path"]
        if not self.__nonzero__():
            # Panel was closed
            return
        derivation_type_code = self.m_typechoice.GetSelection()
        if derivation_type_code == 2:
            # Electrum special path
            if coin["name"][:8] != "Bitcoin ":
                # Use only Bitcoin for the Electrum seed
                self.enable_inputs()
                return
            if coin["type"] == 0:
                # standard
                cpath = "m/{1}/{2}"
            elif coin["type"] == 1 or coin["type"] == 2:
                # p2wsh and segwit
                cpath = "m/{}'/{}/{}"
        if derivation_type_code == 3:
            if coin["name"] != "Bitcoin Legacy":
                # Use only Bitcoin legacy for the Electrum seed
                self.enable_inputs()
                return
            cpath = "m/{1}/{2}"
        if not self.__nonzero__():
            # Panel was closed
            return
        account_idx = str(self.m_account.GetValue())
        is_change = self.is_change.GetValue()
        address_idx = str(self.m_index.GetValue())
        change_idx = 0
        if is_change:
            change_idx = 1
        path = cpath.format(account_idx, change_idx, address_idx)
        key_type = coin["wallet_lib"].get_key_type(coin.get("type", 0))
        if key_type == "ED":
            # Only for last, means all the index down to m shall be hardened
            path += "'"

        if derivation_type_code == 3:
            wallet = ElectrumOldWallet.from_seed(seed)
        else:
            wallet = HD_Wallet.from_seed(seed, key_type)

        pv_key = wallet.derive_key(path)

        coin_key = SeedDevice(pv_key)
        try:
            coin_wallet = blockchainWallet(coin, coin_key, derivation_type_code)
            self.coins.append(coin_wallet)
            CallAfter(self.display_coin, coin_wallet)
        except Exception as exc:
            # Add dummy to stay sync for wallet open
            # Will get the coins index from the displayed row with seekfor_row_wallet
            self.coins.append(None)
            logger.error("Error when getting coin info : %s", str(exc), exc_info=exc)
        if coin_idx < len(coins_list) - 1 and self.__nonzero__():
            # Call for next
            self.async_getcoininfo_idx(coin_idx + 1, seed)
        else:
            # List is finished
            CallAfter(self.enable_inputs)

    def disable_inputs(self):
        self.m_btnseek.Disable()
        self.m_staticTextcopy.Disable()
        self.m_account.Disable()
        self.is_change.Enable()
        self.m_index.Disable()
        self.Disable()

    def enable_inputs(self):
        if self.__nonzero__():
            self.m_btnseek.Enable()
            self.m_staticTextcopy.Enable()
            self.m_account.Enable()
            self.is_change.Enable()
            self.m_index.Enable()
            CallAfter(self.Enable)

    def async_getcoininfo_idx(self, coin_idx, seed):
        getcoin = Thread(target=self.get_coin_info, args=[coin_idx, seed])
        getcoin.start()

    def compute_seed(self, *args):
        try:
            wallet_seed = HD_Wallet.seed_from_mnemonic(*args)
        except Exception as exc:
            error_modal = MessageDialog(
                self,
                "Cannot watch for this wallet\n\n"
                "Because of the following reason:"
                f"\n{str(exc)}.\n\n",
                "Watch Error",
                STAY_ON_TOP | CENTER,
                DefaultPosition,
            )
            error_modal.ShowModal()
            self.enable_inputs()
            return
        self.async_getcoininfo_idx(0, wallet_seed)

    def check_mnemonic(self, mnemo_type):
        """Recompute HD wallet keys"""
        if mnemo_type == 0:
            # BIP39
            test_checksum = bip39_is_checksum_valid
        elif mnemo_type == 1:
            test_checksum = slip39_is_checksum_valid
        else:
            raise Exception("Invalid derivation type for checksum")
        cs, wl = test_checksum(self.m_textCtrl_mnemo.GetValue())
        if wl:
            self.m_bitmap_wl.SetBitmap(self.GOOD_BMP)
        if cs:
            self.m_bitmap_cs.SetBitmap(self.GOOD_BMP)

    def seek_assets(self, event):
        event.Skip()
        self.m_dataViewListCtrl1.DeleteAllItems()
        self.disable_inputs()
        self.coins = []
        mnemo_txt = self.m_textCtrl_mnemo.GetValue()
        password = self.m_textpwd.GetValue()
        if self.m_typechoice.GetSelection() == 4:
            derivation = "BOOST"
        elif self.m_typechoice.GetSelection() == 1:
            derivation = "SLIP39"
        elif self.m_typechoice.GetSelection() == 2:
            derivation = "Electrum"
        elif self.m_typechoice.GetSelection() == 3:
            derivation = "ElectrumOLD"
        else:
            derivation = "BIP39"
        task_compute_seed = Thread(target=self.compute_seed, args=(mnemo_txt, password, derivation))
        task_compute_seed.start()

    def pop_menu(self, event):
        event.Skip()
        if self.m_dataViewListCtrl1.GetItemCount() > 0:
            self.PopupMenu(ContextOptionsMenu(self))

    def copy_account(self, event):
        if TheClipboard.IsOpened() or TheClipboard.Open():
            TheClipboard.Clear()
            sel_row = self.m_dataViewListCtrl1.GetSelectedRow()
            if sel_row == NOT_FOUND:
                return
            addr = self.m_dataViewListCtrl1.GetTextValue(sel_row, 1)
            TheClipboard.SetData(TextDataObject(addr))
            TheClipboard.Flush()
            TheClipboard.Close()
            copied_modal = MessageDialog(
                self,
                f"Account address {addr}\nwas copied in the clipboard",
                "Address copied",
                STAY_ON_TOP | CENTER,
                DefaultPosition,
            )
            copied_modal.ShowModal()

    def open_explorer(self, event):
        sel_row = self.m_dataViewListCtrl1.GetSelectedRow()
        if sel_row == NOT_FOUND:
            return
        sel_wallet = self.seekfor_row_wallet(sel_row)
        if sel_wallet is None:
            return
        open_explorer(self.coins[sel_wallet].wallet.history())

    def seekfor_row_wallet(self, row_index):
        """Give the coins_list index from the row index"""
        target_name = self.m_dataViewListCtrl1.GetTextValue(row_index, 0)
        coins_wallet_index = 0
        while coins_list[coins_wallet_index]["name"] != target_name:
            coins_wallet_index += 1
            if coins_wallet_index >= len(coins_list):
                return None
        return coins_wallet_index

    def open_wallet(self, evt):
        sel_row = self.m_dataViewListCtrl1.GetSelectedRow()
        if sel_row == NOT_FOUND:
            return
        sel_wallet = self.seekfor_row_wallet(sel_row)
        if sel_wallet is None:
            return
        wallet_type = coins_list[sel_wallet].get("type", 0)
        wallet_open = partial(coins_list[sel_wallet]["wallet_lib"], 0, wallet_type)
        key = self.coins[sel_wallet].wallet.current_device.ecpair
        pkcpr = True
        if wallet_type == 0 and self.m_typechoice.GetSelection() == 3:
            # Special case for Bitcoin Electrum old
            pkcpr = False
        self.cb_wallet(wallet_open, key, wallet_type, self.GetParent(), pkcpr)


def start_seedwatcher(app, cb_wallet):
    app.frame_sw = SeedWatcherFrame(app.gui_frame)
    app.frame_sw.SetMinSize(scaleSize(app.frame_sw, (650, 720)))
    app.frame_sw.SetSize(scaleSize(app.frame_sw, (650, 720)))
    app.gui_frame.swrun = True
    app.frame_sw.SetIcons(IconBundle(file_path("gui/uniblow.ico")))
    HAND_CURSOR = Cursor(CURSOR_HAND)
    app.gui_frame.Hide()
    app.panel_sw = SeedWatcherPanel(app.frame_sw)
    app.panel_sw.m_textCtrl_mnemo.SetFocus()
    if sys.platform.startswith("darwin"):
        app.panel_sw.m_staticTextcopy.SetLabel(
            "Select asset line, then right click on it to open menu"
        )

    app.panel_sw.m_button_gen.SetBitmap(
        Bitmap(file_path("gui/images/btns/GenSeed.png"), BITMAP_TYPE_PNG)
    )
    app.panel_sw.m_btnseek.SetBitmap(
        Bitmap(file_path("gui/images/btns/SeekAssets.png"), BITMAP_TYPE_PNG)
    )

    app.panel_sw.m_button_gen.SetCursor(HAND_CURSOR)
    app.panel_sw.m_choice_nwords.SetCursor(HAND_CURSOR)
    app.panel_sw.m_typechoice.SetCursor(HAND_CURSOR)
    app.panel_sw.m_btnseek.SetCursor(HAND_CURSOR)
    if sys.platform.startswith("darwin"):
        app.panel_sw.m_textCtrl_mnemo.SetFont(Font(FontInfo(18)))
    app.panel_sw.initialize(cb_wallet)
    app.frame_sw.Show()
