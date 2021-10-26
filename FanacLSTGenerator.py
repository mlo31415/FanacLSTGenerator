from __future__ import annotations
from typing import Union, Optional
from dataclasses import dataclass
import os
import wx
import wx.grid
import sys
from collections import defaultdict

from GenGUIClass import MainFrame

from WxDataGrid import DataGrid, GridDataSource, Color, GridDataSource
from LSTFile import *
from HelpersPackage import Bailout, Int, CanonicizeColumnHeaders
from FanzineIssueSpecPackage import ValidateData
from Log import LogOpen

class MainWindow(MainFrame):
    def __init__(self, parent, title):
        MainFrame.__init__(self, parent)
        self._grid: DataGrid=DataGrid(self.gRowGrid)
        self._grid.Datasource=FanzineTablePage()

        self.highlightRows: list[str]=[]       # A List of the names of fanzines in highlighted rows
        self.clipboard=None         # The grid's clipboard
        self.userSelection=None
        self.cntlDown: bool=False
        self.rightClickedColumn=None

        self.dirname=''
        if len(sys.argv) > 1:
            self.dirname=os.getcwd()

        stdColHeader: defaultdict[str, ColHeader]=defaultdict()
        stdColHeader["Link"]=ColHeader("Link", type="str")
        stdColHeader["Issue"]=ColHeader("Issue", type="str")
        stdColHeader["Title"]=ColHeader("Title", type="str", preferred="Issue")
        stdColHeader["Whole"]=ColHeader("Whole", type="int", width=75)
        stdColHeader["WholeNum"]=ColHeader("WholeNum", type="int", width=75, preferred="Whole")
        stdColHeader["Vol"]=ColHeader("Vol", type="int", width=50)
        stdColHeader["Volume"]=ColHeader("Volume", type="int", width=50, preferred="Vol")
        stdColHeader["Num"]=ColHeader("Num", type="int", width=50)
        stdColHeader["Number"]=ColHeader("Numver", type="int", width=50, preferred="Num")
        stdColHeader["Month"]=ColHeader("Month", type="str", width=75)
        stdColHeader["Day"]=ColHeader("Day", type="int", width=50)
        stdColHeader["Year"]=ColHeader("Year", type="int", width=50)
        stdColHeader["Pages"]=ColHeader("Pages", type="int", width=50)
        stdColHeader["PDF"]=ColHeader("PDF", type="str", width=50)
        stdColHeader["Notes"]=ColHeader("Notes", type="str", width=120)
        stdColHeader["Scanned"]=ColHeader("Scanned", type="str", width=100)
        stdColHeader["APA"]=ColHeader("APA", type="str", width=100)
        stdColHeader["Country"]=ColHeader("Country", type="str", width=50)
        stdColHeader["Editor"]=ColHeader("Editor", type="str", width=75)
        stdColHeader["Author"]=ColHeader("Author", type="str", width=75)
        stdColHeader["Repro"]=ColHeader("Repro", type="str", width=75)
        self.stdColHeader=stdColHeader

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
        pathname=os.path.join(self.dirname, self.lstFilename)
        try:
            self.lstData.Read(pathname)
        except Exception as e:
            Bailout(e, "MainWindow: Failure reading LST file '"+pathname+"'", "LSTError")

        # Fill in the upper stuff
        self.tTopMatter.SetValue(self.lstData.FirstLine)
        if len(self.lstData.TopTextLines) > 0:
            self.tPText.SetValue("\n".join(self.lstData.TopTextLines))
        elif len(self.lstData.BottomTextLines) > 0:
            self.tPText.SetValue("\n".join(self.lstData.BottomTextLines))

        # The grid is a bit non-standard, since I want to be able to edit row numbers and column headers
        # The row and column labels are actually the (editable) 1st column and 1st row of the spreadsheet (they're colored gray)
        # and the "real" row and column labels are hidden.
        self.gRowGrid.HideRowLabels()
        #self.gRowGrid.HideColLabels()

        # And now determine the identities of the column headers. (There are many ways to label a column that amount to the same thing.)
        self.lstData.IdentifyColumnHeaders()

        # Define the grid's columns
        # First add the invisible column which is actually the link destination
        # It's the first part of the funny xxxxx>yyyyy thing in the LST file's 1st column
        sch=self.stdColHeader["Link"]
        self._grid.Datasource._colheaders.append(sch.Preferred)
        self._grid.Datasource._colminwidths.append(sch.width)
        self._grid.Datasource._coldatatypes.append(sch.type)
        self._grid.Datasource._coleditable.append(sch.editable)
        # Followed by the headers defined in the LST file
        for i in range(len(self.lstData.ColumnHeaders)):
            name=self.lstData.ColumnHeaders[i]
            name=self.stdColHeader[name].Preferred
            sch=self.stdColHeader[name]
            self._grid.Datasource._colheaders.append(sch.Preferred)
            self._grid.Datasource._colminwidths.append(sch.width)
            self._grid.Datasource._coldatatypes.append(sch.type)
            self._grid.Datasource._coleditable.append(sch.editable)
            # Fill in the column definitions with the new data

        self._grid.SetColHeaders(self._grid.Datasource._colheaders)

        # Copy the row data over
        FTRList: list[FanzineTableRow]=[]
        for row in self.lstData.Rows:
            if len(row) != len(self._grid.Datasource._colheaders):
                Log(f"Mismatched column count for Row={row}")
                continue
            FTRList.append(FanzineTableRow(row))
        self._grid.Datasource._fanzineList=FTRList


        self.RefreshGridFromLSTData()
        self.MarkAsSaved()
        self.RefreshWindow()

        i=0

    # ------------------
    # The LSTFile object has the official information. This function refreshes the display from it.
    def RefreshGridFromLSTData(self):
        grid=self.gRowGrid
        grid.EvtHandlerEnabled=False
        grid.ClearGrid()

        # Now insert the row data
        grid.AppendRows(len(self.lstData.Rows))
        i=0
        for row in self.lstData.Rows:
            j=0
            for cell in row:
                grid.SetCellValue(i, j, cell)
                j+=1
            i+=1

        #self.ColorCellByValue()
        grid.ForceRefresh()
        grid.AutoSizeColumns()
        grid.EvtHandlerEnabled=True


    #------------------
    def OnLoadNewLSTFile(self, event):
        self.LoadLSTFile()
        pass

    # Define some RGB color constants
    labelGray=wx.Colour(230, 230, 230)
    pink=wx.Colour(255, 230, 230)
    lightGreen=wx.Colour(240, 255, 240)
    lightBlue=wx.Colour(240, 230, 255)
    white=wx.Colour(255, 255, 255)

    #------------------
    # Save an LSTFile object to disk.
    def OnSaveLSTFile(self, event):
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
            Bailout(PermissionError, "OnSaveLSTFile fails when trying to rename "+oldname+" to "+newname, "LSTError")

        try:
            self.lstData.Save(oldname)
        except:
            Bailout(PermissionError, "OnSaveLSTFile fails when trying to write file "+newname, "LSTError")


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
            Bailout(ValueError, "FanacLSTGenerator.DecodeIssueFileName: Missing $$ in '"+filename+"'", "LSTError")
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


    def RefreshWindow(self)-> None:
        self._grid.RefreshGridFromData()

    # ----------------------------------------------
    # Used to determine if anything has been updated
    def Signature(self) -> int:
        #stuff=self.ConInstanceName.strip()+self.ConInstanceTopText.strip()+self.ConInstanceFancyURL.strip()+self.Credits.strip()
        #return hash(stuff)+self._grid.Signature()
        return self._grid.Signature()

    def MarkAsSaved(self):
        self._signature=self.Signature()

    def NeedsSaving(self):
        return self._signature != self.Signature()

    #------------------
    def OnTextTopMatter(self, event):
        self.lstData.FirstLine=self.tTopMatter.GetValue()

    #------------------
    def OnTextComments(self, event):
        if self.lstData.TopTextLines is not None and len(self.lstData.TopTextLines) > 0:
            self.lstData.TopTextLines=self.tPText.GetValue().split("\n")
        elif self.lstData.BottomTextLines is not None and len(self.lstData.BottomTextLines) > 0:
            self.lstData.BottomTextLines=self.tPText.GetValue().split("\n")
        else:
            self.lstData.TopTextLines=self.tPText.GetValue().split("\n")

    #-------------------
    def OnKeyDown(self, event):
        self._grid.OnKeyDown(event) # Pass event to WxDataGrid to handle

    #-------------------
    def OnKeyUp(self, event):
        self._grid.OnKeyUp(event) # Pass event to WxDataGrid to handle

    # ------------------
    def ExtractScanner(self, col):
        # Start by adding a Scanned column to the right of the Notes column. (We check to see if one already exists.)
        # Located the Notes and Scanned columns, if any.
        scannedCol=None
        for i in range(0, len(self.lstData.ColumnHeaders)):
            if self.lstData.ColumnHeaders[i] == "Scanned":
                scannedCol=i
                break
        notesCol=None
        for i in range(0, len(self.lstData.ColumnHeaders)):
            if self.lstData.ColumnHeaders[i] == "Notes":
                notesCol=i
                break

        # Add the Scanned column if needed
        if scannedCol is None:
            for i in range(0, len(self.lstData.Rows)):
                row=self.lstData.Rows[i]
                row=row[:notesCol+2]+[""]+row[notesCol+2:]
                self.lstData.Rows[i]=row
            self.lstData.ColumnHeaders=self.lstData.ColumnHeaders[:notesCol+1]+["Scanned"]+self.lstData.ColumnHeaders[notesCol+1:]
            scannedCol=notesCol+1
            notesCol=notesCol

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
        for i in range(0, len(self.lstData.Rows)):
            row=self.lstData.Rows[i]
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
        self.RefreshGridFromLSTData()


@dataclass
class ColHeader:
    name: str
    width: int=100
    type: str=""
    editable: bool=True
    preferred: str=""

    @property
    def Preferred(self) -> str:
        if self.preferred != "":
            return self.preferred
        return self.name


# An individual file to be listed under a convention
# This is a single row
class FanzineTableRow(GridDataSource):

    def __init__(self, row: list[str]):
        self._cells: list[str]=row


    def __str__(self):
        return str(self._cells)

    # Make a deep copy of a FanzineTableRow
    def Copy(self) -> FanzineTableRow:
        ftr=FanzineTableRow()
        ftr._cells=self._cells
        return ftr

    def Signature(self) -> int:
        return hash(self._cells)

    # Serialize and deserialize
    def ToJson(self) -> str:
        d={"ver": 9,
           "_displayTitle": self._displayTitle,
           "_notes": self._notes,
           "_localpathname": self._localpathname,
           "_filename": self._localfilename,
           "_sitefilename": self._sitefilename,
           "_URL": self._URL,
           "_pages": self._pages,
           "_size": self._size}
        return json.dumps(d)

    def FromJson(self, val: str) -> FanzineTableRow:
        d=json.loads(val)
        self._displayTitle=d["_displayTitle"]
        self._notes=d["_notes"]
        self._localpathname=d["_localpathname"]
        self._localfilename=d["_filename"]
        self._size=d["_size"]
        if d["ver"] > 4:
            self._sitefilename=d["_sitefilename"]
        if d["ver"] <= 4 or self._sitefilename.strip() == "":
            self._sitefilename=self._displayTitle
        if d["ver"] > 6:
            self._pages=d["_pages"]
        if d["ver"] > 8:
            self._URL=d["_URL"]
        return self

    @property
    def Cells(self) -> str:
        return self._Cells
    @Cells.setter
    def Cells(self, val: str) -> None:
        self._Cells=val

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
    # Fixed information shared by all instances
    _colheaders: list[str]=[]
    _coldatatypes: list[str]=[]
    _colminwidths: list[int]=[]
    _coleditable: list[bool]=[]
    _element=FanzineTableRow

    def __init__(self):
        GridDataSource.__init__(self)
        self._fanzineList: list[FanzineTableRow]=[]
        self._name: str=""
        self._specialTextColor: Optional[Color, bool]=True

    # Serialize and deserialize
    def ToJson(self) -> str:
        dl=[]
        for con in self._fanzineList:
            dl.append(con.ToJson())
        d={"ver": 3,
           "_name": self._name,
           "_fanzineList": dl}
        return json.dumps(d)

    def FromJson(self, val: str) -> FanzineTablePage:
        d=json.loads(val)
        if d["ver"] >= 1:
            self._name=d["_name"]
            cfld=d["_fanzineList"]
            self._fanzineList=[]
            for c in cfld:
                self._fanzineList.append(FanzineTableRow().FromJson(c))

        return self

    # Inherited from GridDataSource
    @property
    def ColHeaders(self) -> list[str]:
        return self._colheaders

    @property
    def ColDataTypes(self) -> list[str]:
        return self._coldatatypes

    @property
    def ColMinWidths(self) -> list[int]:
        return self._colminwidths

    @property
    def ColEditable(self) -> list[bool]:
        return self._coleditable

    @property
    def Rows(self) -> list[FanzineTableRow]:
        return self._fanzineList

    @Rows.setter
    def Rows(self, rows: list) -> None:
        self._fanzineList=rows
    #
    # @property
    # def Name(self) -> str:
    #     return self._name
    #
    # @Name.setter
    # def Name(self, val: str) -> None:
    #     self._name=val

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

    def ColHeaderNameToIndex(self, name: str) -> int:
        assert name in self._colheaders
        return self._colheaders.index(name)

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