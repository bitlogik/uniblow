# -*- coding: utf8 -*-

# UNIBLOW NFT Gallery window
# Copyright (C) 2022- BitLogiK

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3 of the License.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>


from logging import getLogger
from threading import Thread
import webbrowser
import wx

from wallets.ETHwallet import testaddr, ETH_wallet
from wallets.NFTwallet import get_image_file
from wallets.name_service import resolve
from gui.utils import icon_file, file_path
from gui.gallerygui import GalleryFrame, GalleryPanel


logger = getLogger(__name__)


opensea_chains = {
    1: "ethereum",
    137: "matic",
    42161: "arbitrum",
    43114: "avalanche",
    10: "optimism",
    56: "bsc",
}


def opensea_url(chain_id, contract, id):
    chaincode = opensea_chains.get(chain_id)
    if chaincode is None:
        return ""
    return f"https://opensea.io/assets/{chaincode}/{contract}/{id}"


class Gallery:
    img_width = 178
    img_border = 20
    n_cols = 4
    min_height = 310
    max_height = 950

    def __init__(self, parent_frame, wallet, cb_end):
        self.frame = GalleryFrame(parent_frame)
        wicon = wx.IconBundle(icon_file)
        self.frame.SetIcons(wicon)
        self.panel = GalleryPanel(self.frame)
        self.cb_end = cb_end
        self.img_sizer = wx.FlexGridSizer(0, Gallery.n_cols, Gallery.img_border, Gallery.img_border)
        self.img_sizer.SetFlexibleDirection(wx.BOTH)
        self.img_sizer.SetNonFlexibleGrowMode(wx.FLEX_GROWMODE_SPECIFIED)
        self.panel.scrwin.SetSizer(self.img_sizer, False)
        self.symb = wallet.get_symbol()
        if self.symb == "---":
            self.panel.wait_text.SetLabel("Wrong blockchain, or incompatible contract.")
            self.add_close_btn()
        else:
            wx.CallAfter(self.panel.collection_name.SetLabel, f"{self.symb} NFT")
            self.nwallet = wallet
            self.panel.wait_text.SetLabel("Loading data... Please wait... ")
            wx.CallLater(500, Thread(target=self.read_balance).run)
        self.frame.Bind(wx.EVT_CLOSE, self.on_close)
        self.frame.Show()

    def close_frombtn(self, evt=None):
        """Close the window, from close button"""
        self.on_close(None)
        self.frame.Close()

    def on_close(self, evt):
        self.frame.GetParent().Show()
        self.cb_end(None)
        if evt is not None:
            evt.Skip()

    def show_message(self, err):
        wx.MessageDialog(self.frame, err).ShowModal()

    def add_close_btn(self):
        """Add a close button in the frame."""
        close_btn = wx.BitmapButton(
            self.panel,
            wx.ID_ANY,
            wx.NullBitmap,
            wx.DefaultPosition,
            wx.DefaultSize,
            wx.BU_AUTODRAW | 0 | wx.BORDER_NONE,
        )
        close_btn.SetBitmap(wx.Bitmap(file_path("gui/images/btns/close.png"), wx.BITMAP_TYPE_PNG))
        self.panel.GetSizer().Add(close_btn, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.BOTTOM, 32)
        close_btn.SetCursor(wx.Cursor(wx.CURSOR_HAND))
        close_btn.Bind(wx.EVT_BUTTON, self.close_frombtn)
        self.panel.Layout()

    def read_balance(self):
        """Start filling the Gallery content."""
        try:
            self.bal = self.nwallet.get_balance()
        except Exception:
            self.show_message(
                "Error when reading the NFT balance.\n"
                "Internet connectivity issue, or incompatible contract type."
            )
            self.close_frombtn()
            return
        self.update_balance()
        self.panel.Layout()
        self.panel.Refresh()
        wx.CallLater(100, self.load_nft_list)

    def load_nft_list(self):
        if self.bal > 0:
            try:
                id_list = self.nwallet.get_tokens_list(self.bal)
            except Exception:
                self.show_message(
                    "Error when reading the NFT list.\n"
                    "Internet connectivity issue, or incompatible contract type."
                )
                self.close_frombtn()
                return
            wx.CallAfter(self.load_nft, id_list)
        else:
            self.panel.wait_text.SetLabel(
                "No such NFT in this wallet.\nReceive NFT using the\nwallet address."
            )
            self.add_close_btn()

    def load_image(self, nft_info, id_list):
        """Get image of a NFT."""
        try:
            nft_info["image_data"] = get_image_file(nft_info["url"])
        except Exception:
            nft_info["image_data"] = None
        if self.panel:
            self.add_image(nft_info)
            wx.CallLater(80, self.load_nft, id_list)

    def load_nft(self, id_list):
        """Load the NFT list info."""
        if len(id_list) > 0:
            id = id_list.pop()
            try:
                img_url = self.get_nft_image(id)
            except Exception:
                img_url = None
            nft_info = {
                "id": id,
                "url": img_url,
                "chain": self.nwallet.wallet.chainID,
                "contract": self.nwallet.wallet.eth.contract,
            }
            self.panel.wait_text.SetLabel(
                f"Loading data... {self.bal-len(id_list)}/{self.bal} Please wait..."
            )
            Thread(target=self.load_image, args=(nft_info, id_list)).run()
        else:
            self.panel.wait_text.SetLabel("")
            wx.CallLater(500, self.resize_window)

    def update_balance(self):
        """Display the balance in UI."""
        self.panel.balance_text.SetLabel(f"You have {self.bal} item{'s' if self.bal >= 2 else ''}")

    def get_nft_image(self, id):
        """Get metadata and the image URL of a NFT."""
        metadata = self.nwallet.get_metadata(id)
        image_url = ""
        if metadata is not None:
            image_url = metadata.get("image")
        return image_url

    def resize_window(self):
        wn = self.bal
        if wn < 2:
            wn = 2
        if wn > Gallery.n_cols:
            wn = Gallery.n_cols
        hn = self.bal // Gallery.n_cols + 1
        wunit = Gallery.img_width + 2 * Gallery.img_border
        wsz = wunit * wn
        if wn > Gallery.n_cols:
            wsz += wx.SYS_VSCROLL_X
        hsz = wunit * hn + 280
        if hsz < Gallery.min_height:
            hsz = Gallery.min_height
        if hsz > Gallery.max_height:
            hsz = Gallery.max_height
        self.frame.SetSize(wsz, hsz)
        self.panel.scrwin.Layout()
        self.panel.Layout()
        self.panel.Refresh()
        self.frame.Refresh()

    def open_url(self, url):
        webbrowser.open(url, 2)

    def send_nft(self, nft):
        # Ask the receiving address
        dest_modal = wx.TextEntryDialog(
            self.frame,
            "Input the destination address or domain",
            f"Send the {self.symb} #{nft['id']}",
        )
        ret_mod = dest_modal.ShowModal()
        dest_str = dest_modal.GetValue()
        dest_modal.Destroy()
        if ret_mod != wx.ID_OK:
            return
        # Resolve domain
        resolved = resolve(dest_str, self.nwallet.wallet.__class__.coin)
        if not resolved:
            resolved = resolve(dest_str, ETH_wallet.coin)
        if resolved:
            dest_addr = resolved
        else:
            dest_addr = dest_str
        # Check address
        dest_addr = testaddr(dest_addr)
        if not dest_addr:
            self.show_message("Wrong address or domain provided.")
            return

        # Confirm
        disp_dest = dest_addr
        if "." in dest_str:
            disp_dest += f" ({dest_str})"
        conf_modal = wx.MessageDialog(
            self.frame,
            f"Confirm sending {self.symb} NFT #{nft['id']}\n" f"to {disp_dest} ?",
            style=wx.OK | wx.CENTRE | wx.CANCEL,
        )
        ret_conf = conf_modal.ShowModal()
        conf_modal.Destroy()
        if ret_conf != wx.ID_OK:
            logger.debug("Cancelled by user")
            return

        # Transfer
        try:
            txid = self.nwallet.wallet.transfer_nft(nft["id"], dest_addr)
        except Exception as exc:
            self.show_message(f"Error during NFT transaction :\n{str(exc)}")
            return
        self.show_message(f"Transaction performed :\n{txid}")

    def add_image(self, nft_data):
        """Add a NFT in the gallery UI."""
        szr = wx.BoxSizer(wx.VERTICAL)
        if nft_data["image_data"] is not None:
            try:
                img = wx.Image(nft_data["image_data"], type=wx.BITMAP_TYPE_ANY, index=-1)
                imgh = img.GetHeight()
                imgw = img.GetWidth()
                scale_h = Gallery.img_width / imgh
                scale_w = Gallery.img_width / imgw
                scale = min(scale_h, scale_w)
                if img.IsOk():
                    img.Rescale(int(scale * imgw), int(scale * imgh), wx.IMAGE_QUALITY_HIGH)
                else:
                    img = wx.Image(file_path("gui/images/nonft.png"))
            except Exception:
                img = wx.Image(file_path("gui/images/nonft.png"))
        else:
            img = wx.Image(file_path("gui/images/nonft.png"))
        bmp = wx.StaticBitmap(
            self.panel.scrwin,
            wx.ID_ANY,
            img.ConvertToBitmap(),
            wx.DefaultPosition,
            wx.DefaultSize,
            0,
        )
        szr.Add(bmp, 0, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL, 5)
        szr_btn = wx.BoxSizer(wx.HORIZONTAL)
        img = wx.Image(file_path("gui/images/btns/nftinfo.png"), wx.BITMAP_TYPE_PNG)
        info_btn = wx.BitmapButton(
            self.panel.scrwin,
            wx.ID_ANY,
            img.ConvertToBitmap(),
            wx.DefaultPosition,
            wx.DefaultSize,
            wx.BU_AUTODRAW | wx.BORDER_NONE,
        )
        info_btn.SetBackgroundColour(wx.Colour(248, 250, 252))
        info_btn.SetCursor(wx.Cursor(wx.CURSOR_HAND))
        info_btn.SetToolTip(f"About the {self.symb} #{nft_data['id']}")
        szr_btn.Add(info_btn, 0, wx.TOP | wx.BOTTOM, 12)
        url_osea = opensea_url(nft_data["chain"], nft_data["contract"], nft_data["id"])
        if url_osea:
            info_btn.Bind(wx.EVT_BUTTON, lambda _: self.open_url(url_osea))
        else:
            info_btn.Disable()
        img = wx.Image(file_path("gui/images/btns/sendnft.png"), wx.BITMAP_TYPE_PNG)
        send_btn = wx.BitmapButton(
            self.panel.scrwin,
            wx.ID_ANY,
            img.ConvertToBitmap(),
            wx.DefaultPosition,
            wx.DefaultSize,
            wx.BU_AUTODRAW | wx.BORDER_NONE,
        )
        send_btn.SetBackgroundColour(wx.Colour(248, 250, 252))
        send_btn.SetCursor(wx.Cursor(wx.CURSOR_HAND))
        szr_btn.Add(send_btn, 0, wx.TOP | wx.BOTTOM, 12)
        szr.Add(szr_btn, 0, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL, 0)
        send_btn.Bind(wx.EVT_BUTTON, lambda _: self.send_nft(nft_data))

        if self.panel:
            self.img_sizer.Add(szr, 1, wx.EXPAND, 5)
