# -*- coding: utf-8 -*-

###########################################################################
## Python code generated with wxFormBuilder (version Oct 26 2018)
## http://www.wxformbuilder.org/
##
## PLEASE DO *NOT* EDIT THIS FILE!
###########################################################################

import wx
import wx.xrc
import wx.grid

###########################################################################
## Class MainFrame
###########################################################################

class MainFrame ( wx.Frame ):

	def __init__( self, parent ):
		wx.Frame.__init__ ( self, parent, id = wx.ID_ANY, title = wx.EmptyString, pos = wx.DefaultPosition, size = wx.Size( 1000,700 ), style = wx.DEFAULT_FRAME_STYLE|wx.TAB_TRAVERSAL )

		self.SetSizeHints( wx.DefaultSize, wx.DefaultSize )

		self.m_toolBarTop = self.CreateToolBar( wx.TB_HORIZONTAL, wx.ID_ANY )
		self.mLoadNewIssues = wx.Button( self.m_toolBarTop, wx.ID_ANY, u"Load New Issue(s)", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_toolBarTop.AddControl( self.mLoadNewIssues )
		self.bLoadNewLSTFile = wx.Button( self.m_toolBarTop, wx.ID_ANY, u"Load New LST File", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_toolBarTop.AddControl( self.bLoadNewLSTFile )
		self.bSaveLSTFile = wx.Button( self.m_toolBarTop, wx.ID_ANY, u"Save LST File", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_toolBarTop.AddControl( self.bSaveLSTFile )
		self.m_toolBarTop.Realize()

		bSizerMain = wx.BoxSizer( wx.VERTICAL )

		bSizerTopMatter = wx.BoxSizer( wx.HORIZONTAL )

		self.m_staticText1 = wx.StaticText( self, wx.ID_ANY, u"Top matter:", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText1.Wrap( -1 )

		bSizerTopMatter.Add( self.m_staticText1, 0, wx.ALL, 5 )

		self.tTopMatter = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size( 800,-1 ), 0 )
		bSizerTopMatter.Add( self.tTopMatter, 0, wx.ALL|wx.EXPAND, 5 )


		bSizerMain.Add( bSizerTopMatter, 1, wx.EXPAND, 5 )

		fgSizerComments = wx.FlexGridSizer( 1, 2, 0, 0 )
		fgSizerComments.AddGrowableCol( 1 )
		fgSizerComments.AddGrowableRow( 0 )
		fgSizerComments.SetFlexibleDirection( wx.BOTH )
		fgSizerComments.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )

		self.m_staticText2 = wx.StaticText( self, wx.ID_ANY, u"<P>Comments</P>:", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText2.Wrap( -1 )

		fgSizerComments.Add( self.m_staticText2, 1, wx.ALL, 5 )

		self.tPText = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.TE_MULTILINE )
		self.tPText.SetMinSize( wx.Size( -1,100 ) )

		fgSizerComments.Add( self.tPText, 1, wx.ALL|wx.EXPAND, 5 )


		bSizerMain.Add( fgSizerComments, 1, wx.ALL|wx.EXPAND, 5 )

		theIssueGrid = wx.BoxSizer( wx.VERTICAL )

		self.gRowGrid = wx.grid.Grid( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, 0 )

		# Grid
		self.gRowGrid.CreateGrid( 100, 15 )
		self.gRowGrid.EnableEditing( True )
		self.gRowGrid.EnableGridLines( True )
		self.gRowGrid.EnableDragGridSize( False )
		self.gRowGrid.SetMargins( 0, 0 )

		# Columns
		self.gRowGrid.AutoSizeColumns()
		self.gRowGrid.EnableDragColMove( True )
		self.gRowGrid.EnableDragColSize( True )
		self.gRowGrid.SetColLabelSize( 30 )
		self.gRowGrid.SetColLabelAlignment( wx.ALIGN_CENTER, wx.ALIGN_CENTER )

		# Rows
		self.gRowGrid.AutoSizeRows()
		self.gRowGrid.EnableDragRowSize( True )
		self.gRowGrid.SetRowLabelSize( 80 )
		self.gRowGrid.SetRowLabelAlignment( wx.ALIGN_CENTER, wx.ALIGN_CENTER )

		# Label Appearance

		# Cell Defaults
		self.gRowGrid.SetDefaultCellAlignment( wx.ALIGN_LEFT, wx.ALIGN_TOP )
		self.m_menu1 = wx.Menu()
		self.m_menuItemCopy = wx.MenuItem( self.m_menu1, wx.ID_ANY, u"Copy", wx.EmptyString, wx.ITEM_NORMAL )
		self.m_menu1.Append( self.m_menuItemCopy )

		self.m_menuItemPaste = wx.MenuItem( self.m_menu1, wx.ID_ANY, u"Paste", wx.EmptyString, wx.ITEM_NORMAL )
		self.m_menu1.Append( self.m_menuItemPaste )

		self.gRowGrid.Bind( wx.EVT_RIGHT_DOWN, self.gRowGridOnContextMenu )

		theIssueGrid.Add( self.gRowGrid, 0, wx.ALL|wx.EXPAND, 5 )


		bSizerMain.Add( theIssueGrid, 1, wx.EXPAND, 5 )


		self.SetSizer( bSizerMain )
		self.Layout()
		self.m_CellPopupMenu = wx.Menu()
		self.m_menuItemPopupCopy = wx.MenuItem( self.m_CellPopupMenu, wx.ID_ANY, u"Copy", wx.EmptyString, wx.ITEM_NORMAL )
		self.m_CellPopupMenu.Append( self.m_menuItemPopupCopy )

		self.m_menuItemPopupPaste = wx.MenuItem( self.m_CellPopupMenu, wx.ID_ANY, u"Paste", wx.EmptyString, wx.ITEM_NORMAL )
		self.m_CellPopupMenu.Append( self.m_menuItemPopupPaste )

		self.m_menuItemPopupDelCol = wx.MenuItem( self.m_CellPopupMenu, wx.ID_ANY, u"Delete Column", wx.EmptyString, wx.ITEM_NORMAL )
		self.m_CellPopupMenu.Append( self.m_menuItemPopupDelCol )

		self.m_menuItemPopupInsertColLeft = wx.MenuItem( self.m_CellPopupMenu, wx.ID_ANY, u"Insert Column to Left", wx.EmptyString, wx.ITEM_NORMAL )
		self.m_CellPopupMenu.Append( self.m_menuItemPopupInsertColLeft )

		self.m_menuItemPopupExtractScanner = wx.MenuItem( self.m_CellPopupMenu, wx.ID_ANY, u"Extract Scanner", wx.EmptyString, wx.ITEM_NORMAL )
		self.m_CellPopupMenu.Append( self.m_menuItemPopupExtractScanner )

		self.m_menuItemPopupMoveColRight = wx.MenuItem( self.m_CellPopupMenu, wx.ID_ANY, u"Move Column Right", wx.EmptyString, wx.ITEM_NORMAL )
		self.m_CellPopupMenu.Append( self.m_menuItemPopupMoveColRight )

		self.m_menuItemPopupMoveColLeft = wx.MenuItem( self.m_CellPopupMenu, wx.ID_ANY, u"Move Column Left", wx.EmptyString, wx.ITEM_NORMAL )
		self.m_CellPopupMenu.Append( self.m_menuItemPopupMoveColLeft )

		self.m_menuItemPopupMoveSelRight = wx.MenuItem( self.m_CellPopupMenu, wx.ID_ANY, u"Move Selection Right", wx.EmptyString, wx.ITEM_NORMAL )
		self.m_CellPopupMenu.Append( self.m_menuItemPopupMoveSelRight )

		self.m_menuItemPopupMoveSelLeft = wx.MenuItem( self.m_CellPopupMenu, wx.ID_ANY, u"Move Selection Left", wx.EmptyString, wx.ITEM_NORMAL )
		self.m_CellPopupMenu.Append( self.m_menuItemPopupMoveSelLeft )

		self.Bind( wx.EVT_RIGHT_DOWN, self.MainFrameOnContextMenu )


		self.Centre( wx.BOTH )

		# Connect Events
		self.mLoadNewIssues.Bind( wx.EVT_BUTTON, self.OnLoadNewIssues )
		self.bLoadNewLSTFile.Bind( wx.EVT_BUTTON, self.OnLoadNewLSTFile )
		self.bSaveLSTFile.Bind( wx.EVT_BUTTON, self.OnSaveLSTFile )
		self.tTopMatter.Bind( wx.EVT_TEXT, self.OnTextTopMatter )
		self.tPText.Bind( wx.EVT_TEXT, self.OnTextComments )
		self.gRowGrid.Bind( wx.grid.EVT_GRID_CELL_CHANGED, self.OnGridCellChange )
		self.gRowGrid.Bind( wx.grid.EVT_GRID_CELL_RIGHT_CLICK, self.OnGridCellRightClick )
		self.gRowGrid.Bind( wx.EVT_KEY_DOWN, self.OnKeyDown )
		self.gRowGrid.Bind( wx.EVT_KEY_UP, self.OnKeyUp )
		self.Bind( wx.EVT_MENU, self.OnPopupCopy, id = self.m_menuItemCopy.GetId() )
		self.Bind( wx.EVT_MENU, self.OnPopupPaste, id = self.m_menuItemPaste.GetId() )
		self.Bind( wx.EVT_MENU, self.OnPopupCopy, id = self.m_menuItemPopupCopy.GetId() )
		self.Bind( wx.EVT_MENU, self.OnPopupPaste, id = self.m_menuItemPopupPaste.GetId() )
		self.Bind( wx.EVT_MENU, self.OnPopupDelCol, id = self.m_menuItemPopupDelCol.GetId() )
		self.Bind( wx.EVT_MENU, self.OnPopupInsertColLeft, id = self.m_menuItemPopupInsertColLeft.GetId() )
		self.Bind( wx.EVT_MENU, self.OnPopupExtractScanner, id = self.m_menuItemPopupExtractScanner.GetId() )
		self.Bind( wx.EVT_MENU, self.OnPopupMoveColRight, id = self.m_menuItemPopupMoveColRight.GetId() )
		self.Bind( wx.EVT_MENU, self.OnPopupMoveColLeft, id = self.m_menuItemPopupMoveColLeft.GetId() )
		self.Bind( wx.EVT_MENU, self.OnPopupMoveSelRight, id = self.m_menuItemPopupMoveSelRight.GetId() )
		self.Bind( wx.EVT_MENU, self.OnPopupMoveSelLeft, id = self.m_menuItemPopupMoveSelLeft.GetId() )

	def __del__( self ):
		pass


	# Virtual event handlers, overide them in your derived class
	def OnLoadNewIssues( self, event ):
		event.Skip()

	def OnLoadNewLSTFile( self, event ):
		event.Skip()

	def OnSaveLSTFile( self, event ):
		event.Skip()

	def OnTextTopMatter( self, event ):
		event.Skip()

	def OnTextComments( self, event ):
		event.Skip()

	def OnGridCellChange( self, event ):
		event.Skip()

	def OnGridCellRightClick( self, event ):
		event.Skip()

	def OnKeyDown( self, event ):
		event.Skip()

	def OnKeyUp( self, event ):
		event.Skip()

	def OnPopupCopy( self, event ):
		event.Skip()

	def OnPopupPaste( self, event ):
		event.Skip()



	def OnPopupDelCol( self, event ):
		event.Skip()

	def OnPopupInsertColLeft( self, event ):
		event.Skip()

	def OnPopupExtractScanner( self, event ):
		event.Skip()

	def OnPopupMoveColRight( self, event ):
		event.Skip()

	def OnPopupMoveColLeft( self, event ):
		event.Skip()

	def OnPopupMoveSelRight( self, event ):
		event.Skip()

	def OnPopupMoveSelLeft( self, event ):
		event.Skip()

	def gRowGridOnContextMenu( self, event ):
		self.gRowGrid.PopupMenu( self.m_menu1, event.GetPosition() )

	def MainFrameOnContextMenu( self, event ):
		self.PopupMenu( self.m_CellPopupMenu, event.GetPosition() )


