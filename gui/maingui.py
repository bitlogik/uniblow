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

        self.m_scrolledWindow1 = wx.ScrolledWindow( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.HSCROLL|wx.VSCROLL )
        self.m_scrolledWindow1.SetScrollRate( 5, 5 )
        bSizer2 = wx.BoxSizer( wx.VERTICAL )

        self.m_bpButton1 = wx.BitmapButton( self.m_scrolledWindow1, wx.ID_ANY, wx.NullBitmap, wx.DefaultPosition, wx.Size( 32,32 ), wx.BU_AUTODRAW|0 )
        bSizer2.Add( self.m_bpButton1, 0, wx.ALL, 5 )

        self.m_bpButton2 = wx.BitmapButton( self.m_scrolledWindow1, wx.ID_ANY, wx.NullBitmap, wx.DefaultPosition, wx.DefaultSize, wx.BU_AUTODRAW|0 )
        self.m_bpButton2.SetBackgroundColour( wx.SystemSettings.GetColour( wx.SYS_COLOUR_INFOBK ) )

        bSizer2.Add( self.m_bpButton2, 0, wx.ALL, 5 )

        self.m_bpButton3 = wx.BitmapButton( self.m_scrolledWindow1, wx.ID_ANY, wx.NullBitmap, wx.DefaultPosition, wx.DefaultSize, wx.BU_AUTODRAW|0 )
        bSizer2.Add( self.m_bpButton3, 0, wx.ALL, 5 )

        self.m_bpButton4 = wx.BitmapButton( self.m_scrolledWindow1, wx.ID_ANY, wx.NullBitmap, wx.DefaultPosition, wx.DefaultSize, wx.BU_AUTODRAW|0 )
        bSizer2.Add( self.m_bpButton4, 0, wx.ALL, 5 )

        self.m_bpButton5 = wx.BitmapButton( self.m_scrolledWindow1, wx.ID_ANY, wx.NullBitmap, wx.DefaultPosition, wx.DefaultSize, wx.BU_AUTODRAW|0 )
        bSizer2.Add( self.m_bpButton5, 0, wx.ALL, 5 )

        self.m_bpButton6 = wx.BitmapButton( self.m_scrolledWindow1, wx.ID_ANY, wx.NullBitmap, wx.DefaultPosition, wx.DefaultSize, wx.BU_AUTODRAW|0 )
        bSizer2.Add( self.m_bpButton6, 0, wx.ALL, 5 )

        self.m_bpButton7 = wx.BitmapButton( self.m_scrolledWindow1, wx.ID_ANY, wx.NullBitmap, wx.DefaultPosition, wx.DefaultSize, wx.BU_AUTODRAW|0 )
        bSizer2.Add( self.m_bpButton7, 0, wx.ALL, 5 )

        self.m_bpButton8 = wx.BitmapButton( self.m_scrolledWindow1, wx.ID_ANY, wx.NullBitmap, wx.DefaultPosition, wx.DefaultSize, wx.BU_AUTODRAW|0 )
        bSizer2.Add( self.m_bpButton8, 0, wx.ALL, 5 )

        self.m_bpButton9 = wx.BitmapButton( self.m_scrolledWindow1, wx.ID_ANY, wx.NullBitmap, wx.DefaultPosition, wx.DefaultSize, wx.BU_AUTODRAW|0 )
        bSizer2.Add( self.m_bpButton9, 0, wx.ALL, 5 )

        self.m_bpButton10 = wx.BitmapButton( self.m_scrolledWindow1, wx.ID_ANY, wx.NullBitmap, wx.DefaultPosition, wx.DefaultSize, wx.BU_AUTODRAW|0 )
        bSizer2.Add( self.m_bpButton10, 0, wx.ALL, 5 )

        self.m_bpButton11 = wx.BitmapButton( self.m_scrolledWindow1, wx.ID_ANY, wx.NullBitmap, wx.DefaultPosition, wx.DefaultSize, wx.BU_AUTODRAW|0 )
        bSizer2.Add( self.m_bpButton11, 0, wx.ALL, 5 )


        self.m_scrolledWindow1.SetSizer( bSizer2 )
        self.m_scrolledWindow1.Layout()
        bSizer2.Fit( self.m_scrolledWindow1 )
        bSizer1.Add( self.m_scrolledWindow1, 0, wx.ALL, 5 )

        self.m_panel1 = wx.Panel( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
        bSizer6 = wx.BoxSizer( wx.VERTICAL )

        bSizer4 = wx.BoxSizer( wx.HORIZONTAL )

        self.txt_bal = wx.StaticText( self.m_panel1, wx.ID_ANY, u"MyLabel", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.txt_bal.Wrap( -1 )

        self.txt_bal.SetFont( wx.Font( 14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, wx.EmptyString ) )

        bSizer4.Add( self.txt_bal, 1, wx.ALIGN_CENTER_VERTICAL|wx.LEFT, 16 )

        bSizer5 = wx.BoxSizer( wx.VERTICAL )

        self.m_staticText2 = wx.StaticText( self.m_panel1, wx.ID_ANY, u"Network", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText2.Wrap( -1 )

        bSizer5.Add( self.m_staticText2, 0, wx.ALL|wx.ALIGN_CENTER_HORIZONTAL, 5 )

        m_choice1Choices = []
        self.m_choice1 = wx.Choice( self.m_panel1, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, m_choice1Choices, 0 )
        self.m_choice1.SetSelection( 0 )
        bSizer5.Add( self.m_choice1, 0, wx.ALL|wx.ALIGN_CENTER_HORIZONTAL, 5 )


        bSizer4.Add( bSizer5, 0, wx.RIGHT, 24 )


        bSizer6.Add( bSizer4, 1, wx.EXPAND, 5 )

        bSizer9 = wx.BoxSizer( wx.HORIZONTAL )

        self.m_button21 = wx.Button( self.m_panel1, wx.ID_ANY, u"MyButton", wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer9.Add( self.m_button21, 0, wx.ALL, 5 )

        self.m_button22 = wx.Button( self.m_panel1, wx.ID_ANY, u"MyButton", wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer9.Add( self.m_button22, 0, wx.ALL, 5 )

        self.m_button23 = wx.Button( self.m_panel1, wx.ID_ANY, u"MyButton", wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer9.Add( self.m_button23, 0, wx.ALL, 5 )


        bSizer6.Add( bSizer9, 1, wx.EXPAND, 5 )

        self.m_staticText4 = wx.StaticText( self.m_panel1, wx.ID_ANY, u"MyLabel", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText4.Wrap( -1 )

        self.m_staticText4.SetFont( wx.Font( 12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, wx.EmptyString ) )

        bSizer6.Add( self.m_staticText4, 0, wx.ALL, 5 )

        bSizer12 = wx.BoxSizer( wx.HORIZONTAL )

        self.m_bitmap1 = wx.StaticBitmap( self.m_panel1, wx.ID_ANY, wx.NullBitmap, wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_bitmap1.SetMinSize( wx.Size( 120,120 ) )

        bSizer12.Add( self.m_bitmap1, 0, wx.ALL, 5 )

        bSizer13 = wx.BoxSizer( wx.VERTICAL )

        bSizer14 = wx.BoxSizer( wx.HORIZONTAL )

        self.m_bpButton20 = wx.BitmapButton( self.m_panel1, wx.ID_ANY, wx.NullBitmap, wx.DefaultPosition, wx.DefaultSize, wx.BU_AUTODRAW|0 )
        bSizer14.Add( self.m_bpButton20, 0, wx.RIGHT, 32 )

        bSizer15 = wx.BoxSizer( wx.VERTICAL )

        self.m_staticText6 = wx.StaticText( self.m_panel1, wx.ID_ANY, u"type", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText6.Wrap( -1 )

        bSizer15.Add( self.m_staticText6, 0, wx.ALL|wx.ALIGN_CENTER_HORIZONTAL, 5 )

        m_choice3Choices = []
        self.m_choice3 = wx.Choice( self.m_panel1, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, m_choice3Choices, 0 )
        self.m_choice3.SetSelection( 0 )
        bSizer15.Add( self.m_choice3, 0, wx.ALL|wx.ALIGN_CENTER_HORIZONTAL, 5 )


        bSizer14.Add( bSizer15, 1, wx.EXPAND|wx.LEFT, 32 )


        bSizer13.Add( bSizer14, 0, wx.ALIGN_CENTER_HORIZONTAL, 5 )

        self.m_bpButton19 = wx.BitmapButton( self.m_panel1, wx.ID_ANY, wx.NullBitmap, wx.DefaultPosition, wx.DefaultSize, wx.BU_AUTODRAW|0 )
        bSizer13.Add( self.m_bpButton19, 0, wx.BOTTOM, 16 )


        bSizer12.Add( bSizer13, 1, wx.EXPAND, 5 )


        bSizer6.Add( bSizer12, 1, wx.EXPAND, 5 )


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

        self.d_btn01 = wx.BitmapButton( self, wx.ID_ANY, wx.NullBitmap, wx.DefaultPosition, wx.DefaultSize, wx.BU_AUTODRAW|0 )
        fgSizer1.Add( self.d_btn01, 0, wx.ALL, 5 )

        self.d_btn02 = wx.BitmapButton( self, wx.ID_ANY, wx.NullBitmap, wx.DefaultPosition, wx.DefaultSize, wx.BU_AUTODRAW|0 )
        fgSizer1.Add( self.d_btn02, 0, wx.ALL, 5 )

        self.d_btn03 = wx.BitmapButton( self, wx.ID_ANY, wx.NullBitmap, wx.DefaultPosition, wx.DefaultSize, wx.BU_AUTODRAW|0 )
        fgSizer1.Add( self.d_btn03, 0, wx.ALL, 5 )

        self.d_btn04 = wx.BitmapButton( self, wx.ID_ANY, wx.NullBitmap, wx.DefaultPosition, wx.DefaultSize, wx.BU_AUTODRAW|0 )
        fgSizer1.Add( self.d_btn04, 0, wx.ALL, 5 )

        self.d_btn05 = wx.BitmapButton( self, wx.ID_ANY, wx.NullBitmap, wx.DefaultPosition, wx.DefaultSize, wx.BU_AUTODRAW|0 )
        fgSizer1.Add( self.d_btn05, 0, wx.ALL, 5 )


        bSizer3.Add( fgSizer1, 0, wx.ALIGN_CENTER_HORIZONTAL, 5 )


        self.SetSizer( bSizer3 )
        self.Layout()
        bSizer3.Fit( self )

    def __del__( self ):
        pass


