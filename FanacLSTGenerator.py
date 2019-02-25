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

        # The grid is a bit non-standard, since I want to be able to edit row numbers
        # The row labels are actually the (editable) 1st column f the spreadsheet and the row labels are hidden.
        grid.HideRowLabels()

        # Add the column headers
        grid.SetColLabelValue(0, "")
        grid.SetColLabelValue(1, "First Page")
        i=2
        for colhead in self.lstData.ColumnHeaders:
            grid.SetColLabelValue(i, colhead)
            i+=1

        # Now insert the row data
        grid.AppendRows(len(self.lstData.Rows))
        i=0
        for row in self.lstData.Rows:
            j=2
            for cell in row:
                grid.SetCellValue(i, j, cell)
                j+=1
            i+=1

        # Make the first column contain editable row numbers
        for i in range(1, grid.GetNumberRows()):
            grid.SetCellValue(i, 0, str(i))
            grid.SetCellBackgroundColour(i,0, wx.NamedColour("light grey"))

        # We need to split the contents of col 2 into two parts, one for col 1 and the rest for col 2
        for i in range(0, len(self.lstData.Rows)):
            val=grid.GetCellValue(i, 2).split(">")
            grid.SetCellValue(i, 1, val[0])
            grid.SetCellValue(i, 2, val[1])

        grid.AutoSizeColumns()

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

    def OnTextTopMatter(self, event):
        pass

    def OnTextComments(self, event):
        pass

    def OnGridCellChanged(self, event):
        row=event.GetRow()
        col=event.GetCol()

        # The first three columns are special.  So start by dealing with the ordinary cases
        if col > 2:
            self.lstData.Rows[row][col-2]=self.gRowGrid.GetCellValue(row, col)
            return
        if col == 2 or col == 1:
            self.lstData.Rows[row][0]=self.gRowGrid.GetCellValue(row, 1)+">"+self.gRowGrid.GetCellValue(row, 2)
            return
        # This is tricky. We need to confirm that the user entered a new number.  (If not, we restore the old one and we're done.)
        # If there is a new number, we re-arrange the rows and then renumber them.
        try:
            newnum=float(self.gRowGrid.GetCellValue(row, col))
        except:
            self.gRowGrid.SetCellValue(row, 0, str(row))
            return

        # Determine the new position of this row and rearrange the rows accordingly.



app = wx.App(False)
frame = MainWindow(None, "Sample editor")
app.MainLoop()