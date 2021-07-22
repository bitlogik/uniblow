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
## Class TopFrame
###########################################################################

class TopFrame ( wx.Frame ):

    def __init__( self, parent ):
        wx.Frame.__init__ ( self, parent, id = wx.ID_ANY, title = wx.EmptyString, pos = wx.DefaultPosition, size = wx.Size( 996,383 ), style = wx.CAPTION|wx.CLOSE_BOX|wx.MINIMIZE_BOX|wx.SYSTEM_MENU|wx.TAB_TRAVERSAL )

        self.SetSizeHints( wx.DefaultSize, wx.DefaultSize )


        self.Centre( wx.BOTH )

    def __del__( self ):
        pass


###########################################################################
## Class TopPanel
###########################################################################

class TopPanel ( wx.Panel ):

    def __init__( self, parent, id = wx.ID_ANY, pos = wx.DefaultPosition, size = wx.Size( -1,-1 ), style = wx.TAB_TRAVERSAL, name = wx.EmptyString ):
        wx.Panel.__init__ ( self, parent, id = id, pos = pos, size = size, style = style, name = name )

        self.SetFont( wx.Font( wx.NORMAL_FONT.GetPointSize(), wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, wx.EmptyString ) )

        bSizer1 = wx.BoxSizer( wx.HORIZONTAL )

        bSizer2 = wx.BoxSizer( wx.VERTICAL )

        self.device_label = wx.StaticText( self, wx.ID_ANY, u"Device", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.device_label.Wrap( -1 )

        self.device_label.SetFont( wx.Font( 11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, wx.EmptyString ) )

        bSizer2.Add( self.device_label, 0, wx.ALL|wx.ALIGN_CENTER_HORIZONTAL, 5 )

        devices_choiceChoices = []
        self.devices_choice = wx.Choice( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, devices_choiceChoices, 0 )
        self.devices_choice.SetSelection( 0 )
        self.devices_choice.SetFont( wx.Font( 12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, wx.EmptyString ) )

        bSizer2.Add( self.devices_choice, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.BOTTOM, 20 )

        self.coins_label = wx.StaticText( self, wx.ID_ANY, u"Blockchain", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.coins_label.Wrap( -1 )

        self.coins_label.SetFont( wx.Font( 10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, wx.EmptyString ) )

        bSizer2.Add( self.coins_label, 0, wx.ALL|wx.ALIGN_CENTER_HORIZONTAL, 5 )

        coins_choiceChoices = []
        self.coins_choice = wx.Choice( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, coins_choiceChoices, 0 )
        self.coins_choice.SetSelection( 0 )
        self.coins_choice.SetFont( wx.Font( 12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, wx.EmptyString ) )
        self.coins_choice.Enable( False )

        bSizer2.Add( self.coins_choice, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER_HORIZONTAL, 5 )

        self.network_label = wx.StaticText( self, wx.ID_ANY, u"Network", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.network_label.Wrap( -1 )

        self.network_label.SetFont( wx.Font( 10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, wx.EmptyString ) )
        self.network_label.Enable( False )

        bSizer2.Add( self.network_label, 0, wx.ALL|wx.ALIGN_CENTER_HORIZONTAL, 5 )

        network_choiceChoices = []
        self.network_choice = wx.Choice( self, wx.ID_ANY, wx.DefaultPosition, wx.Size( 120,-1 ), network_choiceChoices, 0 )
        self.network_choice.SetSelection( 0 )
        self.network_choice.SetFont( wx.Font( 12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, wx.EmptyString ) )
        self.network_choice.Enable( False )

        bSizer2.Add( self.network_choice, 0, wx.ALL|wx.ALIGN_CENTER_HORIZONTAL, 5 )

        self.wallopt_label = wx.StaticText( self, wx.ID_ANY, u"Account Type", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.wallopt_label.Wrap( -1 )

        self.wallopt_label.SetFont( wx.Font( 10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, wx.EmptyString ) )
        self.wallopt_label.Enable( False )

        bSizer2.Add( self.wallopt_label, 0, wx.ALL|wx.ALIGN_CENTER_HORIZONTAL, 5 )

        wallopt_choiceChoices = []
        self.wallopt_choice = wx.Choice( self, wx.ID_ANY, wx.DefaultPosition, wx.Size( 150,-1 ), wallopt_choiceChoices, 0 )
        self.wallopt_choice.SetSelection( 0 )
        self.wallopt_choice.SetFont( wx.Font( 12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, wx.EmptyString ) )
        self.wallopt_choice.Enable( False )

        bSizer2.Add( self.wallopt_choice, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.TOP, 5 )


        bSizer2.Add( ( 220, 32), 1, wx.EXPAND, 5 )


        bSizer1.Add( bSizer2, 0, wx.ALIGN_CENTER_VERTICAL, 5 )

        bSizer3 = wx.BoxSizer( wx.VERTICAL )

        bSizer5 = wx.BoxSizer( wx.HORIZONTAL )

        self.account_label = wx.StaticText( self, wx.ID_ANY, u"Account :", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.account_label.Wrap( -1 )

        self.account_label.SetFont( wx.Font( 14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, wx.EmptyString ) )

        bSizer5.Add( self.account_label, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5 )

        self.account_addr = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size( 585,-1 ), wx.TE_READONLY|wx.BORDER_NONE )
        self.account_addr.SetFont( wx.Font( 14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, wx.EmptyString ) )

        bSizer5.Add( self.account_addr, 1, wx.ALIGN_CENTER_VERTICAL, 2 )


        bSizer3.Add( bSizer5, 1, wx.EXPAND, 3 )

        bSizer6 = wx.BoxSizer( wx.HORIZONTAL )

        self.balance_label = wx.StaticText( self, wx.ID_ANY, u"Balance :", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.balance_label.Wrap( -1 )

        self.balance_label.SetFont( wx.Font( 14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, wx.EmptyString ) )

        bSizer6.Add( self.balance_label, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )

        self.balance_info = wx.StaticText( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
        self.balance_info.Wrap( -1 )

        self.balance_info.SetFont( wx.Font( 16, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, wx.EmptyString ) )

        bSizer6.Add( self.balance_info, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5 )

        self.hist_button = wx.Button( self, wx.ID_ANY, u"History", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.hist_button.Enable( False )

        bSizer6.Add( self.hist_button, 0, wx.BOTTOM|wx.RIGHT|wx.LEFT, 5 )

        self.copy_button = wx.Button( self, wx.ID_ANY, u"Copy", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.copy_button.Enable( False )

        bSizer6.Add( self.copy_button, 0, wx.LEFT, 16 )

        self.copy_status = wx.StaticText( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
        self.copy_status.Wrap( -1 )

        bSizer6.Add( self.copy_status, 0, wx.ALL, 5 )

        bSizer8 = wx.BoxSizer( wx.VERTICAL )

        self.qrimg = wx.StaticBitmap( self, wx.ID_ANY, wx.NullBitmap, wx.DefaultPosition, wx.Size( 140,140 ), 0 )
        bSizer8.Add( self.qrimg, 0, wx.ALIGN_RIGHT|wx.RIGHT, 50 )


        bSizer6.Add( bSizer8, 1, wx.EXPAND, 5 )


        bSizer3.Add( bSizer6, 1, wx.EXPAND, 5 )

        bSizer4 = wx.BoxSizer( wx.HORIZONTAL )

        self.dest_label = wx.StaticText( self, wx.ID_ANY, u"To :", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.dest_label.Wrap( -1 )

        self.dest_label.SetFont( wx.Font( 14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, wx.EmptyString ) )

        bSizer4.Add( self.dest_label, 0, wx.ALL|wx.ALIGN_BOTTOM, 6 )

        self.addr_panel = wx.Panel( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
        bSizer11 = wx.BoxSizer( wx.HORIZONTAL )

        self.dest_addr = wx.TextCtrl( self.addr_panel, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size( 570,-1 ), 0 )
        self.dest_addr.SetFont( wx.Font( 14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, wx.EmptyString ) )

        bSizer11.Add( self.dest_addr, 0, wx.ALIGN_BOTTOM|wx.ALL, 2 )


        self.addr_panel.SetSizer( bSizer11 )
        self.addr_panel.Layout()
        bSizer11.Fit( self.addr_panel )
        bSizer4.Add( self.addr_panel, 0, wx.ALIGN_BOTTOM, 5 )


        bSizer3.Add( bSizer4, 1, wx.EXPAND, 5 )

        bSizer7 = wx.BoxSizer( wx.HORIZONTAL )

        self.amount_label = wx.StaticText( self, wx.ID_ANY, u"Amount :", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.amount_label.Wrap( -1 )

        self.amount_label.SetFont( wx.Font( 14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, wx.EmptyString ) )

        bSizer7.Add( self.amount_label, 0, wx.ALL, 7 )

        self.amount = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.TE_PROCESS_ENTER )
        self.amount.SetFont( wx.Font( 14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, wx.EmptyString ) )

        bSizer7.Add( self.amount, 0, wx.ALL, 5 )


        bSizer7.Add( ( 32, 0), 0, 0, 5 )

        bSizer9 = wx.BoxSizer( wx.VERTICAL )

        self.fee_slider = wx.Slider( self, wx.ID_ANY, 1, 0, 2, wx.DefaultPosition, wx.DefaultSize, wx.SL_HORIZONTAL )
        bSizer9.Add( self.fee_slider, 0, wx.LEFT|wx.RIGHT|wx.TOP, 10 )

        self.fee_setting = wx.StaticText( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.ALIGN_CENTER_HORIZONTAL )
        self.fee_setting.Wrap( -1 )

        self.fee_setting.SetFont( wx.Font( 10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, wx.EmptyString ) )

        bSizer9.Add( self.fee_setting, 0, 0, 5 )


        bSizer7.Add( bSizer9, 0, 0, 0 )

        self.send_button = wx.Button( self, wx.ID_ANY, u"Send", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.send_button.SetFont( wx.Font( 12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, wx.EmptyString ) )
        self.send_button.Enable( False )

        bSizer7.Add( self.send_button, 0, wx.ALL, 5 )

        self.send_all = wx.Button( self, wx.ID_ANY, u"Swipe Max", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.send_all.SetFont( wx.Font( 12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, wx.EmptyString ) )
        self.send_all.Enable( False )

        bSizer7.Add( self.send_all, 0, wx.ALL, 5 )


        bSizer3.Add( bSizer7, 1, wx.EXPAND, 5 )


        bSizer1.Add( bSizer3, 1, wx.EXPAND, 5 )


        self.SetSizer( bSizer1 )
        self.Layout()

    def __del__( self ):
        pass


