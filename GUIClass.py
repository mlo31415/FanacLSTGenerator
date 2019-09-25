# -*- coding: utf-8 -*-

###########################################################################
## Python code generated with wxFormBuilder (version Jun 17 2015)
## http://www.wxformbuilder.org/
##
## PLEASE DO "NOT" EDIT THIS FILE!
###########################################################################

import wx
import wx.xrc
import wx.grid


###########################################################################
## Class MainFrame
###########################################################################

class GUIClass(wx.Frame):

    def __init__(self, parent):
        wx.Frame.__init__(self, parent, id=wx.ID_ANY, title=wx.EmptyString, pos=wx.DefaultPosition, size=wx.Size(1000, 700), style=wx.DEFAULT_FRAME_STYLE|wx.TAB_TRAVERSAL)

        self.SetSizeHints(wx.DefaultSize, wx.DefaultSize)

        self.m_toolBar2=self.CreateToolBar(wx.TB_HORIZONTAL, wx.ID_ANY)
        self.mLoadNewIssues=wx.Button(self.m_toolBar2, wx.ID_ANY, u"Load New Issue(s)", wx.DefaultPosition, wx.DefaultSize, 0)
        self.m_toolBar2.AddControl(self.mLoadNewIssues)
        self.bLoadNewLSTFile=wx.Button(self.m_toolBar2, wx.ID_ANY, u"Load New LST File", wx.DefaultPosition, wx.DefaultSize, 0)
        self.m_toolBar2.AddControl(self.bLoadNewLSTFile)
        self.bSaveLSTFile=wx.Button(self.m_toolBar2, wx.ID_ANY, u"Save LST File", wx.DefaultPosition, wx.DefaultSize, 0)
        self.m_toolBar2.AddControl(self.bSaveLSTFile)
        self.m_toolBar2.Realize()

        bSizer1=wx.BoxSizer(wx.VERTICAL)

        bSizer3=wx.BoxSizer(wx.HORIZONTAL)

        self.m_staticText1=wx.StaticText(self, wx.ID_ANY, u"Top matter:", wx.DefaultPosition, wx.DefaultSize, 0)
        self.m_staticText1.Wrap(-1)
        bSizer3.Add(self.m_staticText1, 0, wx.ALL, 5)

        self.tTopMatter=wx.TextCtrl(self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size(800, -1), 0)
        bSizer3.Add(self.tTopMatter, 0, wx.ALL|wx.EXPAND, 5)

        bSizer1.Add(bSizer3, 1, wx.EXPAND, 5)

        fgSizer2=wx.FlexGridSizer(2, 2, 0, 0)
        fgSizer2.AddGrowableCol(1)
        fgSizer2.AddGrowableRow(1)
        fgSizer2.SetFlexibleDirection(wx.BOTH)
        fgSizer2.SetNonFlexibleGrowMode(wx.FLEX_GROWMODE_SPECIFIED)

        self.m_staticText2=wx.StaticText(self, wx.ID_ANY, u"<P>Comments</P>:", wx.DefaultPosition, wx.DefaultSize, 0)
        self.m_staticText2.Wrap(-1)
        fgSizer2.Add(self.m_staticText2, 0, wx.ALL, 5)

        self.tPText=wx.TextCtrl(self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.TE_MULTILINE)
        self.tPText.SetMinSize(wx.Size(-1, 100))

        fgSizer2.Add(self.tPText, 1, wx.ALL|wx.EXPAND, 5)

        bSizer1.Add(fgSizer2, 1, wx.ALL|wx.EXPAND, 5)

        theIssueGrid=wx.BoxSizer(wx.VERTICAL)

        self.gRowGrid=wx.grid.Grid(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, 0)

        # Grid
        self.gRowGrid.CreateGrid(300, 30)
        self.gRowGrid.EnableEditing(True)
        self.gRowGrid.EnableGridLines(True)
        self.gRowGrid.EnableDragGridSize(False)
        self.gRowGrid.SetMargins(0, 0)

        # Columns
        self.gRowGrid.AutoSizeColumns()
        self.gRowGrid.EnableDragColMove(True)
        self.gRowGrid.EnableDragColSize(True)
        self.gRowGrid.SetColLabelSize(30)
        self.gRowGrid.SetColLabelAlignment(wx.ALIGN_CENTRE, wx.ALIGN_CENTRE)

        # Rows
        self.gRowGrid.AutoSizeRows()
        self.gRowGrid.EnableDragRowSize(True)
        self.gRowGrid.SetRowLabelSize(80)
        self.gRowGrid.SetRowLabelAlignment(wx.ALIGN_CENTRE, wx.ALIGN_CENTRE)

        # Label Appearance

        # Cell Defaults
        self.gRowGrid.SetDefaultCellAlignment(wx.ALIGN_LEFT, wx.ALIGN_TOP)
        self.m_popupMenu1=wx.Menu()
        self.m_menuItemCopy=wx.MenuItem(self.m_popupMenu1, wx.ID_ANY, u"Copy", wx.EmptyString, wx.ITEM_NORMAL)
        self.m_popupMenu1.Append(self.m_menuItemCopy)
        self.m_menuItemPaste=wx.MenuItem(self.m_popupMenu1, wx.ID_ANY, u"Paste", wx.EmptyString, wx.ITEM_NORMAL)
        self.m_popupMenu1.Append        (self.m_menuItemPaste)
        self.m_menuItemDelete=wx.MenuItem(self.m_popupMenu1, wx.ID_ANY, u"Delete", wx.EmptyString, wx.ITEM_NORMAL)
        self.m_popupMenu1.Append        (self.m_menuItemDelete)

        self.gRowGrid.Bind(wx.EVT_RIGHT_DOWN, self.gRowGridOnContextMenu)

        theIssueGrid.Add(self.gRowGrid, 0, wx.ALL|wx.EXPAND, 5)

        bSizer1.Add(theIssueGrid, 1, wx.EXPAND, 5)

        self.SetSizer(bSizer1)
        self.Layout()

        self.Centre(wx.BOTH)

        # Connect Events
        self.mLoadNewIssues.Bind(wx.EVT_BUTTON, self.OnLoadNewIssues)
        self.bLoadNewLSTFile.Bind(wx.EVT_BUTTON, self.OnLoadNewLSTFile)
        self.bSaveLSTFile.Bind(wx.EVT_BUTTON, self.OnSaveLSTFile)
        self.tTopMatter.Bind(wx.EVT_TEXT, self.OnTextTopMatter)
        self.tPText.Bind(wx.EVT_TEXT, self.OnTextComments)
        self.gRowGrid.Bind(wx.grid.EVT_GRID_CELL_CHANGED, self.OnGridCellChanged)
        self.gRowGrid.Bind(wx.grid.EVT_GRID_CELL_RIGHT_CLICK, self.OnGridCellRightClick)
        self.gRowGrid.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)
        self.gRowGrid.Bind(wx.EVT_KEY_UP, self.OnKeyUp)
        self.Bind(wx.EVT_MENU, self.OnPopupCopy, id=self.m_menuItemCopy.GetId())
        self.Bind(wx.EVT_MENU, self.OnPopupPaste, id=self.m_menuItemPaste.GetId())
        self.Bind(wx.EVT_MENU, self.OnPopupDelete, id=self.m_menuItemDelete.GetId())

    def __del__(self):
        pass

    # Virtual event handlers, overide them in your derived class
    def OnLoadNewIssues(self, event):
        event.Skip()

    def OnLoadNewLSTFile(self, event):
        event.Skip()

    def OnSaveLSTFile(self, event):
        event.Skip()

    def OnTextTopMatter(self, event):
        event.Skip()

    def OnTextComments(self, event):
        event.Skip()

    def OnGridCellChanged(self, event):
        event.Skip()

    def OnGridCellRightClick(self, event):
        event.Skip()

    def OnKeyDown(self, event):
        event.Skip()

    def OnKeyUp(self, event):
        event.Skip()

    def OnPopupCopy(self, event):
        event.Skip()

    def OnPopupPaste(self, event):
        event.Skip()

    def OnPopupDelete(self, event):
        event.Skip()

    def gRowGridOnContextMenu(self, event):
        self.gRowGrid.PopupMenu(self.m_popupMenu1, event.GetPosition())


