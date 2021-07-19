import ctypes

import sys
import wx
import gui.swgui

from cryptolib.HDwallet import HD_Wallet, generate_mnemonic, bip39_is_checksum_valid
from wallets.BTCwallet import BTC_wallet
from wallets.ETHwallet import ETH_wallet
from wallets.BSCwallet import BSC_wallet
from wallets.LTCwallet import LTC_wallet
from wallets.DOGEwallet import DOGE_wallet
from wallets.XTZwallet import XTZ_wallet


# from wallets.EOSwallet import EOS_wallet
# from wallets.BNBwallet import BNB_wallet


coins_list = [
    {"name": "Bitcoin", "path": "m/84'/ 0'/0'/0/0", "wallet_lib": BTC_wallet, "type": 2},
    {"name": "Ethereum", "path": "m/44'/60'/0'/0/0", "wallet_lib": ETH_wallet},
    {"name": "BSC", "path": "m/44'/60'/0'/0/0", "wallet_lib": BSC_wallet},
    # {"name": "Binance", "path": "m/44'/714'/0'/0/0", "wallet_lib": BNB_wallet},
    {"name": "Litecoin", "path": "m/44'/2'/0'/0/0", "wallet_lib": LTC_wallet},
    {"name": "Dogecoin", "path": "m/44'/3'/0'/0/0", "wallet_lib": DOGE_wallet},
    # {"name": "EOSio", "path": "m/44'/194'/0'/0/0", "wallet_lib": EOS_wallet},
    {"name": "Tezos", "path": "m/44'/1729'/0'/0/0", "wallet_lib": XTZ_wallet},
]


class SeedDevice:
    def __init__(self, ecpair):
        self.ecpair = ecpair

    def get_public_key(self):
        return self.ecpair.get_public_key().hex()


class blockchainWallet:
    def __init__(self, coin_data, device):
        self.name = coin_data["name"]
        self.path = coin_data["name"]
        wallet_type = coin_data.get("type", 0)
        self.wallet = coin_data["wallet_lib"](0, wallet_type, device)


class SeedWatcherFrame(gui.swgui.MainFrame):
    def closesw(self, event):
        event.Skip()
        self.GetParent().Show()


class SeedWatcherPanel(gui.swgui.MainPanel):
    def mnemo_changed(self, event):
        event.Skip()
        mnemo_txt = event.GetString()
        self.m_dataViewListCtrl1.DeleteAllItems()
        if hasattr(self, "cl"):
            self.cl.Stop()
            self.cl.Start(750, mnemo_txt)
        else:
            self.cl = wx.CallLater(750, self.refresh_wallet, mnemo_txt)

    def goSweep(self, event):
        event.Skip()

    def initialize(self):
        self.GOOD_BMP = wx.Bitmap("gui/good.bmp")
        self.BAD_BMP = wx.Bitmap("gui/bad.bmp")
        ctab = self.m_dataViewListCtrl1
        dv1 = wx.dataview.DataViewColumn("Name", wx.dataview.DataViewTextRenderer(), 0)
        ctab.AppendColumn(dv1)
        dv2 = wx.dataview.DataViewColumn("Account", wx.dataview.DataViewTextRenderer(), 1)
        dv2.SetWidth(400)
        ctab.AppendColumn(dv2)
        dv3 = wx.dataview.DataViewColumn("Balance", wx.dataview.DataViewTextRenderer(), 2)
        ctab.AppendColumn(dv3)

        mnemonic = (
            "rabbit tilt arm protect banner ill "
            "produce vendor april bike much identify "
            "pond upset front easily glass gallery "
            "address hair priority focus forest angle"
        )
        # Trigger wallet table computations
        self.fill_mnemonic(mnemonic)

    def fill_mnemonic(self, mnemo):
        self.m_textCtrl_mnemo.SetValue(mnemo)

    def add_coin(self, coin):
        self.m_dataViewListCtrl1.AppendItem(
            [coin.name, coin.wallet.get_account(), coin.wallet.get_balance()]
        )

    def display_coins(self, coins):
        for coin in coins:
            self.add_coin(coin)
        self.m_dataViewListCtrl1.SetRowHeight(28)

    def refresh_wallet(self, current_mnemonic):
        """Recompute HD wallet keys"""
        cs, wl = bip39_is_checksum_valid(current_mnemonic)
        WLBMP = self.GOOD_BMP if wl else self.BAD_BMP
        CSBMP = self.GOOD_BMP if cs else self.BAD_BMP
        self.m_bitmap_wl.SetBitmap(WLBMP)
        self.m_bitmap_cs.SetBitmap(CSBMP)
        wallet = HD_Wallet.from_mnemonic(current_mnemonic)
        coins = []
        for coin in coins_list:
            coin_key = SeedDevice(wallet.derive_key(coin["path"]))
            try:
                coin_wallet = blockchainWallet(coin, coin_key)
                coins.append(coin_wallet)
            except Exception as exc:
                if not getattr(sys, "frozen", False):
                    # output the exception when dev environment
                    print(exc)

        self.display_coins(coins)


def start_seedwatcher(app):
    app.frame_sw = SeedWatcherFrame(app.gui_frame)
    app.gui_panel.devices_choice.SetSelection(0)
    app.gui_frame.Hide()
    app.panel_sw = SeedWatcherPanel(app.frame_sw)
    app.panel_sw.initialize()
    app.frame_sw.Show()
