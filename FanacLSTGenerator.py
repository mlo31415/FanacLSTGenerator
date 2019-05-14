import os
import wx
import wx.grid
import math
import sys
from GUIClass import GUIClass
from LSTFile import *

def Bailout(e, s: str):
    ctypes.windll.user32.MessageBoxW(0, s, "Main error", 1)
    raise

class MainWindow(GUIClass):
    def __init__(self, parent, title):
        GUIClass.__init__(self, parent)

        self.highlightRows=[]       # A List of the names of fanzines in highlighted rows
        self.clipboard=None         # The grid's clipboard
        self.userSelection=None

        self.dirname=''
        if len(sys.argv) > 1:
            self.dirname=os.getcwd()

        # Read the LST file
        self.LoadLSTFile()

        self.Show(True)

    # Given a LST file loaded into self
    def LoadLSTFile(self):

        # Clear out any old information
        self.lstData=LSTFile()
        self.tTopMatter.SetValue("")
        self.tPText.SetValue("")
        for i in range(0, self.gRowGrid.NumberCols):
            for j in range(0, self.gRowGrid.NumberRows):
                self.gRowGrid.SetCellValue(j, i, "")

        # Call the File Open dialog to get an LST file
        dlg=wx.FileDialog(self, "Select LST file to load", self.dirname, "", "*.LST", wx.FD_OPEN)
        if dlg.ShowModal() != wx.ID_OK:
            dlg.Destroy()
            return

        self.lstFilename=dlg.GetFilename()
        self.dirname=dlg.GetDirectory()
        dlg.Destroy()

        try:
            pathname=os.path.join(self.dirname, self.lstFilename)
            self.lstData.Read(pathname)
        except Exception as e:
            Bailout(e, "MainWindow: Failure reading LST file '"+pathname+"'")

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


    def OnLoadNewLSTFile(self, event):
        self.LoadLSTFile()
        pass


    def RefreshDataRows(self):
        grid=self.gRowGrid
        headerGray=wx.Colour(230, 230, 230)
        # Make the first grid column contain editable row numbers
        for i in range(1, grid.GetNumberRows()):
            grid.SetCellValue(i, 0, str(i))
            grid.SetCellBackgroundColour(i, 0, headerGray)
        grid.SetCellBackgroundColour(0, 0, headerGray)

        # Now insert the row data
        grid.AppendRows(len(self.lstData.Rows))
        i=0
        for row in self.lstData.Rows:
            j=0
            for cell in row:
                grid.SetCellValue(i+1, j+1, cell)
                j+=1
            i+=1
        # Set the proper highlighting.
        for i in range(0, len(self.lstData.Rows)):
            cellcolor=wx.Colour(255, 240, 240) if grid.GetCellValue(i+1, 2) in self.highlightRows else wx.Colour(255, 255, 255)
            for j in range(0, grid.GetNumberCols()):
                grid.SetCellBackgroundColour(i+1, j+1, cellcolor)


    def OnSaveLSTFile(self, event):
        try:
            # Rename the old file
            oldname=os.path.join(self.dirname, self.lstFilename)
            newname=os.path.join(self.dirname, os.path.splitext(self.lstFilename)[0]+"-old.LST")
            i=0
            while os.path.exists(newname):
                i+=1
                newname=os.path.join(self.dirname, os.path.splitext(self.lstFilename)[0]+"-old-"+str(i)+".LST")

            os.rename(oldname, newname)
        except:
            Bailout(PermissionError, "OnSaveLSTFile fails when trying to rename "+oldname+" to "+newname)

        try:
            self.lstData.Save(oldname)
        except:
            Bailout(PermissionError, "OnSaveLSTFile fails when trying to write file "+newname)


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
            self.highlightRows.append(row[0][1:])   # Add this row's fanzine name to the list of newly-added rows.

        self.RefreshDataRows()
        pass


    def DecodeIssueFileName(self, filename: str):
        if filename is None or len(filename) == 0:
            return None

        # Start by dividing on the "$$"
        sections=filename.split("$$")
        if len(sections) != 2:
            Bailout(ValueError, "FanacLSTGenerator.DecodeIssueFileName: Missing $$ in '"+filename+"'")
        namePrefix=sections[0].strip()

        # Now remove the extension and divide the balance of the name by spaces
        balance=os.path.splitext(sections[1])[0]    # Get the filename and then drop the extension
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
                    pass    # Just ignore the error and the column
        row[0]=namePrefix
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

    def OnGridCellRightClick(self, event):
        # Gray out the Past popup menu item if there is nothing to paste
        item_id=self.m_popupMenu1.FindItem("Paste")
        item=self.m_popupMenu1.FindItemById(item_id)
        item.Enabled=self.clipboard is not None and len(self.clipboard) > 0 and len(self.clipboard[0]) > 0  # Enable only if the clipboard contains actual content

        self.PopupMenu(self.m_popupMenu1)

    def OnPopupCopy(self, event):
        # We need to copy the selected cells into the clipboard object.
        # (We can't simply store the coordinates because the user might edit the cells before pasting.)
        self.clipboard=[]
        if len(self.gRowGrid.SelectedCells) == 0:
            topleft=self.gRowGrid.SelectionBlockTopLeft[0]
            bottomright=self.gRowGrid.SelectionBlockBottomRight[0]
        else:
            topleft=bottomright=self.gRowGrid.SelectedCells[0]
        # We must remember that the first two data columns map to a single LST column.

        for row in self.lstData.Rows[topleft[0]-1 : bottomright[0]]:
            self.clipboard.append(row[topleft[1]-1 : bottomright[1]])

        event.Skip()

    def OnPopupPaste(self, event):
        # We paste the clipboard data into the block of the save size with the upper-left at the mouse's position
        i=self.gRowGrid.GridCursorRow
        for row in self.clipboard:
            j=self.gRowGrid.GridCursorCol
            for cell in row:
                self.lstData.Rows[i][j]=cell
                j+=1
            i+=1

        self.RefreshDataRows()
        event.Skip()

    def OnGridRangeSelect(self, event):
        if event.TopRow != 0 or event.LeftCol != 0 or event.BottomRow+1 != event.EventObject.NumberRows or event.RightCol+1 != event.EventObject.NumberCols:
            self.userSelection=(event.TopRow, event.LeftCol, event.BottomRow, event.RightCol)
            print("select: ("+str(event.TopRow)+", "+str(event.LeftCol)+") -- ("+str(event.BottomRow)+", "+str(event.RightCol)+")")
            if len(self.gRowGrid.SelectedCells) == 0:
                topleft=self.gRowGrid.SelectionBlockTopLeft[0]
                bottomright=self.gRowGrid.SelectionBlockBottomRight[0]
            else:
                topleft=bottomright=self.gRowGrid.SelectedCells[0]
            print("        ("+str(topleft[0])+", "+str(topleft[1])+") -- ("+str(bottomright[0])+", "+str(bottomright[1])+")")


    def OnGridCellChanged(self, event):
        row=event.GetRow()
        col=event.GetCol()
        newVal=self.gRowGrid.GetCellValue(row, col)

        # The first row is the column headers
        if row == 0:
            self.lstData.ColumnHeaders[col-2]=newVal
            return

        # If we're entering data in a new row or a new column, append the necessary number of new rows of columns to lstData
        while row > len(self.lstData.Rows):
            self.lstData.Rows.append([""])

        while col > len(self.lstData.Rows[row-1]):
            self.lstData.Rows[row-1].append("")

        # Ordinary columns
        if col > 0:
            self.lstData.Rows[row-1][col-1]=newVal
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
