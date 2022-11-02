from threading import Thread

import wx

from wallets.NFTwallet import get_image_file
from gui.gallerygui import GalleryFrame, GalleryPanel


class Gallery:
    def __init__(self, parent_frame, wallet):
        self.frame = GalleryFrame(parent_frame)
        self.panel = GalleryPanel(self.frame)
        top_sizer = self.panel.collection_name.GetParent().GetSizer()
        self.img_sizer = wx.FlexGridSizer(0, 4, 12, 12)
        # self.img_sizer.SetFlexibleDirection(wx.BOTH)
        # self.img_sizer.SetNonFlexibleGrowMode(wx.FLEX_GROWMODE_SPECIFIED)
        top_sizer.Add(self.img_sizer, 0, wx.EXPAND | wx.TOP | wx.BOTTOM | wx.LEFT, 12)
        wx.CallAfter(self.panel.collection_name.SetLabel, f"{wallet.get_symbol()} NFT")
        self.wallet = wallet
        self.panel.wait_text.SetLabel(
            "Loading data... Please wait... "
        )
        self.frame.Show()
        bal = self.wallet.get_balance()
        self.update_balance(bal)
        self.panel.Layout()
        self.panel.Refresh()
        wx.CallLater(800, self.load_nft_list, bal)

    def load_nft_list(self, bal):
        if bal > 0:
            ids = self.wallet.get_tokens_list(bal)
            wx.CallAfter(self.load_nft, ids, bal)

    def load_image(self, imgurl, ids, bal):
        img = get_image_file(imgurl)
        if self.panel:
            self.add_image(img)
            wx.CallLater(80, self.load_nft, ids, bal)

    def load_nft(self, ids, bal):
        if len(ids) > 0:
            id = ids.pop()
            img_url = self.get_nft_image(id)
            if img_url:
                self.panel.wait_text.SetLabel(
                    "Loading data... Please wait... "
                    f"{bal-len(ids)}/{bal}"
                )
                Thread(target=self.load_image, args=(img_url, ids, bal)).run()
        else:
            self.panel.wait_text.SetLabel("")
            wx.CallLater(800, self.resize_window)

    def update_balance(self, bal):
        self.panel.balance_text.SetLabel(
            f"You have {bal} item{'s' if bal >= 2 else ''}"
        )

    def get_nft_image(self, id):
        metadata = self.wallet.get_metadata(id)
        image_url = ""
        if metadata is not None:
            image_url = metadata.get("image")
        return image_url

    def resize_window(self):
        top_sizer = self.panel.collection_name.GetParent().GetSizer()
        top_sizer.Fit(self.frame)
        self.panel.Layout()

    def add_image(self, image):
        szr = wx.BoxSizer(wx.VERTICAL)
        if image is not None:
            try:
                img = wx.Image(image, type=wx.BITMAP_TYPE_ANY, index=-1)
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

        m_button1 = wx.Button(self.panel, wx.ID_ANY, "Send", wx.DefaultPosition, wx.DefaultSize, 0)
        m_button1.SetCursor(wx.Cursor(wx.CURSOR_HAND))
        szr.Add(m_button1, 0, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL, 5)

        if self.panel:
            self.img_sizer.Add(szr, 1, wx.EXPAND, 5)
