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
from Settings import Settings

class MainWindow(MainFrame):
    def __init__(self, parent, title):
        MainFrame.__init__(self, parent)
        self._dataGrid: DataGrid=DataGrid(self.wxGrid)
        self.Datasource=FanzineTablePage()

        self._initialSignature=0
        self.lstFilename="Init value"
        self.dirname="Init value"

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

        self.dirname=''
        if len(sys.argv) > 1:
            self.dirname=os.getcwd()

        # Read the LST file
        lstfile=self.LoadLSTFile()
        if lstfile is None:
            return

        self.InitializeDatasourceFromLSTfile(lstfile)
        self._dataGrid.RefreshWxGridFromDatasource()

        # Fill in the upper stuff
        self.ClearDisplay()
        self.tTopMatter.SetValue(lstfile.FirstLine)
        if len(lstfile.TopTextLines) > 0:
            self.tPText.SetValue("\n".join(lstfile.TopTextLines))
        elif len(lstfile.BottomTextLines) > 0:
            self.tPText.SetValue("\n".join(lstfile.BottomTextLines))

        # Position the window on the screen it was on before
        tlwp=Settings().Get("Top Level Window Position")
        if tlwp is not None and len(tlwp) > 0:
            self.SetPosition(tlwp)
        tlws=Settings().Get("Top Level Windows Size")
        if tlws is not None and len(tlws) > 0:
            self.SetSize(tlws)

        self.MarkAsSaved()
        self.RefreshWindow()

        self.Show(True)

    @property
    def Datasource(self) -> FanzineTablePage:
        return self._Datasource
    @Datasource.setter
    def Datasource(self, val: FanzineTablePage):
        self._Datasource=val
        self._dataGrid.Datasource=val


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

        # And now determine the identities of the column headers. (There are many ways to label a column that amount to the same thing.)
        # lstfile.IdentifyColumnHeaders()

        return lstfile


    # Take the LST file which has been loaded into self.lstData and fill the Datasource
    def InitializeDatasourceFromLSTfile(self, lstfile: LSTFile):

        self._dataGrid.NumCols=0
        self._dataGrid.DeleteRows(0, self._dataGrid.NumRows)
        self._dataGrid.Grid.ScrollLines(-999)   # Scroll down a long ways to show start of file

        # Turn the Column Headers into the grid's columns
        self.Datasource.ColDefs=ColDefinitionsList([])
        for name in lstfile.ColumnHeaders:
            if name in self.stdColHeaders:
                name=self.stdColHeaders[name].Preferred
                self.Datasource.ColDefs.append(self.stdColHeaders[name])
            else:
                self.Datasource.ColDefs.append(ColDefinition(name))

        # Copy the row data over into the Datasource class
        FTRList: list[FanzineTableRow]=[]
        for row in lstfile.Rows:
            if len(row) != len(self.Datasource.ColDefs):
                Log(f"Mismatched column count for Row={row}", isError=True)
                continue
            FTRList.append(FanzineTableRow(row))
        self.Datasource._fanzineList=FTRList


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
        ncols=len(self.Datasource.ColDefs)    # ncols must be at least this big.

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
    def CreateLSTFileFromDatasourceEtc(self) -> LSTFile:

        lstfile=LSTFile()

        # Fill in the upper stuff
        lstfile.FirstLine=self.tTopMatter.GetValue()
        lstfile.TopTextLines=self.tPText.GetValue().split()
        lstfile.BottomTextLines=self.tPText.GetValue().split()

        # Copy over the column headers
        lstfile.ColumnHeaders=self.Datasource.ColHeaders

        # Now copy the grid's cell contents to the LSTFile structure
        lstfile.Rows=[]
        for i in range(self.Datasource.NumRows):
            row=[None]*self.Datasource.NumCols
            for j in range(self.Datasource.NumCols):
                row[j]=self.wxGrid.GetCellValue(i, j)
            lstfile.Rows.append(row)

        return lstfile

    def OnExitClicked(self, event):
        self.OnClose(event)


    def OnClose(self, event):
        if self.NeedsSaving():
            if event.CanVeto():
                ret=wx.MessageBox("The LST file has been updated and not yet saved. Exit anyway?", 'Warning', wx.OK|wx.CANCEL|wx.ICON_WARNING)
                if ret == wx.CANCEL:
                    event.Veto()
                    return

        # Save the window's position
        pos=self.GetPosition()
        Settings().Put("Top Level Window Position", (pos.x, pos.y))
        size=self.GetSize()
        Settings().Put("Top Level Windows Size", (size.width, size.height))

        self.Destroy()
        sys.exit(1)


    #------------------
    # Load an LST file from disk into an LSTFile class
    def OnLoadNewLSTFile(self, event):

        lstfile=self.LoadLSTFile()
        if lstfile is None:
            return

        self.InitializeDatasourceFromLSTfile(lstfile)
        self._dataGrid.RefreshWxGridFromDatasource()

        # Fill in the upper stuff
        self.ClearDisplay()
        self.tTopMatter.SetValue(lstfile.FirstLine)
        if len(lstfile.TopTextLines) > 0:
            self.tPText.SetValue("\n".join(lstfile.TopTextLines))
        elif len(lstfile.BottomTextLines) > 0:
            self.tPText.SetValue("\n".join(lstfile.BottomTextLines))

        self.MarkAsSaved()
        self.RefreshWindow()


    #------------------
    # Save an LSTFile object to disk.
    def OnSaveLSTFile(self, event):

        self.UpdateDatasourceFromWxGrid()
        lstfile=self.CreateLSTFileFromDatasourceEtc()

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
        s="Editing "+self.lstFilename
        if self.NeedsSaving():
            s=s+" *"        # Add on a change marker if needed
        self.SetTitle(s)
        self._dataGrid.RefreshWxGridFromDatasource()

    # ----------------------------------------------
    # Used to determine if anything has been updated
    def Signature(self) -> int:
        h=hash("".join(self.Datasource.TopTextLines))
        h+=hash("".join(self.Datasource.BottomTextLines))
        h+=hash(self.tTopMatter.GetValue())
        h+=self._dataGrid.Signature()
        return h

    def MarkAsSaved(self):
        self._initialSignature=self.Signature()

    def NeedsSaving(self):
        return self._initialSignature != self.Signature()

    #------------------
    def OnTextTopMatter(self, event):
        self.FirstLine=self.tTopMatter.GetValue()
        self.RefreshWindow()

    #------------------
    def OnTextComments(self, event):
        if self.Datasource.TopTextLines is not None and len(self.Datasource.TopTextLines) > 0:
            self.Datasource.TopTextLines=self.tPText.GetValue().split("\n")
        elif self.Datasource.BottomTextLines is not None and len(self.Datasource.BottomTextLines) > 0:
            self.Datasource.BottomTextLines=self.tPText.GetValue().split("\n")
        else:
            self.Datasource.TopTextLines=self.tPText.GetValue().split("\n")

        self.RefreshWindow()

    #-------------------
    def OnKeyDown(self, event):
        self._dataGrid.OnKeyDown(event) # Pass event to WxDataGrid to handle

    #-------------------
    def OnKeyUp(self, event):
        self._dataGrid.OnKeyUp(event) # Pass event to WxDataGrid to handle

    #------------------
    def OnGridCellChanged(self, event):
        self._dataGrid.OnGridCellChanged(event)  # Pass event handling to WxDataGrid
        self.RefreshWindow()

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
        if self._dataGrid.clickedColumn > self.Datasource.NumCols:    # Click is outside populated columns.  The +1 is because of the split of the 1st column
            return
        if self._dataGrid.clickedRow > self.Datasource.NumRows:      # Click is outside the populated rows
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
            if self.Datasource.Element.CanDeleteColumns:
                Enable("Delete Column(s)")

        # We enable the Add Column to right item if we're on any existing column
        if self._dataGrid.clickedColumn > 0:        # Can't insert columns between the 1st two
            Enable("Insert Column to Right")

        if self._dataGrid.clickedRow == -1: #Indicates we're on a column header
            Enable("Rename Column")

        # We only enable Extract Scanner when we're in the Notes column and there's something to extract.
        mi=self.m_GridPopup.FindItemById(self.m_GridPopup.FindItem("Extract Scanner"))
        if self.Datasource.ColDefs[self._dataGrid.clickedColumn].Preferred == "Notes":
            # We only want to enable the "Extract Scanner" item if the Notes column contains scanned by information
            for row in self.Datasource.Rows:
                note=row[self._dataGrid.clickedColumn].lower()
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

        if "Notes" not in self.Datasource.ColDefs:
            return
        notesCol=self.Datasource.ColDefs.index("Notes")

        # Start by adding a Scanned column to the right of the Notes column, if needed. (We check to see if one already exists.)
        if "Scanned" not in self.Datasource.ColDefs:
            # Add the Scanned column if needed
            self.InsertColumnMaybeQuery(notesCol, name="Scanned")

        scannedCol=self.Datasource.ColDefs.index("Scanned")
        notesCol=self.Datasource.ColDefs.index("Notes")

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
        pattern='[sS](?:can by|cans by|canned by|canned at|canning by) ([A-Z][a-z]+ (?:Mc|Mac|O\'\s?)?[A-Z][a-z]+|[A-Z]\\.[A-Z][a-z]+|[A-Z][a-z]+|[0-9]+)'

        for i in range(self.Datasource.NumRows):
            row=self.Datasource.Rows[i]
            note=row[notesCol]
            m=re.search(pattern, note)
            if m is not None:
                # Append the matched name to scanned
                if len(row[scannedCol]) > 0:
                    row[scannedCol]+="; "     # Use a semi-colon separator if there was already something there
                row[scannedCol]+=m.groups()[0]

                note=re.sub(pattern, "", note)  # Delete the matched text from the note
                note=re.sub("^([ ,]*)", "", note)          # Now remove leading and trailing spans of spaces and commas from the note.
                note=re.sub("([ ,]*)$", "", note)
                row[notesCol]=note

        # And redisplay
        self._dataGrid.RefreshWxGridFromDatasource()
        self.RefreshWindow()

    def OnPopupCopy(self, event):
        self._dataGrid.OnPopupCopy(event) # Pass event to WxDataGrid to handle
        self.RefreshWindow()

    def OnPopupPaste(self, event):
        self._dataGrid.OnPopupPaste(event) # Pass event to WxDataGrid to handle
        self.RefreshWindow()

    def OnPopupClearSelection(self, event):
        self._dataGrid.OnPopupClearSelection(event) # Pass event to WxDataGrid to handle
        self.RefreshWindow()

    def OnPopupDelCol(self, event):
        if self.Datasource.Element.CanDeleteColumns:
            self._dataGrid.DeleteSelectedColumns() # Pass event to WxDataGrid to handle
        self.RefreshWindow()

    def OnPopupDelRow(self, event):
        self._dataGrid.DeleteSelectedRows() # Pass event to WxDataGrid to handle
        self.RefreshWindow()

    def OnPopupRenameCol(self, event):
        self._dataGrid.OnPopupRenameCol(event) # Pass event to WxDataGrid to handle

        # Now we check the column header to see if it iss one of the standard header. If so, we use the std definition for that header
        # (We have to do this here because WxDataGrid doesn't know about header semantics.)
        icol=self._dataGrid.clickedColumn
        cd=self.Datasource.ColDefs[icol]
        if cd.Name in self.stdColHeaders:
            self.Datasource.ColDefs[icol]=self.stdColHeaders[cd.Name]
        self._dataGrid.RefreshWxGridFromDatasource()
        self.RefreshWindow()


    def OnPopupInsertColLeft(self, event):
        self._dataGrid.OnPopupInsertColLeft(event) # Pass event to WxDataGrid to handle
        self.RefreshWindow()

    def OnPopupInsertColRight(self, event):
        self._dataGrid.OnPopupInsertColRight(event) # Pass event to WxDataGrid to handle
        self.RefreshWindow()

    def OnPopupExtractScanner(self, event):
        self.ExtractScanner(self.Datasource.ColDefs.index("Notes"))
        self.RefreshWindow()


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


    def __getitem__(self, index: Union[int, slice]) -> str:
        if type(index) is int:
            return self._cells[index]
        if type(index) is slice:
            assert False
            #return self._cells(self.List[index])
        raise KeyError

    def __setitem__(self, index: Union[str, int, slice], value: Union[str, int, bool]) -> None:
        if type(index) is int:
            self._cells[index]=value
            return
        raise KeyError

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

    def __getitem__(self, index: int) -> FanzineTableRow:
        return self.Rows[index]

    def __setitem__(self, index: int, val: FanzineTableRow) -> None:
        self._fanzineList[index]=val


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

    # Load the global settings dictionary
    Settings().Load("FanacLSTGenerator settings.json")

    app=wx.App(False)
    frame=MainWindow(None, "Sample editor")
    app.MainLoop()

if __name__ == "__main__":
    main()