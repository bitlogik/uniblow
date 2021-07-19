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
        wx.Frame.__init__ ( self, parent, id = wx.ID_ANY, title = u"  [ Uniblow ]    Seed Watcher", pos = wx.DefaultPosition, size = wx.Size( 652,657 ), style = wx.DEFAULT_FRAME_STYLE|wx.TAB_TRAVERSAL )

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

    def __init__( self, parent, id = wx.ID_ANY, pos = wx.DefaultPosition, size = wx.Size( 560,602 ), style = wx.TAB_TRAVERSAL, name = wx.EmptyString ):
        wx.Panel.__init__ ( self, parent, id = id, pos = pos, size = size, style = style, name = name )

        bSizer11 = wx.BoxSizer( wx.VERTICAL )


        bSizer11.Add( ( 0, 0), 0, wx.BOTTOM, 15 )

        bSizer3 = wx.BoxSizer( wx.HORIZONTAL )

        self.m_staticText12 = wx.StaticText( self, wx.ID_ANY, u"wallet mnemonic", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText12.Wrap( -1 )

        self.m_staticText12.SetFont( wx.Font( 12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, wx.EmptyString ) )

        bSizer3.Add( self.m_staticText12, 1, wx.ALIGN_CENTER|wx.RIGHT|wx.TOP, 25 )

        self.m_staticText5 = wx.StaticText( self, wx.ID_ANY, u"  Words in list", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText5.Wrap( -1 )

        bSizer3.Add( self.m_staticText5, 0, wx.ALIGN_BOTTOM|wx.ALL, 5 )

        self.m_bitmap_wl = wx.StaticBitmap( self, wx.ID_ANY, wx.NullBitmap, wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer3.Add( self.m_bitmap_wl, 0, wx.ALIGN_BOTTOM|wx.ALL, 5 )

        self.m_staticText6 = wx.StaticText( self, wx.ID_ANY, u"  Checksum", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText6.Wrap( -1 )

        bSizer3.Add( self.m_staticText6, 0, wx.ALIGN_BOTTOM|wx.ALL, 5 )

        self.m_bitmap_cs = wx.StaticBitmap( self, wx.ID_ANY, wx.NullBitmap, wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer3.Add( self.m_bitmap_cs, 0, wx.ALIGN_BOTTOM|wx.ALL, 5 )


        bSizer11.Add( bSizer3, 0, wx.ALIGN_CENTER_HORIZONTAL, 5 )

        self.m_textCtrl_mnemo = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size( -1,80 ), wx.TE_MULTILINE )
        self.m_textCtrl_mnemo.SetFont( wx.Font( 11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, wx.EmptyString ) )

        bSizer11.Add( self.m_textCtrl_mnemo, 0, wx.ALL|wx.EXPAND, 5 )

        bSizer31 = wx.BoxSizer( wx.HORIZONTAL )

        bSizer31.SetMinSize( wx.Size( -1,40 ) )
        self.m_button_gen = wx.Button( self, wx.ID_ANY, u"Generate New", wx.DefaultPosition, wx.Size( 160,45 ), 0 )
        self.m_button_gen.SetFont( wx.Font( 11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, wx.EmptyString ) )

        bSizer31.Add( self.m_button_gen, 0, wx.ALL, 10 )

        m_choice_nwordsChoices = []
        self.m_choice_nwords = wx.Choice( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, m_choice_nwordsChoices, 0 )
        self.m_choice_nwords.SetSelection( 0 )
        self.m_choice_nwords.SetFont( wx.Font( 11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, wx.EmptyString ) )

        bSizer31.Add( self.m_choice_nwords, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )


        bSizer11.Add( bSizer31, 0, wx.ALIGN_CENTER_HORIZONTAL, 5 )


        bSizer11.Add( ( 0, 0), 0, wx.ALIGN_CENTER_HORIZONTAL|wx.TOP, 25 )

        self.m_staticText16 = wx.StaticText( self, wx.ID_ANY, u"wallet assets", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText16.Wrap( -1 )

        bSizer11.Add( self.m_staticText16, 0, wx.ALL|wx.ALIGN_CENTER_HORIZONTAL, 5 )

        self.m_dataViewListCtrl1 = wx.dataview.DataViewListCtrl( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.dataview.DV_HORIZ_RULES|wx.dataview.DV_SINGLE|wx.dataview.DV_VERT_RULES )
        self.m_dataViewListCtrl1.SetMinSize( wx.Size( -1,149 ) )

        bSizer11.Add( self.m_dataViewListCtrl1, 1, wx.ALL|wx.EXPAND, 5 )


        bSizer11.Add( ( 0, 0), 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 10 )


        self.SetSizer( bSizer11 )
        self.Layout()

        # Connect Events
        self.m_textCtrl_mnemo.Bind( wx.EVT_TEXT, self.mnemo_changed )
        self.m_button_gen.Bind( wx.EVT_BUTTON, self.gen_new_mnemonic )

    def __del__( self ):
        pass


    # Virtual event handlers, overide them in your derived class
    def mnemo_changed( self, event ):
        event.Skip()

    def gen_new_mnemonic( self, event ):
        event.Skip()


