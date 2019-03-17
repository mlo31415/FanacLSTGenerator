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

        # Read the LST file
        self.lstData=LSTFile()
        self.lstData.Read(self.lstFilename)

        # Fill in the upper stuff
        self.tTopMatter.SetValue(self.lstData.FirstLine)
        if len(self.lstData.TopTextLines) > 0:
            self.tPText.SetValue("\n".join(self.lstData.TopTextLines))

        # The grid is a bit non-standard, since I want to be able to edit row numbers and column headers
        # The row and column labels are actually the (editable) 1st column and 1st row of the spreadsheet (they're colored gray)
        # and the "real" row and column labels are hidden.
        self.gRowGrid.HideRowLabels()
        self.gRowGrid.HideColLabels()
        # In effect, this makes all row and col references to data (as opposed to the labels) to be 1-based

        labelGray=wx.Colour(230, 230, 230)

        # Add the column headers
        self.gRowGrid.SetCellValue(0, 0, "")
        self.gRowGrid.SetCellValue(0, 1, "First Page")
        i=2
        for colhead in self.lstData.ColumnHeaders:
            self.gRowGrid.SetCellValue(0, i, colhead)
            self.gRowGrid.SetCellBackgroundColour(0, i, labelGray)
            i+=1
        self.gRowGrid.SetCellBackgroundColour(0, 0, labelGray)
        self.gRowGrid.SetCellBackgroundColour(0, 1, labelGray)

        # And now determine the identities of the column headers. (There are many ways to label a column that amount to the same thing.)
        self.lstData.IdentifyColumnHeaders()

        # Insert the row data into the grid
        self.RefreshDataRows()

        self.gRowGrid.AutoSizeColumns()

        self.Show(True)


    def RefreshDataRows(self):
        grid=self.gRowGrid
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
        content=[self.lstData.FirstLine, ""]
        if len(self.lstData.TopTextLines) > 0:
            for line in self.lstData.TopTextLines:
                content.append(line)
            content.append("")
        content.append("; ".join(self.lstData.ColumnHeaders))
        content.append("")
        for row in self.lstData.Rows:
            content.append("; ".join(row))

        # Temporarily write the LST file with a "-1" at the end of the name
        newname=os.path.join(self.dirname, os.path.splitext(self.lstFilename)[0]+"-1.LST")
        # And write it out
        with open(newname, "w+") as f:
            f.writelines([c+"\n" for c in content])


    # We load a bunch of files, including one or more.issue files.
    # The .issue files tell us what image files we have present.
    # Add one row for each .issue file
    def OnLoadNewIssues(self, event):
        # Call the File Open dialog to get the .issue files
        self.dirname=''
        dlg=wx.FileDialog(self, "Select .issue files to load", self.dirname, "", "*.issue", wx.FD_OPEN|wx.FD_MULTIPLE)
        if dlg.ShowModal() != wx.ID_OK:
            dlg.Destroy()
            return
        files=dlg.GetFilenames()
        dlg.Destroy()
        for file in files:
            # Decode the file name to get the row info.
            # The filename consists of:
            #       A first section (ending in $$) which is the prefix of the associated image files
            #       A number of space-delimited segments consisting of a capital letter followed by data
            row=self.DecodeIssueFileName(file)
            bestColTypes=self.lstData.GetInsertCol(row)
            fIndex=self.lstData.GetBestRowIndex(bestColTypes, row)  # "findex" to remind me this is probably a floating point number to indicate an insertion between two rows
            self.lstData.Rows.append(row)
            self.MoveRow(len(self.lstData.Rows)-1, fIndex)

        self.RefreshDataRows()
        pass


    def DecodeIssueFileName(self, filename: str):
        if filename is None or len(filename) == 0:
            return None

        # Start by dividing on the "$$"
        sections=filename.split("$$")
        if len(sections) != 2:
            return None
        namePrefix=sections[0].strip()

        # Now remove the extension and divide the balance of the name by spaces
        balance=os.path.splitext(sections[1])[0]    # Get the filename and then drop the extension
        rest: list  # Type hint
        rest=[r for r in balance.split(" ") if len(r) > 0]

        # We have the table of column headers types in lstData.ColumnHeaderTypes
        # Match them up and create the new row with the right stuff in each column.
        row=[""]*len(self.lstData.ColumnHeaders)    # Create an empty list of the correct size
        for val in rest:
            if len(val) > 1:
                valtype=val[0]
                val=val[1:]     # The value is the part after the initial character (which is the val type)
                if not valtype.isupper():
                    continue
                try:
                    index=self.lstData.ColumnHeaderTypes.index(valtype)
                    row[index]=val
                except:
                    pass    # Just ignore the error
        row[0]=">"+namePrefix
        return row


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
        newVal=self.gRowGrid.GetCellValue(row, col)

        # The first row is the column headers
        if row == 0:
            self.lstData.ColumnHeaders[col-2]=newVal
            return

        # Columns 3 and later are ordinary colums. Just accept whatever edit is made.
        if col > 2:
            self.lstData.Rows[row-1][col-2]=newVal
            return

        # Columns 1 and 2 are the name and coded name. They are stored separately in lstData and thus need to be handled separately.
        if col == 2 or col == 1:
            self.lstData.Rows[row-1][0]=self.gRowGrid.GetCellValue(row, 1)+">"+self.gRowGrid.GetCellValue(row, 2)
            return

        # What's left is column zero and thus the user is editing a row number
        # If it's an "X", the row has been deleted.
        if newVal.lower() == "x":
            del self.lstData.Rows[row-1]
            return

        # If it's a number, it is tricky. We need to confirm that the user entered a new number.  (If not, we restore the old one and we're done.)
        # If there is a new number, we re-arrange the rows and then renumber them.
        try:
            newnumf=float(newVal)
        except:
            self.gRowGrid.SetCellValue(row, 0, str(row))    # Restore the old value
            return
        newnumf-=0.00001    # When the user supplies an integer, we drop the row *just* before that integer. No overwriting!

        # The indexes the user sees start with 1, but the rows list is 0-based.  Adjust accordingly.
        oldrow=row-1

        # We *should* have a fractional value or an integer value out of range. Check for this.
        self.MoveRow(oldrow, newnumf)
        self.RefreshDataRows()
        return


    def MoveRow(self, oldrow, newnumf):
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
            if oldrow < newrow:
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


app = wx.App(False)
frame = MainWindow(None, "Sample editor")
app.MainLoop()