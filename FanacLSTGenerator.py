import os
import wx
import wx.grid
from GUIClass import GUIClass
from LSTFile import *

class MainWindow(GUIClass):
    def __init__(self, parent, title):
        GUIClass.__init__(self, parent)

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
        grid=self.gRowGrid

        # grid.HideRowLabels()

        # Add the column headers
        grid.SetColLabelValue(0, "First Page")
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
        # Inside that we have a top sizer for small controls and a second sizer below it for the gRowGrid.
        gbs=wx.GridBagSizer(4,2)

        self.Show(True)

    def OnSaveLSTFile(self, event):
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

    def OnLoadNewIssues(self, event):
        pass

    def OnGridCellKeyUp(self, event):
        i=0

    def OnTextTopMatter(self, event):
        pass

    def OnTextComments(self, event):
        pass

    def OnGridCellChanged(self, event):
        row=event.GetRow()
        col=event.GetCol()
        if col > 1:
            self.lstData.Rows[row][col-1]=self.gRowGrid.GetCellValue(row, col)
        else:
            self.lstData.Rows[row][0]=self.gRowGrid.GetCellValue(row, 0)+">"+self.gRowGrid.GetCellValue(row, 1)


app = wx.App(False)
frame = MainWindow(None, "Sample editor")
app.MainLoop()