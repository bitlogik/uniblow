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
## Class InfoDialog
###########################################################################

class InfoDialog ( wx.Dialog ):

	def __init__( self, parent ):
		wx.Dialog.__init__ ( self, parent, id = wx.ID_ANY, title = u"Info", pos = wx.DefaultPosition, size = wx.Size( 500,250 ), style = wx.DEFAULT_DIALOG_STYLE|wx.STAY_ON_TOP )

		self.SetSizeHints( wx.Size( 500,250 ), wx.DefaultSize )

		bSizer1 = wx.BoxSizer( wx.VERTICAL )

		self.m_textCtrl = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.TE_MULTILINE|wx.TE_READONLY|wx.TE_WORDWRAP|wx.BORDER_NONE )
		self.m_textCtrl.SetBackgroundColour( wx.SystemSettings.GetColour( wx.SYS_COLOUR_WINDOW ) )

		bSizer1.Add( self.m_textCtrl, 1, wx.ALL|wx.EXPAND, 24 )

		bSizer2 = wx.BoxSizer( wx.HORIZONTAL )

		self.m_button_cpy = wx.Button( self, wx.ID_ANY, u"Copy Text", wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer2.Add( self.m_button_cpy, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )


		bSizer2.Add( ( 20, 0), 1, wx.EXPAND, 5 )

		self.m_button_ok = wx.Button( self, wx.ID_ANY, u"OK", wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer2.Add( self.m_button_ok, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )


		bSizer1.Add( bSizer2, 0, wx.ALIGN_CENTER_HORIZONTAL, 5 )


		bSizer1.Add( ( 0, 20), 0, wx.ALIGN_CENTER_HORIZONTAL, 5 )


		self.SetSizer( bSizer1 )
		self.Layout()

		self.Centre( wx.BOTH )

		# Connect Events
		self.m_button_cpy.Bind( wx.EVT_BUTTON, self.copy_text_dialog )
		self.m_button_ok.Bind( wx.EVT_BUTTON, self.close_info )

	def __del__( self ):
		pass


	# Virtual event handlers, overide them in your derived class
	def copy_text_dialog( self, event ):
		event.Skip()

	def close_info( self, event ):
		event.Skip()


