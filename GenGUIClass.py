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

		self.wxGrid = wx.grid.Grid(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, 0)

		# Grid
		self.wxGrid.CreateGrid(100, 15)
		self.wxGrid.EnableEditing(True)
		self.wxGrid.EnableGridLines(True)
		self.wxGrid.EnableDragGridSize(False)
		self.wxGrid.SetMargins(0, 0)

		# Columns
		self.wxGrid.AutoSizeColumns()
		self.wxGrid.EnableDragColMove(True)
		self.wxGrid.EnableDragColSize(False)
		self.wxGrid.SetColLabelSize(30)
		self.wxGrid.SetColLabelAlignment(wx.ALIGN_CENTER, wx.ALIGN_CENTER)

		# Rows
		self.wxGrid.AutoSizeRows()
		self.wxGrid.EnableDragRowSize(True)
		self.wxGrid.SetRowLabelSize(80)
		self.wxGrid.SetRowLabelAlignment(wx.ALIGN_CENTER, wx.ALIGN_CENTER)

		# Label Appearance

		# Cell Defaults
		self.wxGrid.SetDefaultCellAlignment(wx.ALIGN_LEFT, wx.ALIGN_TOP)
		theIssueGrid.Add(self.wxGrid, 0, wx.ALL|wx.EXPAND, 5)


		bSizerMain.Add( theIssueGrid, 1, wx.EXPAND, 5 )


		self.SetSizer( bSizerMain )
		self.Layout()
		self.m_GridPopup = wx.Menu()
		self.m_menuItemPopupCopy = wx.MenuItem( self.m_GridPopup, wx.ID_ANY, u"Copy", wx.EmptyString, wx.ITEM_NORMAL )
		self.m_GridPopup.Append( self.m_menuItemPopupCopy )

		self.m_menuItemPopupPaste = wx.MenuItem( self.m_GridPopup, wx.ID_ANY, u"Paste", wx.EmptyString, wx.ITEM_NORMAL )
		self.m_GridPopup.Append( self.m_menuItemPopupPaste )

		self.m_menuItemPopupClearSelection = wx.MenuItem( self.m_GridPopup, wx.ID_ANY, u"Clear Selection", wx.EmptyString, wx.ITEM_NORMAL )
		self.m_GridPopup.Append( self.m_menuItemPopupClearSelection )

		self.m_menuItemPopupDelCol = wx.MenuItem( self.m_GridPopup, wx.ID_ANY, u"Delete Column(s)", wx.EmptyString, wx.ITEM_NORMAL )
		self.m_GridPopup.Append( self.m_menuItemPopupDelCol )

		self.m_menuItemPopupDelRow = wx.MenuItem( self.m_GridPopup, wx.ID_ANY, u"Delete Row(s)", wx.EmptyString, wx.ITEM_NORMAL )
		self.m_GridPopup.Append( self.m_menuItemPopupDelRow )

		self.m_menuItemPopupRenameCol = wx.MenuItem( self.m_GridPopup, wx.ID_ANY, u"Rename Column", wx.EmptyString, wx.ITEM_NORMAL )
		self.m_GridPopup.Append( self.m_menuItemPopupRenameCol )

		self.m_menuItemPopupInsertColLeft = wx.MenuItem( self.m_GridPopup, wx.ID_ANY, u"Insert Column to Left", wx.EmptyString, wx.ITEM_NORMAL )
		self.m_GridPopup.Append( self.m_menuItemPopupInsertColLeft )

		self.m_menuItemPopupInsertColRight = wx.MenuItem( self.m_GridPopup, wx.ID_ANY, u"Insert Column to Right", wx.EmptyString, wx.ITEM_NORMAL )
		self.m_GridPopup.Append( self.m_menuItemPopupInsertColRight )

		self.m_menuItemPopupExtractScanner = wx.MenuItem( self.m_GridPopup, wx.ID_ANY, u"Extract Scanner", wx.EmptyString, wx.ITEM_NORMAL )
		self.m_GridPopup.Append( self.m_menuItemPopupExtractScanner )

		self.Bind( wx.EVT_RIGHT_DOWN, self.MainFrameOnContextMenu )


		self.Centre( wx.BOTH )

		# Connect Events
		self.mLoadNewIssues.Bind( wx.EVT_BUTTON, self.OnLoadNewIssues )
		self.bLoadNewLSTFile.Bind( wx.EVT_BUTTON, self.OnLoadNewLSTFile )
		self.bSaveLSTFile.Bind( wx.EVT_BUTTON, self.OnSaveLSTFile )
		self.tTopMatter.Bind( wx.EVT_TEXT, self.OnTextTopMatter )
		self.tPText.Bind( wx.EVT_TEXT, self.OnTextComments )
		self.wxGrid.Bind(wx.grid.EVT_GRID_CELL_CHANGED, self.OnGridCellChanged)
		self.wxGrid.Bind(wx.grid.EVT_GRID_CELL_LEFT_DCLICK, self.OnGridCellDoubleClick)
		self.wxGrid.Bind(wx.grid.EVT_GRID_CELL_RIGHT_CLICK, self.OnGridCellRightClick)
		self.wxGrid.Bind(wx.grid.EVT_GRID_EDITOR_HIDDEN, self.OnGridEditorShown)
		self.wxGrid.Bind(wx.grid.EVT_GRID_LABEL_LEFT_CLICK, self.OnGridLabelLeftClick)
		self.wxGrid.Bind(wx.grid.EVT_GRID_LABEL_RIGHT_CLICK, self.OnGridLabelRightClick)
		self.wxGrid.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)
		self.wxGrid.Bind(wx.EVT_KEY_UP, self.OnKeyUp)
		self.Bind( wx.EVT_MENU, self.OnPopupCopy, id = self.m_menuItemPopupCopy.GetId() )
		self.Bind( wx.EVT_MENU, self.OnPopupPaste, id = self.m_menuItemPopupPaste.GetId() )
		self.Bind( wx.EVT_MENU, self.OnPopupClearSelection, id = self.m_menuItemPopupClearSelection.GetId() )
		self.Bind( wx.EVT_MENU, self.OnPopupDelCol, id = self.m_menuItemPopupDelCol.GetId() )
		self.Bind( wx.EVT_MENU, self.OnPopupDelRow, id = self.m_menuItemPopupDelRow.GetId() )
		self.Bind( wx.EVT_MENU, self.OnPopupRenameCol, id = self.m_menuItemPopupRenameCol.GetId() )
		self.Bind( wx.EVT_MENU, self.OnPopupInsertColLeft, id = self.m_menuItemPopupInsertColLeft.GetId() )
		self.Bind( wx.EVT_MENU, self.OnPopupInsertColRight, id = self.m_menuItemPopupInsertColRight.GetId() )
		self.Bind( wx.EVT_MENU, self.OnPopupExtractScanner, id = self.m_menuItemPopupExtractScanner.GetId() )

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

	def OnGridCellChanged( self, event ):
		event.Skip()

	def OnGridCellDoubleClick( self, event ):
		event.Skip()

	def OnGridCellRightClick( self, event ):
		event.Skip()

	def OnGridEditorShown( self, event ):
		event.Skip()

	def OnGridLabelLeftClick( self, event ):
		event.Skip()

	def OnGridLabelRightClick( self, event ):
		event.Skip()

	def OnKeyDown( self, event ):
		event.Skip()

	def OnKeyUp( self, event ):
		event.Skip()

	def OnPopupCopy( self, event ):
		event.Skip()

	def OnPopupPaste( self, event ):
		event.Skip()

	def OnPopupClearSelection( self, event ):
		event.Skip()

	def OnPopupDelCol( self, event ):
		event.Skip()

	def OnPopupDelRow( self, event ):
		event.Skip()

	def OnPopupRenameCol( self, event ):
		event.Skip()

	def OnPopupInsertColLeft( self, event ):
		event.Skip()

	def OnPopupInsertColRight( self, event ):
		event.Skip()

	def OnPopupExtractScanner( self, event ):
		event.Skip()

	def MainFrameOnContextMenu( self, event ):
		self.PopupMenu( self.m_GridPopup, event.GetPosition() )


