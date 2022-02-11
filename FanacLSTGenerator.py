from __future__ import annotations
from typing import Union, Optional

import os
import shutil
import wx
import wx.grid
import sys
from GenGUIClass import MainFrame

from WxDataGrid import DataGrid, Color, GridDataSource, ColDefinition, ColDefinitionsList, GridDataRowClass
from WxHelpers import OnCloseHandling, ProgressMessage
from LSTFile import *
from HelpersPackage import Bailout, IsInt, Int0, ZeroIfNone, MessageBox
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
        self.DirectoryLocal=""  # Local directory where the LST file, etc., reside
        self.DirectoryServer="" # Server directory to be created under /fanzines
        self.Complete=False     # Is this fanzine series complete?
        self.NewDirectory=False # Are we creating a new directory? (Alternative is that we're editing an old one.)
        self.OldDirectory=False
        self.Credits=""         # Who is to be credited for this affair?

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

        self.DirectoryLocal=''
        if len(sys.argv) > 1:
            self.DirectoryLocal=os.getcwd()

        # Read the LST file
        self.MarkAsSaved()      # We don't need to save whatever it is that is present now.

        # Position the window on the screen it was on before
        tlwp=Settings().Get("Top Level Window Position")
        if tlwp:
            self.SetPosition(tlwp)
        tlws=Settings().Get("Top Level Windows Size")
        if tlws:
            self.SetSize(tlws)

        label=Settings().Get("Root directory", default=".").replace("\\", "/")
        label="Local Directory: "+label+"/"
        self.lLocalDirectory.SetWindowStyle(self.lLocalDirectory.GetWindowStyle() | wx.ST_ELLIPSIZE_MIDDLE)
        self.lLocalDirectory.SetLabel(label)
        self.lLocalDirectory.GetContainingSizer().Layout()

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


    # Look at information availabe and color buttons and fields accordingly.
    def ColorFields(self):

        # To start with, everything is disabled except the buttons to Load an old LST file or to create a new one
        self.bSave.Enabled=False
        self.bAddNewIssues.Enabled=False
        self.tFanzineName.SetEditable(False)
        self.tEditors.SetEditable(False)
        self.tDates.SetEditable(False)
        self.tFanzineType.Enabled=False
        self.tTopText.SetEditable(False)
        self.tLocaleText.SetEditable(False)
        self.rbComplete.Enabled=True
        self.tDirectoryLocal.SetEditable(False)
        self.tDirectoryServer.SetEditable(False)
        self.wxGrid.Enabled=False

        # Some things are turned on for both Load and Create
        if self.NewDirectory or self.OldDirectory:
            self.bAddNewIssues.Enabled=True
            self.tFanzineName.SetEditable(True)
            self.tEditors.SetEditable(True)
            self.tDates.SetEditable(True)
            self.tFanzineType.Enabled=True
            self.tTopText.SetEditable(True)
            self.tLocaleText.SetEditable(True)
            self.rbComplete.Enabled=True
            self.wxGrid.Enabled=True

        # The basic split is whether we are editing an existing LST or creating a new directory
        if self.NewDirectory:
            self.tDirectoryLocal.SetEditable(True)
            self.tDirectoryServer.SetEditable(True)
            if len(self.tDirectoryLocal.GetValue()) > 0 and len(self.tDirectoryServer.GetValue()) > 0 and len(self.tFanzineName.GetValue()) > 0 and len(self.Datasource.Rows) > 0:
                self.bSave.Enabled=True
            # Can't add new issues until we have a target directory defined
            self.bAddNewIssues.Enabled=len(self.tDirectoryLocal.GetValue()) > 0 and len(self.tFanzineName.GetValue()) > 0

        elif self.OldDirectory:
            if self.tFanzineName.GetValue() and len(self.Datasource.Rows) > 0:
                self.bSave.Enabled=True
                # Can't add new issues until we have a target directory defined
                self.bAddNewIssues.Enabled=True



    #------------------
    # Open a dialog to allow the user to select an LSTFile on disk.
    # Load it (and some other stuff) into self's 'LSFFile() object
    def LoadLSTFile(self) -> bool:       # MainWindow(MainFrame)

        # Clear out any old information from form.
        lstfile=LSTFile()

        # Read the lst file
        pathname=os.path.join(self.DirectoryLocal, self.lstFilename)
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

        self._dataGrid.RefreshWxGridFromDatasource(IgnoreCurrentGrid=True)

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
                           defaultDir=self.DirectoryLocal,
                           wildcard="PDF files (*.pdf)|*.pdf",
                           style=wx.FD_OPEN | wx.FD_MULTIPLE | wx.FD_FILE_MUST_EXIST | wx.STAY_ON_TOP) as dlg:

            if dlg.ShowModal() != wx.ID_OK:
                return

            files=dlg.GetFilenames()
            sourceDirectory=dlg.GetDirectory()

        if not files:  # Empty selection
            return

        # Move the files from the source directory to the fanzine's directory.
        rootDirectory=Settings().Get("Root directory", default=".")
        fanzineDirectory=os.path.splitext(os.path.join(rootDirectory, self.lstFilename))[0]
        for file in files:
            os.rename(os.path.join(sourceDirectory, file), os.path.join(fanzineDirectory, file))

        # We have a list of file names. Sort them and add them to the rows at the bottom
        # Start by removing any empty trailing rows
        while self.Datasource.Rows:
            last=self.Datasource.Rows.pop()
            if any([cell != "" for cell in last.Cells]):
                self.Datasource.Rows.append(last)
                break
        files.sort()
        nrows=self.Datasource.NumRows
        self.Datasource.AppendEmptyRows(len(files))
        for i, file in enumerate(files):
            self.Datasource.Rows[nrows+i][0]=file

        rows=slice(nrows, nrows+len(files))     # Slice of the new rows
        self.UpdatePDFColumn(rows)

        self._dataGrid.RefreshWxGridFromDatasource()
        self.RefreshWindow()


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

        rootDirectory=Settings().Get("Root directory", default=".")
        fanzineDirectory=os.path.splitext(os.path.join(rootDirectory, self.lstFilename))[0]

        self.Datasource.AppendEmptyRows(rows.stop-rows.start)
        for i, row in enumerate(self.Datasource.Rows[rows]):
            # If it's a PDF, get its pagecount and add it to the row
            irow=rows.start+i   # We know that the step is always 1 for a slice argument to this function
            if row[0].lower().endswith(".pdf"):
                self.Datasource.Rows[irow][iPdf]="PDF"
                pages=GetPdfPageCount(os.path.join(fanzineDirectory, row[0]))
                if pages is not None:
                    pagesCol=self.Datasource.ColHeaderIndex("pages")
                    if pagesCol != -1:
                        self.Datasource.Rows[irow][pagesCol]=str(pages)


    #------------------
    # Load an LST file from disk into an LSTFile class
    def OnLoadExistingLSTFile(self, event):       # MainWindow(MainFrame)

        if OnCloseHandling(None, self.NeedsSaving(), "The LST file has been updated and not yet saved. Replace anyway?"):
            return
        self.MarkAsSaved()  # The contents have been declared doomed

        self.tDirectoryLocal.SetValue("")
        self.tDirectoryServer.SetValue("")
        self.NewDirectory=False
        self.OldDirectory=True

        # Call the File Open dialog to get an LST file
        dlg=wx.FileDialog(self, "Select LST file to load", self.DirectoryLocal, "", "*.LST", wx.FD_OPEN)
        dlg.SetWindowStyle(wx.STAY_ON_TOP)

        if dlg.ShowModal() != wx.ID_OK:
            dlg.Raise()
            dlg.Destroy()
            return False

        self.lstFilename=dlg.GetFilename()
        self.DirectoryLocal=dlg.GetDirectory()
        dlg.Destroy()

        if not self.LoadLSTFile():
            return

        # Rummage through the setup.bld file in the LST file's directory to get Complete and Credits
        # The file consists of lots of lines of the form xxx=yyy
        # We want to edit two of them.
        filename=os.path.join(self.DirectoryLocal, "setup.bld")
        if os.path.exists(filename):
            Log(f"Opening {filename}")
            with open(filename, "r") as fd:
                lines=fd.readlines()
            lines=[line.removesuffix("\n") for line in lines]
            Log(f"Read {lines=}")
            for i, line in enumerate(lines):
                m=re.match("^([a-zA-Z0-9_ ]+)=(.*)$", line)
                if m:
                    if m.groups()[0].lower().strip() == "credit":
                        if not self.Credits:
                            self.Credits=m.groups()[1].strip().strip("'")   # The text is quoted in the LST file
                            self.tCredits.SetValue(self.Credits)
                    if m.groups()[0].lower().strip() == "complete":
                        self.Complete=(m.groups()[1].lower() == "true")
                        self.rbComplete.SetValue(self.Complete)
        else:
            Log(f"{filename} not found")


        self.MarkAsSaved()
        self.RefreshWindow()

    # ------------------
    # Create a new, empty LST file
    def OnCreateNewFanzineDir(self, event):       # MainWindow(MainFrame)

        if OnCloseHandling(None, self.NeedsSaving(), "The LST file has been updated and not yet saved. Erase anyway?"):
            return
        self.MarkAsSaved()  # Existing contents have been declared doomed

        self.lstFilename=""
        self.DirectoryLocal=""

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

        # Create an empty datasource
        self.Datasource._fanzineList=[]

        # Update the dialog's grid from the data
        self._dataGrid.RefreshWxGridFromDatasource(IgnoreCurrentGrid=True)

        # Fill in the dialog's upper stuff
        self.tFanzineName.SetValue("")
        self.tEditors.SetValue("")
        self.tDates.SetValue("")
        self.tFanzineType.SetSelection(0)
        self.tLocaleText.SetValue("")

        self.Credits=Settings().Get("Credits", default="")
        self.tCredits.SetValue(self.Credits)

        rootDirectory=Settings().Get("Root directory", default=".")
        templateDirectory=Settings().Get("Template directory", default=".")

        # Both directories are editable, for now at least.
        self.tDirectoryLocal.SetValue("")
        self.NewDirectory=True
        self.OldDirectory=False

        self.MarkAsSaved()
        self.RefreshWindow()
        self.Show(True)


    #------------------
    # Save an LSTFile object to disk and maybe create a whole new directory
    def OnSave(self, event):       # MainWindow(MainFrame)

        if self.NewDirectory:
            self.CreateLSTDirectory()
        else:
            self.SaveExistingLSTFile()


    #------------------
    # Save an existing LST file by simply overwriting what exists.
    def SaveExistingLSTFile(self):       # MainWindow(MainFrame)
        # Create an instance of the LSTfile class from the datasource
        lstfile=self.CreateLSTFileFromDatasourceEtc()

        # Rename the old file
        oldname=os.path.join(self.DirectoryLocal, self.lstFilename)
        newname=os.path.join(self.DirectoryLocal, os.path.splitext(self.lstFilename)[0]+"-old.LST")
        try:
            i=0
            while os.path.exists(newname):
                i+=1
                newname=os.path.join(self.DirectoryLocal, os.path.splitext(self.lstFilename)[0]+"-old-"+str(i)+".LST")

            os.rename(oldname, newname)
        except Exception as e:
            Log(f"OnSave fails when trying to rename {oldname} to {newname}", isError=True)
            Bailout(PermissionError, f"OnSave fails when trying to rename {oldname} to {newname}", "LSTError")

        self.SaveFile(lstfile, oldname)


    #------------------
    # Create a new fanzine directory and LSTfile
    def CreateLSTDirectory(self):       # MainWindow(MainFrame)
        rootDirectory=Settings().Get("Root directory", default=".")

        # If a directory was not specified in the main dialog, use the Save dialog to decide where to save it.
        if not self.DirectoryLocal:
            dlg=wx.DirDialog(self, "Create new directory", "", wx.DD_DEFAULT_STYLE)
            dlg.SetWindowStyle(wx.STAY_ON_TOP)

            if dlg.ShowModal() != wx.ID_OK:
                dlg.Raise()
                dlg.Destroy()
                return False

            self.DirectoryLocal=dlg.GetPath()
            dlg.Destroy()

        newDirectory=os.path.join(rootDirectory, self.DirectoryLocal)

        progMsg=ProgressMessage(self)
        progMsg.Show(f"Creating {self.tFanzineName.GetValue()}")

        # The directory must not exist, otherwise
        if os.path.exists(newDirectory):
            MessageBox(f"Directory {newDirectory} already exists.")
            #return         For now, just keep going
        else:
            # Create the new directory
            os.mkdir(newDirectory)

        # Copy the files setup.ftp and setup.bld from the templates source to the new directory.
        templateDirectory=Settings().Get("Template directory", default=".")

        # Look in Settings to find the names of the template files.
        # Copy them from the template directory to the LST file's directory
        if not self.CopyTemplateFile("setup.ftp template", "setup.ftp", newDirectory, templateDirectory):
            progMsg.Close(delay=1)
            return
        if not self.CopyTemplateFile("setup.bld template", "setup.bld", newDirectory, templateDirectory):
            progMsg.Close(delay=1)
            return
        # Edit them based on what the user filled in in the main dialog
        if not self.UpdateSetupFtp(newDirectory):
            progMsg.Close(delay=1)
            return
        if not self.UpdateSetupBld(newDirectory):
            progMsg.Close(delay=1)
            return

        # Save the LSTFile in the new directory
        name, ext=os.path.splitext(self.DirectoryLocal)
        if ext.lower() != ".lst":
            self.lstFilename=name+".LST"

        lstfile=self.CreateLSTFileFromDatasourceEtc()
        self.SaveFile(lstfile, self.lstFilename)

        progMsg.Close(delay=1)


    def UpdateSetupBld(self, path) -> bool:
        # Read setup.bld, edit it, and save the result back
        # The file consists of lots of lines of the form xxx=yyy
        # We want to edit two of them.
        filename=os.path.join(path, "setup.bld")
        Log(f"Opening {filename}")
        with open(filename, "r") as fd:
            lines=fd.readlines()
        lines=[line.removesuffix("\n") for line in lines]
        Log(f"Read {lines=}")
        found=False
        for i, line in enumerate(lines):
            m=re.match("^([a-zA-Z0-9_ ]+)=(.*)$", line)
            if m:
                if m.groups()[0].lower().strip() == "credit":
                    if self.Credits:
                        lines[i]=f"{m.groups()[0]}='{self.Credits}'"
                    found=True
                if m.groups()[0].lower().strip() == "complete":
                    lines[i]=f"{m.groups()[0]}={'TRUE' if self.rbComplete.GetValue() != 0 else 'FALSE'}"
                    found=True
        if not found:
            MessageBox("Can't edit setup.bld. Save failed.")
            Log("CreateLSTDirectory: Can't edit setup.ftp. Save failed.")
            return False
        Log(f"Write {lines=}")
        with open(filename, "w") as fd:
            fd.writelines(lines)
        return True


    def UpdateSetupFtp(self, path) -> bool:
        filename=os.path.join(path, "setup.ftp")
        Log(f"Opening {filename}")
        with open(filename, "r") as fd:
            lines=fd.read()
        Log(f"Read {lines=}")
        if lines.find("<<dir name>>") == -1:
            MessageBox("Can't edit setup.ftp. Save failed.")
            Log("CreateLSTDirectory: Can't edit setup.ftp. Save failed.")
            return False
        lines=lines.replace("<<dir name>>", self.DirectoryServer)
        Log(f"Write {lines=}")
        with open(filename, "w") as fd:
            fd.write(lines)
        return True


    def CopyTemplateFile(self, settingName: str, newName: str, newDirectory: str, templateDirectory: str) -> bool:
        setupTemplateName=Settings().Get(settingName, default="")
        if not setupTemplateName:
            MessageBox(f"Settings files does not contain value for {settingName}. Save failed.")
            return False

        # Remove the template if it already exists in the target directory
        filename=os.path.join(newDirectory, setupTemplateName)
        if os.path.exists(filename):  # Delete any existing file
            Log(f"CreateLSTDirectory: {filename} already exists")
            os.remove(filename)

        # Copy the template over, renaming it setup.ftp
        filename=os.path.join(newDirectory, newName)
        shutil.copy(os.path.join(templateDirectory, setupTemplateName), filename)
        return True


    # Save an LST file
    def SaveFile(self, lstfile, name):       # MainWindow(MainFrame)
        try:
            if not lstfile.Save(name):
                Log(f"OnSave failed (1) while trying to save {name}", isError=True)
                MessageBox(f"Failure saving {name}")
                return
            self.MarkAsSaved()
        except:
            Log(f"OnSave failed while trying to save {name}", isError=True)
            Bailout(PermissionError, "OnSave failed (2) when trying to write file "+name, "LSTError")


    def MaybeSetNeedsSavingFlag(self):       # MainWindow(MainFrame)
        s="Editing "+self.lstFilename
        if self.NeedsSaving():
            s=s+" *"        # Add on a change marker if needed
        self.SetTitle(s)


    def RefreshWindow(self)-> None:       # MainWindow(MainFrame)
        self.MaybeSetNeedsSavingFlag()
        self._dataGrid.RefreshWxGridFromDatasource()
        self.ColorFields()


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

    def FanzineNameToDirName(self, s: str) -> str:       # MainWindow(MainFrame)
        return re.sub("[^a-zA-Z0-9\-]+", "_", s)


    def AddChar(self, text: str, code) -> str:       # MainWindow(MainFrame)
        if code == wx.WXK_BACK and len(text) > 0:
            return text[:-1]
        if code < 32 or code > 126:
            return text
        return text+chr(code)


    def OnFanzineNameChar(self, event):       # MainWindow(MainFrame)
        MainFrame.OnFanzineNameChar(self, event)
        # The only time we update the local directory
        fname=self.AddChar(self.tFanzineName.GetValue(), event.GetKeyCode())
        #Log(f"OnFanzineNameChar: {fname=}  {event.GetKeyCode()}")
        converted=self.FanzineNameToDirName(fname)
        dname=self.tDirectoryLocal.GetValue()
        if converted.startswith(dname) or dname.startswith(converted) or converted == dname:
            self.tDirectoryLocal.SetValue(converted)

    def OnFanzineName(self, event):       # MainWindow(MainFrame)
        self.Datasource.FanzineName=self.tFanzineName.GetValue()
        self.RefreshWindow()

    def OnEditors(self, event):       # MainWindow(MainFrame)
        self.Datasource.Editors=self.tEditors.GetValue()
        self.RefreshWindow()

    def OnDates(self, event):       # MainWindow(MainFrame)
        self.Datasource.Dates=self.tDates.GetValue()
        self.RefreshWindow()

    def OnFanzineType(self, event):       # MainWindow(MainFrame)
        self.Datasource.FanzineType=self.tFanzineType.GetSelection()
        self.RefreshWindow()

    #------------------
    def OnTextTopComments(self, event):       # MainWindow(MainFrame)
        if self.Datasource.TopComments is not None and len(self.Datasource.TopComments) > 0:
            self.Datasource.TopComments=self.tTopText.GetValue().split("\n")
        else:
            self.Datasource.TopComments=self.tTopText.GetValue().split("\n")

        self.RefreshWindow()

    # ------------------
    def OnCompleteButton(self, event):       # MainWindow(MainFrame)
        self.Complete=self.rbComplete.GetValue()
        self.RefreshWindow()

    # ------------------
    def OnDirectoryLocal(self, event):       # MainWindow(MainFrame)
        self.DirectoryLocal=self.tDirectoryLocal.GetValue()
        self.RefreshWindow()

    # ------------------
    def OnDirectoryServer(self, event):       # MainWindow(MainFrame)
        self.DirectoryServer=self.tDirectoryServer.GetValue()
        self.RefreshWindow()

    #------------------
    def OnTextLocale(self, event):       # MainWindow(MainFrame)
        self.Datasource.Locale=self.tLocaleText.GetValue().split("\n")
        self.RefreshWindow()

    #------------------
    def OnCredits(self, event):
        self.Credits=self.tCredits.GetValue()
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

    def OnPopupExtractApaMailings(self, event):       # MainWindow(MainFrame)
        self.ExtractApaMailings()
        self.RefreshWindow()


    # Run through the rows and columns and look at the Notes column  If an APA mailing note is present,
    # move it to a "Mailing" column (which may need to be created).  Remove the text from the Notes column.
    # Find the Notes column. If there is none, we're done.
    def ExtractApaMailings(self):       # MainWindow(MainFrame)
        if "Notes" in self._Datasource.ColHeaders:
            notescol=self._Datasource.ColHeaders.index("Notes")

            # Look through the rows and extract mailing info, if any
            # We're looking for things like [for/in] <apa> nnn
            mailings=[""]*len(self._Datasource.Rows)     # Collect the mailing into in this until later when we have a chance to put it in its own column
            apas: list[str]=["FAPA", "SAPS", "OMPA", "ANZAPA", "VAPA", "FLAP"]
            for i, row in enumerate(self._Datasource.Rows):
                for apa in apas:
                    # Sometimes the apa reference is part of a hyperlink.  Look for that, first
                    pat=f"(<a HREF=.+>)(?:for|in|[^a-zA-Z]*){apa}\s+([0-9]+[AB]?)(</a>)[,;]?"
                    m=re.search(pat, row[notescol])
                    if m is not None:
                        # We found a mailing inside a hyperlink.  Add it to the temporary list of mailings and remove it from the mailings column
                        mailings[i]=m.groups()[0]+apa+" "+m.groups()[1]+m.groups()[2]
                        row[notescol]=re.sub(pat, "", row[notescol]).strip()

                    pat=f"(?:for|in|)[^a-zA-Z]+{apa}\s+([0-9]+)[,;]?"
                    m=re.search(pat, row[notescol])
                    if m is not None:
                        # We found a mailing.  Add it to the tenmorary list of mailings and remove it from the mailings column
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
    def Cells(self) -> list[str]:      # FanzineTableRow(GridDataRowClass)
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



    def Signature(self) -> int:        # FanzineTablePage(GridDataSource)
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

    def InsertEmptyRows(self, insertat: int, num: int=1) -> None:        # FanzineTablePage(GridDataSource)
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