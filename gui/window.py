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
        wx.Frame.__init__ ( self, parent, id = wx.ID_ANY, title = wx.EmptyString, pos = wx.DefaultPosition, size = wx.Size( 918,418 ), style = wx.CAPTION|wx.CLOSE_BOX|wx.MINIMIZE_BOX|wx.SYSTEM_MENU|wx.TAB_TRAVERSAL )

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
        self.network_choice = wx.Choice( self, wx.ID_ANY, wx.DefaultPosition, wx.Size( 150,-1 ), network_choiceChoices, 0 )
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
        self.wallopt_choice = wx.Choice( self, wx.ID_ANY, wx.DefaultPosition, wx.Size( 185,-1 ), wallopt_choiceChoices, 0 )
        self.wallopt_choice.SetSelection( 0 )
        self.wallopt_choice.SetFont( wx.Font( 12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, wx.EmptyString ) )
        self.wallopt_choice.Enable( False )

        bSizer2.Add( self.wallopt_choice, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.TOP, 5 )


        bSizer2.Add( ( 220, 32), 1, wx.EXPAND, 5 )


        bSizer1.Add( bSizer2, 0, wx.ALIGN_CENTER_VERTICAL, 5 )

        bSizer3 = wx.BoxSizer( wx.VERTICAL )

        bSizer5 = wx.BoxSizer( wx.VERTICAL )

        self.account_label = wx.StaticText( self, wx.ID_ANY, u"Account", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.account_label.Wrap( -1 )

        self.account_label.SetFont( wx.Font( 14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, wx.EmptyString ) )

        bSizer5.Add( self.account_label, 0, wx.TOP|wx.RIGHT|wx.LEFT, 5 )

        self.account_addr = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size( 585,-1 ), wx.TE_CENTER|wx.TE_READONLY|wx.BORDER_NONE )
        self.account_addr.SetFont( wx.Font( 14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, wx.EmptyString ) )

        bSizer5.Add( self.account_addr, 0, wx.BOTTOM|wx.TOP|wx.ALIGN_CENTER_HORIZONTAL, 16 )


        bSizer3.Add( bSizer5, 0, wx.LEFT|wx.TOP|wx.ALIGN_CENTER_HORIZONTAL, 12 )

        bSizer6 = wx.BoxSizer( wx.HORIZONTAL )

        bSizer18 = wx.BoxSizer( wx.VERTICAL )

        bSizer19 = wx.BoxSizer( wx.HORIZONTAL )

        self.hist_button = wx.BitmapButton( self, wx.ID_ANY, wx.NullBitmap, wx.DefaultPosition, wx.DefaultSize, wx.BU_AUTODRAW|wx.BORDER_NONE )

        self.hist_button.SetBitmap( wx.NullBitmap )
        self.hist_button.Enable( False )

        bSizer19.Add( self.hist_button, 0, wx.LEFT, 25 )

        self.copy_button = wx.BitmapButton( self, wx.ID_ANY, wx.NullBitmap, wx.DefaultPosition, wx.DefaultSize, wx.BU_AUTODRAW|wx.BORDER_NONE )

        self.copy_button.SetBitmap( wx.NullBitmap )
        self.copy_button.Enable( False )

        bSizer19.Add( self.copy_button, 0, wx.LEFT, 75 )


        bSizer18.Add( bSizer19, 0, 0, 5 )

        bSizer16 = wx.BoxSizer( wx.HORIZONTAL )

        self.balance_label = wx.StaticText( self, wx.ID_ANY, u"Balance :", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.balance_label.Wrap( -1 )

        self.balance_label.SetFont( wx.Font( 15, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, wx.EmptyString ) )

        bSizer16.Add( self.balance_label, 0, wx.ALIGN_BOTTOM|wx.TOP|wx.LEFT, 20 )

        self.balance_info = wx.StaticText( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
        self.balance_info.Wrap( -1 )

        self.balance_info.SetFont( wx.Font( 15, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, wx.EmptyString ) )

        bSizer16.Add( self.balance_info, 0, wx.ALIGN_BOTTOM|wx.TOP|wx.LEFT, 16 )


        bSizer18.Add( bSizer16, 0, wx.TOP, 16 )


        bSizer6.Add( bSizer18, 1, 0, 5 )

        self.copy_status = wx.StaticText( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
        self.copy_status.Wrap( -1 )

        bSizer6.Add( self.copy_status, 0, wx.TOP|wx.LEFT, 10 )

        self.qrimg = wx.StaticBitmap( self, wx.ID_ANY, wx.NullBitmap, wx.DefaultPosition, wx.Size( 140,140 ), 0 )
        bSizer6.Add( self.qrimg, 0, wx.LEFT, 148 )


        bSizer3.Add( bSizer6, 0, wx.ALIGN_CENTER_HORIZONTAL, 8 )

        bSizer4 = wx.BoxSizer( wx.HORIZONTAL )

        self.dest_label = wx.StaticText( self, wx.ID_ANY, u"To :", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.dest_label.Wrap( -1 )

        self.dest_label.SetFont( wx.Font( 14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, wx.EmptyString ) )

        bSizer4.Add( self.dest_label, 0, wx.ALL|wx.ALIGN_BOTTOM, 8 )

        self.addr_panel = wx.Panel( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
        bSizer20 = wx.BoxSizer( wx.VERTICAL )

        self.dest_addr = wx.TextCtrl( self.addr_panel, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size( 584,-1 ), 0 )
        self.dest_addr.SetFont( wx.Font( 14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, wx.EmptyString ) )
        self.dest_addr.Enable( False )

        bSizer20.Add( self.dest_addr, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 3 )


        self.addr_panel.SetSizer( bSizer20 )
        self.addr_panel.Layout()
        bSizer20.Fit( self.addr_panel )
        bSizer4.Add( self.addr_panel, 0, wx.ALIGN_BOTTOM, 3 )


        bSizer3.Add( bSizer4, 0, wx.EXPAND|wx.TOP, 8 )

        bSizer7 = wx.BoxSizer( wx.HORIZONTAL )

        self.amount_label = wx.StaticText( self, wx.ID_ANY, u"Amount :", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.amount_label.Wrap( -1 )

        self.amount_label.SetFont( wx.Font( 14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, wx.EmptyString ) )

        bSizer7.Add( self.amount_label, 0, wx.LEFT|wx.TOP, 8 )

        self.amount = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.TE_PROCESS_ENTER )
        self.amount.SetFont( wx.Font( 14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, wx.EmptyString ) )
        self.amount.Enable( False )

        bSizer7.Add( self.amount, 0, wx.ALL, 5 )

        bSizer9 = wx.BoxSizer( wx.VERTICAL )

        self.fee_slider = wx.Slider( self, wx.ID_ANY, 1, 0, 2, wx.DefaultPosition, wx.DefaultSize, wx.SL_HORIZONTAL )
        bSizer9.Add( self.fee_slider, 0, wx.LEFT|wx.TOP, 6 )

        self.fee_setting = wx.StaticText( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.ALIGN_CENTER_HORIZONTAL )
        self.fee_setting.Wrap( -1 )

        self.fee_setting.SetFont( wx.Font( 10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, wx.EmptyString ) )

        bSizer9.Add( self.fee_setting, 0, wx.LEFT, 6 )


        bSizer7.Add( bSizer9, 0, 0, 0 )

        self.send_button = wx.BitmapButton( self, wx.ID_ANY, wx.NullBitmap, wx.DefaultPosition, wx.DefaultSize, wx.BU_AUTODRAW|wx.BORDER_NONE )

        self.send_button.SetBitmap( wx.NullBitmap )
        self.send_button.Enable( False )

        bSizer7.Add( self.send_button, 0, wx.TOP|wx.LEFT, 8 )


        bSizer7.Add( ( 0, 0), 1, wx.LEFT, 8 )

        self.send_all = wx.BitmapButton( self, wx.ID_ANY, wx.NullBitmap, wx.DefaultPosition, wx.DefaultSize, wx.BU_AUTODRAW|wx.BORDER_NONE )

        self.send_all.SetBitmap( wx.NullBitmap )
        self.send_all.Enable( False )

        bSizer7.Add( self.send_all, 0, wx.LEFT|wx.TOP, 8 )


        bSizer3.Add( bSizer7, 0, wx.TOP, 12 )


        bSizer1.Add( bSizer3, 1, 0, 5 )


        self.SetSizer( bSizer1 )
        self.Layout()
        bSizer1.Fit( self )

    def __del__( self ):
        pass


###########################################################################
## Class HDDialog
###########################################################################

class HDDialog ( wx.Dialog ):

    def __init__( self, parent ):
        wx.Dialog.__init__ ( self, parent, id = wx.ID_ANY, title = u"HD wallet settings", pos = wx.DefaultPosition, size = wx.Size( 500,438 ), style = wx.CAPTION|wx.CLOSE_BOX|wx.DEFAULT_DIALOG_STYLE|wx.STAY_ON_TOP|wx.SYSTEM_MENU )

        self.SetSizeHints( wx.DefaultSize, wx.DefaultSize )


        self.Centre( wx.BOTH )

    def __del__( self ):
        pass


###########################################################################
## Class HDPanel
###########################################################################

class HDPanel ( wx.Panel ):

    def __init__( self, parent, id = wx.ID_ANY, pos = wx.DefaultPosition, size = wx.Size( -1,-1 ), style = wx.TAB_TRAVERSAL, name = wx.EmptyString ):
        wx.Panel.__init__ ( self, parent, id = id, pos = pos, size = size, style = style, name = name )

        bSizer11 = wx.BoxSizer( wx.VERTICAL )

        bSizer15 = wx.BoxSizer( wx.HORIZONTAL )

        self.m_staticText15 = wx.StaticText( self, wx.ID_ANY, u"Wallet mnemonic input", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText15.Wrap( -1 )

        self.m_staticText15.SetFont( wx.Font( 12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, wx.EmptyString ) )

        bSizer15.Add( self.m_staticText15, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL|wx.LEFT, 42 )


        bSizer15.Add( ( 24, 0), 0, 0, 15 )

        self.m_staticText16 = wx.StaticText( self, wx.ID_ANY, u"Words in list", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText16.Wrap( -1 )

        bSizer15.Add( self.m_staticText16, 0, wx.ALIGN_BOTTOM|wx.ALL, 5 )

        self.m_bitmapHDwl = wx.StaticBitmap( self, wx.ID_ANY, wx.NullBitmap, wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer15.Add( self.m_bitmapHDwl, 0, wx.ALIGN_BOTTOM|wx.BOTTOM, 5 )

        self.m_staticText17 = wx.StaticText( self, wx.ID_ANY, u"Checksum", wx.DefaultPosition, wx.DefaultSize, wx.ST_NO_AUTORESIZE )
        self.m_staticText17.Wrap( -1 )

        bSizer15.Add( self.m_staticText17, 0, wx.ALL|wx.ALIGN_BOTTOM, 5 )

        self.m_bitmapHDcs = wx.StaticBitmap( self, wx.ID_ANY, wx.NullBitmap, wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer15.Add( self.m_bitmapHDcs, 0, wx.ALIGN_BOTTOM|wx.BOTTOM, 5 )


        bSizer11.Add( bSizer15, 1, wx.EXPAND, 5 )

        self.m_textCtrl_mnemo = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.TE_MULTILINE )
        self.m_textCtrl_mnemo.SetFont( wx.Font( 12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, wx.EmptyString ) )

        bSizer11.Add( self.m_textCtrl_mnemo, 1, wx.EXPAND|wx.LEFT|wx.RIGHT, 16 )

        bSizer13 = wx.BoxSizer( wx.HORIZONTAL )


        bSizer13.Add( ( 0, 0), 0, wx.RIGHT, 18 )

        self.m_staticText13 = wx.StaticText( self, wx.ID_ANY, u"Password (optional)", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText13.Wrap( -1 )

        bSizer13.Add( self.m_staticText13, 0, wx.ALIGN_CENTER_VERTICAL, 5 )

        self.m_textCtrl_pwd = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size( 180,-1 ), 0 )
        bSizer13.Add( self.m_textCtrl_pwd, 0, wx.ALL, 5 )

        self.m_checkBox_secboost = wx.CheckBox( self, wx.ID_ANY, u"SecuBoost", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_checkBox_secboost.SetToolTip( u"Extra security boost for mnemonic.\nNot compatible with BIP39.\nRequires >1GB RAM free" )

        bSizer13.Add( self.m_checkBox_secboost, 0, wx.ALIGN_CENTER_VERTICAL|wx.LEFT, 28 )


        bSizer11.Add( bSizer13, 0, wx.ALIGN_CENTER_HORIZONTAL, 5 )

        bSizer14 = wx.BoxSizer( wx.HORIZONTAL )

        self.m_staticText14 = wx.StaticText( self, wx.ID_ANY, u"Account #", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText14.Wrap( -1 )

        bSizer14.Add( self.m_staticText14, 0, wx.ALIGN_CENTER_VERTICAL, 5 )

        self.m_spinCtrl_accountidx = wx.SpinCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size( 75,-1 ), wx.SP_ARROW_KEYS, 0, 10, 0 )
        bSizer14.Add( self.m_spinCtrl_accountidx, 0, wx.ALL, 5 )


        bSizer11.Add( bSizer14, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.TOP, 16 )


        bSizer11.Add( ( 0, 0), 0, wx.TOP, 20 )

        self.m_staticText151 = wx.StaticText( self, wx.ID_ANY, u"Validate this first proposal,\nor insert your mnemonic and settings to import an existing HD wallet.", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText151.Wrap( -1 )

        self.m_staticText151.SetFont( wx.Font( 10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, wx.EmptyString ) )

        bSizer11.Add( self.m_staticText151, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.LEFT|wx.RIGHT, 24 )

        bSizer12 = wx.BoxSizer( wx.HORIZONTAL )

        self.m_butOK = wx.Button( self, wx.ID_ANY, u"OK", wx.DefaultPosition, wx.Size( -1,36 ), 0 )
        bSizer12.Add( self.m_butOK, 0, wx.ALL, 5 )


        bSizer12.Add( ( 0, 0), 1, wx.RIGHT, 25 )

        self.m_butcancel = wx.Button( self, wx.ID_ANY, u"Cancel", wx.DefaultPosition, wx.Size( -1,36 ), 0 )
        bSizer12.Add( self.m_butcancel, 0, wx.ALL, 5 )


        bSizer11.Add( bSizer12, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 20 )


        self.SetSizer( bSizer11 )
        self.Layout()
        bSizer11.Fit( self )

        # Connect Events
        self.m_textCtrl_mnemo.Bind( wx.EVT_TEXT, self.hdmnemo_changed )
        self.m_butOK.Bind( wx.EVT_BUTTON, self.hd_ok )
        self.m_butcancel.Bind( wx.EVT_BUTTON, self.hd_cancel )

    def __del__( self ):
        pass


    # Virtual event handlers, overide them in your derived class
    def hdmnemo_changed( self, event ):
        event.Skip()

    def hd_ok( self, event ):
        event.Skip()

    def hd_cancel( self, event ):
        event.Skip()


###########################################################################
## Class OptionDialog
###########################################################################

class OptionDialog ( wx.Dialog ):

    def __init__( self, parent ):
        wx.Dialog.__init__ ( self, parent, id = wx.ID_ANY, title = wx.EmptyString, pos = wx.DefaultPosition, size = wx.Size( 453,325 ), style = wx.DEFAULT_DIALOG_STYLE )

        self.SetSizeHints( wx.DefaultSize, wx.DefaultSize )


        self.Centre( wx.BOTH )

    def __del__( self ):
        pass


###########################################################################
## Class OptionPanel
###########################################################################

class OptionPanel ( wx.Panel ):

    def __init__( self, parent, id = wx.ID_ANY, pos = wx.DefaultPosition, size = wx.Size( -1,-1 ), style = wx.TAB_TRAVERSAL, name = wx.EmptyString ):
        wx.Panel.__init__ ( self, parent, id = id, pos = pos, size = size, style = style, name = name )

        bSizer18 = wx.BoxSizer( wx.VERTICAL )


        bSizer18.Add( ( 0, 0), 1, wx.TOP, 16 )

        self.preset_text = wx.StaticText( self, wx.ID_ANY, u"Known Preset", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.preset_text.Wrap( -1 )

        self.preset_text.SetFont( wx.Font( 11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, wx.EmptyString ) )

        bSizer18.Add( self.preset_text, 0, wx.ALL|wx.ALIGN_CENTER_HORIZONTAL, 5 )

        known_choiceChoices = []
        self.known_choice = wx.Choice( self, wx.ID_ANY, wx.DefaultPosition, wx.Size( 360,-1 ), known_choiceChoices, 0 )
        self.known_choice.SetSelection( 0 )
        self.known_choice.SetFont( wx.Font( 11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, wx.EmptyString ) )

        bSizer18.Add( self.known_choice, 0, wx.ALL|wx.ALIGN_CENTER_HORIZONTAL, 5 )

        self.m_staticTextor = wx.StaticText( self, wx.ID_ANY, u"OR", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticTextor.Wrap( -1 )

        self.m_staticTextor.SetFont( wx.Font( 11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, wx.EmptyString ) )

        bSizer18.Add( self.m_staticTextor, 0, wx.ALL|wx.ALIGN_CENTER_HORIZONTAL, 5 )

        self.custom_text = wx.StaticText( self, wx.ID_ANY, u"other custom", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.custom_text.Wrap( -1 )

        self.custom_text.SetFont( wx.Font( 11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, wx.EmptyString ) )

        bSizer18.Add( self.custom_text, 0, wx.ALL|wx.ALIGN_CENTER_HORIZONTAL, 5 )

        self.new_choice = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size( 375,-1 ), wx.TE_PROCESS_ENTER )
        self.new_choice.SetFont( wx.Font( 11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, wx.EmptyString ) )

        bSizer18.Add( self.new_choice, 0, wx.ALL|wx.ALIGN_CENTER_HORIZONTAL, 5 )

        bSizer19 = wx.BoxSizer( wx.HORIZONTAL )

        self.m_button4 = wx.Button( self, wx.ID_ANY, u"Cancel", wx.DefaultPosition, wx.Size( -1,40 ), 0 )
        self.m_button4.SetFont( wx.Font( 11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, wx.EmptyString ) )

        bSizer19.Add( self.m_button4, 0, wx.ALL, 5 )


        bSizer19.Add( ( 0, 0), 1, wx.LEFT, 16 )

        self.m_button3 = wx.Button( self, wx.ID_ANY, u"OK", wx.DefaultPosition, wx.Size( -1,40 ), 0 )
        self.m_button3.SetFont( wx.Font( 11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, wx.EmptyString ) )

        bSizer19.Add( self.m_button3, 0, wx.ALL, 5 )


        bSizer18.Add( bSizer19, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.TOP, 28 )


        bSizer18.Add( ( 0, 0), 1, wx.EXPAND, 5 )


        self.SetSizer( bSizer18 )
        self.Layout()
        bSizer18.Fit( self )

        # Connect Events
        self.new_choice.Bind( wx.EVT_TEXT_ENTER, self.valid_custom )
        self.m_button4.Bind( wx.EVT_BUTTON, self.cancelOption )
        self.m_button3.Bind( wx.EVT_BUTTON, self.okOption )

    def __del__( self ):
        pass


    # Virtual event handlers, overide them in your derived class
    def valid_custom( self, event ):
        event.Skip()

    def cancelOption( self, event ):
        event.Skip()

    def okOption( self, event ):
        event.Skip()


