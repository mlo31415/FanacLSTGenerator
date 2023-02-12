import os

from GenGUIClass import NewFanzineDialog
from HelpersPackage import FanzineNameToDirName
from WxHelpers import AddChar

class NewFanzineWindow(NewFanzineDialog):

    def __init__(self, parent, rootDirectory: str):
        self._directory: str=""
        self._fanzineName=""
        self._output: str=""
        self._rootDirectory: str=rootDirectory
        NewFanzineDialog.__init__(self, parent)

    @property
    def Directory(self) -> str:
        return self._directory
    @Directory.setter
    def Directory(self, s: str):
        self._directory=s

    @property
    def FanzineName(self) -> str:
        return self._fanzineName
    @FanzineName.setter
    def FanzineName(self, s: str):
        self._fanzineName=s

    def OnCharFanzine( self, event ):
        # The only time we update the local directory
        fname=AddChar(self.tFanzineName.GetValue(), event.GetKeyCode())
        self.tFanzineName.SetValue(fname)
        self.tDirName.SetValue(FanzineNameToDirName(self.tFanzineName.GetValue()).upper())
        self.tFanzineName.SetInsertionPoint(999)    # Make sure the cursor stays at the end of the string

    def OnTextFanzine( self, event ):
        self.tDirName.SetValue(FanzineNameToDirName(self.tFanzineName.GetValue()))


    def OnCreate(self, event):
        self._directory=self.tDirName.GetValue()
        self._fanzineName=self.tFanzineName.GetValue()

        if self._directory == "":
            self.tOutputBox.SetValue("You must supply a directory name")
            return
        if self._fanzineName == "":
            self.tOutputBox.SetValue("You must supply a fanzine name")
            return

        self._output=""
        self._output+=f"Checking directory {self._directory}...\n"
        self._output+=f"     in root {self._rootDirectory}\n"
        self.tOutputBox.SetValue(self._output)
        if os.path.exists(os.path.join(self._rootDirectory, self._directory)):
            self._output+="Name unavailable\n"
            self._output+=f"Directory named {self._directory} already exists in root directory\n"
            self.tOutputBox.SetValue(self._output)
            return
        self._output+=f"Directory named {self._directory} is OK\n"
        self.tOutputBox.SetValue(self._output)

        self.Destroy()

    def OnCancel(self, event):
        self.Destroy()

