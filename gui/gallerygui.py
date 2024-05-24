# -*- coding: utf-8 -*-

###########################################################################
## Python code generated with wxFormBuilder (version 4.0.0-0-g0efcecf)
## http://www.wxformbuilder.org/
##
## PLEASE DO *NOT* EDIT THIS FILE!
###########################################################################

import wx
import wx.xrc

###########################################################################
## Class GalleryFrame
###########################################################################

class GalleryFrame ( wx.Frame ):

    def __init__( self, parent ):
        wx.Frame.__init__ ( self, parent, id = wx.ID_ANY, title = u"Uniblow NFT Gallery", pos = wx.DefaultPosition, size = wx.Size( 500,300 ), style = wx.DEFAULT_FRAME_STYLE|wx.TAB_TRAVERSAL )

        self.SetSizeHints( wx.DefaultSize, wx.DefaultSize )


        self.Centre( wx.BOTH )

    def __del__( self ):
        pass


###########################################################################
## Class GalleryPanel
###########################################################################

class GalleryPanel ( wx.Panel ):

    def __init__( self, parent, id = wx.ID_ANY, pos = wx.DefaultPosition, size = wx.Size( 500,300 ), style = wx.TAB_TRAVERSAL, name = wx.EmptyString ):
        wx.Panel.__init__ ( self, parent, id = id, pos = pos, size = size, style = style, name = name )

        self.SetBackgroundColour( wx.Colour( 248, 250, 252 ) )

        bSizer1 = wx.BoxSizer( wx.VERTICAL )

        bSizer2 = wx.BoxSizer( wx.HORIZONTAL )


        bSizer2.Add( ( 0, 0), 0, wx.LEFT, 24 )

        self.collection_name = wx.StaticText( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
        self.collection_name.Wrap( -1 )

        self.collection_name.SetFont( wx.Font( 14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, False, wx.EmptyString ) )
        self.collection_name.SetForegroundColour( wx.Colour( 0, 0, 0 ) )

        bSizer2.Add( self.collection_name, 0, wx.ALIGN_BOTTOM|wx.TOP, 12 )


        bSizer2.Add( ( 0, 0), 1, wx.EXPAND, 8 )

        self.balance_text = wx.StaticText( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
        self.balance_text.Wrap( -1 )

        self.balance_text.SetFont( wx.Font( 11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, wx.EmptyString ) )
        self.balance_text.SetForegroundColour( wx.Colour( 0, 0, 0 ) )

        bSizer2.Add( self.balance_text, 0, wx.ALIGN_BOTTOM|wx.TOP|wx.RIGHT|wx.LEFT, 5 )


        bSizer2.Add( ( 0, 0), 0, wx.LEFT, 32 )


        bSizer1.Add( bSizer2, 0, wx.ALL|wx.EXPAND, 24 )

        self.wait_text = wx.StaticText( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
        self.wait_text.Wrap( -1 )

        self.wait_text.SetFont( wx.Font( 12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, wx.EmptyString ) )
        self.wait_text.SetForegroundColour( wx.Colour( 0, 0, 0 ) )

        bSizer1.Add( self.wait_text, 0, wx.ALIGN_CENTER_HORIZONTAL, 5 )

        self.scrwin = wx.ScrolledWindow( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.HSCROLL|wx.VSCROLL )
        self.scrwin.SetScrollRate( 5, 5 )
        bSizer1.Add( self.scrwin, 1, wx.EXPAND |wx.ALL, 5 )


        self.SetSizer( bSizer1 )
        self.Layout()

    def __del__( self ):
        pass


