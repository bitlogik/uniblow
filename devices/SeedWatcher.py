import sys
import wx
import gui.swgui
from gui.app import file_path
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
    {"name": "Bitcoin Legacy", "path": "m/44'/ 0'/0'/0/", "wallet_lib": BTC_wallet, "type": 0},
    {"name": "Bitcoin WP2SH", "path": "m/49'/ 0'/0'/0/", "wallet_lib": BTC_wallet, "type": 1},
    {"name": "Bitcoin SegWit", "path": "m/84'/ 0'/0'/0/", "wallet_lib": BTC_wallet, "type": 2},
    {"name": "Ethereum", "path": "m/44'/60'/0'/0/", "wallet_lib": ETH_wallet},
    {"name": "BSC", "path": "m/44'/60'/0'/0/", "wallet_lib": BSC_wallet},
    # {"name": "Binance", "path": "m/44'/714'/0'/0/", "wallet_lib": BNB_wallet},
    {"name": "Litecoin", "path": "m/44'/2'/0'/0/", "wallet_lib": LTC_wallet},
    {"name": "Dogecoin", "path": "m/44'/3'/0'/0/", "wallet_lib": DOGE_wallet},
    # {"name": "EOSio", "path": "m/44'/194'/0'/0/", "wallet_lib": EOS_wallet},
    {"name": "Tezos", "path": "m/44'/1729'/0'/0/", "wallet_lib": XTZ_wallet},
]

WORDSLEN_LIST = ["12 words", "15 words", "18 words", "21 words", "24 words"]


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
        self.m_dataViewListCtrl1.DeleteAllItems()
        self.m_bitmap_wl.SetBitmap(self.BAD_BMP)
        self.m_bitmap_cs.SetBitmap(self.BAD_BMP)
        self.check_mnemonic()

    def gen_new_mnemonic(self, event):
        event.Skip()
        seli = self.m_choice_nwords.GetSelection()
        selnw = int(WORDSLEN_LIST[seli][:2])
        self.generate_mnemonic(selnw)

    def initialize(self):
        self.GOOD_BMP = wx.Bitmap(file_path("gui/good.bmp"))
        self.BAD_BMP = wx.Bitmap(file_path("gui/bad.bmp"))
        self.m_choice_nwords.Set(WORDSLEN_LIST)
        self.m_choice_nwords.SetSelection(0)
        ctab = self.m_dataViewListCtrl1
        dv1 = wx.dataview.DataViewColumn("Name", wx.dataview.DataViewTextRenderer(), 0)
        ctab.AppendColumn(dv1)
        dv2 = wx.dataview.DataViewColumn("Account", wx.dataview.DataViewTextRenderer(), 1)
        dv2.SetWidth(380)
        ctab.AppendColumn(dv2)
        dv3 = wx.dataview.DataViewColumn("Balance", wx.dataview.DataViewTextRenderer(), 2)
        ctab.AppendColumn(dv3)

    def generate_mnemonic(self, n_words):
        mnemonic = generate_mnemonic(n_words)
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
        self.m_btnseek.Enable()
        self.m_dataViewListCtrl1.SetRowHeight(28)

    def check_mnemonic(self):
        """Recompute HD wallet keys"""
        cs, wl = bip39_is_checksum_valid(self.m_textCtrl_mnemo.GetValue())
        if wl:
            self.m_bitmap_wl.SetBitmap(self.GOOD_BMP)
        if cs:
            self.m_bitmap_cs.SetBitmap(self.GOOD_BMP)

    def seek_assets(self, event):
        event.Skip()
        self.m_btnseek.Disable()
        if self.m_SecuBoost.IsChecked():
            derivation = "BOOST"
        else:
            derivation = "BIP39"
        mnemo_txt = self.m_textCtrl_mnemo.GetValue()
        password = self.m_textpwd.GetValue()
        account_idx = str(self.m_account.GetValue())
        wallet = HD_Wallet.from_mnemonic(mnemo_txt, password, derivation)
        coins = []
        for coin in coins_list:
            coin_key = SeedDevice(wallet.derive_key(coin["path"] + account_idx))
            try:
                coin_wallet = blockchainWallet(coin, coin_key)
                coins.append(coin_wallet)
            except Exception as exc:
                if not getattr(sys, "frozen", False):
                    # output the exception when dev environment
                    print(exc)

        self.display_coins(coins)

    def select_coin(self, event):
        event.Skip()
        if wx.TheClipboard.Open():
            wx.TheClipboard.Clear()
            sel_row = self.m_dataViewListCtrl1.ItemToRow(event.GetItem())
            addr = self.m_dataViewListCtrl1.GetTextValue(sel_row, 1)
            wx.TheClipboard.SetData(wx.TextDataObject(addr))
            wx.TheClipboard.Close()
            wx.TheClipboard.Flush()
            copied_modal = wx.MessageDialog(
                self,
                f"Account address {addr}\nwas copied in the clipboard",
                "Copied",
                wx.STAY_ON_TOP | wx.CENTER,
                wx.DefaultPosition,
            )
            copied_modal.ShowModal()


def start_seedwatcher(app):
    app.frame_sw = SeedWatcherFrame(app.gui_frame)
    app.frame_sw.SetIcons(wx.IconBundle(file_path("gui/uniblow.ico")))
    app.gui_panel.devices_choice.SetSelection(0)
    app.gui_frame.Hide()
    app.panel_sw = SeedWatcherPanel(app.frame_sw)
    app.panel_sw.initialize()
    app.frame_sw.Show()
