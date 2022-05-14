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
        super().__init__(parent)
        self.panel = SendPanel(self)
        self.panel.text_coin.SetLabel(coin)
        self.check_addr_method = check
        self.cb = callback
        handcurs = wx.Cursor(wx.CURSOR_HAND)
        self.GOOD_BMP = wx.Bitmap(file_path("gui/good.bmp"))
        self.BAD_BMP = wx.Bitmap(file_path("gui/bad.bmp"))
        self.Bind(wx.EVT_CLOSE, self.close)
        self.panel.text_dest.Bind(wx.EVT_TEXT, self.check_addr)
        self.panel.check_sendall.Bind(wx.EVT_CHECKBOX, self.check_all)
        self.panel.cancel_btn.SetCursor(handcurs)
        self.panel.ok_btn.SetCursor(handcurs)
        self.panel.fee_slider.Bind(wx.EVT_SCROLL, self.fee_changed)
        self.panel.cancel_btn.Bind(wx.EVT_BUTTON, self.click_cancel)
        self.panel.ok_btn.Bind(wx.EVT_BUTTON, self.click_ok)
        self.panel.bmp_chk.SetBitmap(self.BAD_BMP)

    def close(self, evt):
        self.cb("CLOSE", "", "0")

    def check_all(self, evt):
        print(evt.IsChecked())
        if evt.IsChecked():
            self.panel.text_amount.SetValue("ALL")
            self.panel.text_amount.Disable()
        else:
            self.panel.text_amount.SetValue("")
            self.panel.text_amount.Enable()

    def fee_changed(self, nfeesel):
        self.panel.text_fees.SetLabel(FEES_PRORITY_TEXT[nfeesel.GetSelection()])
    
    def check_addr(self, evt):
        if self.check_addr_method(evt.GetString()):
            self.panel.bmp_chk.SetBitmap(self.GOOD_BMP)
        else:
            self.panel.bmp_chk.SetBitmap(self.BAD_BMP)

    def click_cancel(self, event):
        self.cb("CANCEL", "", "0")

    def click_ok(self, event):
        print("OK")
        amount = self.panel.text_amount.GetValue()
        dest = self.panel.text_dest.GetValue()
        fee_level = self.panel.fee_slider.GetValue()
        self.cb("OK", dest, amount, fee_level)


# def paint_toaddr(color):
# # app.gui_panel.addr_panel.SetBackgroundColour(color)
# pass


# def check_addr(ev):
# ev.Skip()
# paint_toaddr(wx.NullColour)
# if not hasattr(app, "wallet"):
# return
# addr = ev.GetString()
# if len(addr) < 7:
# app.gui_frame.Refresh()
# return
# if app.wallet.check_address(addr):
# paint_toaddr(GREEN_COLOR)
# else:
# paint_toaddr(RED_COLOR)
# app.gui_frame.Refresh()
