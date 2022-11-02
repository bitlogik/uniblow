import wx
from wallets.NFTwallet import get_image_file
from gui.gallerygui import GalleryFrame, GalleryPanel


class Gallery:
    def __init__(self, parent_frame, wallet):
        gframe = GalleryFrame(parent_frame)
        self.panel = GalleryPanel(gframe)
        top_sizer = self.panel.collection_name.GetParent().GetSizer()
        self.img_sizer = wx.FlexGridSizer(0, 3, 12, 12)
        # self.img_sizer.SetFlexibleDirection(wx.BOTH)
        # self.img_sizer.SetNonFlexibleGrowMode(wx.FLEX_GROWMODE_SPECIFIED)
        top_sizer.Add(self.img_sizer, 0, wx.EXPAND | wx.TOP | wx.BOTTOM | wx.LEFT, 12)
        self.panel.collection_name.SetLabel(f"{wallet.get_symbol()} NFT")
        self.wallet = wallet
        gframe.Show()
        bal = self.wallet.get_balance()
        self.update_balance(bal)
        if bal > 0:
            ids = self.wallet.get_tokens_list(bal)
            for id in ids:
                img_url = self.get_nft_image(id)
                if img_url:
                    self.add_image(get_image_file(img_url))
                    print("added")

    def update_balance(self, bal):
        self.panel.balance_text.SetLabel(f"You have {bal} item(s)")

    def get_nft_image(self, id):
        metadata = self.wallet.get_metadata(id)
        image_url = ""
        if metadata is not None:
            image_url = metadata.get("image")
        return image_url

    def add_image(self, image):

        szr = wx.BoxSizer(wx.VERTICAL)
        img = wx.Image(image, type=wx.BITMAP_TYPE_ANY, index=-1)
        m_bitmap2 = wx.StaticBitmap(
            self.panel, wx.ID_ANY, img.ConvertToBitmap(), wx.DefaultPosition, wx.DefaultSize, 0
        )
        szr.Add(m_bitmap2, 0, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL, 5)

        m_button4 = wx.Button(
            self.panel, wx.ID_ANY, "Details", wx.DefaultPosition, wx.DefaultSize, 0
        )
        szr.Add(m_button4, 0, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL, 5)

        m_button1 = wx.Button(self.panel, wx.ID_ANY, "Send", wx.DefaultPosition, wx.DefaultSize, 0)
        szr.Add(m_button1, 0, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL, 5)

        self.img_sizer.Add(szr, 1, wx.EXPAND, 5)
        self.panel.Layout()
