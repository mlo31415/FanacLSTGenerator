import os
import wx
import wx.grid
import math
import sys
from GUIClass import GUIClass
from LSTFile import *
from LSTFile import CanonicizeColumnHeaders

def Bailout(e, s: str):
    ctypes.windll.user32.MessageBoxW(0, s, "Main error", 1)
    raise

class MainWindow(GUIClass):
    def __init__(self, parent, title):
        GUIClass.__init__(self, parent)

        self.highlightRows=[]       # A List of the names of fanzines in highlighted rows
        self.clipboard=None         # The grid's clipboard
        self.userSelection=None
        self.cntlDown=False
        self.rightClickedColumn=None

        self.dirname=''
        if len(sys.argv) > 1:
            self.dirname=os.getcwd()

        # Read the LST file
        self.LoadLSTFile()

        self.Show(True)

    #------------------
    # Given a LST file of disk load it into self
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
        dlg.SetWindowStyle(wx.STAY_ON_TOP)

        if dlg.ShowModal() != wx.ID_OK:
            dlg.Raise()
            dlg.Destroy()
            return

        self.lstFilename=dlg.GetFilename()
        self.dirname=dlg.GetDirectory()
        dlg.Destroy()

        # Read the lst file
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

        # And now determine the identities of the column headers. (There are many ways to label a column that amount to the same thing.)
        self.lstData.IdentifyColumnHeaders()

        # Insert the row data into the grid
        self.RefreshGridFromLSTData()


    #------------------
    def OnLoadNewLSTFile(self, event):
        self.LoadLSTFile()
        pass

    #------------------
    # The LSTFile object has the official information. This function refreshes the display from it.
    def RefreshGridFromLSTData(self):
        grid=self.gRowGrid
        grid.EvtHandlerEnabled=False
        grid.ClearGrid()

        # In effect, this makes all row and col references to data (as opposed to the labels) to be 1-based

        # Color all the column headers white before coloring the ones that actually exist gray.  (This handles cases where a column has been deleted.)
        for i in range(0, self.gRowGrid.NumberCols-1):
            self.gRowGrid.SetCellBackgroundColour(0, i, wx.WHITE)

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

        # Make the first grid column contain editable row numbers
        for i in range(1, grid.GetNumberRows()):
            grid.SetCellValue(i, 0, str(i))
            grid.SetCellBackgroundColour(i, 0, labelGray)
        grid.SetCellBackgroundColour(0, 0, labelGray)

        # Now insert the row data
        grid.AppendRows(len(self.lstData.Rows))
        i=1
        for row in self.lstData.Rows:
            j=1
            for cell in row:
                grid.SetCellValue(i, j, cell)
                j+=1
            i+=1

        # Set the proper highlighting.
        for i in range(0, len(self.lstData.Rows)):
            cellcolor=wx.Colour(255, 240, 240) if grid.GetCellValue(i+1, 2) in self.highlightRows else wx.Colour(255, 255, 255)
            for j in range(0, grid.GetNumberCols()):
                grid.SetCellBackgroundColour(i+1, j+1, cellcolor)

        grid.ForceRefresh()
        grid.AutoSizeColumns()
        grid.EvtHandlerEnabled=True


    #------------------
    # Save an LSTFile object to disk.
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


    #------------------
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

        self.RefreshGridFromLSTData()
        pass


    #------------------
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


    #------------------
    def OnTextTopMatter(self, event):
        self.lstData.FirstLine=self.tTopMatter.GetValue()

    #------------------
    def OnTextComments(self, event):
        self.lstData.TopTextLines=self.tPText.GetValue().split("\n")

    #------------------
    def OnGridCellDoubleclick(self, event):
        if event.GetRow() == 0 and event.GetCol() == 0:
            self.gRowGrid.AutoSize()
            return
        if event.GetRow() == 0 and event.GetCol() > 0:
            self.gRowGrid.AutoSizeColumn(event.GetCol())

    #------------------
    def OnGridCellRightClick(self, event):
        # Gray out the Past popup menu item if there is nothing to paste
        item_id=self.m_popupMenu1.FindItem("Paste")
        item=self.m_popupMenu1.FindItemById(item_id)
        item.Enabled=self.clipboard is not None and len(self.clipboard) > 0 and len(self.clipboard[0]) > 0  # Enable only if the clipboard contains actual content

        self.rightClickedColumn=event.Col
        self.SetPopupHighlight()
        self.PopupMenu(self.m_popupMenu1)


    #-------------------
    # Locate the selection, real or implied
    # There are three cases, in descending order of preference:
    #   There is a selection block defined
    #   There is a SelectedCells defined
    #   There is a GridCurso location
    def LocateSelection(self):
        if len(self.gRowGrid.SelectionBlockTopLeft) > 0 and len(self.gRowGrid.SelectionBlockBottomRight) > 0:
            top, left=self.gRowGrid.SelectionBlockTopLeft[0]
            bottom, right=self.gRowGrid.SelectionBlockBottomRight[0]
        elif len(self.gRowGrid.SelectedCells) > 0:
            top, left=self.gRowGrid.SelectedCells[0]
            bottom, right=top, left
        else:
            left=right=self.gRowGrid.GridCursorCol
            top=bottom=self.gRowGrid.GridCursorRow
        return top, left, bottom, right


    #-------------------
    def OnKeyDown(self, event):
        top, left, bottom, right=self.LocateSelection()

        if event.KeyCode == 67 and self.cntlDown:   # cntl-C
            self.CopyCells(top, left, bottom, right)
        elif event.KeyCode == 86 and self.cntlDown and self.clipboard is not None and len(self.clipboard) > 0: # cntl-V
            self.PasteCells(top, left)
        elif event.KeyCode == 308:                  # cntl
            self.cntlDown=True
        elif event.KeyCode == 68:                   # Kludge to be able to force a refresh
            self.RefreshGridFromLSTData()
        event.Skip()

    #-------------------
    def OnKeyUp(self, event):
        if event.KeyCode == 308:                    # cntl
            self.cntlDown=False

    #------------------
    def OnPopupCopy(self, event):
        # We need to copy the selected cells into the clipboard object.
        # (We can't simply store the coordinates because the user might edit the cells before pasting.)
        top, left, bottom, right=self.LocateSelection()
        self.CopyCells(top, left, bottom, right)
        event.Skip()

    #------------------
    def OnPopupPaste(self, event):
        top, left, bottom, right=self.LocateSelection()
        self.PasteCells(top, left)
        event.Skip()

    #------------------
    def OnPopupDeleteColumn(self, event):
        self.DeleteColumn(self.rightClickedColumn)
        event.Skip()

    #------------------
    def OnPopupExtractScanner(self, event):
        self.ExtractScanner(self.rightClickedColumn)
        event.Skip()

    #------------------
    def CopyCells(self, top, left, bottom, right):
        self.clipboard=[]
        # We must remember that the first two data columns map to a single LST column.
        for row in self.lstData.Rows[top-1: bottom]:
            self.clipboard.append(row[left-1: right])

    #------------------
    def SetPopupHighlight(self):
        if len(self.lstData.ColumnHeaders) <= self.rightClickedColumn-2:
            return

        menuItems=self.m_popupMenu1.GetMenuItems()
        for mi in menuItems:
            if mi.GetItemLabelText() == "Extract Scanner":
                mi.Enable(self.lstData.ColumnHeaders[self.rightClickedColumn-2] == "Notes")

    #------------------
    def PasteCells(self, top, left):
        # We paste the clipboard data into the block of the same size with the upper-left at the mouse's position
        # Might some of the new material be outside the current bounds?  If so, add some blank rows and/or columns

        # Define the bounds of the paste-to box
        pasteTop=top
        pasteBottom=top+len(self.clipboard)
        pasteLeft=left
        pasteRight=left+len(self.clipboard[0])

        # Does the paste-to box extend beyond the end of the available rows?  If so, extend the available rows.
        num=pasteBottom-len(self.lstData.Rows)-1
        if num > 0:
            for i in range(num):
                self.lstData.Rows.append(["" for x in range(len(self.lstData.Rows[0]))])  # The strange contortion is to append a list of distinct empty strings

        # Does the paste-to box extend beyond the right side of the availables? If so, extend the rows with more columns.
        num=pasteRight-len(self.lstData.Rows[0])-1
        if num > 0:
            for row in self.lstData.Rows:
                row.extend(["" for x in range(num)])

        # Copy the cells from the clipboard to the grid in lstData.
        i=pasteTop
        for row in self.clipboard:
            j=pasteLeft
            for cell in row:
                self.lstData.Rows[i-1][j-1]=cell  # The -1 is to deal with the 1-indexing
                j+=1
            i+=1
        self.RefreshGridFromLSTData()

    #------------------
    def DeleteColumn(self, col):
        # Some columns are sacrosanct
        # Column 0 is the row number and col 1 is the "first page" (computerd) column
        # We must subtract 2 from col because the real data only starts at the third column.
        col=col-2
        if col >= len(self.lstData.Rows[0]) or col < 0:
            return

        # For each row, delete the specified column
        # Note that the computed "first page" column *is* in lastData.Rows as it is editable
        for i in range(0, len(self.lstData.Rows)):
            row=self.lstData.Rows[i]
            newrow=[]
            if col > 0:
                newrow.extend(row[:col+1])
            if col < len(row)-3:
                newrow.extend(row[col+2:])
            self.lstData.Rows[i]=newrow

        # Now delete the column header
        del self.lstData.ColumnHeaders[col]

        # And redisplay
        self.RefreshGridFromLSTData()
        pass

    # ------------------
    def ExtractScanner(self, col):
        pass

    #------------------
    def OnGridCellChanged(self, event):
        row=event.GetRow()
        col=event.GetCol()
        newVal=self.gRowGrid.GetCellValue(row, col)

        # The first row is the column headers
        if row == 0:
            event.Veto()  # This is a bit of magic to prevent the event from making later changes to the grid.
            # Note that the Column Headers is offset by *2*. (The first column is the row number column and is blank; the second is the weird filename thingie and is untitled.)
            if len(self.lstData.ColumnHeaders)+1 < col:
                self.lstData.ColumnHeaders.extend(["" for x in range(col-len(self.lstData.ColumnHeaders)-1)])
            self.lstData.ColumnHeaders[col-2]=newVal
            if len(self.lstData.ColumnHeaderTypes)+1 < col:
                self.lstData.ColumnHeaderTypes.extend(["" for x in range(col-len(self.lstData.ColumnHeaderTypes)-1)])
            self.lstData.ColumnHeaderTypes[col-2]=CanonicizeColumnHeaders(newVal)
            self.RefreshGridFromLSTData()
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
            event.Veto()                # This is a bit of magic to prevent the event from making later changes to the grid.
            self.RefreshGridFromLSTData()
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
        event.Veto()  # This is a bit of magic to prevent the event from making later changed to the grid.
        self.RefreshGridFromLSTData()
        return


    #------------------
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


# Start the GUI and run the event loop
app = wx.App(False)
frame = MainWindow(None, "Sample editor")
app.MainLoop()
