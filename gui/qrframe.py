from io import BytesIO
import qrcode
import wx

from gui.utils import icon_file


class QRFrame(wx.Frame):
    def __init__(self, parent, coin, address, btn):

        super().__init__(
            parent,
            id=wx.ID_ANY,
            title=f"  Receive {coin}",
            size=wx.Size(360, 328),
            style=wx.FRAME_FLOAT_ON_PARENT | wx.DEFAULT_FRAME_STYLE | wx.TAB_TRAVERSAL,
        )
        self.btn = btn
        self.SetIcons(wx.IconBundle(icon_file))

        self.SetSizeHints(wx.DefaultSize, wx.DefaultSize)
        self.Centre(wx.BOTH)
        qrpanel = wx.Panel(
            self,
            id=wx.ID_ANY,
            size=(-1, -1),
            style=wx.TAB_TRAVERSAL,
            name=wx.EmptyString,
        )
        qrpanel.SetBackgroundColour(wx.Colour(248, 250, 252))

        imgqr = qrcode.make(
            address,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=4,
            border=3,
        )
        imgbuf = BytesIO()
        imgqr.save(imgbuf, "BMP")
        imgbuf.seek(0)
        wxi = wx.Image(imgbuf, type=wx.BITMAP_TYPE_BMP).ConvertToBitmap()

        siz1 = wx.BoxSizer(wx.VERTICAL)
        qrpanel.bmpqr = wx.StaticBitmap(
            qrpanel, wx.ID_ANY, wxi, wx.DefaultPosition, wx.DefaultSize, 0
        )
        siz1.Add(qrpanel.bmpqr, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.TOP, 32)
        qrpanel.stxt = wx.StaticText(
            qrpanel,
            wx.ID_ANY,
            f"Scan to send {coin} to this wallet.",
            wx.DefaultPosition,
            wx.DefaultSize,
            0,
        )
        qrpanel.stxt.Wrap(-1)
        siz1.Add(qrpanel.stxt, 0, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL, 5)

        qrpanel.close_btn = wx.BitmapButton(
            qrpanel,
            wx.ID_ANY,
            wx.NullBitmap,
            wx.DefaultPosition,
            wx.DefaultSize,
            wx.BU_AUTODRAW | 0 | wx.BORDER_NONE,
        )
        qrpanel.close_btn.SetBitmap(wx.Bitmap("gui/images/btns/close.png", wx.BITMAP_TYPE_ANY))

        siz1.Add(qrpanel.close_btn, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.TOP, 16)
        qrpanel.close_btn.Bind(wx.EVT_BUTTON, self.closing)
        self.Bind(wx.EVT_CLOSE, self.closing)
        qrpanel.close_btn.SetCursor(wx.Cursor(wx.CURSOR_HAND))
        qrpanel.SetSizer(siz1)
        qrpanel.Layout()

        self.Show()

    def closing(self, event):
        self.btn.Enable()
        event.Skip()
        self.Close(True)
