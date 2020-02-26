from dataclasses import dataclass
import re

from HelpersPackage import CanonicizeColumnHeaders, ConsumeHTML, Bailout
from FanzineIssueSpecPackage import FanzineDate
from Log import Log

#----------------------------------
def InterpretIssueSpec(s: str):
    if s is None:
        return 0
    s=s.strip()
    if len(s) == 0:
        return 0

    # First thing to try is to just interpret the string as a number
    try:
        return float(s)
    except:
        # well, that didn't work!
        # See if it can be interpreted as a range a-b
        if "-" in s:
            try:
                return float(s.split("-")[0])      # We only care about the first number in a range
            except:
                # That also failed.  Just fall through to the ignominious end.
                pass
    Bailout(ValueError, "LSTFile.InterpretIssueSpec can't interpret '"+s+"'", "LSTError")



@dataclass(order=False)
class LSTFile:
    FirstLine: str=None
    TopTextLines: list=None
    BottomTextLines: list=None
    ColumnHeaders: list=None        # The actual text of the column headers
    ColumnHeaderTypes: list=None    # The single character types for the corresponding ColumnHeaders
    SortColumn: dict=None           # The single character type(s) of the sort column(s).  Sort on whole num="W", sort on Vol+Num ="VN", etc.
    Rows: list=None


    #--------------------------------
    # Using the columns specified, find the best location to insert the row
    # In all cases we assume that the LST file is sorted in increasing order, so we stop the first time we hit a larger value
    # Note that we may return a negative index, which means to prepend the row.
    def GetBestRowIndex(self, bestCols: str, newRow: list) -> float:
        # The choices are
        #   YM -- use year and month
        #   VN -- use volume and number
        #   W -- use whole number
        #   "" -- use the title
        if bestCols == "Whole":
            if "Whole" not in self.ColumnHeaderTypes:
                Bailout(ValueError, "LSTFile: GetBestRowIndex - can't find columnheader="+bestCols, "LSTError")
            col=self.ColumnHeaderTypes.index("Whole")
            for i in range(0, len(self.Rows)):
                if InterpretIssueSpec(self.Rows[i][col]) > InterpretIssueSpec(newRow[col]):
                    return i+0.5
            return len(self.Rows)+1

        if bestCols == "Vol+Num":
            if "Volume" not in self.ColumnHeaderTypes or "Number" not in self.ColumnHeaderTypes:
                Bailout(ValueError, "LSTFile: GetBestRowIndex - can't find columnheader="+bestCols, "LSTError")
            colV=self.ColumnHeaderTypes.index("Volume")
            colN=self.ColumnHeaderTypes.index("Number")
            for i in range(0, len(self.Rows)):
                if InterpretIssueSpec(self.Rows[i][colV]) > InterpretIssueSpec(newRow[colV]):
                    return i+0.5
                if InterpretIssueSpec(self.Rows[i][colV]) == InterpretIssueSpec(newRow[colV]) and InterpretIssueSpec(self.Rows[i][colN]) == InterpretIssueSpec(newRow[colN]):
                    return i+0.5
            return len(self.Rows)+1

        if bestCols == "Year&Month":
            if "Year" not in self.ColumnHeaderTypes:   # We don't actually need a month in every column for this to be useful
                Bailout(ValueError, "LSTFile: GetBestRowIndex - can't find columnheader="+bestCols, "LSTError")
            colY=self.ColumnHeaderTypes.index("Year")
            colM=self.ColumnHeaderTypes.index("Month")
            fd=FanzineDate.ParseGeneralDateString(newRow[colM]+" "+newRow[colY])
            y=fd.Year
            m=fd.Month
            for i in range(0, len(self.Rows)):
                fd=FanzineDate.ParseGeneralDateString(self.Rows[i][colM]+" "+self.Rows[i][colY])
                if fd.Year > y or (fd.Year == y and fd.Month > m):
                    return i+0.5
            return len(self.Rows)+1

        # OK, try to sort of title which is always col 1
        for i in range(0, len(self.Rows)):
            if InterpretIssueSpec(self.Rows[i][1]) > InterpretIssueSpec(newRow[1]):
                return i+0.5
        return len(self.Rows)+1



    #--------------------------------
    # Figure out what the column headers are (they frequently have variant names)
    # Get some statistics on which columns have info in them, also.
    def IdentifyColumnHeaders(self) -> None:
        # The trick here is that "Number" (in its various forms) is used vaguely: Sometimes it means whole number and sometimes volume number
        # First identify all the easy ones
        self.ColumnHeaderTypes=[]
        for header in self.ColumnHeaders:
            self.ColumnHeaderTypes.append(CanonicizeColumnHeaders(header))

        # In cases where we have a num *and* a vol, the num is treated as the issue's volume number; else its treated as the issue's whole number
        if "Volume" not in self.ColumnHeaderTypes:
            for i in range(0, len(self.ColumnHeaderTypes)):
                if self.ColumnHeaderTypes[i] == "Number":
                    self.ColumnHeaderTypes[i]="Whole"

        # Now gather statistics on what columns have data.  This will be needed to determine the best colums to use for inserting new data
        self.MeasureSortColumns()


    #---------------------------------
    # Take the supplied header types and use the row statistics to determine what column to use to do an insertion.
    def GetInsertCol(self, row: list) -> str:
        if self.SortColumn is None:
            Bailout(ValueError, "class LSTFile: GetInsertCol called while SortColumn is None", "LSTError")

        # ColumnHeaderTypes is a list of the type letters for which this issue has data.
        possibleCols={}
        if "Whole" in self.ColumnHeaderTypes:
            i=self.ColumnHeaderTypes.index("Whole")
            if row[i] is not None and row[i] != "":
                if self.SortColumn["Whole"] > .75:
                    possibleCols["Whole"]=self.SortColumn["Whole"]
        if "Volume" in self.ColumnHeaderTypes and "Number" in self.ColumnHeaderTypes:
            i=self.ColumnHeaderTypes.index("Volume")
            if row[i] is not None and row[i] != "":
                i=self.ColumnHeaderTypes.index("Number")
                if row[i] is not None and row[i] != "":
                    if self.SortColumn["volnum"] > .75:
                        possibleCols["VN"]=self.SortColumn["volnum"]
        if "Year" in self.ColumnHeaderTypes and "Month" in self.ColumnHeaderTypes:
            i=self.ColumnHeaderTypes.index("Year")
            if row[i] is not None and row[i] != "":
                if self.SortColumn["Year&Month"] > .75:
                    possibleCols["Year&Month"]=self.SortColumn["Year&Month"]

        if len(possibleCols) == 0:
            return ""
        keyBestCol=-1
        valBestCol=0
        for item in possibleCols.items():
            if item[1] > valBestCol:
                valBestCol=item[1]
                keyBestCol=item[0]
        return keyBestCol


    #---------------------------------
    # Look through the data and determine the likely column we're sorted on.
    # The column will be (mostly) filled and will be in ascending order.
    # This is necessarily based on heuristics and is inexact.
    # TODO: For the moment we're going to ignore whether the selected column is in fact sorted. We need to fix this later.
    def MeasureSortColumns(self) -> None:
        # A sort column must either be the title or have a type code
        # Start by looking through the columns that have a type code and seeing which are mostly or completely filled.  Do it in order of perceived importance.
        fW=self.CountFilledCells("Whole")
        fV=self.CountFilledCells("Volume")
        fN=self.CountFilledCells("Number")
        fY=self.CountFilledCells("Year")
        fM=self.CountFilledCells("Month")

        self.SortColumn={"Whole": fW, "Vol+Num": fV*fN, "Year&Month": fY*fM}

    #---------------------------------
    # Count the number of filled cells in the column with the specified type code
    # Returns a floating point fraction between 0 and 1
    def CountFilledCells(self, colType: str) -> float:
        try:
            index=self.ColumnHeaderTypes.index(colType)
        except:
            return 0

        # Count the number of filled-in values for this type
        num=0
        for row in self.Rows:
            if index < len(row) and row[index] is not None and len(row[index]) > 0:
                num+=1
        return num/len(self.Rows)


    #---------------------------------
    # Read an LST file, returning its contents as an LSTFile
    def Read(self, filename: str) -> None:

        # Open the file, read the lines in it and strip leading and trailing whitespace (including '\n')
        try:
            fop=open(filename, "r")
        except Exception as e:
            Bailout(e, "Couldn't open "+filename+" for reading", "LST.read")
        contents=list(open(filename))
        contents=[l.strip() for l in contents]

        if contents is None or len(contents) == 0:
            return

        # The structure of an LST file is
        #   Header line
        #   (blank line)
        #   Repeated 0 or more times:
        #       <P>line...</P>
        #           (This may extend ove many lines)
        #       (blank line)
        #   Index table headers
        #   (blank line)
        #   Repeated 0 or more times:
        #       Index table line

        # I will not enforce the blank lines unless forced to. So for now, remove all empty lines
        contents=[l for l in contents if len(l)>0]

        firstLine=contents[0]
        contents=contents[1:]   # Drop the first line, as it has been processed

        # The top text lines are contained in <p>...</p> pairs
        # Collect them.
        topTextLines=[]
        while len(contents) > 0:
            pFound=ConsumeHTML(contents, topTextLines, "p")
            h3Found=ConsumeHTML(contents, topTextLines, "h3")
            if not pFound and not h3Found:
                break

        # The column headers are in the first line
        colHeaderLine=contents[0]
        contents=contents[1:]   # Drop them so we can read the rest later.

        rowLines=[]
        while len(contents) > 0:
            # There may be <p>-bracketed bumpf on the bottom, also.  Check for this and bail if found.
            if contents[0].lower().startswith("<p>"):
                break
            rowLines.append(contents[0])
            contents=contents[1:]

        bottomTextLines=[]
        while len(contents) > 0:
            pFound=ConsumeHTML(contents, bottomTextLines, "p")
            h3Found=ConsumeHTML(contents, bottomTextLines, "h3")
            if not pFound and not h3Found:
                break

        # The firstLine and the topTestLines and bottomTextLines are usable as-is, so we just store them
        self.FirstLine=firstLine
        self.TopTextLines=topTextLines
        self.BottomTextLines=bottomTextLines

        # We need to parse the column headers
        self.ColumnHeaders=[CanonicizeColumnHeaders(h.strip()) for h in colHeaderLine.split(";")]

        # And likewise the rows
        # Note that we have the funny structure (filename>displayname) of the first column. We treat the ">" as a ";" for the purposes of the spreadsheet. (We'll undo this on save.)
        self.Rows=[]
        for row in rowLines:
            # Turn the first ">" before the first ";" into a ";"
            # if there is none, insert one at the start of the line.
            #       (This is one of those bozo rows without scans and will need to be dealt with on write-out, also.)
            if row.find(">") == -1 or (row.find(">") > row.find(";")):  # Case 1 is no '>', case 2 is '>' follows ';', so it's text not delimiter
                row=">"+row
            if row.find(">") != -1 and row.find(">") < row.find(";"):
                row=row[:row.find(">")]+";"+row[row.find(">")+1:]
            # If the line has no content (other than ">" and ";" and whitespace, skip it.
            if re.match("^[>;\s]*$", row):
                continue
            # Split the row on ";"
            self.Rows.append([h.strip() for h in row.split(";")])

    # ---------------------------------
    # Save an LST file back to disk
    def Save(self, filename: str) -> None:

        content=[self.FirstLine, ""]
        if len(self.TopTextLines) > 0:
            for line in self.TopTextLines:
                content.append(line)
            content.append("")

        # Next we determine the last column to have non-blank content in any cell (including the header)
        # Helper function
        def Length(row: list) -> int:
            temp=row
            while len(temp) > 0 and len(temp[-1:][0].strip()) == 0:
                temp=temp[:-1]
            return len(temp)

        # How long is the longest row?
        maxlen=Length(self.ColumnHeaders)
        for row in self.Rows:
            l=Length(row)
            maxlen=max(maxlen, l)

        # Column headers
        if len(self.ColumnHeaders) > maxlen:
            self.ColumnHeaders=self.ColumnHeaders[:maxlen]
        content.append("; ".join(self.ColumnHeaders))
        content.append("")

        # Rows
        for row in self.Rows:
            if len(row) < 3:    # Smallest possible LST file
                continue

            if len(row) > maxlen:
                row=row[:maxlen]    # Truncate if necessary

            # We have to join the first two elements of row into a single element to deal with the LST's odd format
            if len(row[0]) == 0 and len(row[1]) > 0:
                out=row[1]    # If the first column is empty, then we have a bozo row with no link and need to fudge it a bit.
            elif len(row[0]) > 0:
                out=row[0] + ">" + row[1]   # The normal case
            else:
                out=" "     # Leave the first column entirely blank. (Shouldn't happen, but...)
            # Now append the rest of the columns
            out=out+ "; " + ("; ".join(row[2:]))
            if not re.match("^[>;\s]*$", out):  # Save only null rows
                content.append(out)

        if len(self.BottomTextLines) > 0:
            for line in self.BottomTextLines:
                content.append(line)
            content.append("")

        # And write it out
        with open(filename, "w+") as f:
            f.writelines([c+"\n" for c in content])
