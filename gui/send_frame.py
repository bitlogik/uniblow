import wx

from gui.utils import file_path
from gui.maingui import SendDialog, SendPanel


FEES_PRORITY_TEXT = [
    "Economic fee",
    "Normal fee",
    "Faster fee",
]


class SendModal(SendDialog):
    def __init__(self, parent, coin, check, callback):
        bal_txt = parent.balance_info.GetLabel()
        bal_txt += parent.balance_small.GetLabel()
        super().__init__(parent)
        self.panel = SendPanel(self)
        self.panel.text_coin.SetLabel(coin)
        self.check_addr_method = check
        self.cb = callback
        handcurs = wx.Cursor(wx.CURSOR_HAND)
        self.GOOD_BMP = wx.Bitmap(file_path("gui/images/good.bmp"))
        self.BAD_BMP = wx.Bitmap(file_path("gui/images/bad.bmp"))
        self.panel.text_avail.SetLabel(bal_txt)
        self.Bind(wx.EVT_CLOSE, self.close)
        self.panel.text_dest.Bind(wx.EVT_TEXT, self.check_addr)
        self.panel.check_sendall.Bind(wx.EVT_CHECKBOX, self.check_all)
        self.panel.cancel_btn.SetCursor(handcurs)
        self.panel.ok_btn.SetCursor(handcurs)
        self.panel.paste_btn.SetCursor(handcurs)
        self.panel.fee_slider.Bind(wx.EVT_SCROLL, self.fee_changed)
        self.panel.cancel_btn.Bind(wx.EVT_BUTTON, self.click_cancel)
        self.panel.ok_btn.Bind(wx.EVT_BUTTON, self.click_ok)
        self.panel.paste_btn.Bind(wx.EVT_BUTTON, self.paste_addr)
        self.panel.bmp_chk.SetBitmap(self.BAD_BMP)

    def close(self, evt):
        self.cb("CLOSE", "", "0")

    def check_all(self, evt):
        if evt.IsChecked():
            self.panel.text_amount.SetValue("ALL")
            self.panel.text_amount.Disable()
        else:
            self.panel.text_amount.SetValue("")
            self.panel.text_amount.Enable()

    def fee_changed(self, nfeesel):
        self.panel.text_fees.SetLabel(FEES_PRORITY_TEXT[nfeesel.GetSelection()])

    def paste_addr(self, evt):
        evt.Skip()
        text_data = wx.TextDataObject()
        if wx.TheClipboard.Open():
            success = wx.TheClipboard.GetData(text_data)
            wx.TheClipboard.Close()
        if success:
            self.panel.text_dest.SetValue(text_data.GetText())

    def check_addr(self, evt):
        if self.check_addr_method(evt.GetString()):
            self.panel.bmp_chk.SetBitmap(self.GOOD_BMP)
        else:
            self.panel.bmp_chk.SetBitmap(self.BAD_BMP)

    def click_cancel(self, event):
        self.cb("CANCEL", "", "0")

    def click_ok(self, event):
        amount = self.panel.text_amount.GetValue()
        dest = self.panel.text_dest.GetValue()
        fee_level = self.panel.fee_slider.GetValue()
        self.cb("OK", dest, amount, fee_level)
