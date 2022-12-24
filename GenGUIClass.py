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
		wx.Frame.__init__ ( self, parent, id = wx.ID_ANY, title = wx.EmptyString, pos = wx.DefaultPosition, size = wx.Size( 1000,772 ), style = wx.DEFAULT_FRAME_STYLE|wx.TAB_TRAVERSAL )

		self.SetSizeHints( wx.DefaultSize, wx.DefaultSize )

		self.m_toolBarTop = self.CreateToolBar( wx.TB_HORIZONTAL, wx.ID_ANY )
		self.bLoadExistingLSTFile = wx.Button( self.m_toolBarTop, wx.ID_ANY, u"Load Existing LST File", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_toolBarTop.AddControl( self.bLoadExistingLSTFile )
		self.bCreateNewFanzineDir = wx.Button( self.m_toolBarTop, wx.ID_ANY, u"Create New Fanzine Dir.", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_toolBarTop.AddControl( self.bCreateNewFanzineDir )
		self.bAddNewIssues = wx.Button( self.m_toolBarTop, wx.ID_ANY, u"Add New Issue(s)", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_toolBarTop.AddControl( self.bAddNewIssues )
		self.bSave = wx.Button( self.m_toolBarTop, wx.ID_ANY, u"Save", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_toolBarTop.AddControl( self.bSave )
		self.bExit = wx.Button( self.m_toolBarTop, wx.ID_ANY, u"Exit", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_toolBarTop.AddControl( self.bExit )
		self.m_toolBarTop.Realize()

		bSizerMain = wx.BoxSizer( wx.VERTICAL )

		fgSizer4 = wx.FlexGridSizer( 2, 8, 0, 0 )
		fgSizer4.SetFlexibleDirection( wx.BOTH )
		fgSizer4.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )

		self.m_staticText4 = wx.StaticText( self, wx.ID_ANY, u"Fanzine Name", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText4.Wrap( -1 )

		self.m_staticText4.SetMinSize( wx.Size( 200,-1 ) )
		self.m_staticText4.SetMaxSize( wx.Size( -1,50 ) )

		fgSizer4.Add( self.m_staticText4, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL|wx.FIXED_MINSIZE, 5 )

		self.tFanzineName = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size( 200,-1 ), 0 )
		self.tFanzineName.SetToolTip( u"The name of the fanzine serires." )
		self.tFanzineName.SetMinSize( wx.Size( 200,-1 ) )

		fgSizer4.Add( self.tFanzineName, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL|wx.FIXED_MINSIZE, 0 )

		self.m_staticText5 = wx.StaticText( self, wx.ID_ANY, u"Editor(s)", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText5.Wrap( -1 )

		self.m_staticText5.SetMinSize( wx.Size( 200,-1 ) )
		self.m_staticText5.SetMaxSize( wx.Size( -1,50 ) )

		fgSizer4.Add( self.m_staticText5, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL|wx.FIXED_MINSIZE, 5 )

		self.tEditors = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
		self.tEditors.SetToolTip( u"A list of editors separated by commans." )
		self.tEditors.SetMinSize( wx.Size( 200,-1 ) )

		fgSizer4.Add( self.tEditors, 0, wx.ALL, 5 )

		self.m_staticText6 = wx.StaticText( self, wx.ID_ANY, u"Dates", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText6.Wrap( -1 )

		self.m_staticText6.SetMinSize( wx.Size( 200,-1 ) )
		self.m_staticText6.SetMaxSize( wx.Size( -1,50 ) )

		fgSizer4.Add( self.m_staticText6, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL|wx.FIXED_MINSIZE, 5 )

		self.tDates = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
		self.tDates.SetToolTip( u"The date range for this fanzine, years only. E.g., 1965-1974" )
		self.tDates.SetMinSize( wx.Size( 200,-1 ) )

		fgSizer4.Add( self.tDates, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL|wx.FIXED_MINSIZE, 0 )

		self.m_staticText7 = wx.StaticText( self, wx.ID_ANY, u"Fanzine Type", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText7.Wrap( -1 )

		self.m_staticText7.SetMinSize( wx.Size( 200,-1 ) )
		self.m_staticText7.SetMaxSize( wx.Size( -1,50 ) )

		fgSizer4.Add( self.m_staticText7, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL|wx.FIXED_MINSIZE, 5 )

		tFanzineTypeChoices = [ u" ", u"Genzine", u"Apazine", u"Perzine", u"Newszine", u"Collection", u"Related", u"Clubzine", u"Adzine", u"Reference" ]
		self.tFanzineType = wx.Choice( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, tFanzineTypeChoices, 0 )
		self.tFanzineType.SetSelection( 0 )
		self.tFanzineType.SetMinSize( wx.Size( 200,-1 ) )

		fgSizer4.Add( self.tFanzineType, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL|wx.FIXED_MINSIZE, 0 )

		self.cbComplete = wx.CheckBox( self, wx.ID_ANY, u"Complete", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.cbComplete.SetToolTip( u"Is this fanzine series complete on fanac.org?" )

		fgSizer4.Add( self.cbComplete, 0, wx.ALL, 5 )

		self.cbAlphabetizeIndividually = wx.CheckBox( self, wx.ID_ANY, u"Alphabetize Individually", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.cbAlphabetizeIndividually.SetToolTip( u"Do we want to treat the issues in this page as independent fanzines rather than issues of this page?" )

		fgSizer4.Add( self.cbAlphabetizeIndividually, 0, wx.ALL, 5 )


		bSizerMain.Add( fgSizer4, 0, wx.EXPAND, 5 )

		fgSizer2 = wx.FlexGridSizer( 0, 2, 0, 0 )
		fgSizer2.AddGrowableCol( 0 )
		fgSizer2.SetFlexibleDirection( wx.HORIZONTAL )
		fgSizer2.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )

		self.lLocalDirectory = wx.StaticText( self, wx.ID_ANY, u"Local Directory:", wx.DefaultPosition, wx.Size( -1,-1 ), wx.ALIGN_RIGHT )
		self.lLocalDirectory.Wrap( -1 )

		self.lLocalDirectory.SetMinSize( wx.Size( 500,-1 ) )

		fgSizer2.Add( self.lLocalDirectory, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5 )

		self.tDirectoryLocal = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size( -1,-1 ), 0 )
		self.tDirectoryLocal.SetToolTip( u"The name of the local directory (relative to the root displayed to the left) for this fanzine series." )
		self.tDirectoryLocal.SetMinSize( wx.Size( 200,-1 ) )

		fgSizer2.Add( self.tDirectoryLocal, 0, wx.ALIGN_LEFT|wx.ALL, 5 )

		self.lServerDirectory = wx.StaticText( self, wx.ID_ANY, u"Server Directory:", wx.DefaultPosition, wx.Size( -1,-1 ), wx.ALIGN_RIGHT )
		self.lServerDirectory.Wrap( -1 )

		self.lServerDirectory.SetMinSize( wx.Size( 500,-1 ) )

		fgSizer2.Add( self.lServerDirectory, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5 )

		self.tDirectoryServer = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size( -1,-1 ), 0 )
		self.tDirectoryServer.SetToolTip( u"The name of the directory for this fanzine on the fanac.org server." )
		self.tDirectoryServer.SetMinSize( wx.Size( 200,-1 ) )

		fgSizer2.Add( self.tDirectoryServer, 0, wx.ALIGN_LEFT|wx.ALL, 5 )


		bSizerMain.Add( fgSizer2, 0, 0, 5 )

		fgSizerComments = wx.FlexGridSizer( 4, 2, 0, 0 )
		fgSizerComments.AddGrowableCol( 1 )
		fgSizerComments.AddGrowableRow( 1 )
		fgSizerComments.SetFlexibleDirection( wx.BOTH )
		fgSizerComments.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )

		self.m_staticText2 = wx.StaticText( self, wx.ID_ANY, u"Top Comments: ", wx.Point( -1,-1 ), wx.DefaultSize, 0 )
		self.m_staticText2.Wrap( -1 )

		fgSizerComments.Add( self.m_staticText2, 1, wx.ALIGN_RIGHT|wx.ALL, 5 )

		self.tTopComments = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.TE_MULTILINE )
		self.tTopComments.SetToolTip( u"Other top blather for the fanzine series page." )
		self.tTopComments.SetMinSize( wx.Size( -1,100 ) )

		fgSizerComments.Add( self.tTopComments, 1, wx.ALL|wx.EXPAND, 5 )

		self.m_staticText21 = wx.StaticText( self, wx.ID_ANY, u"Locale Info:", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText21.Wrap( -1 )

		fgSizerComments.Add( self.m_staticText21, 0, wx.ALIGN_RIGHT|wx.ALL, 5 )

		self.tLocaleText = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.TE_MULTILINE )
		self.tLocaleText.SetToolTip( u"The location for this fanzine: Country, Country: City, State: City" )
		self.tLocaleText.SetMinSize( wx.Size( -1,30 ) )
		self.tLocaleText.SetMaxSize( wx.Size( -1,30 ) )

		fgSizerComments.Add( self.tLocaleText, 0, wx.ALL|wx.EXPAND, 5 )

		self.m_staticText9 = wx.StaticText( self, wx.ID_ANY, u"Credits: ", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText9.Wrap( -1 )

		fgSizerComments.Add( self.m_staticText9, 0, wx.ALIGN_RIGHT|wx.ALL, 5 )

		self.tCredits = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
		self.tCredits.SetToolTip( u"A free-form list of people who have contributed scans to this fanzine series." )
		self.tCredits.SetMinSize( wx.Size( -1,30 ) )
		self.tCredits.SetMaxSize( wx.Size( -1,30 ) )

		fgSizerComments.Add( self.tCredits, 0, wx.ALL|wx.EXPAND, 5 )


		bSizerMain.Add( fgSizerComments, 0, wx.ALL|wx.EXPAND, 5 )

		theIssueGrid = wx.BoxSizer( wx.VERTICAL )

		self.wxGrid = wx.grid.Grid( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, 0 )

		# Grid
		self.wxGrid.CreateGrid( 150, 15 )
		self.wxGrid.EnableEditing( True )
		self.wxGrid.EnableGridLines( True )
		self.wxGrid.EnableDragGridSize( False )
		self.wxGrid.SetMargins( 0, 0 )

		# Columns
		self.wxGrid.AutoSizeColumns()
		self.wxGrid.EnableDragColMove( True )
		self.wxGrid.EnableDragColSize( False )
		self.wxGrid.SetColLabelSize( 30 )
		self.wxGrid.SetColLabelAlignment( wx.ALIGN_CENTER, wx.ALIGN_CENTER )

		# Rows
		self.wxGrid.AutoSizeRows()
		self.wxGrid.EnableDragRowSize( True )
		self.wxGrid.SetRowLabelSize( 80 )
		self.wxGrid.SetRowLabelAlignment( wx.ALIGN_CENTER, wx.ALIGN_CENTER )

		# Label Appearance

		# Cell Defaults
		self.wxGrid.SetDefaultCellAlignment( wx.ALIGN_LEFT, wx.ALIGN_TOP )
		theIssueGrid.Add( self.wxGrid, 1, wx.ALL|wx.EXPAND, 5 )


		bSizerMain.Add( theIssueGrid, 1, wx.EXPAND, 5 )


		self.SetSizer( bSizerMain )
		self.Layout()
		self.m_GridPopup = wx.Menu()
		self.m_menuItemPopupCopy = wx.MenuItem( self.m_GridPopup, wx.ID_ANY, u"Copy", wx.EmptyString, wx.ITEM_NORMAL )
		self.m_GridPopup.Append( self.m_menuItemPopupCopy )

		self.m_menuItemPopupPaste = wx.MenuItem( self.m_GridPopup, wx.ID_ANY, u"Paste", wx.EmptyString, wx.ITEM_NORMAL )
		self.m_GridPopup.Append( self.m_menuItemPopupPaste )

		self.m_menuItemPopupEraseSelection = wx.MenuItem( self.m_GridPopup, wx.ID_ANY, u"Erase Selection", wx.EmptyString, wx.ITEM_NORMAL )
		self.m_GridPopup.Append( self.m_menuItemPopupEraseSelection )

		self.m_menuItemPopupDelCol = wx.MenuItem( self.m_GridPopup, wx.ID_ANY, u"Delete Column(s)", wx.EmptyString, wx.ITEM_NORMAL )
		self.m_GridPopup.Append( self.m_menuItemPopupDelCol )

		self.m_menuItemPopupDelRow = wx.MenuItem( self.m_GridPopup, wx.ID_ANY, u"Delete Row(s)", wx.EmptyString, wx.ITEM_NORMAL )
		self.m_GridPopup.Append( self.m_menuItemPopupDelRow )

		self.m_menuItemPopupInsertRow = wx.MenuItem( self.m_GridPopup, wx.ID_ANY, u"Insert a Row", wx.EmptyString, wx.ITEM_NORMAL )
		self.m_GridPopup.Append( self.m_menuItemPopupInsertRow )

		self.m_menuItemPopupRenameCol = wx.MenuItem( self.m_GridPopup, wx.ID_ANY, u"Rename Column", wx.EmptyString, wx.ITEM_NORMAL )
		self.m_GridPopup.Append( self.m_menuItemPopupRenameCol )

		self.m_menuItemPopupInsertColLeft = wx.MenuItem( self.m_GridPopup, wx.ID_ANY, u"Insert Column to Left", wx.EmptyString, wx.ITEM_NORMAL )
		self.m_GridPopup.Append( self.m_menuItemPopupInsertColLeft )

		self.m_menuItemPopupInsertColRight = wx.MenuItem( self.m_GridPopup, wx.ID_ANY, u"Insert Column to Right", wx.EmptyString, wx.ITEM_NORMAL )
		self.m_GridPopup.Append( self.m_menuItemPopupInsertColRight )

		self.m_menuItemPopupSortOnCol = wx.MenuItem( self.m_GridPopup, wx.ID_ANY, u"Sort on Selected Column", wx.EmptyString, wx.ITEM_NORMAL )
		self.m_GridPopup.Append( self.m_menuItemPopupSortOnCol )

		self.m_menuItemPopupExtractScanner = wx.MenuItem( self.m_GridPopup, wx.ID_ANY, u"Extract Scanner", wx.EmptyString, wx.ITEM_NORMAL )
		self.m_GridPopup.Append( self.m_menuItemPopupExtractScanner )

		self.m_menuItemPopupExtractApaMailings = wx.MenuItem( self.m_GridPopup, wx.ID_ANY, u"Extract APA Mailings", wx.EmptyString, wx.ITEM_NORMAL )
		self.m_GridPopup.Append( self.m_menuItemPopupExtractApaMailings )

		self.m_menuItemPopupExtractEditor = wx.MenuItem( self.m_GridPopup, wx.ID_ANY, u"Extract Editor", wx.EmptyString, wx.ITEM_NORMAL )
		self.m_GridPopup.Append( self.m_menuItemPopupExtractEditor )

		self.m_menuItemPopupPropagateEditor = wx.MenuItem( self.m_GridPopup, wx.ID_ANY, u"Propagate Editor", wx.EmptyString, wx.ITEM_NORMAL )
		self.m_GridPopup.Append( self.m_menuItemPopupPropagateEditor )

		self.m_menuItemMerge = wx.MenuItem( self.m_GridPopup, wx.ID_ANY, u"Merge", wx.EmptyString, wx.ITEM_NORMAL )
		self.m_GridPopup.Append( self.m_menuItemMerge )

		self.m_menuItemClearLinks = wx.MenuItem( self.m_GridPopup, wx.ID_ANY, u"Clear All Links", wx.EmptyString, wx.ITEM_NORMAL )
		self.m_GridPopup.Append( self.m_menuItemClearLinks )

		self.m_menuItemAddLink = wx.MenuItem( self.m_GridPopup, wx.ID_ANY, u"Add a Link", wx.EmptyString, wx.ITEM_NORMAL )
		self.m_GridPopup.Append( self.m_menuItemAddLink )

		self.Bind( wx.EVT_RIGHT_DOWN, self.MainFrameOnContextMenu )


		self.Centre( wx.BOTH )

		# Connect Events
		self.Bind( wx.EVT_CLOSE, self.OnClose )
		self.bLoadExistingLSTFile.Bind( wx.EVT_BUTTON, self.OnLoadExistingLSTFile )
		self.bCreateNewFanzineDir.Bind( wx.EVT_BUTTON, self.OnCreateNewFanzineDir )
		self.bAddNewIssues.Bind( wx.EVT_BUTTON, self.OnAddNewIssues )
		self.bSave.Bind( wx.EVT_BUTTON, self.OnSave )
		self.bExit.Bind( wx.EVT_BUTTON, self.OnExitClicked )
		self.tFanzineName.Bind( wx.EVT_CHAR, self.OnFanzineNameChar )
		self.tFanzineName.Bind( wx.EVT_TEXT, self.OnFanzineName )
		self.tEditors.Bind( wx.EVT_TEXT, self.OnEditors )
		self.tDates.Bind( wx.EVT_TEXT, self.OnDates )
		self.tFanzineType.Bind( wx.EVT_CHOICE, self.OnFanzineType )
		self.cbComplete.Bind( wx.EVT_CHECKBOX, self.OnCheckComplete )
		self.cbAlphabetizeIndividually.Bind( wx.EVT_CHECKBOX, self.OnCheckAlphabetizeIndividually )
		self.tDirectoryLocal.Bind( wx.EVT_TEXT, self.OnDirectoryLocal )
		self.tDirectoryServer.Bind( wx.EVT_TEXT, self.OnDirectoryServer )
		self.tTopComments.Bind( wx.EVT_TEXT, self.OnTopComments )
		self.tLocaleText.Bind( wx.EVT_TEXT, self.OnTextLocale )
		self.tCredits.Bind( wx.EVT_TEXT, self.OnCredits )
		self.wxGrid.Bind( wx.grid.EVT_GRID_CELL_CHANGED, self.OnGridCellChanged )
		self.wxGrid.Bind( wx.grid.EVT_GRID_CELL_LEFT_DCLICK, self.OnGridCellDoubleClick )
		self.wxGrid.Bind( wx.grid.EVT_GRID_CELL_RIGHT_CLICK, self.OnGridCellRightClick )
		self.wxGrid.Bind( wx.grid.EVT_GRID_EDITOR_HIDDEN, self.OnGridEditorShown )
		self.wxGrid.Bind( wx.grid.EVT_GRID_LABEL_LEFT_CLICK, self.OnGridLabelLeftClick )
		self.wxGrid.Bind( wx.grid.EVT_GRID_LABEL_RIGHT_CLICK, self.OnGridLabelRightClick )
		self.wxGrid.Bind( wx.EVT_KEY_DOWN, self.OnKeyDown )
		self.wxGrid.Bind( wx.EVT_KEY_UP, self.OnKeyUp )
		self.Bind( wx.EVT_MENU, self.OnPopupCopy, id = self.m_menuItemPopupCopy.GetId() )
		self.Bind( wx.EVT_MENU, self.OnPopupPaste, id = self.m_menuItemPopupPaste.GetId() )
		self.Bind( wx.EVT_MENU, self.OnPopupEraseSelection, id = self.m_menuItemPopupEraseSelection.GetId() )
		self.Bind( wx.EVT_MENU, self.OnPopupDelCol, id = self.m_menuItemPopupDelCol.GetId() )
		self.Bind( wx.EVT_MENU, self.OnPopupDelRow, id = self.m_menuItemPopupDelRow.GetId() )
		self.Bind( wx.EVT_MENU, self.OnPopupInsertRow, id = self.m_menuItemPopupInsertRow.GetId() )
		self.Bind( wx.EVT_MENU, self.OnPopupRenameCol, id = self.m_menuItemPopupRenameCol.GetId() )
		self.Bind( wx.EVT_MENU, self.OnPopupInsertColLeft, id = self.m_menuItemPopupInsertColLeft.GetId() )
		self.Bind( wx.EVT_MENU, self.OnPopupInsertColRight, id = self.m_menuItemPopupInsertColRight.GetId() )
		self.Bind( wx.EVT_MENU, self.OnPopupSortOnSelectedColumn, id = self.m_menuItemPopupSortOnCol.GetId() )
		self.Bind( wx.EVT_MENU, self.OnPopupExtractScanner, id = self.m_menuItemPopupExtractScanner.GetId() )
		self.Bind( wx.EVT_MENU, self.OnPopupExtractApaMailings, id = self.m_menuItemPopupExtractApaMailings.GetId() )
		self.Bind( wx.EVT_MENU, self.OnPopupExtractEditor, id = self.m_menuItemPopupExtractEditor.GetId() )
		self.Bind( wx.EVT_MENU, self.OnPopupPropagateEditor, id = self.m_menuItemPopupPropagateEditor.GetId() )
		self.Bind( wx.EVT_MENU, self.OnPopupMerge, id = self.m_menuItemMerge.GetId() )
		self.Bind( wx.EVT_MENU, self.OnPopupClearAllLinks, id = self.m_menuItemClearLinks.GetId() )
		self.Bind( wx.EVT_MENU, self.OnPopupAddLink, id = self.m_menuItemAddLink.GetId() )

	def __del__( self ):
		pass


	# Virtual event handlers, overide them in your derived class
	def OnClose( self, event ):
		event.Skip()

	def OnLoadExistingLSTFile( self, event ):
		event.Skip()

	def OnCreateNewFanzineDir( self, event ):
		event.Skip()

	def OnAddNewIssues( self, event ):
		event.Skip()

	def OnSave( self, event ):
		event.Skip()

	def OnExitClicked( self, event ):
		event.Skip()

	def OnFanzineNameChar( self, event ):
		event.Skip()

	def OnFanzineName( self, event ):
		event.Skip()

	def OnEditors( self, event ):
		event.Skip()

	def OnDates( self, event ):
		event.Skip()

	def OnFanzineType( self, event ):
		event.Skip()

	def OnCheckComplete( self, event ):
		event.Skip()

	def OnCheckAlphabetizeIndividually( self, event ):
		event.Skip()

	def OnDirectoryLocal( self, event ):
		event.Skip()

	def OnDirectoryServer( self, event ):
		event.Skip()

	def OnTopComments( self, event ):
		event.Skip()

	def OnTextLocale( self, event ):
		event.Skip()

	def OnCredits( self, event ):
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

	def OnPopupEraseSelection( self, event ):
		event.Skip()

	def OnPopupDelCol( self, event ):
		event.Skip()

	def OnPopupDelRow( self, event ):
		event.Skip()

	def OnPopupInsertRow( self, event ):
		event.Skip()

	def OnPopupRenameCol( self, event ):
		event.Skip()

	def OnPopupInsertColLeft( self, event ):
		event.Skip()

	def OnPopupInsertColRight( self, event ):
		event.Skip()

	def OnPopupSortOnSelectedColumn( self, event ):
		event.Skip()

	def OnPopupExtractScanner( self, event ):
		event.Skip()

	def OnPopupExtractApaMailings( self, event ):
		event.Skip()

	def OnPopupExtractEditor( self, event ):
		event.Skip()

	def OnPopupPropagateEditor( self, event ):
		event.Skip()

	def OnPopupMerge( self, event ):
		event.Skip()

	def OnPopupClearAllLinks( self, event ):
		event.Skip()

	def OnPopupAddLink( self, event ):
		event.Skip()

	def MainFrameOnContextMenu( self, event ):
		self.PopupMenu( self.m_GridPopup, event.GetPosition() )


