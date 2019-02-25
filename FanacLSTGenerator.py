import os
import wx
import wx.grid
import math
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

        # Fill in the upper stuff
        self.tTopMatter.SetValue(self.lstData.FirstLine)
        if len(self.lstData.TopTextLines) > 0:
            self.tPText.SetValue("\n".join(self.lstData.TopTextLines))

        # The grid is a bit non-standard, since I want to be able to edit row numbers and column headers
        # The row and column labels are actually the (editable) 1st column and 1st row of the spreadsheet and the "real" row and column labels are hidden.
        self.gRowGrid.HideRowLabels()
        self.gRowGrid.HideColLabels()
        # In effect, this makes all row and col references to data (as opposed to to labels) to be 1-based

        headerGray=wx.Colour(230, 230, 230)

        # Add the column headers
        self.gRowGrid.SetCellValue(0, 0, "")
        self.gRowGrid.SetCellValue(0, 1, "First Page")
        i=2
        for colhead in self.lstData.ColumnHeaders:
            self.gRowGrid.SetCellValue(0, i, colhead)
            self.gRowGrid.SetCellBackgroundColour(0, i, headerGray)
            i+=1
        self.gRowGrid.SetCellBackgroundColour(0, 0, headerGray)
        self.gRowGrid.SetCellBackgroundColour(0, 1, headerGray)

        # Insert the row data into the grid
        self.RefreshDataRows(self.gRowGrid)

        self.gRowGrid.AutoSizeColumns()

        self.Show(True)

    def RefreshDataRows(self, grid):
        headerGray=wx.Colour(230, 230, 230)
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
        self.lstData.FirstLine=self.tTopMatter.GetValue()

    def OnTextComments(self, event):
        self.lstData.TopTextLines=self.tPText.GetValue().split("\n")

    def OnGridCellDoubleclick(self, event):
        if event.GetRow() == 0 and event.GetCol() == 0:
            self.gRowGrid.AutoSize()
            return
        if event.GetRow() == 0 and event.GetCol() > 0:
            self.gRowGrid.AutoSizeColumn(event.GetCol())


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

        # So the user is editing a row number
        # This is tricky. We need to confirm that the user entered a new number.  (If not, we restore the old one and we're done.)
        # If there is a new number, we re-arrange the rows and then renumber them.
        try:
            newnumf=float(self.gRowGrid.GetCellValue(row, col))
        except:
            self.gRowGrid.SetCellValue(row, 0, str(row))
            return
        newnumf-=0.00001    # when the user supplies an integer, we drop it just before that integer

        # The indexes the user sees start with 1, but the rows list is 0-based.  Adjust accordingly.
        oldrow=row-1

        # We *should* have a fractional value or an integer value out of range. Check for this.
        newrows=[]
        if newnumf < 0:
            # Ok, it's being moved to the beginning
            newrows.append(self.lstData.Rows[oldrow])
            newrows.extend(self.lstData.Rows[0:oldrow])
            newrows.extend(self.lstData.Rows[oldrow+1:])
        elif newnumf > len(self.lstData.Rows):
            # OK, it's being moved to the end
            newrows.extend(self.lstData.Rows[0:oldrow])
            newrows.extend(self.lstData.Rows[oldrow+1:])
            newrows.append(self.lstData.Rows[oldrow])
        else:
            # OK, it've being moved internally
            newrow=math.ceil(newnumf)-1
            if row <= newrow:
                # Moving later
                newrows.extend(self.lstData.Rows[0:oldrow])
                newrows.extend(self.lstData.Rows[oldrow+1:newrow])
                newrows.append(self.lstData.Rows[oldrow])
                newrows.extend(self.lstData.Rows[newrow:])
            else:
                # Moving earlier
                newrows.extend(self.lstData.Rows[0:newrow])
                newrows.append(self.lstData.Rows[oldrow])
                newrows.extend(self.lstData.Rows[newrow:oldrow])
                newrows.extend(self.lstData.Rows[oldrow+1:])
        self.lstData.Rows=newrows
        self.RefreshDataRows(self.gRowGrid)


app = wx.App(False)
frame = MainWindow(None, "Sample editor")
app.MainLoop()