# -*- coding: utf-8 -*-

###########################################################################
## Python code generated with wxFormBuilder (version Oct 26 2018)
## http://www.wxformbuilder.org/
##
## PLEASE DO *NOT* EDIT THIS FILE!
###########################################################################

import wx
import wx.xrc

###########################################################################
## Class UniblowFrame
###########################################################################

class UniblowFrame ( wx.Frame ):

    def __init__( self, parent ):
        wx.Frame.__init__ ( self, parent, id = wx.ID_ANY, title = wx.EmptyString, pos = wx.DefaultPosition, size = wx.Size( 500,350 ), style = wx.CAPTION|wx.CLOSE_BOX|wx.MINIMIZE|wx.MINIMIZE_BOX|wx.SYSTEM_MENU|wx.TAB_TRAVERSAL )

        self.SetSizeHints( wx.DefaultSize, wx.DefaultSize )


        self.Centre( wx.BOTH )

    def __del__( self ):
        pass


###########################################################################
## Class WalletPanel
###########################################################################

class WalletPanel ( wx.Panel ):

    def __init__( self, parent, id = wx.ID_ANY, pos = wx.DefaultPosition, size = wx.Size( 652,337 ), style = wx.TAB_TRAVERSAL, name = wx.EmptyString ):
        wx.Panel.__init__ ( self, parent, id = id, pos = pos, size = size, style = style, name = name )

        self.SetBackgroundColour( wx.Colour( 248, 250, 252 ) )

        bSizer1 = wx.BoxSizer( wx.HORIZONTAL )

        sbSizer5 = wx.StaticBoxSizer( wx.StaticBox( self, wx.ID_ANY, u"chains" ), wx.VERTICAL )

        self.scrolled_coins = wx.ScrolledWindow( sbSizer5.GetStaticBox(), wx.ID_ANY, wx.DefaultPosition, wx.Size( 64,340 ), wx.HSCROLL|wx.VSCROLL )
        self.scrolled_coins.SetScrollRate( 5, 5 )
        sbSizer5.Add( self.scrolled_coins, 0, 0, 5 )


        bSizer1.Add( sbSizer5, 0, wx.EXPAND, 5 )

        self.m_panel1 = wx.Panel( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
        bSizer6 = wx.BoxSizer( wx.VERTICAL )

        bSizer4 = wx.BoxSizer( wx.HORIZONTAL )

        self.balance_info = wx.StaticText( self.m_panel1, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
        self.balance_info.Wrap( -1 )

        self.balance_info.SetFont( wx.Font( 16, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, wx.EmptyString ) )

        bSizer4.Add( self.balance_info, 1, wx.ALIGN_CENTER_VERTICAL|wx.LEFT, 24 )

        bSizer5 = wx.BoxSizer( wx.VERTICAL )

        network_choiceChoices = []
        self.network_choice = wx.Choice( self.m_panel1, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, network_choiceChoices, 0 )
        self.network_choice.SetSelection( 0 )
        self.network_choice.SetFont( wx.Font( 12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, wx.EmptyString ) )
        self.network_choice.SetMinSize( wx.Size( 120,-1 ) )

        bSizer5.Add( self.network_choice, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.TOP|wx.RIGHT, 20 )


        bSizer4.Add( bSizer5, 0, wx.RIGHT, 24 )


        bSizer6.Add( bSizer4, 1, wx.EXPAND, 5 )

        bSizer9 = wx.BoxSizer( wx.HORIZONTAL )

        self.but_evt1 = wx.BitmapButton( self.m_panel1, wx.ID_ANY, wx.NullBitmap, wx.DefaultPosition, wx.DefaultSize, wx.BU_AUTODRAW|wx.BORDER_NONE )
        bSizer9.Add( self.but_evt1, 0, wx.LEFT, 12 )

        self.but_evt2 = wx.BitmapButton( self.m_panel1, wx.ID_ANY, wx.NullBitmap, wx.DefaultPosition, wx.DefaultSize, wx.BU_AUTODRAW|wx.BORDER_NONE )
        bSizer9.Add( self.but_evt2, 0, wx.RIGHT|wx.LEFT, 36 )

        self.btn_send = wx.BitmapButton( self.m_panel1, wx.ID_ANY, wx.NullBitmap, wx.DefaultPosition, wx.DefaultSize, wx.BU_AUTODRAW|wx.BORDER_NONE )
        bSizer9.Add( self.btn_send, 0, wx.ALL, 5 )

        self.alt_text = wx.StaticText( self.m_panel1, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
        self.alt_text.Wrap( 120 )

        self.alt_text.SetFont( wx.Font( 11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, wx.EmptyString ) )

        bSizer9.Add( self.alt_text, 0, wx.ALL, 5 )


        bSizer6.Add( bSizer9, 1, wx.ALIGN_CENTER_HORIZONTAL, 5 )

        self.account_addr = wx.StaticText( self.m_panel1, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.ST_ELLIPSIZE_END )
        self.account_addr.Wrap( -1 )

        self.account_addr.SetFont( wx.Font( 12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, wx.EmptyString ) )

        bSizer6.Add( self.account_addr, 0, wx.LEFT, 12 )

        bSizer12 = wx.BoxSizer( wx.HORIZONTAL )

        self.qrimg = wx.StaticBitmap( self.m_panel1, wx.ID_ANY, wx.NullBitmap, wx.DefaultPosition, wx.DefaultSize, 0 )
        self.qrimg.SetMinSize( wx.Size( 120,120 ) )

        bSizer12.Add( self.qrimg, 0, wx.ALL, 12 )


        bSizer12.Add( ( 0, 0), 0, 0, 24 )

        bSizer13 = wx.BoxSizer( wx.VERTICAL )

        bSizer14 = wx.BoxSizer( wx.HORIZONTAL )

        bSizer11 = wx.BoxSizer( wx.HORIZONTAL )


        bSizer11.Add( ( 0, 0), 0, wx.LEFT, 20 )

        self.copy_button = wx.BitmapButton( self.m_panel1, wx.ID_ANY, wx.NullBitmap, wx.DefaultPosition, wx.DefaultSize, wx.BU_AUTODRAW|wx.BORDER_NONE )
        bSizer11.Add( self.copy_button, 0, wx.TOP, 8 )

        self.copy_status = wx.StaticText( self.m_panel1, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size( 60,-1 ), 0 )
        self.copy_status.Wrap( -1 )

        bSizer11.Add( self.copy_status, 0, wx.TOP|wx.LEFT, 10 )

        self.btn_chkaddr = wx.BitmapButton( self.m_panel1, wx.ID_ANY, wx.NullBitmap, wx.DefaultPosition, wx.DefaultSize, wx.BU_AUTODRAW|0|wx.BORDER_NONE )
        self.btn_chkaddr.Hide()

        bSizer11.Add( self.btn_chkaddr, 0, wx.TOP|wx.LEFT, 8 )


        bSizer14.Add( bSizer11, 1, wx.EXPAND, 5 )

        bSizer15 = wx.BoxSizer( wx.VERTICAL )


        bSizer15.Add( ( 0, 0), 0, wx.TOP, 16 )

        self.wallopt_label = wx.StaticText( self.m_panel1, wx.ID_ANY, u"Wallet type", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.wallopt_label.Wrap( -1 )

        bSizer15.Add( self.wallopt_label, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.TOP|wx.RIGHT|wx.LEFT, 5 )

        wallopt_choiceChoices = []
        self.wallopt_choice = wx.Choice( self.m_panel1, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wallopt_choiceChoices, 0 )
        self.wallopt_choice.SetSelection( 0 )
        self.wallopt_choice.SetFont( wx.Font( 9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, wx.EmptyString ) )

        bSizer15.Add( self.wallopt_choice, 0, wx.ALL|wx.ALIGN_CENTER_HORIZONTAL, 5 )


        bSizer14.Add( bSizer15, 1, wx.LEFT, 32 )


        bSizer13.Add( bSizer14, 0, wx.EXPAND, 5 )

        self.hist_button = wx.BitmapButton( self.m_panel1, wx.ID_ANY, wx.NullBitmap, wx.DefaultPosition, wx.DefaultSize, wx.BU_AUTODRAW|wx.BORDER_NONE )
        bSizer13.Add( self.hist_button, 0, wx.LEFT, 32 )


        bSizer12.Add( bSizer13, 1, wx.EXPAND, 5 )


        bSizer6.Add( bSizer12, 0, wx.EXPAND, 5 )


        bSizer6.Add( ( 0, 0), 0, wx.TOP, 8 )


        self.m_panel1.SetSizer( bSizer6 )
        self.m_panel1.Layout()
        bSizer6.Fit( self.m_panel1 )
        bSizer1.Add( self.m_panel1, 1, wx.EXPAND |wx.ALL, 5 )


        self.SetSizer( bSizer1 )
        self.Layout()

    def __del__( self ):
        pass


###########################################################################
## Class DevicesPanel
###########################################################################

class DevicesPanel ( wx.Panel ):

    def __init__( self, parent, id = wx.ID_ANY, pos = wx.DefaultPosition, size = wx.Size( -1,-1 ), style = wx.TAB_TRAVERSAL, name = wx.EmptyString ):
        wx.Panel.__init__ ( self, parent, id = id, pos = pos, size = size, style = style, name = name )

        self.SetBackgroundColour( wx.Colour( 248, 250, 252 ) )

        bSizer3 = wx.BoxSizer( wx.VERTICAL )

        self.m_staticText1 = wx.StaticText( self, wx.ID_ANY, u"Select Device", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText1.Wrap( -1 )

        self.m_staticText1.SetFont( wx.Font( 16, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, wx.EmptyString ) )

        bSizer3.Add( self.m_staticText1, 0, wx.ALL|wx.ALIGN_CENTER_HORIZONTAL, 16 )

        fgSizer1 = wx.FlexGridSizer( 0, 2, 12, 36 )
        fgSizer1.SetFlexibleDirection( wx.BOTH )
        fgSizer1.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )

        self.d_btn01 = wx.BitmapButton( self, wx.ID_ANY, wx.NullBitmap, wx.DefaultPosition, wx.DefaultSize, wx.BU_AUTODRAW|wx.BORDER_NONE )
        fgSizer1.Add( self.d_btn01, 0, wx.ALL, 5 )

        self.d_btn02 = wx.BitmapButton( self, wx.ID_ANY, wx.NullBitmap, wx.DefaultPosition, wx.DefaultSize, wx.BU_AUTODRAW|wx.BORDER_NONE )
        fgSizer1.Add( self.d_btn02, 0, wx.ALL, 5 )

        self.d_btn03 = wx.BitmapButton( self, wx.ID_ANY, wx.NullBitmap, wx.DefaultPosition, wx.DefaultSize, wx.BU_AUTODRAW|wx.BORDER_NONE )
        fgSizer1.Add( self.d_btn03, 0, wx.ALL, 5 )

        self.d_btn04 = wx.BitmapButton( self, wx.ID_ANY, wx.NullBitmap, wx.DefaultPosition, wx.DefaultSize, wx.BU_AUTODRAW|wx.BORDER_NONE )
        fgSizer1.Add( self.d_btn04, 0, wx.ALL, 5 )

        self.d_btn05 = wx.BitmapButton( self, wx.ID_ANY, wx.NullBitmap, wx.DefaultPosition, wx.DefaultSize, wx.BU_AUTODRAW|wx.BORDER_NONE )
        fgSizer1.Add( self.d_btn05, 0, wx.ALL, 5 )


        bSizer3.Add( fgSizer1, 0, wx.ALIGN_CENTER_HORIZONTAL, 5 )


        self.SetSizer( bSizer3 )
        self.Layout()
        bSizer3.Fit( self )

    def __del__( self ):
        pass


###########################################################################
## Class SendDialog
###########################################################################

class SendDialog ( wx.Dialog ):

    def __init__( self, parent ):
        wx.Dialog.__init__ ( self, parent, id = wx.ID_ANY, title = u"Sending", pos = wx.DefaultPosition, size = wx.Size( 520,420 ), style = wx.DEFAULT_DIALOG_STYLE )

        self.SetSizeHints( wx.DefaultSize, wx.DefaultSize )


        self.Centre( wx.BOTH )

    def __del__( self ):
        pass


###########################################################################
## Class SendPanel
###########################################################################

class SendPanel ( wx.Panel ):

    def __init__( self, parent, id = wx.ID_ANY, pos = wx.DefaultPosition, size = wx.Size( -1,-1 ), style = wx.TAB_TRAVERSAL, name = wx.EmptyString ):
        wx.Panel.__init__ ( self, parent, id = id, pos = pos, size = size, style = style, name = name )

        self.SetBackgroundColour( wx.Colour( 248, 250, 252 ) )

        bSizer13 = wx.BoxSizer( wx.HORIZONTAL )


        bSizer13.Add( ( 0, 0), 0, wx.RIGHT, 16 )

        bSizer23 = wx.BoxSizer( wx.VERTICAL )


        bSizer23.Add( ( 0, 0), 0, wx.BOTTOM, 24 )

        bSizer201 = wx.BoxSizer( wx.HORIZONTAL )

        self.m_staticText7 = wx.StaticText( self, wx.ID_ANY, u"Destination Address", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText7.Wrap( -1 )

        bSizer201.Add( self.m_staticText7, 0, wx.LEFT, 5 )

        self.paste_btn = wx.Button( self, wx.ID_ANY, u"Paste", wx.DefaultPosition, wx.Size( 80,24 ), 0 )
        self.paste_btn.SetFont( wx.Font( 9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, wx.EmptyString ) )

        bSizer201.Add( self.paste_btn, 0, wx.LEFT, 24 )


        bSizer23.Add( bSizer201, 0, 0, 5 )

        bSizer14 = wx.BoxSizer( wx.HORIZONTAL )

        self.text_dest = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer14.Add( self.text_dest, 1, wx.RIGHT|wx.LEFT, 5 )


        bSizer14.Add( ( 0, 0), 0, wx.RIGHT, 6 )

        self.bmp_chk = wx.StaticBitmap( self, wx.ID_ANY, wx.NullBitmap, wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer14.Add( self.bmp_chk, 0, wx.TOP, 5 )


        bSizer23.Add( bSizer14, 0, wx.EXPAND, 5 )


        bSizer23.Add( ( 0, 0), 0, wx.TOP, 16 )

        bSizer15 = wx.BoxSizer( wx.HORIZONTAL )

        sbSizer3 = wx.StaticBoxSizer( wx.StaticBox( self, wx.ID_ANY, u"Amount" ), wx.VERTICAL )

        sbSizer3.SetMinSize( wx.Size( -1,175 ) )
        bSizer18 = wx.BoxSizer( wx.VERTICAL )

        self.m_staticTextAvailLabel = wx.StaticText( sbSizer3.GetStaticBox(), wx.ID_ANY, u"Available : ", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticTextAvailLabel.Wrap( -1 )

        bSizer18.Add( self.m_staticTextAvailLabel, 0, wx.RIGHT|wx.LEFT|wx.ALIGN_CENTER_HORIZONTAL, 5 )

        self.text_avail = wx.StaticText( sbSizer3.GetStaticBox(), wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size( -1,-1 ), 0 )
        self.text_avail.Wrap( -1 )

        bSizer18.Add( self.text_avail, 0, wx.BOTTOM|wx.RIGHT|wx.LEFT, 5 )


        sbSizer3.Add( bSizer18, 0, wx.LEFT, 8 )

        bSizer20 = wx.BoxSizer( wx.HORIZONTAL )

        self.text_amount = wx.TextCtrl( sbSizer3.GetStaticBox(), wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
        self.text_amount.SetMinSize( wx.Size( 150,-1 ) )

        bSizer20.Add( self.text_amount, 0, wx.BOTTOM|wx.RIGHT|wx.LEFT, 8 )

        self.text_coin = wx.StaticText( sbSizer3.GetStaticBox(), wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
        self.text_coin.Wrap( -1 )

        bSizer20.Add( self.text_coin, 0, wx.TOP|wx.BOTTOM|wx.RIGHT, 5 )


        sbSizer3.Add( bSizer20, 0, 0, 5 )

        self.check_sendall = wx.CheckBox( sbSizer3.GetStaticBox(), wx.ID_ANY, u"Send all", wx.DefaultPosition, wx.DefaultSize, 0 )
        sbSizer3.Add( self.check_sendall, 0, wx.LEFT, 32 )


        sbSizer3.Add( ( 0, 0), 0, wx.TOP, 8 )

        bSizer191 = wx.BoxSizer( wx.HORIZONTAL )

        self.m_staticTextFiat = wx.StaticText( sbSizer3.GetStaticBox(), wx.ID_ANY, u"value ~", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticTextFiat.Wrap( -1 )

        self.m_staticTextFiat.SetFont( wx.Font( 9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, wx.EmptyString ) )

        bSizer191.Add( self.m_staticTextFiat, 0, wx.ALL, 5 )

        self.fiat_value = wx.StaticText( sbSizer3.GetStaticBox(), wx.ID_ANY, u"1234 $", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.fiat_value.Wrap( -1 )

        self.fiat_value.SetFont( wx.Font( 9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, wx.EmptyString ) )

        bSizer191.Add( self.fiat_value, 0, wx.ALL, 5 )


        sbSizer3.Add( bSizer191, 0, 0, 5 )


        bSizer15.Add( sbSizer3, 0, 0, 5 )

        sbSizer2 = wx.StaticBoxSizer( wx.StaticBox( self, wx.ID_ANY, u"Fees" ), wx.VERTICAL )

        sbSizer2.SetMinSize( wx.Size( -1,175 ) )

        sbSizer2.Add( ( 0, 0), 0, wx.TOP, 24 )

        self.fee_slider = wx.Slider( sbSizer2.GetStaticBox(), wx.ID_ANY, 1, 0, 2, wx.DefaultPosition, wx.DefaultSize, wx.SL_HORIZONTAL )
        sbSizer2.Add( self.fee_slider, 0, wx.ALL|wx.ALIGN_CENTER_HORIZONTAL, 5 )

        self.text_fees = wx.StaticText( sbSizer2.GetStaticBox(), wx.ID_ANY, u"Normal fee", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.text_fees.Wrap( -1 )

        self.text_fees.SetFont( wx.Font( 9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, wx.EmptyString ) )

        sbSizer2.Add( self.text_fees, 0, wx.ALL|wx.ALIGN_CENTER_HORIZONTAL, 5 )


        bSizer15.Add( sbSizer2, 0, wx.ALIGN_CENTER_VERTICAL|wx.LEFT, 24 )


        bSizer23.Add( bSizer15, 0, wx.ALIGN_CENTER_HORIZONTAL, 5 )

        bSizer19 = wx.BoxSizer( wx.HORIZONTAL )

        self.cancel_btn = wx.Button( self, wx.ID_ANY, u"Cancel", wx.DefaultPosition, wx.Size( -1,40 ), 0 )
        self.cancel_btn.SetFont( wx.Font( 10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, wx.EmptyString ) )

        bSizer19.Add( self.cancel_btn, 0, wx.ALL, 5 )


        bSizer19.Add( ( 0, 0), 0, wx.RIGHT, 32 )

        self.ok_btn = wx.Button( self, wx.ID_ANY, u"Proceed", wx.DefaultPosition, wx.Size( -1,40 ), 0 )
        self.ok_btn.SetFont( wx.Font( 11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, wx.EmptyString ) )

        bSizer19.Add( self.ok_btn, 0, wx.ALL, 5 )


        bSizer23.Add( bSizer19, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.TOP, 24 )


        bSizer23.Add( ( 0, 0), 0, wx.TOP, 16 )


        bSizer13.Add( bSizer23, 1, wx.EXPAND, 5 )


        bSizer13.Add( ( 0, 0), 0, wx.RIGHT, 24 )


        self.SetSizer( bSizer13 )
        self.Layout()
        bSizer13.Fit( self )

    def __del__( self ):
        pass


