from __future__ import annotations
from typing import Union, Optional

import os
import wx
import wx.grid
import sys
from GenGUIClass import MainFrame

from WxDataGrid import DataGrid, Color, GridDataSource, ColDefinition, ColDefinitionsList, GridDataRowClass
from WxHelpers import OnCloseHandling
from LSTFile import *
from HelpersPackage import Bailout, IsInt, Int0, ZeroIfNone
from PDFHelpers import GetPdfPageCount
from Log import LogOpen, Log, LogClose
from Settings import Settings
from FanzineIssueSpecPackage import MonthNameToInt

class MainWindow(MainFrame):
    def __init__(self, parent, title):
        MainFrame.__init__(self, parent)
        self._dataGrid: DataGrid=DataGrid(self.wxGrid)
        self.Datasource=FanzineTablePage()

        self._signature=0
        self.lstFilename=""
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
        self.MarkAsSaved()      # We don't need to save whatever it is that is present now.
        if not self.LoadLSTFile():
            return

        # Position the window on the screen it was on before
        tlwp=Settings().Get("Top Level Window Position")
        if tlwp:
            self.SetPosition(tlwp)
        tlws=Settings().Get("Top Level Windows Size")
        if tlws:
            self.SetSize(tlws)

        self.MarkAsSaved()
        self.RefreshWindow()

        self.Show(True)

    @property
    def Datasource(self) -> FanzineTablePage:       # MainWindow(MainFrame)
        return self._Datasource
    @Datasource.setter
    def Datasource(self, val: FanzineTablePage):
        self._Datasource=val
        self._dataGrid.Datasource=val


    #------------------
    # Open a dialog to allow the user to select an LSTFile on disk.
    # Load it (and some other stuff) into self's 'LSFFile() object
    def LoadLSTFile(self) -> bool:       # MainWindow(MainFrame)

        # Call the File Open dialog to get an LST file
        dlg=wx.FileDialog(self, "Select LST file to load", self.dirname, "", "*.LST", wx.FD_OPEN)
        dlg.SetWindowStyle(wx.STAY_ON_TOP)

        if dlg.ShowModal() != wx.ID_OK:
            dlg.Raise()
            dlg.Destroy()
            self.OnCreateNewLSTFile(None)
            return False

        # Clear out old information from form.
        lstfile=LSTFile()

        self.lstFilename=dlg.GetFilename()
        self.dirname=dlg.GetDirectory()
        dlg.Destroy()

        # Read the lst file
        pathname=os.path.join(self.dirname, self.lstFilename)
        try:
            lstfile.Load(pathname)
        except Exception as e:
            Log(f"MainWindow: Failure reading LST file '{pathname}'", isError=True)
            Bailout(e, f"MainWindow: Failure reading LST file '{pathname}'", "LSTError")

        self._dataGrid.NumCols=0
        self._dataGrid.DeleteRows(0, self._dataGrid.NumRows)
        self._dataGrid.Grid.ScrollLines(-999)   # Scroll down a long ways to show start of file

        # Copy the row data over into the Datasource class
        # Because the LST data tends to be especially sloppy in the column count (extra or missing semicolons),
        # we expand to cover the maximum number of columns found so as to drop nothing.
        FTRList: list[FanzineTableRow]=[FanzineTableRow(row) for row in lstfile.Rows]
        # Find the longest row and lengthen all the rows to that length
        maxlen=max([len(row) for row in FTRList])
        maxlen=max(maxlen, len(lstfile.ColumnHeaders))
        if len(lstfile.ColumnHeaders) < maxlen:
            lstfile.ColumnHeaders.extend([""]*(maxlen-len(lstfile.ColumnHeaders)))
        for row in FTRList:
            if len(row) < maxlen:
                row.Extend([""]*(maxlen-len(row)))

        # Turn the Column Headers into the grid's columns
        self.Datasource.ColDefs=ColDefinitionsList([])
        for name in lstfile.ColumnHeaders:
            if name == "":
                self.Datasource.ColDefs.append(ColDefinition())
            elif name in self.stdColHeaders:
                name=self.stdColHeaders[name].Preferred
                self.Datasource.ColDefs.append(self.stdColHeaders[name])
            else:
                self.Datasource.ColDefs.append(ColDefinition(name))

        self.Datasource._fanzineList=FTRList

        self.ExtractApaMailings()

        self._dataGrid.RefreshWxGridFromDatasource()

        # Fill in the upper stuff
        self.tTopText.SetValue("")
        self.tLocaleText.SetValue("")
        self.wxGrid.ClearGrid()
        self.tFanzineName.SetValue(lstfile.FanzineName)
        self.tEditors.SetValue(lstfile.Editors)
        self.tDates.SetValue(lstfile.Dates)
        num=self.tFanzineType.FindString(lstfile.FanzineType)
        if num == -1:
            num=0
        self.tFanzineType.SetSelection(num)
        if len(lstfile.TopComments) > 0:
            self.tTopText.SetValue("\n".join(lstfile.TopComments))
        if lstfile.Locale:
            self.tLocaleText.SetValue("\n".join(lstfile.Locale))

        return True


    # Create a new LSTFile from the datasource
    def CreateLSTFileFromDatasourceEtc(self) -> LSTFile:       # MainWindow(MainFrame)

        lstfile=LSTFile()

        # Fill in the upper stuff
        lstfile.FanzineName=self.tFanzineName.GetValue().strip()
        lstfile.Editors=self.tEditors.GetValue().strip()
        lstfile.Dates=self.tDates.GetValue().strip()
        lstfile.FanzineType=self.tFanzineType.GetString(self.tFanzineType.GetSelection()).strip()

        lstfile.TopComments=self.tTopText.GetValue().split("\n")
        lstfile.Locale=[self.tLocaleText.GetValue().strip()]

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

    def OnExitClicked(self, event):       # MainWindow(MainFrame)
        self.OnClose(event)


    def OnClose(self, event):       # MainWindow(MainFrame)
        if OnCloseHandling(event, self.NeedsSaving(), "The LST file has been updated and not yet saved. Exit anyway?"):
            return
        self.MarkAsSaved()  # The contents have been declared doomed

        # Save the window's position
        pos=self.GetPosition()
        Settings().Put("Top Level Window Position", (pos.x, pos.y))
        size=self.GetSize()
        Settings().Put("Top Level Windows Size", (size.width, size.height))

        self.Destroy()

    def OnAddNewIssues(self, event):       # MainWindow(MainFrame)
        files=[]
        # Call the File Open dialog to select PDF files
        with wx.FileDialog(self,
                           message="Select PDF files to add",
                           defaultDir=self.dirname,
                           wildcard="PDF files (*.pdf)|*.pdf",
                           style=wx.FD_OPEN | wx.FD_MULTIPLE | wx.FD_FILE_MUST_EXIST | wx.STAY_ON_TOP) as dlg:

            if dlg.ShowModal() != wx.ID_OK:
                return

            files=dlg.GetFilenames()
            self.dirname=dlg.GetDirectory()

        if not files:  # Empty selection
            return

        # We have a list of file names. Sort them and add them to the rows at the bottom
        files.sort()
        iPdf=-1     # Just to make static error checking happy
        # Are any of these PDFs?
        if any([file.lower().endswith(".pdf") for file in files]):
            # Do we need to add a PDF column?
            iPdf=self.Datasource.ColHeaderIndex("pdf")
            if iPdf == -1:
                # Add the PDF column as the third column
                self.Datasource.InsertColumnHeader(2, ColDefinition("PDF"))
                for i, row in enumerate(self.Datasource.Rows):
                    cells=self.Datasource.Rows[i].Cells
                    self.Datasource.Rows[i].Cells=cells[:2]+[""]+cells[2:]
                iPdf=2

        nrows=self.Datasource.NumRows
        self.Datasource.AppendEmptyRows(len(files))
        for i, file in enumerate(files):
            self.Datasource.Rows[nrows+i][0]=file

        rows=slice(nrows, nrows+len(files))     # Slice of the new rows
        self.UpdatePDFColumn(rows)

        self._dataGrid.RefreshWxGridFromDatasource()

    #--------------------------
    # Check a specific subset of rows (as defined by the slice) to see if one of the file is a pdf
    # If a pdf is found possibly add a PDF column and fill the PDF column in for those rows.
    def UpdatePDFColumn(self, rows: slice):
        assert rows.step == 1 or rows.step is None
        # Are any of these PDFs?
        if not any([row[0].lower().endswith(".pdf") for row in self.Datasource.Rows[rows]]):
            return

        # Do we need to add a PDF column?
        iPdf=self.Datasource.ColHeaderIndex("pdf")
        if iPdf == -1:
            # We don't have an existing PDF column, but we now have at least one pdf file
            # Add the PDF column as the third column to the existing rows
            self.Datasource.InsertColumnHeader(2, ColDefinition("PDF"))
            for i, row in enumerate(self.Datasource.Rows):
                self.Datasource.Rows[i].Cells=row.Cells[:2]+[""]+row.Cells[2:]
            iPdf=2

        self.Datasource.AppendEmptyRows(rows.stop-rows.start)
        for i, row in enumerate(self.Datasource.Rows[rows]):
            # If it's a PDF, get its pagecount and add it to the row
            irow=rows.start+i   # We know that the step is always 1 for a slice argument to this function
            if row[0].lower().endswith(".pdf"):
                self.Datasource.Rows[irow][iPdf]="PDF"
                pages=GetPdfPageCount(row[0])
                if pages is not None:
                    pagesCol=self.Datasource.ColHeaderIndex("pages")
                    if pagesCol != -1:
                        self.Datasource.Rows[irow][pagesCol]=str(pages)

    #------------------
    # Load an LST file from disk into an LSTFile class
    def OnLoadNewLSTFile(self, event):       # MainWindow(MainFrame)

        if OnCloseHandling(None, self.NeedsSaving(), "The LST file has been updated and not yet saved. Replace anyway?"):
            return
        self.MarkAsSaved()  # The contents have been declared doomed

        if not self.LoadLSTFile():
            return

        self.MarkAsSaved()
        self.RefreshWindow()

    # ------------------
    # Create a new, empty LST file
    def OnCreateNewLSTFile(self, event):       # MainWindow(MainFrame)

        if OnCloseHandling(None, self.NeedsSaving(), "The LST file has been updated and not yet saved. Erase anyway?"):
            return
        self.MarkAsSaved()  # The contents have been declared doomed

        # THe strategy is to fill in the dialog and then create the LSTfile from it
        self.lstFilename=""
        self.dirname=""

        # Create default column headers
        self._Datasource.ColDefs=ColDefinitionsList([
            self.stdColHeaders["Filename"],
            self.stdColHeaders["Issue"],
            self.stdColHeaders["Whole"],
            self.stdColHeaders["Vol"],
            self.stdColHeaders["Number"],
            self.stdColHeaders["Month"],
            self.stdColHeaders["Day"],
            self.stdColHeaders["Year"],
            self.stdColHeaders["Pages"],
            self.stdColHeaders["Notes"]
        ])

        # Create one empty row
        self.Datasource._fanzineList=[]#[FanzineTableRow([""]*self.Datasource.NumCols)]

        # Update the dialog's grid from the data
        self._dataGrid.RefreshWxGridFromDatasource()

        # Fill in the dialog's upper stuff
        self.tFanzineName.SetValue("")
        self.tEditors.SetValue("")
        self.tDates.SetValue("")
        self.tFanzineType.SetSelection(0)
        self.tLocaleText.SetValue("")

        self.MarkAsSaved()
        self.RefreshWindow()
        self.Show(True)


    #------------------
    # Save an LSTFile object to disk.
    def OnSaveLSTFile(self, event):       # MainWindow(MainFrame)

        # Handle the case where we are saving a new file
        if self.lstFilename == "":
            # Use the Save dialog to decide where to save it.
            dlg=wx.FileDialog(self, "Save LST file", self.dirname, "", "*.LST", wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT | wx.FD_CHANGE_DIR)
            dlg.SetWindowStyle(wx.STAY_ON_TOP)

            if dlg.ShowModal() != wx.ID_OK:
                dlg.Raise()
                dlg.Destroy()
                return False

            self.lstFilename=dlg.GetFilename()
            name, ext=os.path.splitext(self.lstFilename)
            if ext.lower() != ".lst":
                self.lstFilename=name+".LST"
            self.dirname=dlg.GetDirectory()
            dlg.Destroy()

            lstfile=self.CreateLSTFileFromDatasourceEtc()

            self.SaveFile(lstfile, self.lstFilename)
            return

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

        self.SaveFile(lstfile, oldname)

    # Save an LST file
    def SaveFile(self, lstfile, name):
        try:
            lstfile.Save(name)
            self.MarkAsSaved()
        except:
            Log(f"OnSaveLSTFile failed while trying to save {name}", isError=True)
            Bailout(PermissionError, "OnSaveLSTFile failed when trying to write file "+name, "LSTError")

    def MaybeSetNeedsSavingFlag(self):
        s="Editing "+self.lstFilename
        if self.NeedsSaving():
            s=s+" *"        # Add on a change marker if needed
        self.SetTitle(s)


    def RefreshWindow(self)-> None:       # MainWindow(MainFrame)
        self.MaybeSetNeedsSavingFlag()
        self._dataGrid.RefreshWxGridFromDatasource()

    # ----------------------------------------------
    # Used to determine if anything has been updated
    def Signature(self) -> int:       # MainWindow(MainFrame)
        h=hash("".join(self.Datasource.TopComments))
        h+=hash(f"{self.Datasource.FanzineName};{self.Datasource.Editors};{self.Datasource.Dates};{self.Datasource.FanzineType}")
        h+=hash("".join(self.Datasource.Locale))
        h+=self.Datasource.Signature()
        return h

    def MarkAsSaved(self):       # MainWindow(MainFrame)
        self._signature=self.Signature()

    def NeedsSaving(self):       # MainWindow(MainFrame)
        return self._signature != self.Signature()

    def OnFanzineName(self, event):
        self.Datasource.FanzineName=self.tFanzineName.GetValue()
        self.RefreshWindow()

    def OnEditors(self, event):
        self.Datasource.Editors=self.tEditors.GetValue()
        self.RefreshWindow()

    def OnDates(self, event):
        self.Datasource.Dates=self.tDates.GetValue()
        self.RefreshWindow()

    def OnFanzineType(self, event):
        self.Datasource.FanzineType=self.tFanzineType.GetSelection()
        self.RefreshWindow()
    #------------------
    def OnTextTopComments(self, event):       # MainWindow(MainFrame)
        if self.Datasource.TopComments is not None and len(self.Datasource.TopComments) > 0:
            self.Datasource.TopComments=self.tTopText.GetValue().split("\n")
        else:
            self.Datasource.TopComments=self.tTopText.GetValue().split("\n")

        self.RefreshWindow()

    #------------------
    def OnTextLocale(self, event):       # MainWindow(MainFrame)
        self.Datasource.Locale=self.tLocaleText.GetValue().split("\n")
        self.RefreshWindow()

    #-------------------
    def OnKeyDown(self, event):       # MainWindow(MainFrame)
        self._dataGrid.OnKeyDown(event) # Pass event to WxDataGrid to handle
        self.MaybeSetNeedsSavingFlag()

    #-------------------
    def OnKeyUp(self, event):       # MainWindow(MainFrame)
        self._dataGrid.OnKeyUp(event) # Pass event to WxDataGrid to handle

    #------------------
    def OnGridCellChanged(self, event):       # MainWindow(MainFrame)
        self._dataGrid.OnGridCellChanged(event)  # Pass event handling to WxDataGrid

        row=event.GetRow()
        col=event.GetCol()
        if col == 0:    # If the Filename changes
            self.UpdatePDFColumn(slice(row, row+1))
        self.RefreshWindow()

    #------------------
    def OnGridCellRightClick(self, event):       # MainWindow(MainFrame)
        # Do generic RMB on grid processing
        self._dataGrid.OnGridCellRightClick(event, self.m_GridPopup)

        # Call the RMB handler
        self.RMBHandler(True, event)

    # ------------------
    def OnGridLabelLeftClick(self, event):       # MainWindow(MainFrame)
        self._dataGrid.OnGridLabelLeftClick(event)

    #------------------
    def OnGridLabelRightClick(self, event):       # MainWindow(MainFrame)
        # Do generic RMB on grid processing
        self._dataGrid.OnGridCellRightClick(event, self.m_GridPopup)

        # Call the RMB handler
        self.RMBHandler(False, event)

    # RMB click handling for grid and grid label clicks
    def RMBHandler(self, isCellClick: bool, event):       # MainWindow(MainFrame)
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
            _, left, _, right=self._dataGrid.SelectionBoundingBox()
            if left == right:
                Enable("Sort on Selected Column")

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
        if self.Datasource.ColDefs[self._dataGrid.clickedColumn].Preferred == "Notes":
            # We only want to enable the "Extract Scanner" item if the Notes column contains scanned by information
            for row in self.Datasource.Rows:
                note=row[self._dataGrid.clickedColumn].lower()
                if "scan by" in note or \
                        "scans by" in note or \
                        "scanned by" in note or \
                        "scanning by" in note or \
                        "scanned at" in note:
                    Enable("Extract Scanner")
                    break

        if self.Datasource.ColHeaders[self._dataGrid.clickedColumn] == "Notes":
            Enable("Extract APA Mailings")

        # Pop the menu up.
        self.PopupMenu(self.m_GridPopup)

    # ------------------
    # Extract 'scanned by' information from the Notes column, if any
    def ExtractScanner(self, col):       # MainWindow(MainFrame)

        if "Notes" not in self.Datasource.ColDefs:
            return
        notesCol=self.Datasource.ColDefs.index("Notes")

        # Start by adding a Scanned column to the right of the Notes column, if needed. (We check to see if one already exists.)
        if "Scanned" not in self.Datasource.ColDefs:
            # Add the Scanned column if needed
            self._dataGrid.InsertColumnMaybeQuery(notesCol, name="Scanned")

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

    def OnPopupCopy(self, event):       # MainWindow(MainFrame)
        self._dataGrid.OnPopupCopy(event) # Pass event to WxDataGrid to handle
        self.RefreshWindow()

    def OnPopupPaste(self, event):       # MainWindow(MainFrame)
        self._dataGrid.OnPopupPaste(event) # Pass event to WxDataGrid to handle
        self.RefreshWindow()

    def OnPopupClearSelection(self, event):       # MainWindow(MainFrame)
        self._dataGrid.OnPopupClearSelection(event) # Pass event to WxDataGrid to handle
        self.RefreshWindow()

    def OnPopupDelCol(self, event):       # MainWindow(MainFrame)
        if self.Datasource.Element.CanDeleteColumns:
            self._dataGrid.DeleteSelectedColumns() # Pass event to WxDataGrid to handle
        self.RefreshWindow()

    def OnPopupDelRow(self, event):       # MainWindow(MainFrame)
        self._dataGrid.DeleteSelectedRows() # Pass event to WxDataGrid to handle
        self.RefreshWindow()

    def OnPopupRenameCol(self, event):       # MainWindow(MainFrame)
        self._dataGrid.OnPopupRenameCol(event) # Pass event to WxDataGrid to handle

        # Now we check the column header to see if it iss one of the standard header. If so, we use the std definition for that header
        # (We have to do this here because WxDataGrid doesn't know about header semantics.)
        icol=self._dataGrid.clickedColumn
        cd=self.Datasource.ColDefs[icol]
        if cd.Name in self.stdColHeaders:
            self.Datasource.ColDefs[icol]=self.stdColHeaders[cd.Name]
        self._dataGrid.RefreshWxGridFromDatasource()
        self.RefreshWindow()

    def OnPopupSortOnSelectedColumn(self, event):       # MainWindow(MainFrame)
        # We already know that only a single column is selected
        _, col, _, _=self._dataGrid.SelectionBoundingBox()
        # If the column consists on thong but empty cells and numbers, we do a special numerical sort.
        testIsInt=all([(x[col] == "" or IsInt(x[col])) for x in self.Datasource.Rows])
        if testIsInt:
            self.Datasource.Rows.sort(key=lambda x: Int0(x[col]))
        else:
            testIsMonth=all([(x[col] == "" or MonthNameToInt(x[col])) is not None for x in self.Datasource.Rows])
            if testIsMonth:
                self.Datasource.Rows.sort(key=lambda x: ZeroIfNone(MonthNameToInt(x[col])))
            else:
                self.Datasource.Rows.sort(key=lambda x:x[col])
        self.RefreshWindow()

    def OnPopupInsertColLeft(self, event):       # MainWindow(MainFrame)
        self._dataGrid.OnPopupInsertColLeft(event) # Pass event to WxDataGrid to handle
        self.RefreshWindow()

    def OnPopupInsertColRight(self, event):       # MainWindow(MainFrame)
        self._dataGrid.OnPopupInsertColRight(event) # Pass event to WxDataGrid to handle
        self.RefreshWindow()

    def OnPopupExtractScanner(self, event):       # MainWindow(MainFrame)
        self.ExtractScanner(self.Datasource.ColDefs.index("Notes"))
        self.RefreshWindow()

    def OnPopupExtractApaMailings(self, event):
        self.ExtractApaMailings()
        self.RefreshWindow()


    # Run through the rows and columns and look at the Notes column  If an APA mailing note is present,
    # move it to a "Mailing" column (which may need to be created).  Remove the text from the Notes column.
    # Find the Notes column. If there is none, we're done.
    def ExtractApaMailings(self):
        if "Notes" in self._Datasource.ColHeaders:
            notescol=self._Datasource.ColHeaders.index("Notes")

            # Look through the rows and extract mailing info, if any
            # We're looking for things like [for/in] <apa> nnn
            mailings=[""]*len(self._Datasource.Rows)     # Collect the mailing into in this until later when we have a chance to put it in its own column
            apas: list[str]=["FAPA", "SAPS", "OMPA", "ANZAPA", "VAPA", "FLAP"]
            for i, row in enumerate(self._Datasource.Rows):
                for apa in apas:
                    pat=f"(?:for|in|)[^a-zA-Z]+{apa}\s+([0-9]+)[,;]?"
                    m=re.search(pat, row[notescol])
                    if m is not None:
                        # We found a mailing.  Add it to the tenporary list of mailings and remove it from the mailings column
                        mailings[i]=apa+" "+m.groups()[0]
                        row[notescol]=re.sub(pat, "", row[notescol]).strip()

            # If any mailings were found, we need to put them into their new column (and maybe create the new column as well.)
            if any([m for m in mailings]):
                # Append a mailing column if needed
                if "Mailing" not in self._Datasource.ColHeaders:
                    self._Datasource.InsertColumnHeader(-1, self.stdColHeaders["Mailing"])
                # And in each row append an empty cell
                for i, row in enumerate(self._Datasource.Rows):
                    if len(row) < len(self._Datasource.ColHeaders):
                        self._Datasource.Rows[i].Extend([""])

                # And move the mailing info
                mailcol=self._Datasource.ColHeaders.index("Mailing")
                for i, row in enumerate(self._Datasource.Rows):
                    row[mailcol]=mailings[i]


#=============================================================
# An individual file to be listed under a convention
# This is a single row
class FanzineTableRow(GridDataRowClass):

    def __init__(self, cells: list[str]):
        GridDataRowClass.__init__(self)
        self._cells: list[str]=cells

    def __str__(self):      # FanzineTableRow(GridDataRowClass)
        return str(self._cells)

    def __len__(self):     # FanzineTableRow(GridDataRowClass)
        return len(self._cells)

    def Extend(self, s: list[str]) -> None:    # FanzineTableRow(GridDataRowClass)
        self._cells.extend(s)

    # Make a deep copy of a FanzineTableRow
    def Copy(self) -> FanzineTableRow:      # FanzineTableRow(GridDataRowClass)
        ftr=FanzineTableRow([])
        ftr._cells=self._cells
        return ftr

    # We multiply the cell has by the cell index (+1) so that moves right and left also change the signature
    def Signature(self) -> int:      # FanzineTableRow(GridDataRowClass)
        return sum([(i+1)*hash(x) for i, x in enumerate(self._cells)])

    @property
    def Cells(self) -> list[str]:
        return self._cells
    @Cells.setter
    def Cells(self, newcells: list[str]):
        self._cells=newcells

    @property
    def CanDeleteColumns(self) -> bool:      # FanzineTableRow(GridDataRowClass)
        return True

    # This deletes a single column from the datasource.
    # It must be implemented here because WxDataGrid doesn't understand the details of the DataSource
    def DelCol(self, icol: int) -> None:      # FanzineTableRow(GridDataRowClass)
        del self._cells[icol]


    def __getitem__(self, index: Union[int, slice]) -> str:      # FanzineTableRow(GridDataRowClass)
        if type(index) is int:
            return self._cells[index]
        if type(index) is slice:
            assert False
            #return self._cells(self.List[index])
        raise KeyError

    def __setitem__(self, index: Union[str, int, slice], value: Union[str, int, bool]) -> None:      # FanzineTableRow(GridDataRowClass)
        if type(index) is int:
            self._cells[index]=value
            return
        raise KeyError


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
        self.TopComments: list[str]=[]
        self.Locale: list[str]=[]
        self.FanzineName: str=""
        self.Editors: str=""
        self.Dates: str=""
        self.FanzineType: str=""



    def Signature(self) -> int:
        s=self._colDefs.Signature()
        s+=hash(self._name.strip()+"".join(self.TopComments).strip()+"".join(self.Locale).strip())
        s+=hash(f"{self.FanzineName};{self.Editors};{self.Dates};{self.FanzineType}")
        s+=sum([x.Signature()*(i+1) for i, x in enumerate(self._fanzineList)])
        return s+hash(self._specialTextColor)+self._colDefs.Signature()

    # Inherited from GridDataSource
    @property
    def Rows(self) -> list[FanzineTableRow]:        # FanzineTablePage(GridDataSource)
        return self._fanzineList

    @Rows.setter
    def Rows(self, rows: list) -> None:        # FanzineTablePage(GridDataSource)
        self._fanzineList=rows

    @property
    def NumRows(self) -> int:        # FanzineTablePage(GridDataSource)
        return len(self._fanzineList)

    def __getitem__(self, index: int) -> FanzineTableRow:        # FanzineTablePage(GridDataSource)
        return self.Rows[index]

    def __setitem__(self, index: int, val: FanzineTableRow) -> None:        # FanzineTablePage(GridDataSource)
        self._fanzineList[index]=val


    @property
    def SpecialTextColor(self) -> Optional[Color]:        # FanzineTablePage(GridDataSource)
        return self._specialTextColor
    @SpecialTextColor.setter
    def SpecialTextColor(self, val: Optional[Color]) -> None:        # FanzineTablePage(GridDataSource)
        self._specialTextColor=val

    def CanAddColumns(self) -> bool:        # FanzineTablePage(GridDataSource)
        return True

    def InsertEmptyRows(self, insertat: int, num: int=1) -> None:
        for i in range(num):
            ftr=FanzineTableRow([""]*self.NumCols)
            self._fanzineList.insert(insertat+i, ftr)



def main():
    # Start the GUI and run the event loop
    LogOpen("Log -- FanacLSTGenerator.txt", "Log (Errors) -- FanacLSTGenerator.txt")

    # Load the global settings dictionary
    Settings().Load("FanacLSTGenerator settings.json")

    app=wx.App(False)
    frame=MainWindow(None, "Sample editor")
    app.MainLoop()

    LogClose()

    sys.exit(1)

if __name__ == "__main__":
    main()