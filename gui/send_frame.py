import wx

from decimal import Decimal
from sys import platform

from gui.utils import file_path
from gui.maingui import SendDialog, SendPanel


FEES_PRORITY_TEXT = [
    "Economic fee",
    "Normal fee",
    "Faster fee",
]

BAD_AMNT_INPUT = "Input an amount value to transfer."
BAD_ADDR_INPUT = "Input an destination address/domain."
LOW_BALANCE = "Not enough balance for this transfer."


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
        self.GOOD_BMP = wx.Bitmap(file_path("gui/images/good.png"))
        self.BAD_BMP = wx.Bitmap(file_path("gui/images/bad.png"))
        self.panel.fiat_label.Hide()
        self.panel.fiat_value.Hide()
        self.panel.text_avail.SetLabel(bal_txt)
        self.Bind(wx.EVT_CLOSE, self.close)
        self.panel.text_dest.Bind(wx.EVT_TEXT, self.check_addr)
        self.panel.text_amount.Bind(wx.EVT_TEXT, self.compute_value)
        self.panel.check_sendall.Bind(wx.EVT_CHECKBOX, self.check_all)
        self.panel.cancel_btn.SetCursor(handcurs)
        self.panel.ok_btn.SetCursor(handcurs)
        self.panel.paste_btn.SetBitmap(
            wx.Bitmap(file_path("gui/images/btns/paste.png"), wx.BITMAP_TYPE_PNG)
        )
        self.panel.ok_btn.SetBitmap(
            wx.Bitmap(file_path("gui/images/btns/ok.png"), wx.BITMAP_TYPE_PNG)
        )
        self.panel.cancel_btn.SetBitmap(
            wx.Bitmap(file_path("gui/images/btns/cancel.png"), wx.BITMAP_TYPE_PNG)
        )
        self.panel.paste_btn.SetCursor(handcurs)
        self.panel.fee_slider.Bind(wx.EVT_SCROLL, self.fee_changed)
        self.panel.cancel_btn.Bind(wx.EVT_BUTTON, self.click_cancel)
        self.panel.ok_btn.Bind(wx.EVT_BUTTON, self.click_ok)
        self.panel.text_dest.Bind(wx.EVT_TEXT_ENTER, self.click_ok)
        self.panel.text_amount.Bind(wx.EVT_TEXT_ENTER, self.click_ok)
        self.panel.paste_btn.Bind(wx.EVT_BUTTON, self.paste_addr)
        self.panel.bmp_chk.SetBitmap(self.BAD_BMP)
        self.dest_addr = ""
        if platform.startswith("darwin"):
            self.panel.fiat_label.SetFont(wx.Font(wx.FontInfo(14)))
            self.panel.fiat_value.SetFont(wx.Font(wx.FontInfo(14)))
            self.panel.text_fees.SetFont(wx.Font(wx.FontInfo(14)))
        self.panel.text_dest.SetFocus()

    def close(self, evt):
        self.cb("CLOSE", "", "0")

    def show_message(self, message, title, icon=wx.ICON_INFORMATION):
        wx.MessageDialog(
            self,
            message,
            caption=title,
            style=wx.OK | wx.CENTRE | icon,
            pos=wx.DefaultPosition,
        ).ShowModal()

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
        self.dest_addr = ""
        dest = self.check_addr_method(evt.GetString())
        if dest:
            self.panel.bmp_chk.SetBitmap(self.GOOD_BMP)
            self.dest_addr = dest
        else:
            self.panel.bmp_chk.SetBitmap(self.BAD_BMP)

    def compute_value(self, evt):
        # Update total balance
        bal_txt = self.GetParent().balance_info.GetLabel()
        bal_txt += self.GetParent().balance_small.GetLabel()
        self.panel.text_avail.SetLabel(bal_txt)
        app_panel = self.GetParent()
        if hasattr(app_panel, "fiat_price"):
            try:
                amnt_str = evt.GetString()
                if amnt_str == "ALL":
                    amnt = float(bal_txt)
                else:
                    amnt = float(evt.GetString())
                rate = self.GetParent().fiat_price
                self.panel.fiat_label.Show()
                self.panel.fiat_value.Show()
                self.panel.fiat_value.SetLabel(f"$ {amnt * rate:.2f}")
                self.panel.Layout()
            except ValueError:
                self.panel.fiat_label.Hide()
                self.panel.fiat_value.Hide()

    def click_cancel(self, event):
        self.cb("CANCEL", "", "0")

    def click_ok(self, event):
        dest = self.panel.text_dest.GetValue()
        if len(dest) <= 0:
            self.show_message(BAD_ADDR_INPUT, "Invalid destination")
            return
        amount = self.panel.text_amount.GetValue()
        if len(amount) <= 0:
            self.show_message(BAD_AMNT_INPUT, "Invalid amount")
            return
        if amount != "ALL":
            try:
                float(amount)
            except ValueError:
                self.show_message("Unvalid amount input.", "Invalid amount")
                return
            bal_txt = self.GetParent().balance_info.GetLabel()
            bal_txt += self.GetParent().balance_small.GetLabel()
            if Decimal(amount) > Decimal(bal_txt):
                self.show_message(
                    LOW_BALANCE,
                    "Amount too high",
                    wx.ICON_WARNING,
                )
                return
        if "." in dest:
            domain = dest
            dest = self.dest_addr
        else:
            domain = ""
        fee_level = self.panel.fee_slider.GetValue()
        self.cb("OK", dest, amount, fee_level, domain)
