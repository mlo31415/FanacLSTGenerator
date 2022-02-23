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
## Class LogDialog
###########################################################################

class LogDialog ( wx.Dialog ):

	def __init__( self, parent ):
		wx.Dialog.__init__ ( self, parent, id = wx.ID_ANY, title = u"Log", pos = wx.DefaultPosition, size = wx.Size( 742,405 ), style = wx.DEFAULT_DIALOG_STYLE )

		self.SetSizeHints( wx.DefaultSize, wx.DefaultSize )

		gSizer1 = wx.GridSizer( 1, 1, 0, 0 )

		self.lLogText = wx.StaticText( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
		self.lLogText.Wrap( -1 )

		gSizer1.Add( self.lLogText, 0, wx.ALL|wx.EXPAND, 5 )


		self.SetSizer( gSizer1 )
		self.Layout()

		self.Centre( wx.BOTH )

	def __del__( self ):
		pass


