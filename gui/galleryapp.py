from logging import getLogger
from threading import Thread
import webbrowser
import wx

from wallets.ETHwallet import testaddr
from wallets.NFTwallet import get_image_file
from gui.gallerygui import GalleryFrame, GalleryPanel


logger = getLogger(__name__)


opensea_chains = {1: "ethereum", 137: "matic"}


def opensea_url(chain_id, contract, id):
    chaincode = opensea_chains.get(chain_id)
    if chaincode is None:
        return ""
    return f"https://opensea.io/assets/{chaincode}/{contract}/{id}"


class Gallery:
    def __init__(self, parent_frame, wallet, cb_end):
        self.frame = GalleryFrame(parent_frame)
        self.panel = GalleryPanel(self.frame)
        self.cb_end = cb_end
        top_sizer = self.panel.collection_name.GetParent().GetSizer()
        self.img_sizer = wx.FlexGridSizer(0, 4, 12, 12)
        top_sizer.Add(self.img_sizer, 0, wx.EXPAND | wx.TOP | wx.BOTTOM | wx.LEFT, 12)
        wx.CallAfter(self.panel.collection_name.SetLabel, f"{wallet.get_symbol()} NFT")
        self.nwallet = wallet
        self.panel.wait_text.SetLabel("Loading data... Please wait... ")
        self.frame.Show()
        self.frame.Bind(wx.EVT_CLOSE, self.on_close)
        wx.CallLater(500, Thread(target=self.read_balance).run)

    def on_close(self, evt):
        self.frame.GetParent().Show()
        self.cb_end(None)
        evt.Skip()

    def read_balance(self):
        self.bal = self.nwallet.get_balance()
        self.update_balance(self.bal)
        self.panel.Layout()
        self.panel.Refresh()
        wx.CallLater(100, self.load_nft_list)

    def load_nft_list(self):
        if self.bal > 0:
            id_list = self.nwallet.get_tokens_list(self.bal)
            wx.CallAfter(self.load_nft, id_list)
        else:
            self.panel.wait_text.SetLabel("")

    def load_image(self, nft_info, id_list):
        nft_info["image_data"] = get_image_file(nft_info["url"])
        if self.panel:
            self.add_image(nft_info)
            wx.CallLater(80, self.load_nft, id_list)

    def load_nft(self, id_list):
        if len(id_list) > 0:
            id = id_list.pop()
            img_url = self.get_nft_image(id)
            nft_info = {
                "id": id,
                "url": img_url,
                "chain": self.nwallet.wallet.chainID,
                "contract": self.nwallet.wallet.eth.contract,
            }
            self.panel.wait_text.SetLabel(
                "Loading data... Please wait... " f"{self.bal-len(id_list)}/{self.bal}"
            )
            Thread(target=self.load_image, args=(nft_info, id_list)).run()
        else:
            self.panel.wait_text.SetLabel("")
            wx.CallLater(500, self.resize_window)

    def update_balance(self, bal):
        self.panel.balance_text.SetLabel(f"You have {bal} item{'s' if bal >= 2 else ''}")

    def get_nft_image(self, id):
        metadata = self.nwallet.get_metadata(id)
        image_url = ""
        if metadata is not None:
            image_url = metadata.get("image")
        return image_url

    def resize_window(self):
        top_sizer = self.panel.collection_name.GetParent().GetSizer()
        top_sizer.Fit(self.frame)
        self.panel.Layout()

    def open_url(self, url):
        webbrowser.open(url, 2)

    def send_nft(self, nft):
        # Ask the receiving address
        dest_modal = wx.TextEntryDialog(
            self.frame, "Input the destination address :", f"Send the NFT #{nft['id']}"
        )
        ret_mod = dest_modal.ShowModal()
        if ret_mod != wx.ID_OK:
            dest_modal.Destroy()
            return
        dest_addr = dest_modal.GetValue()
        dest_modal.Destroy()
        # Check address
        if not testaddr(dest_addr):
            wx.MessageDialog(self.frame, "Bad address format provided.").ShowModal()
            return

        # Confirm
        conf_modal = wx.MessageDialog(
            self.frame,
            f"Confirm sending NFT #{nft['id']} to {dest_addr} ?",
            style=wx.OK | wx.CENTRE | wx.CANCEL,
        )
        ret_conf = conf_modal.ShowModal()
        dest_modal.Destroy()
        if ret_conf != wx.ID_OK:
            logger.debug("Cancelled by user")
            return

        # Transfer
        txid = self.nwallet.wallet.transfer_nft(nft["id"], dest_addr)
        wx.MessageDialog(self.frame, f"Transaction performed : {txid}").ShowModal()

    def add_image(self, nft_data):
        szr = wx.BoxSizer(wx.VERTICAL)
        if nft_data["image_data"] is not None:
            try:
                img = wx.Image(nft_data["image_data"], type=wx.BITMAP_TYPE_ANY, index=-1)
                if img.IsOk():
                    img.Rescale(128, 128, wx.IMAGE_QUALITY_HIGH)
                else:
                    img = wx.Image(1, 1)
            except Exception:
                img = wx.Image(1, 1)

            m_bitmap2 = wx.StaticBitmap(
                self.panel, wx.ID_ANY, img.ConvertToBitmap(), wx.DefaultPosition, wx.DefaultSize, 0
            )
            szr.Add(m_bitmap2, 0, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL, 5)

        m_button4 = wx.Button(
            self.panel, wx.ID_ANY, "Details", wx.DefaultPosition, wx.DefaultSize, 0
        )
        m_button4.SetCursor(wx.Cursor(wx.CURSOR_HAND))
        szr.Add(m_button4, 0, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL, 5)
        url_osea = opensea_url(nft_data["chain"], nft_data["contract"], nft_data["id"])
        if url_osea:
            m_button4.Bind(wx.EVT_BUTTON, lambda x: self.open_url(url_osea))
        else:
            m_button4.Disable()
        m_button1 = wx.Button(self.panel, wx.ID_ANY, "Send", wx.DefaultPosition, wx.DefaultSize, 0)
        m_button1.SetCursor(wx.Cursor(wx.CURSOR_HAND))
        szr.Add(m_button1, 0, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL, 5)
        m_button1.Bind(wx.EVT_BUTTON, lambda x: self.send_nft(nft_data))

        if self.panel:
            self.img_sizer.Add(szr, 1, wx.EXPAND, 5)
