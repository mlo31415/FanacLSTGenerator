import os
import wx
import wx.grid
from LSTFile import *

class MainWindow(wx.Frame):
    def __init__(self, parent, title):
        wx.Frame.__init__(self, parent, title=title, size=(600,600))
        #self.control = wx.TextCtrl(self, style=wx.TE_MULTILINE)
        self.statusbar=self.CreateStatusBar() # A Statusbar in the bottom of the window

        # Setting up the menu.
        filemenu=wx.Menu()
        # wx.ID_ABOUT and wx.ID_EXIT are standard IDs provided by wxWidgets.
        filemenu.Append(wx.ID_ABOUT, "&About", " Information about this program")
        filemenu.AppendSeparator()
        filemenu.Append(wx.ID_EXIT, "E&xit", " Terminate the program")

        # Creating the menubar.
        menuBar=wx.MenuBar()
        menuBar.Append(filemenu, "&File")  # Adding the "filemenu" to the MenuBar
        self.SetMenuBar(menuBar)  # Adding the MenuBar to the Frame content.
        panel=wx.Panel(self)

        # Call the File Open dialog to get an LST file
        self.dirname=''
        dlg=wx.FileDialog(self, "Select LST file to load", self.dirname, "", "*.LST", wx.FD_OPEN)
        if dlg.ShowModal() != wx.ID_OK:
            dlg.Destroy()
            return

        self.lstFilename=dlg.GetFilename()
        self.dirname=dlg.GetDirectory()
        dlg.Destroy()

        self.lstData=ReadLstFile(self.lstFilename)

        # Create a wxGrid object
        self.grid=grid=wx.grid.Grid()
        # Call CreateGrid to set the dimensions of the grid
        grid.Create(panel)
        grid.CreateGrid(1, 1+len(self.lstData.ColumnHeaders))
        grid.SetDefaultColSize(50, True)
        grid.SetDefaultRowSize(20, True)

        grid.HideRowLabels()
        #grid.EnableGridLines(False)

        # Add the column headers
        i=1
        for colhead in self.lstData.ColumnHeaders:
            grid.SetColLabelValue(i, colhead)
            i+=1

        # Now insert the row data
        grid.AppendRows(len(self.lstData.Rows))
        i=0
        for row in self.lstData.Rows:
            j=1
            for cell in row:
                grid.SetCellValue(i, j, cell)
                j+=1
            i+=1

        # We need to split the contents of col 1 into two parts, one for col 0 and the rest for col 1
        for i in range(0, len(self.lstData.Rows)):
            val=grid.GetCellValue(i, 1).split(">")
            grid.SetCellValue(i, 0, val[0])
            grid.SetCellValue(i, 1, val[1])

        grid.AutoSizeColumns()

        # Let's lay out the space.  We fill the panel with a vertical sizer so things in it are stacked vertically.
        # Inside that we have a top sizer for small controls and a second sizer below it for the grid.
        gbs=wx.GridBagSizer(4,2)

        # The top gridbag row gets buttons
        self.buttonLoad=wx.Button(panel, id=wx.ID_ANY, label="Save LST file")
        gbs.Add(self.buttonLoad, (0,0))
        self.buttonLoad.Bind(wx.EVT_BUTTON, self.OnSaveLSTButtonClicked)

        self.buttonGenerate=wx.Button(panel, id=wx.ID_ANY, label="Rename")
        gbs.Add(self.buttonGenerate, (0,1))

        # Now put a pair of buttons with labels above them in the middle two gridbag rows
        gbs.Add(wx.StaticText(panel, label=" Fanzine name"), (1,0))
        self.fanzineNameTextbox=wx.TextCtrl(panel, id=wx.ID_ANY)
        gbs.Add(self.fanzineNameTextbox, (2,0))
        self.fanzineNameTextbox.Bind(wx.EVT_TEXT, self.OnFanzinenameOrIssueTextboxChanged)

        gbs.Add(wx.StaticText(panel, label=" Issue number"), (1,1))
        self.fanzineIssuenumber=wx.TextCtrl(panel, id=wx.ID_ANY)
        gbs.Add(self.fanzineIssuenumber, (2,1))
        self.fanzineIssuenumber.Bind(wx.EVT_TEXT, self.OnFanzinenameOrIssueTextboxChanged)

        self.grid.Bind(wx.grid.EVT_GRID_CELL_CHANGED, self.OnGridCellChanged)

        # And the grid itself goes in the bottom gridbag row, spanning both columns
        gbs.Add(grid, (3,0), span=(2,2))

        panel.SetSizerAndFit(gbs)

        self.Show(True)


    def OnSaveLSTButtonClicked(self, event):
        if event.EventObject.Label != "Save LST file":
            return
        content=[]
        content.append(self.lstData.FirstLine)
        content.append("")
        if len(self.lstData.TopTextLines) > 0:
            for line in self.lstData.TopTextLines:
                content.append(line)
            content.append("")
        content.append("; ".join(self.lstData.ColumnHeaders))
        content.append("")
        for row in self.lstData.Rows:
            content.append("; ".join(row))
        newname=os.path.join(self.dirname, os.path.splitext(self.lstFilename)[0]+"-1.LST")
        with open(newname, "w+") as f:
            f.writelines([c+"\n" for c in content])


    def OnGridCellChanged(self, evt):
        row=evt.GetRow()
        col=evt.GetCol()
        if col > 1:
            self.lstData.Rows[row][col-1]=self.grid.GetCellValue(row, col)
        else:
            self.lstData.Rows[row][0]=self.grid.GetCellValue(row, 0)+">"+self.grid.GetCellValue(row, 1)


    def UpdateNewFilenames(self):
        for i in range(0, len(self.pageNum)):
            name=self.fanzineNameTextbox.Value+self.fanzineIssuenumber.Value+self.grid.GetCellValue(i,1)
            self.grid.SetCellValue(i, 2, name+".jpg")
            self.grid.SetCellBackgroundColour(i, 2, wx.Colour(255,230,230) if len(name) > 8 else wx.Colour(255,255,255))

    def OnFanzinenameOrIssueTextboxChanged(self, event):
        self.UpdateNewFilenames()

app = wx.App(False)
frame = MainWindow(None, "Sample editor")
app.MainLoop()