from dataclasses import dataclass, field
import re

from HelpersPackage import CanonicizeColumnHeaders, Bailout
from FanzineIssueSpecPackage import FanzineDate

# #----------------------------------
# def InterpretIssueSpec(s: str) -> float:
#     if s is None:
#         return 0
#     s=s.strip()
#     if len(s) == 0:
#         return 0
#
#     # First thing to try is to just interpret the string as a number
#     try:
#         return float(s)
#     except:
#         # well, that didn't work!
#         # See if it can be interpreted as a range a-b
#         if "-" in s:
#             try:
#                 return float(s.split("-")[0])      # We only care about the first number in a range
#             except:
#                 # That also failed.  Just fall through to the ignominious end.
#                 pass
#     Bailout(ValueError, "LSTFile.InterpretIssueSpec can't interpret '"+s+"'", "LSTError")



@dataclass(order=False)
class LSTFile:
    FirstLine: str=""
    TopTextLines: list[str] = field(default_factory=list)
    BottomTextLines: list[str] = field(default_factory=list)
    ColumnHeaders: list[str] = field(default_factory=list)        # The actual text of the column headers
    ColumnHeaderTypes: list[str] = field(default_factory=list)    # The single character types for the corresponding ColumnHeaders
    SortColumn: dict[str, float]   = field(default_factory=dict)# The single character type(s) of the sort column(s).  Sort on whole num="W", sort on Vol+Num ="VN", etc.
    Rows: list[list[str]] = field(default_factory=list)



    # #--------------------------------
    # # Using the columns specified, find the best location to insert the row
    # # In all cases we assume that the LST file is sorted in increasing order, so we stop the first time we hit a larger value
    # # Note that we may return a negative index, which means to prepend the row.
    # def GetBestRowIndex(self, bestCols: str, newRow: list) -> float:
    #     # The choices are
    #     #   YM -- use year and month
    #     #   VN -- use volume and number
    #     #   W -- use whole number
    #     #   "" -- use the title
    #     if bestCols == "Whole":
    #         if "Whole" not in self.ColumnHeaderTypes:
    #             Bailout(ValueError, "LSTFile: GetBestRowIndex - can't find columnheader="+bestCols, "LSTError")
    #         col=self.ColumnHeaderTypes.index("Whole")
    #         for i in range(0, len(self.Rows)):
    #             if InterpretIssueSpec(self.Rows[i][col]) > InterpretIssueSpec(newRow[col]):
    #                 return i+0.5
    #         return len(self.Rows)+1
    #
    #     if bestCols == "Vol+Num":
    #         if "Volume" not in self.ColumnHeaderTypes or "Number" not in self.ColumnHeaderTypes:
    #             Bailout(ValueError, "LSTFile: GetBestRowIndex - can't find columnheader="+bestCols, "LSTError")
    #         colV=self.ColumnHeaderTypes.index("Volume")
    #         colN=self.ColumnHeaderTypes.index("Number")
    #         for i in range(0, len(self.Rows)):
    #             if InterpretIssueSpec(self.Rows[i][colV]) > InterpretIssueSpec(newRow[colV]):
    #                 return i+0.5
    #             if InterpretIssueSpec(self.Rows[i][colV]) == InterpretIssueSpec(newRow[colV]) and InterpretIssueSpec(self.Rows[i][colN]) == InterpretIssueSpec(newRow[colN]):
    #                 return i+0.5
    #         return len(self.Rows)+1
    #
    #     if bestCols == "Year&Month":
    #         if "Year" not in self.ColumnHeaderTypes:   # We don't actually need a month in every column for this to be useful
    #             Bailout(ValueError, "LSTFile: GetBestRowIndex - can't find columnheader="+bestCols, "LSTError")
    #         colY=self.ColumnHeaderTypes.index("Year")
    #         colM=self.ColumnHeaderTypes.index("Month")
    #         fd=FanzineDate().Match(newRow[colM]+" "+newRow[colY])
    #         y=fd.Year
    #         m=fd.Month
    #         for i in range(0, len(self.Rows)):
    #             fd=FanzineDate().Match(self.Rows[i][colM]+" "+self.Rows[i][colY])
    #             if fd.Year > y or (fd.Year == y and fd.Month > m):
    #                 return i+0.5
    #         return len(self.Rows)+1
    #
    #     # OK, try to sort of title which is always col 1
    #     for i in range(0, len(self.Rows)):
    #         if InterpretIssueSpec(self.Rows[i][1]) > InterpretIssueSpec(newRow[1]):
    #             return i+0.5
    #     return len(self.Rows)+1



    # #--------------------------------
    # # Figure out what the column headers are (they frequently have variant names)
    # # Get some statistics on which columns have info in them, also.
    # def IdentifyColumnHeaders(self) -> None:
    #     # The trick here is that "Number" (in its various forms) is used vaguely: Sometimes it means whole number and sometimes volume number
    #     # First identify all the easy ones
    #     self.ColumnHeaderTypes=[]
    #     for header in self.ColumnHeaders:
    #         self.ColumnHeaderTypes.append(CanonicizeColumnHeaders(header))
    #
    #     # In cases where we have a num *and* a vol, the num is treated as the issue's volume number; else its treated as the issue's whole number
    #     if "Volume" not in self.ColumnHeaderTypes:
    #         for i in range(0, len(self.ColumnHeaderTypes)):
    #             if self.ColumnHeaderTypes[i] == "Number":
    #                 self.ColumnHeaderTypes[i]="Whole"
    #
    #     # Now gather statistics on what columns have data.  This will be needed to determine the best columns to use for inserting new data
    #     self.MeasureSortColumns()


    # #---------------------------------
    # # Take the supplied header types and use the row statistics to determine what column to use to do an insertion.
    # def GetInsertCol(self, row: list) -> str:
    #     if len(self.SortColumn) == 0:
    #         Bailout(ValueError, "class LSTFile: GetInsertCol called while SortColumn is None", "LSTError")
    #
    #     # ColumnHeaderTypes is a list of the type letters for which this issue has data.
    #     possibleCols={}
    #     if "Whole" in self.ColumnHeaderTypes:
    #         i=self.ColumnHeaderTypes.index("Whole")
    #         if row[i] is not None and row[i] != "":
    #             if self.SortColumn["Whole"] > .75:
    #                 possibleCols["Whole"]=self.SortColumn["Whole"]
    #     if "Volume" in self.ColumnHeaderTypes and "Number" in self.ColumnHeaderTypes:
    #         i=self.ColumnHeaderTypes.index("Volume")
    #         if row[i] is not None and row[i] != "":
    #             i=self.ColumnHeaderTypes.index("Number")
    #             if row[i] is not None and row[i] != "":
    #                 if self.SortColumn["volnum"] > .75:
    #                     possibleCols["VN"]=self.SortColumn["volnum"]
    #     if "Year" in self.ColumnHeaderTypes and "Month" in self.ColumnHeaderTypes:
    #         i=self.ColumnHeaderTypes.index("Year")
    #         if row[i] is not None and row[i] != "":
    #             if self.SortColumn["Year&Month"] > .75:
    #                 possibleCols["Year&Month"]=self.SortColumn["Year&Month"]
    #
    #     if len(possibleCols) == 0:
    #         return ""
    #     keyBestCol=-1
    #     valBestCol=0
    #     for item in possibleCols.items():
    #         if item[1] > valBestCol:
    #             valBestCol=item[1]
    #             keyBestCol=item[0]
    #     return keyBestCol


    # #---------------------------------
    # # Look through the data and determine the likely column we're sorted on.
    # # The column will be (mostly) filled and will be in ascending order.
    # # This is necessarily based on heuristics and is inexact.
    # # TODO: For the moment we're going to ignore whether the selected column is in fact sorted. We need to fix this later.
    # def MeasureSortColumns(self) -> None:
    #     # A sort column must either be the title or have a type code
    #     # Start by looking through the columns that have a type code and seeing which are mostly or completely filled.  Do it in order of perceived importance.
    #     fW=self.CountFilledCells("Whole")
    #     fV=self.CountFilledCells("Volume")
    #     fN=self.CountFilledCells("Number")
    #     fY=self.CountFilledCells("Year")
    #     fM=self.CountFilledCells("Month")
    #
    #     self.SortColumn={"Whole": fW, "Vol+Num": fV*fN, "Year&Month": fY*fM}

    # #---------------------------------
    # # Count the number of filled cells in the column with the specified type code
    # # Returns a floating point fraction between 0 and 1
    # def CountFilledCells(self, colType: str) -> float:
    #     try:
    #         index=self.ColumnHeaderTypes.index(colType)
    #     except:
    #         return 0
    #
    #     # Count the number of filled-in values for this type
    #     num=0
    #     for row in self.Rows:
    #         if index < len(row) and row[index] is not None and len(row[index]) > 0:
    #             num+=1
    #     return num/len(self.Rows)


    #---------------------------------
    # Read an LST file, returning its contents as an LSTFile
    def Read(self, filename: str) -> None:

        # Open the file, read the lines in it and strip leading and trailing whitespace (including '\n')
        try:
            open(filename, "r")
        except Exception as e:
            Bailout(e, "Couldn't open "+filename+" for reading", "LST.read")

        # This is really ugly!  One LST file (that I know of) has the character 0x92 (a curly quote) which is somehow bogus (unclear how)
        # I prefer to use just plain-old-Python for reading the LST file, but it triggers an exception on the 0x92
        # In that case, I read the file using cp1252, a Windows character set which is OK with 0x92.
        try:
            contents=list(open(filename))
        except:
            f=open(filename, mode="rb")
            contents=f.read()
            f.close()
            contents=contents.decode("cp1252").split("\r\n")
        contents=[l.strip() for l in contents]

        if len(contents) == 0:
            return

        # Collapse all runs of empty lines down to a single empty line
        output=[]
        lastlinemepty=False
        for c in contents:
            if len(c) == 0:
                if lastlinemepty:
                    continue        # Skip the line
                lastlinemepty=True
            else:
                lastlinemepty=False
            output.append(c)
        contents=output
        if len(contents) == 0:
            return

        # The structure of an LST file is
        #   Header line
        #   (blank line)
        #   Repeated 0 or more times:
        #       <P>line...</P> blah, blah, blah
        #           (This may extend over many lines)
        #       (blank line)
        #   Index table headers
        #   (blank line)
        #   Repeated 0 or more times:
        #       Index table line
        # The table contains *only* tablelines (see below) and empty lines
        # Then maybe some more random bottom text lines


        # The header is ill-defined stuff
        # ALL table lines consist of one instance of either of the characters ">" or ";" and two more of ";", all separated by spans of other stuff.
        # No lines of that sort appear in the toplines section

        # The first line is the first line
        self.FirstLine=contents[0]
        contents=contents[1:]   # Drop the first line, as it has been processed

        def IsTableLine(s: str) -> bool:
            # Column header pattern is four repetitions of (a span of at least one character followed by a semicolon)
            return re.search(".+[>;].+;.+;.+;", s) is not None

        # Go through the lines one-by-one, looking for a table line. Until that is found, accumulate toptext lines
        self.TopTextLines=[]
        self.BottomTextLines=[]
        rowLines=[]
        pasttable=False
        for line in contents:
            line=line.strip()
            if len(rowLines) > 0 and not pasttable and len(line) == 0:
                continue    # Skip blank lines within the table
            if IsTableLine(line):
                rowLines.append(line)
            else:
                if len(rowLines) == 0:  # Non table lines go in top text lines until the table has been found; then they go in bottom text lines
                    self.TopTextLines.append(line)
                else:
                    self.BottomTextLines.append(line)
                    pasttable=True  # Now we can't go back to adding on table lines

        if len(self.TopTextLines) == 0:
            Bailout(ValueError, "No top text lines found", "LST Generator: Read LST file")
        if len(rowLines) == 0:
            Bailout(ValueError, "No row lines found", "LST Generator: Read LST file")
        if len(rowLines) == 1:
            Bailout(ValueError, "Only one row line found -- either header or contents missing", "LST Generator: Read LST file")

        # The column headers are in the first table line
        colHeaderLine=rowLines[0]
        rowLines=rowLines[1:]

        # Change the column headers to their standard form
        self.ColumnHeaders=[CanonicizeColumnHeaders(h.strip()) for h in colHeaderLine.split(";") if len(h) > 0]

        # And likewise the rows
        # We need to do some special processing on the first column
        # There are three formats that I've found so far.
        # (1) The most common format has (filename>displayname) in the first column. We treat the ">" as a ";" for the purposes of the spreadsheet. (We'll undo this on save.)
        #   This format is to a specific issue of a fanzine.
        # (2) An especially annoying one is where fanzine data has been entered, but there's no actual scan.
        #   We deal with this by adding a ">" at the start of the line and then handling it like case (1)
        # (3) A less common format is has "<a HREF="http://fanac.org/fanzines/abc/">xyz" where abc is the directory name of the target index.html, and xyz is the display name.
        #   Normally, abc seems to be the same as xyz, but we'll make allowance for the possibility it me be different.
        #   In this second case, the whole HREF is too big, so we'll hide it and just show "<abc>" in col 1
        #   (There's actually two versions of case (3), with and without 'www.' preceding the URL
        self.Rows=[]
        for row in rowLines:
            col1, colrest=row.split(";", 1)
            # Look for case (2), and add the ">" to make it case 1
            if col1.find(">") == -1:    #If there's no ">" in col1, put it there.
                row=">"+row
                col1=row.split(";", 1)[0]

            # The characteristic of Case (3) is that it starts "<a href...".  Look for that and handle it, turning it into Case (1)
            r=col1
            r=re.sub("<a href=.*?/fanzines/", "<", r, re.IGNORECASE)
            if len(col1) != len(r):
                row=r.replace('">', '>>')+";"+colrest      # Get rid of the trailing double quote in the URL and add in an extra '>' to designate that it's Case 3

            # Now we can handle them all as case (1)
            if row.find(">>") != -1 and row.find(">>") < row.find(";"):
                row=row[:row.find(">>")]+">;"+row[row.find(">>")+2:]
            elif row.find(">") != -1 and row.find(">") < row.find(";"):
                row=row[:row.find(">")]+";"+row[row.find(">")+1:]

            # If the line has no content (other than ">" and ";" and whitespace, skip it.
            if re.match("^[>;\s]*$", row):
                continue

            # Split the row on ";"
            self.Rows.append([h.strip() for h in row.split(";")])

        # Define the grid's columns
        # First add the invisible column which is actually the link destination
        # It's the first part of the funny xxxxx>yyyyy thing in the LST file's 1st column
        self.ColumnHeaders=["Filename"]+self.ColumnHeaders

        # If any rows are shorter than the headers row, pad them with blanks
        for row in self.Rows:
            if len(row) < len(self.ColumnHeaders):
                row.extend([""]*(len(self.ColumnHeaders)-len(row)))

        # Run through the rows and columns and look at the Notes column  If an APA mailing note is present,
        # move it to a "Mailing" column (which may need to be created).  Remove the text from the Notes column.
        # Find the Notes column. If there is none, we're done.
        if "Notes" in self.ColumnHeaders:
            notescol=self.ColumnHeaders.index("Notes")

            # Look through the rows and extract mailing info, if any
            # We're looking for things like [for/in] <apa> nnn
            apas: list[str]=["FAPA", "SAPS", "OMPA", "ANZAPA", "VAPA"]
            mailing=[""]*len(self.Rows)
            found=False
            for i, row in enumerate(self.Rows):
                for apa in apas:
                    pat=f"(?:for|in|)[^a-zA-Z]+{apa}\s+([0-9]+)"
                    m=re.search(pat, row[notescol])
                    if m is not None:
                        mailing[i]=apa+" "+m.groups()[0]
                        row[notescol]=re.sub(pat, "", row[notescol]).strip()
                        found=True

            if found:
                # Append a mailing column if needed
                if "Mailing" not in self.ColumnHeaders:
                    self.ColumnHeaders.append("Mailing")
                mailcol=self.ColumnHeaders.index("Mailing")

                for i, row in enumerate(self.Rows):
                    if len(row) < len(self.ColumnHeaders):
                        row.append("")
                    row[mailcol]=mailing[i]


    # ---------------------------------
    # Format the data and save it as an LST file on disk
    def Save(self, filename: str) -> None:

        content=[self.FirstLine, ""]

        if len(self.TopTextLines) > 0:
            for line in self.TopTextLines:
                content.append(line)
            content.append("")

        # Column headers.  Need to remove the "Filename" column which was added when the LST file was loaded.  It is the 1st col.
        content.append("; ".join(self.ColumnHeaders[1:]))

        maxlen=len(self.ColumnHeaders)

        # Rows
        for row in self.Rows:
            if len(row) < 3:    # Smallest possible LST file
                continue

            if len(row) > maxlen:
                row=row[:maxlen]    # Truncate if necessary

            # We have to join the first two elements of row into a single element to deal with the LST's odd format. (See the reading code, above.)
            # We also have to be aware of the input Case (3) and handle that correctly
            if len(row[0]) == 0 and len(row[1]) > 0:
                out=row[1]    # If the first column is empty, then we have a case (2) row with no link and need to fudge it a bit.
            elif len(row[0]) > 0:
                # Case (3) is marked by the first column beginning and ending with pointy brackets
                if row[0][0] == "<" and row[0][-1:] == ">":
                    out='<a href="https://fanac.org/fanzines/'+row[0][1:-1]+'">'+row[1]
                else:
                    out=row[0] + ">" + row[1]   # Case (1)
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
