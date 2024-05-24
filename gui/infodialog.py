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
## Class InfoDialog
###########################################################################

class InfoDialog ( wx.Dialog ):

	def __init__( self, parent ):
		wx.Dialog.__init__ ( self, parent, id = wx.ID_ANY, title = u"Info", pos = wx.DefaultPosition, size = wx.Size( 500,250 ), style = wx.DEFAULT_DIALOG_STYLE|wx.STAY_ON_TOP )

		self.SetSizeHints( wx.Size( 500,250 ), wx.DefaultSize )


		self.Centre( wx.BOTH )

	def __del__( self ):
		pass


###########################################################################
## Class InfoPanel
###########################################################################

class InfoPanel ( wx.Panel ):

	def __init__( self, parent, id = wx.ID_ANY, pos = wx.DefaultPosition, size = wx.Size( -1,-1 ), style = wx.TAB_TRAVERSAL, name = wx.EmptyString ):
		wx.Panel.__init__ ( self, parent, id = id, pos = pos, size = size, style = style, name = name )

		self.SetBackgroundColour( wx.SystemSettings.GetColour( wx.SYS_COLOUR_WINDOW ) )

		bSizer1 = wx.BoxSizer( wx.VERTICAL )

		self.m_textCtrl = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.TE_MULTILINE|wx.TE_READONLY|wx.TE_WORDWRAP|wx.BORDER_NONE )
		self.m_textCtrl.SetFont( wx.Font( 10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, wx.EmptyString ) )
		self.m_textCtrl.SetForegroundColour( wx.SystemSettings.GetColour( wx.SYS_COLOUR_WINDOWTEXT ) )

		bSizer1.Add( self.m_textCtrl, 1, wx.ALL|wx.EXPAND, 24 )

		bSizer2 = wx.BoxSizer( wx.HORIZONTAL )

		self.m_button_ok = wx.Button( self, wx.ID_ANY, u"OK", wx.DefaultPosition, wx.DefaultSize, 0 )

		self.m_button_ok.SetBitmap( wx.NullBitmap )
		self.m_button_ok.SetFont( wx.Font( wx.NORMAL_FONT.GetPointSize(), wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, False, wx.EmptyString ) )

		bSizer2.Add( self.m_button_ok, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )


		bSizer2.Add( ( 20, 0), 1, wx.EXPAND, 5 )

		self.m_button_cpy = wx.Button( self, wx.ID_ANY, u"Copy text", wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer2.Add( self.m_button_cpy, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )


		bSizer1.Add( bSizer2, 0, wx.ALIGN_CENTER_HORIZONTAL, 5 )


		bSizer1.Add( ( 0, 20), 0, wx.ALIGN_CENTER_HORIZONTAL, 5 )


		self.SetSizer( bSizer1 )
		self.Layout()
		bSizer1.Fit( self )

	def __del__( self ):
		pass


