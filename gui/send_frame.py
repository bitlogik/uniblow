import wx

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
        self.cb = callback
        handcurs = wx.Cursor(wx.CURSOR_HAND)
        self.Bind(wx.EVT_CLOSE, self.close)
        self.panel.check_sendall.Bind(wx.EVT_CHECKBOX, self.check_all)
        self.panel.cancel_btn.SetCursor(handcurs)
        self.panel.ok_btn.SetCursor(handcurs)
        self.panel.fee_slider.Bind(wx.EVT_SCROLL, self.fee_changed)
        self.panel.cancel_btn.Bind(wx.EVT_BUTTON, self.click_cancel)
        self.panel.ok_btn.Bind(wx.EVT_BUTTON, self.click_ok)

    def close(self, evt):
        self.cb("CLOSE", "", "0")

    def check_all(self, evt):
        print(evt.IsChecked())
        if evt.IsChecked():
            self.panel.text_amount.SetValue("ALL")
            self.panel.text_amount.Disable()
        else:
            self.panel.text_amount.Enable()

    def fee_changed(self, nfeesel):
        self.panel.text_fees.SetLabel(FEES_PRORITY_TEXT[nfeesel.GetSelection()])

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
