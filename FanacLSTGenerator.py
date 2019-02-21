# Pubs1 Main.
import os
import wx
import wx.grid

class MainWindow(wx.Frame):
    def __init__(self, parent, title):
        wx.Frame.__init__(self, parent, title=title, size=(400,300))
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

        # Create a wxGrid object
        self.grid=grid=wx.grid.Grid()
        # Then we call CreateGrid to set the dimensions of the grid
        # (100 rows and 10 columns in this example)
        grid.Create(panel)
        grid.CreateGrid(1, 10)
        grid.SetDefaultColSize(50, True)
        grid.SetDefaultRowSize(20, True)

        grid.HideRowLabels()
        grid.EnableGridLines(False)

        grid.AppendRows(grid.GetNumberCols())
        for i in range(1, grid.GetNumberCols()):
            grid.SetColLabelValue(i, "")
        grid.SetColLabelValue(0, "Filename")
        grid.SetColLabelValue(1, "Page")
        grid.SetColLabelValue(2, "New name")
        grid.AutoSizeColumns()

        # Let's lay out the space.  We fill the panel with a vertical sizer so things in it are stcked vertically.
        # Inside that we have a top sizer for small controls and a secon sizer below it for the grid.
        gbs=wx.GridBagSizer(4,2)

        # The top gridbag row gets buttons
        self.buttonLoad=wx.Button(panel, id=wx.ID_ANY, label="Load")
        gbs.Add(self.buttonLoad, (0,0))
        self.buttonLoad.Bind(wx.EVT_BUTTON, self.OnLoadButtonClicked)
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

        # And the grid itself goes in the bottom gridbag row, spanning both columns
        gbs.Add(grid, (3,0), span=(2,2))

        panel.SetSizerAndFit(gbs)

        self.Show(True)


    def OnLoadButtonClicked(self, event):
        if event.EventObject.Label == "Load":
            self.dirname=''
            dlg=wx.FileDialog(self, "Select pages", self.dirname, "", "*.*", wx.FD_OPEN|wx.FD_MULTIPLE)
            if dlg.ShowModal() == wx.ID_OK:
                self.selectedfiles=dlg.GetFilenames()
                self.dirname=dlg.GetDirectory()
            dlg.Destroy()
            if len(self.selectedfiles) == 0:
                return

            # Add rows to the grid if needed.
            self.grid.AppendRows(len(self.selectedfiles))

            # Fill in the grid with the filenames
            i=0
            for name in self.selectedfiles:
                self.grid.SetCellValue(i, 0, name)
                i+=1
                self.grid.AutoSizeColumns()

            # We expect that filename will be in three sections:
            #   A prefix common to all which is the fanzine name
            #   Followed by an issue designation
            #   Followed by a page which is either pnnn or fc or bc or ifc, or ibc (no internal spaces, though)
            # Divide up the name into its components and display them
            # Start by looking for the last token in each name
            self.pageNum=[]
            rest=[]
            for name in self.selectedfiles:
                self.pageNum.append(name.split()[-1:][0])
                rest.append(" ".join(name.split()[:-1]))
            for i, val in enumerate(self.pageNum):
                val=os.path.splitext(val)[0]        # Drop the extension
                if val[0] == 'p': val=val[1:]       # Drop any leading 'p'
                self.grid.SetCellValue(i, 1, val)
            self.grid.AutoSizeColumns()

            # Find the leading string common to all of the files.  It is probably the fanzine's name followed by the fanzine's issue number
            # The page number will be different from one scan to the next.
            # We will break each filename up into whitespace-delimited tokens, and first determine the common set of leading tokens.  This will drop the page numbers.
            list=[]
            for name in self.selectedfiles:
                list.append(name.split())
            leadingTokens=[]
            for i in range(0, len(list[0])):
                t=list[0][i]
                failed=False
                for tokens in list:
                    if tokens[i] != t:
                        failed=True
                        break
                if failed:
                    break
                leadingTokens.append(t)

            if len(leadingTokens) < 1:
                return

            # Normally, the last token is the issue number
            self.fanzineNameTextbox.SetValue(" ".join(leadingTokens[:-1]))
            fn=leadingTokens[-1:][0]
            if fn[0] == "#":
                fn=fn[1:]
            self.fanzineIssuenumber.SetValue(fn)
            self.UpdateNewFilenames()
            self.grid.AutoSizeColumns()

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