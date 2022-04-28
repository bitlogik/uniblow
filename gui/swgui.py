# -*- coding: utf-8 -*-

###########################################################################
## Python code generated with wxFormBuilder (version Oct 26 2018)
## http://www.wxformbuilder.org/
##
## PLEASE DO *NOT* EDIT THIS FILE!
###########################################################################

import wx
import wx.xrc
import wx.dataview

###########################################################################
## Class MainFrame
###########################################################################

class MainFrame ( wx.Frame ):

    def __init__( self, parent ):
        wx.Frame.__init__ ( self, parent, id = wx.ID_ANY, title = u"  [ Uniblow ]    Seed Watcher", pos = wx.DefaultPosition, size = wx.Size( 650,700 ), style = wx.CAPTION|wx.CLOSE_BOX|wx.SYSTEM_MENU|wx.FULL_REPAINT_ON_RESIZE|wx.TAB_TRAVERSAL )

        self.SetSizeHints( wx.DefaultSize, wx.DefaultSize )


        self.Centre( wx.BOTH )

        # Connect Events
        self.Bind( wx.EVT_CLOSE, self.closesw )

    def __del__( self ):
        pass


    # Virtual event handlers, overide them in your derived class
    def closesw( self, event ):
        event.Skip()


###########################################################################
## Class MainPanel
###########################################################################

class MainPanel ( wx.Panel ):

    def __init__( self, parent, id = wx.ID_ANY, pos = wx.DefaultPosition, size = wx.Size( -1,-1 ), style = wx.TAB_TRAVERSAL, name = wx.EmptyString ):
        wx.Panel.__init__ ( self, parent, id = id, pos = pos, size = size, style = style, name = name )

        bSizer11 = wx.BoxSizer( wx.VERTICAL )


        bSizer11.Add( ( 0, 0), 0, wx.BOTTOM, 15 )

        bSizer31 = wx.BoxSizer( wx.HORIZONTAL )

        bSizer31.SetMinSize( wx.Size( -1,40 ) )
        self.m_button_gen = wx.BitmapButton( self, wx.ID_ANY, wx.NullBitmap, wx.DefaultPosition, wx.DefaultSize, wx.BU_AUTODRAW|wx.BORDER_NONE )

        self.m_button_gen.SetBitmap( wx.NullBitmap )
        bSizer31.Add( self.m_button_gen, 0, wx.ALIGN_CENTER_VERTICAL|wx.BOTTOM|wx.RIGHT|wx.LEFT, 10 )

        bSizer6 = wx.BoxSizer( wx.VERTICAL )

        self.m_staticText9 = wx.StaticText( self, wx.ID_ANY, u"Generation option", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText9.Wrap( -1 )

        self.m_staticText9.SetFont( wx.Font( 9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, wx.EmptyString ) )

        bSizer6.Add( self.m_staticText9, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.TOP|wx.RIGHT|wx.LEFT, 5 )

        m_choice_nwordsChoices = []
        self.m_choice_nwords = wx.Choice( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, m_choice_nwordsChoices, 0 )
        self.m_choice_nwords.SetSelection( 0 )
        self.m_choice_nwords.SetFont( wx.Font( 11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, wx.EmptyString ) )

        bSizer6.Add( self.m_choice_nwords, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER_HORIZONTAL|wx.RIGHT|wx.LEFT, 10 )


        bSizer31.Add( bSizer6, 1, wx.EXPAND, 5 )


        bSizer11.Add( bSizer31, 0, wx.ALIGN_CENTER_HORIZONTAL, 5 )


        bSizer11.Add( ( 0, 0), 0, wx.TOP, 8 )

        bSizer3 = wx.BoxSizer( wx.HORIZONTAL )

        self.m_staticText12 = wx.StaticText( self, wx.ID_ANY, u"Wallet mnemonic", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText12.Wrap( -1 )

        self.m_staticText12.SetFont( wx.Font( 12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, wx.EmptyString ) )

        bSizer3.Add( self.m_staticText12, 1, wx.ALIGN_BOTTOM|wx.RIGHT, 40 )

        self.m_staticText5 = wx.StaticText( self, wx.ID_ANY, u"  Words in list", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText5.Wrap( -1 )

        bSizer3.Add( self.m_staticText5, 0, wx.ALL, 5 )

        self.m_bitmap_wl = wx.StaticBitmap( self, wx.ID_ANY, wx.NullBitmap, wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer3.Add( self.m_bitmap_wl, 0, wx.ALIGN_CENTER, 7 )


        bSizer3.Add( ( 0, 0), 0, wx.RIGHT, 8 )

        self.m_staticText6 = wx.StaticText( self, wx.ID_ANY, u"  Checksum", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText6.Wrap( -1 )

        bSizer3.Add( self.m_staticText6, 0, wx.ALL, 5 )

        self.m_bitmap_cs = wx.StaticBitmap( self, wx.ID_ANY, wx.NullBitmap, wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer3.Add( self.m_bitmap_cs, 0, wx.ALIGN_CENTER_VERTICAL, 7 )


        bSizer11.Add( bSizer3, 0, wx.ALIGN_CENTER_HORIZONTAL, 5 )

        self.m_textCtrl_mnemo = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size( -1,100 ), wx.TE_MULTILINE|wx.TE_PROCESS_ENTER|wx.BORDER_SIMPLE )
        self.m_textCtrl_mnemo.SetFont( wx.Font( 12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, wx.EmptyString ) )

        bSizer11.Add( self.m_textCtrl_mnemo, 0, wx.ALL|wx.EXPAND, 5 )

        bSizer4 = wx.BoxSizer( wx.HORIZONTAL )


        bSizer4.Add( ( 0, 0), 0, wx.RIGHT, 35 )

        self.m_staticText51 = wx.StaticText( self, wx.ID_ANY, u"Der. password (optional)", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText51.Wrap( -1 )

        bSizer4.Add( self.m_staticText51, 0, wx.ALIGN_CENTER_VERTICAL|wx.TOP|wx.BOTTOM|wx.RIGHT, 5 )

        self.m_textpwd = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size( 190,-1 ), wx.TE_PROCESS_ENTER )
        bSizer4.Add( self.m_textpwd, 0, wx.TOP|wx.BOTTOM, 5 )


        bSizer4.Add( ( 0, 0), 0, wx.RIGHT, 18 )

        self.m_staticText7 = wx.StaticText( self, wx.ID_ANY, u"Type", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText7.Wrap( -1 )

        bSizer4.Add( self.m_staticText7, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )

        m_typechoiceChoices = [ u"BIP39", u"Electrum", u"Electrum old", u"SecuBoost" ]
        self.m_typechoice = wx.Choice( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, m_typechoiceChoices, 0 )
        self.m_typechoice.SetSelection( 0 )
        bSizer4.Add( self.m_typechoice, 0, wx.LEFT|wx.RIGHT|wx.TOP, 4 )


        bSizer11.Add( bSizer4, 0, wx.EXPAND, 5 )


        bSizer11.Add( ( 0, 0), 0, wx.ALIGN_CENTER_HORIZONTAL|wx.TOP, 16 )

        bSizer5 = wx.BoxSizer( wx.HORIZONTAL )

        self.m_staticTextAcct = wx.StaticText( self, wx.ID_ANY, u"Account #", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticTextAcct.Wrap( -1 )

        bSizer5.Add( self.m_staticTextAcct, 0, wx.ALIGN_CENTER_VERTICAL, 5 )

        self.m_account = wx.SpinCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size( 112,-1 ), wx.SP_ARROW_KEYS, 0, 2147483647, 0 )
        bSizer5.Add( self.m_account, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5 )

        self.is_change = wx.CheckBox( self, wx.ID_ANY, u"internal", wx.DefaultPosition, wx.DefaultSize, wx.ALIGN_RIGHT )
        bSizer5.Add( self.is_change, 0, wx.ALIGN_CENTER_VERTICAL|wx.LEFT, 22 )

        self.m_staticTextIdx = wx.StaticText( self, wx.ID_ANY, u"Index", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticTextIdx.Wrap( -1 )

        bSizer5.Add( self.m_staticTextIdx, 0, wx.ALIGN_CENTER_VERTICAL|wx.LEFT, 25 )

        self.m_index = wx.SpinCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size( 112,-1 ), wx.SP_ARROW_KEYS, 0, 2147483647, 0 )
        bSizer5.Add( self.m_index, 0, wx.ALIGN_CENTER_VERTICAL|wx.TOP|wx.BOTTOM|wx.LEFT, 5 )


        bSizer11.Add( bSizer5, 0, wx.ALIGN_CENTER, 5 )

        self.m_btnseek = wx.BitmapButton( self, wx.ID_ANY, wx.NullBitmap, wx.DefaultPosition, wx.DefaultSize, wx.BU_AUTODRAW|wx.BORDER_NONE )

        self.m_btnseek.SetBitmap( wx.NullBitmap )
        bSizer11.Add( self.m_btnseek, 0, wx.ALL|wx.ALIGN_CENTER_HORIZONTAL, 14 )

        self.m_staticTextcopy = wx.StaticText( self, wx.ID_ANY, u"Right click on asset line to open menu", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticTextcopy.Wrap( -1 )

        self.m_staticTextcopy.SetFont( wx.Font( 10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, wx.EmptyString ) )
        self.m_staticTextcopy.Enable( False )

        bSizer11.Add( self.m_staticTextcopy, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.TOP|wx.RIGHT|wx.LEFT, 5 )

        self.m_dataViewListCtrl1 = wx.dataview.DataViewListCtrl( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.dataview.DV_HORIZ_RULES|wx.dataview.DV_SINGLE|wx.dataview.DV_VERT_RULES )
        self.m_dataViewListCtrl1.SetMinSize( wx.Size( -1,149 ) )

        bSizer11.Add( self.m_dataViewListCtrl1, 1, wx.ALIGN_LEFT|wx.EXPAND, 5 )


        bSizer11.Add( ( 0, 0), 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 8 )


        self.SetSizer( bSizer11 )
        self.Layout()
        bSizer11.Fit( self )

        # Connect Events
        self.m_button_gen.Bind( wx.EVT_BUTTON, self.gen_new_mnemonic )
        self.m_textCtrl_mnemo.Bind( wx.EVT_TEXT, self.mnemo_changed )
        self.m_textCtrl_mnemo.Bind( wx.EVT_TEXT_ENTER, self.seek_assets )
        self.m_textpwd.Bind( wx.EVT_TEXT, self.mnemo_changed )
        self.m_textpwd.Bind( wx.EVT_TEXT_ENTER, self.seek_assets )
        self.m_typechoice.Bind( wx.EVT_CHOICE, self.mnemo_changed )
        self.m_account.Bind( wx.EVT_SPINCTRL, self.mnemo_changed )
        self.is_change.Bind( wx.EVT_CHECKBOX, self.mnemo_changed )
        self.m_index.Bind( wx.EVT_SPINCTRL, self.mnemo_changed )
        self.m_btnseek.Bind( wx.EVT_BUTTON, self.seek_assets )
        self.m_dataViewListCtrl1.Bind( wx.dataview.EVT_DATAVIEW_ITEM_CONTEXT_MENU, self.pop_menu, id = wx.ID_ANY )

    def __del__( self ):
        pass


    # Virtual event handlers, overide them in your derived class
    def gen_new_mnemonic( self, event ):
        event.Skip()

    def mnemo_changed( self, event ):
        event.Skip()

    def seek_assets( self, event ):
        event.Skip()








    def pop_menu( self, event ):
        event.Skip()


