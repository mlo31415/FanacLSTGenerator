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

        # The grid is a bit non-standard, since I want to be able to edit row numbers and column headers
        # The row and column labels are actually the (editable) 1st column and 1st row of the spreadsheet and the "real" row and column labels are hidden.
        grid.HideRowLabels()
        grid.HideColLabels()
        # In effect, this makes all row and col references to data (as opposed to to labels) being 1-based

        headerGray=wx.Colour(240, 240, 240)

        # Add the column headers
        grid.SetCellValue(0, 0, "")
        grid.SetCellValue(0, 1, "First Page")
        i=2
        for colhead in self.lstData.ColumnHeaders:
            grid.SetCellValue(0, i, colhead)
            grid.SetCellBackgroundColour(0, i, headerGray)
            i+=1
        grid.SetCellBackgroundColour(0, 0, headerGray)

        # Make the first column contain editable row numbers
        for i in range(1, grid.GetNumberRows()):
            grid.SetCellValue(i, 0, str(i))
            grid.SetCellBackgroundColour(i, 0, headerGray)
        grid.SetCellBackgroundColour(0, 0, headerGray)

        # Now insert the row data (except for the first col from the LST file which we'll deal with next)
        grid.AppendRows(len(self.lstData.Rows))
        i=0
        for row in self.lstData.Rows:
            j=1
            for cell in row:
                grid.SetCellValue(i+1, j+1, cell)
                j+=1
            i+=1

        # We need to split the contents of col 2 into two parts, one for col 1 and the rest for col 2
        for i in range(0, len(self.lstData.Rows)):
            val=grid.GetCellValue(i+1, 2).split(">")
            grid.SetCellValue(i+1, 1, val[0])
            grid.SetCellValue(i+1, 2, val[1])

        grid.AutoSizeColumns()

        self.Show(True)

    def OnSaveLSTFile(self, event):
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