from __future__ import annotations
from typing import Union, Optional

import os
import wx
import wx.grid
import sys

from GenGUIClass import MainFrame

from WxDataGrid import DataGrid, Color, GridDataSource, ColDefinition, ColDefinitionsList, GridDataRowClass
from LSTFile import *
from HelpersPackage import Bailout
from Log import LogOpen, Log

class MainWindow(MainFrame):
    def __init__(self, parent, title):
        MainFrame.__init__(self, parent)
        self._dataGrid: DataGrid=DataGrid(self.wxGrid)
        self._dataGrid.Datasource=FanzineTablePage()

        # TODO: How many of these are duplicated in WxDataGrid?
        self.highlightRows: list[str]=[]       # A List of the names of fanzines in highlighted rows
        self.clipboard=None         # The grid's clipboard
        self.userSelection=None
        self.cntlDown: bool=False
        self._dataGrid.clickedColumn=None

        self.dirname=''
        if len(sys.argv) > 1:
            self.dirname=os.getcwd()

        self.stdColHeaders: ColDefinitionsList=ColDefinitionsList([
                                                              ColDefinition("Filename", Type="str"),
                                                              ColDefinition("Issue", Type="str"),
                                                              ColDefinition("Title", Type="str", preferred="Issue"),
                                                              ColDefinition("Whole", Type="int", Width=75),
                                                              ColDefinition("WholeNum", Type="int", Width=75, preferred="Whole"),
                                                              ColDefinition("Vol", Type="int", Width=50),
                                                              ColDefinition("Volume", Type="int", Width=50, preferred="Vol"),
                                                              ColDefinition("Num", Type="int", Width=50),
                                                              ColDefinition("Numver", Type="int", Width=50, preferred="Num"),
                                                              ColDefinition("Month", Type="str", Width=75),
                                                              ColDefinition("Day", Type="int", Width=50),
                                                              ColDefinition("Year", Type="int", Width=50),
                                                              ColDefinition("Pages", Type="int", Width=50),
                                                              ColDefinition("PDF", Type="str", Width=50),
                                                              ColDefinition("Notes", Type="str", Width=120),
                                                              ColDefinition("Scanned", Type="str", Width=100),
                                                              ColDefinition("APA", Type="str", Width=100),
                                                              ColDefinition("Country", Type="str", Width=50),
                                                              ColDefinition("Editor", Type="str", Width=75),
                                                              ColDefinition("Author", Type="str", Width=75),
                                                              ColDefinition("Mailing", Type="str", Width=75),
                                                              ColDefinition("Repro", Type="str", Width=75)
                                                              ])
        # Read the LST file
        lstfile=self.LoadLSTFile()
        if lstfile is None:
            return

        self.InitializeDatasourceFromLSTfile(lstfile)
        self._dataGrid.RefreshWxGridFromDatasource()
        self.MarkAsSaved()
        self.RefreshWindow()

        self.Show(True)

    #------------------
    # Open a dialog to allow the user to select an LSTFile on disk.
    # Load it (and some other stuff) into self's 'LSFFile() object
    def LoadLSTFile(self) -> Optional[LSTFile]:

        # Call the File Open dialog to get an LST file
        dlg=wx.FileDialog(self, "Select LST file to load", self.dirname, "", "*.LST", wx.FD_OPEN)
        dlg.SetWindowStyle(wx.STAY_ON_TOP)

        if dlg.ShowModal() != wx.ID_OK:
            dlg.Raise()
            dlg.Destroy()
            return None

        # Clear out old information from form.
        self.ClearDisplay()
        lstfile=LSTFile()

        self.lstFilename=dlg.GetFilename()
        self.dirname=dlg.GetDirectory()
        dlg.Destroy()

        # Read the lst file
        pathname=os.path.join(self.dirname, self.lstFilename)
        try:
            lstfile.Read(pathname)
        except Exception as e:
            Log(f"MainWindow: Failure reading LST file '{pathname}'", isError=True)
            Bailout(e, f"MainWindow: Failure reading LST file '{pathname}'", "LSTError")

        # Fill in the upper stuff
        self.tTopMatter.SetValue(lstfile.FirstLine)
        if len(lstfile.TopTextLines) > 0:
            self.tPText.SetValue("\n".join(lstfile.TopTextLines))
        elif len(lstfile.BottomTextLines) > 0:
            self.tPText.SetValue("\n".join(lstfile.BottomTextLines))

        # And now determine the identities of the column headers. (There are many ways to label a column that amount to the same thing.)
        lstfile.IdentifyColumnHeaders()

        return lstfile


    # Take the LST file which has been loaded into self.lstData and fill the Datasource
    def InitializeDatasourceFromLSTfile(self, lstfile: LSTFile):

        # Turn the Column Headers into the grid's columns
        self._dataGrid.Datasource.ColDefs=ColDefinitionsList([])
        for name in lstfile.ColumnHeaders:
            if name in self.stdColHeaders:
                name=self.stdColHeaders[name].Preferred
                self._dataGrid.Datasource.ColDefs.append(self.stdColHeaders[name])
            else:
                self._dataGrid.Datasource.ColDefs.append(ColDefinition(name))

        # Copy the row data over into the Datasource class
        FTRList: list[FanzineTableRow]=[]
        for row in lstfile.Rows:
            if len(row) != len(self._dataGrid.Datasource.ColDefs):
                Log(f"Mismatched column count for Row={row}", isError=True)
                continue
            FTRList.append(FanzineTableRow(row))
        self._dataGrid.Datasource._fanzineList=FTRList


    #TODO: Either use this more widely or merge it in
    def ClearDisplay(self):
        self.tTopMatter.SetValue("")
        self.tPText.SetValue("")
        self.wxGrid.ClearGrid()

    # ------------------
    # The Datasource object has the official information. This function updates it from edits made on the display.
    def UpdateDatasourceFromWxGrid(self):

        #TODO: Need to pull in the header stuff?

        # Not all rows and all columns defined in the grid may be filled.  Compute the actual number of rows and columns
        ncols=len(self._dataGrid.Datasource.ColDefs)    # ncols must be at least this big.

        # Walk the rows from last to first looking for last row with content
        for i in range(self.wxGrid.NumberRows, 0, -1):
            found=False
            for j in range(self.wxGrid.NumberCols):
                if self.wxGrid.GetCellValue(i-1, j) != "":
                    found=True
                    break
            if found:
                nrows=i
                break

        # Walk the remaining columns (if any) from last to first looking for the last col with content
        for i in range(self.wxGrid.NumberCols, 0, -1):
            found=False
            for j in range(self.wxGrid.NumberRows):
                if j == ncols:
                    break
                if self.wxGrid.GetCellValue(i-1, j) != "":
                    found=True
                    break
            if found:
                ncols=i
                break

        # We don't need to copy column headers because the code which manages updates to the headers updates the ColDefinitionsList
        # Likewise, the ancilliary text box handling updates the datasource


    # Create a new LSTFile from the datasource
    def CreateLSTDataFromDatasource(self) -> LSTFile:

        lstfile=LSTFile()

        #TODO: Need to copy ancillary text box material
        #TODO: Need to copy column headers

        # Now copy the grid's cell contents to the LSTFile structure
        lstfile.Rows=[]
        for i in range(self._dataGrid.Datasource.NumRows):
            row=[None]*self._dataGrid.Datasource.NumCols
            for j in range(self._dataGrid.Datasource.NumCols):
                row[j]=self.wxGrid.GetCellValue(i, j)
            lstfile.Rows.append(row)

        return lstfile

# Need:
#     One place to hold loaded-in data.  LSTFile?
#     One way to clear the display
#     One way to load data from the datasource to the display
#     One way to update the datasource from the display

    #------------------
    # Load an LST file from disk into an LSTFile class
    def OnLoadNewLSTFile(self, event):
        self._dataGrid.NumCols=0
        self._dataGrid.DeleteRows(0, self._dataGrid.NumRows)
        self._dataGrid.Grid.ScrollLines(-999)   # Scroll down a long ways to show start of file

        lstfile=self.LoadLSTFile()
        if lstfile is None:
            return

        self.InitializeDatasourceFromLSTfile(lstfile)
        self._dataGrid.RefreshWxGridFromDatasource()
        self.MarkAsSaved()
        self.RefreshWindow()
        pass

    #------------------
    # Save an LSTFile object to disk.
    def OnSaveLSTFile(self, event):

        self.UpdateDatasourceFromWxGrid()
        lstfile=self.CreateLSTDataFromDatasource()

        # Fill in the upper stuff
        lstfile.FirstLine=self.tTopMatter.GetValue()
        lstfile.TopTextLines=self.tPText.GetValue().split()
        lstfile.BottomTextLines=self.tPText.GetValue().split()

        # Copy over the column headers
        lstfile.ColumnHeaders=self._dataGrid.Datasource.ColHeaders

        # Rename the old file
        oldname=os.path.join(self.dirname, self.lstFilename)
        newname=os.path.join(self.dirname, os.path.splitext(self.lstFilename)[0]+"-old.LST")
        try:
            i=0
            while os.path.exists(newname):
                i+=1
                newname=os.path.join(self.dirname, os.path.splitext(self.lstFilename)[0]+"-old-"+str(i)+".LST")

            os.rename(oldname, newname)
        except:
            Log(f"OnSaveLSTFile fails when trying to rename {oldname} to {newname}", isError=True)
            Bailout(PermissionError, f"OnSaveLSTFile fails when trying to rename {oldname} to {newname}", "LSTError")

        try:
            lstfile.Save(oldname)
        except:
            Log(f"OnSaveLSTFile failed while trying to save {oldname}", isError=True)
            Bailout(PermissionError, "OnSaveLSTFile failed when trying to write file "+oldname, "LSTError")


    def RefreshWindow(self)-> None:
        self._dataGrid.RefreshWxGridFromDatasource()

    # ----------------------------------------------
    # Used to determine if anything has been updated
    def Signature(self) -> int:
        #TODO: Add in the top stuff
        #stuff=self.ConInstanceName.strip()+self.ConInstanceTopText.strip()+self.ConInstanceFancyURL.strip()+self.Credits.strip()
        #return hash(stuff)+self._dataGrid.Signature()
        return self._dataGrid.Signature()

    def MarkAsSaved(self):
        self._initialSignature=self.Signature()

    def NeedsSaving(self):
        return self._initialSignature != self.Signature()

    #------------------
    def OnTextTopMatter(self, event):
        self.FirstLine=self.tTopMatter.GetValue()

    #------------------
    def OnTextComments(self, event):
        if self._dataGrid.Datasource.TopTextLines is not None and len(self._dataGrid.Datasource.TopTextLines) > 0:
            self._dataGrid.Datasource.TopTextLines=self.tPText.GetValue().split("\n")
        elif self._dataGrid.Datasource.BottomTextLines is not None and len(self._dataGrid.Datasource.BottomTextLines) > 0:
            self._dataGrid.Datasource.BottomTextLines=self.tPText.GetValue().split("\n")
        else:
            self._dataGrid.Datasource.TopTextLines=self.tPText.GetValue().split("\n")

    #-------------------
    def OnKeyDown(self, event):
        self._dataGrid.OnKeyDown(event) # Pass event to WxDataGrid to handle

    #-------------------
    def OnKeyUp(self, event):
        self._dataGrid.OnKeyUp(event) # Pass event to WxDataGrid to handle

    #------------------
    def OnGridCellChanged(self, event):
        self._dataGrid.OnGridCellChanged(event)  # Pass event handling to WxDataGrid

    #------------------
    def OnGridCellRightClick(self, event):
        # Do generic RMB on grid processing
        self._dataGrid.OnGridCellRightClick(event, self.m_GridPopup)

        # Call the RMB handler
        self.RMBHandler(True, event)

    # ------------------
    def OnGridLabelLeftClick(self, event):
        self._dataGrid.OnGridLabelLeftClick(event)

    #------------------
    def OnGridLabelRightClick(self, event):
        # Do generic RMB on grid processing
        self._dataGrid.OnGridCellRightClick(event, self.m_GridPopup)

        # Call the RMB handler
        self.RMBHandler(False, event)

    # RMB click handling for grid and grid label clicks
    def RMBHandler(self, isCellClick: bool, event):
        isLabelClick=not isCellClick

        # Everything remains disabled when we're outside the defined columns
        if self._dataGrid.clickedColumn > self._dataGrid.Datasource.NumCols:    # Click is outside populated columns.  The +1 is because of the split of the 1st column
            return
        if self._dataGrid.clickedRow > self._dataGrid.Datasource.NumRows:      # Click is outside the populated rows
            return
        if isCellClick and self._dataGrid.clickedColumn == 0:   # What's this for?
            return

        def Enable(name: str) -> None:
            mi=self.m_GridPopup.FindItemById(self.m_GridPopup.FindItem(name))
            if mi is not None:
                mi.Enable(True)

        if self._dataGrid.HasSelection():
            Enable("Copy")
            Enable("Clear Selection")

        if self._dataGrid.clipboard is not None:
            Enable("Paste")

        if self._dataGrid.clickedRow != -1:
            Enable("Delete Row(s)")

        # We enable the Add Column to Left item if we're on a column to the left of the first -- it can be off the right and a column will be added to the right
        if self._dataGrid.clickedColumn > 1:
            Enable("Insert Column to Left")
            if self._dataGrid.Datasource.Element.CanDeleteColumns:
                Enable("Delete Column(s)")

        # We enable the Add Column to right item if we're on any existing column
        if self._dataGrid.clickedColumn > 0:        # Can't insert columns between the 1st two
            Enable("Insert Column to Right")

        if self._dataGrid.clickedRow == -1: #Indicates we're on a column header
            Enable("Rename Column")

        # We only enable Extract Scanner when we're in the Notes column and there's something to extract.
        mi=self.m_GridPopup.FindItemById(self.m_GridPopup.FindItem("Extract Scanner"))
        if self._dataGrid.Datasource.ColDefs[self._dataGrid.clickedColumn].Preferred == "Notes":
            # We only want to enable the "Extract Scanner" item if the Notes column contains scanned by information
            for row in self._dataGrid.Datasource.Rows:
                note=row.Cells[self._dataGrid.clickedColumn].lower()
                if "scan by" in note or \
                        "scans by" in note or \
                        "scanned by" in note or \
                        "scanning by" in note or \
                        "scanned at" in note:
                    mi.Enable(True)


        # Pop the menu up.
        self.PopupMenu(self.m_GridPopup)

    # ------------------
    # Extract 'scanned by' information from the Notes column, if any
    def ExtractScanner(self, col):

        if "Notes" not in self._dataGrid.Datasource.ColDefs:
            return
        notesCol=self._dataGrid.Datasource.ColDefs.index("Notes")

        # Start by adding a Scanned column to the right of the Notes column, if needed. (We check to see if one already exists.)
        if "Scanned" not in self._dataGrid.Datasource.ColDefs:
            # Add the Scanned column if needed
            self._dataGrid.InsertColumn(notesCol, name="Scanned")

        scannedCol=self._dataGrid.Datasource.ColDefs.index("Scanned")
        notesCol=self._dataGrid.Datasource.ColDefs.index("Notes")

        # Now parse the notes looking for scanning information
        # Scanning Info will look like one of the four prefixes (Scan by, Scanned by, Scanned at, Scanning by) followed by
        #   two capitalized words
        #   or a capitalized word, then "Mc", then a capitalized word  (e.g., "Sam McDonald")
        #   or a capitalized word, then "Mac", then a capitalized word  (e.g., "Anne MacCaffrey")
        #   or "O'Neill"
        #   or a capitalized word, then a letter followed by a period, then a capitalized word  (e.g., "John W. Campbell")
        #   or a capitalized word followed by a number
        pattern=(
            "[sS](can by|cans by|canned by|canned at|canning by) ([A-Z][a-z]+) ("   # A variation of "scanned by" followed by a first name;
            #   This all followed by one of these:
            "(?:Mc|Mac|O')[A-Z][a-z]+|"     # Celtic names
            "[A-Z]\.[A-Z][a-z]+|"   # Middle initial
            "[A-Z][a-z]+|" # This needs to go last because it will ignore characters after it finds a match (with "Sam McDonald" it matches "Sam Mc")
            "[0-9]+)"       # Boskone 23
        )
        for i in range(self._dataGrid.Datasource.NumRows):
            row=self._dataGrid.Datasource.Rows[i]
            note=row[notesCol+1]
            m=re.search(pattern, note)
            if m is not None:
                row[scannedCol+1]=m.groups()[1]+" "+m.groups()[2]     # Put the matched name in the scanned
                note=re.sub(pattern, "", note)  # Delete the matched text from the note
                # Now remove leading and trailing spans of spaces and commas from the note.
                note=re.sub("^([ ,]*)", "", note)
                note=re.sub("([ ,]*)$", "", note)
                row[notesCol+1]=note

        # And redisplay
        self._dataGrid.RefreshWxGridFromDatasource()

    def OnPopupCopy(self, event):
        self._dataGrid.OnPopupCopy(event) # Pass event to WxDataGrid to handle

    def OnPopupPaste(self, event):
        self._dataGrid.OnPopupPaste(event) # Pass event to WxDataGrid to handle

    def OnPopupClearSelection(self, event):
        self._dataGrid.OnPopupClearSelection(event)

    def OnPopupDelCol(self, event):
        if self._dataGrid.Datasource.Element.CanDeleteColumns:
            self._dataGrid.DeleteSelectedColumns() # Pass event to WxDataGrid to handle
        event.Skip()

    def OnPopupDelRow(self, event):
        self._dataGrid.DeleteSelectedRows() # Pass event to WxDataGrid to handle
        event.Skip()

    def OnPopupRenameCol(self, event):
        self._dataGrid.OnPopupRenameCol(event) # Pass event to WxDataGrid to handle

        # Now we check the column header to see if it iss one of the standard header. If so, we use the std definition for that header
        # (We have to do this here because WxDataGrid doesn't know about header semantics.)
        icol=self._dataGrid.clickedColumn
        cd=self._dataGrid.Datasource.ColDefs[icol]
        if cd.Name in self.stdColHeaders:
            self._dataGrid.Datasource.ColDefs[icol]=self.stdColHeaders[cd.Name]
        self._dataGrid.RefreshWxGridFromDatasource()


    def OnPopupInsertColLeft(self, event):
        self._dataGrid.OnPopupInsertColLeft(event) # Pass event to WxDataGrid to handle

    def OnPopupInsertColRight(self, event):
        self._dataGrid.OnPopupInsertColRight(event) # Pass event to WxDataGrid to handle

    def OnPopupExtractScanner(self, event):
        self.ExtractScanner(self._dataGrid.Datasource.ColDefs.index("Notes"))
        #TODO: Add the needed code
        event.Skip()


# An individual file to be listed under a convention
# This is a single row
class FanzineTableRow(GridDataRowClass):

    def __init__(self, cells: list[str]):
        GridDataRowClass.__init__(self)
        self._cells: list[str]=cells

    def __str__(self):
        return str(self._cells)

    # Make a deep copy of a FanzineTableRow
    def Copy(self) -> FanzineTableRow:
        ftr=FanzineTableRow([])
        ftr._cells=self._cells
        return ftr

    def Signature(self) -> int:
        return sum([hash(x) for x in self._cells])

    # # Serialize and deserialize
    # def ToJson(self) -> str:
    #     d={"ver": 9,
    #        "_displayTitle": self._displayTitle,
    #        "_notes": self._notes,
    #        "_localpathname": self._localpathname,
    #        "_filename": self._localfilename,
    #        "_sitefilename": self._sitefilename,
    #        "_URL": self._URL,
    #        "_pages": self._pages,
    #        "_size": self._size}
    #     return json.dumps(d)
    #
    # def FromJson(self, val: str) -> FanzineTableRow:
    #     d=json.loads(val)
    #     self._displayTitle=d["_displayTitle"]
    #     self._notes=d["_notes"]
    #     self._localpathname=d["_localpathname"]
    #     self._localfilename=d["_filename"]
    #     self._size=d["_size"]
    #     if d["ver"] > 4:
    #         self._sitefilename=d["_sitefilename"]
    #     if d["ver"] <= 4 or self._sitefilename.strip() == "":
    #         self._sitefilename=self._displayTitle
    #     if d["ver"] > 6:
    #         self._pages=d["_pages"]
    #     if d["ver"] > 8:
    #         self._URL=d["_URL"]
    #     return self

    @property
    def CanDeleteColumns(self) -> bool:
        return True

    # This deletes a single column from the datasource.
    # It must be implemented here because WxDataGrid doesn't understand the details of the DataSource
    def DelCol(self, icol: int) -> None:
        del self._cells[icol]

    @property
    def Cells(self) -> str:
        return self._cells
    @Cells.setter
    def Cells(self, val: str) -> None:
        self._cells=val

    # Get or set a value by name or column number in the grid
    def GetVal(self, icol: int) -> Union[str, int, bool]:
        return self._cells[icol]

    def SetVal(self, icol: int, val: Union[str, int, bool]) -> None:
        self._cells[icol]=val

    @property
    def IsLinkRow(self) -> bool:
        return False            # Override only if needed

    @property
    def IsTextRow(self) -> bool:
        return False            # Override only if needed



#####################################################################################################
#####################################################################################################

class FanzineTablePage(GridDataSource):
    def __init__(self):
        GridDataSource.__init__(self)
        self._colDefs: ColDefinitionsList=ColDefinitionsList([])
        self._fanzineList: list[FanzineTableRow]=[]
        self._gridDataRowClass=FanzineTableRow
        self._name: str=""
        self._specialTextColor: Optional[Color, bool]=True
        self.TopTextLines: str=""
        self.BottomTextLines: str=""
        self.FirstLine=""

    # # Serialize and deserialize
    # def ToJson(self) -> str:
    #     dl=[]
    #     for con in self._fanzineList:
    #         dl.append(con.ToJson())
    #     d={"ver": 3,
    #        "_name": self._name,
    #        "_fanzineList": dl}
    #     return json.dumps(d)
    #
    # def FromJson(self, val: str) -> FanzineTablePage:
    #     d=json.loads(val)
    #     if d["ver"] >= 1:
    #         self._name=d["_name"]
    #         cfld=d["_fanzineList"]
    #         self._fanzineList=[]
    #         for c in cfld:
    #             self._fanzineList.append(FanzineTableRow().FromJson(c))
    #
    #     return self

    # Inherited from GridDataSource
    @property
    def Rows(self) -> list[FanzineTableRow]:
        return self._fanzineList

    @Rows.setter
    def Rows(self, rows: list) -> None:
        self._fanzineList=rows

    @property
    def NumRows(self) -> int:
        return len(self._fanzineList)

    def SetDataVal(self, irow: int, icol: int, val: Union[int, str]) -> None:
        self._fanzineList[irow].SetVal(icol, val)

    def GetData(self, iRow: int, iCol: int) -> str:
        return self.Rows[iRow].GetVal(iCol)

    @property
    def SpecialTextColor(self) -> Optional[Color]:
        return self._specialTextColor
    @SpecialTextColor.setter
    def SpecialTextColor(self, val: Optional[Color]) -> None:
        self._specialTextColor=val

    def CanAddColumns(self) -> bool:
        return True



def main():
    # Start the GUI and run the event loop
    LogOpen("Log -- FanacLSTGenerator.txt", "Log (Errors) -- FanacLSTGenerator.txt")
    app=wx.App(False)
    frame=MainWindow(None, "Sample editor")
    app.MainLoop()

if __name__ == "__main__":
    main()