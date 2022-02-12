from dataclasses import dataclass, field
import re

from HelpersPackage import CanonicizeColumnHeaders, Bailout, StripSpecificTag


@dataclass(order=False)
class LSTFile:
    FanzineName: str=""
    Editors: str=""
    Dates: str=""
    FanzineType: str=""

    TopComments: list[str] = field(default_factory=list)
    Locale: list[str] = field(default_factory=list)
    ColumnHeaders: list[str] = field(default_factory=list)        # The actual text of the column headers
    #ColumnHeaderTypes: list[str] = field(default_factory=list)    # The single character types for the corresponding ColumnHeaders
    #SortColumn: dict[str, float]   = field(default_factory=dict)# The single character type(s) of the sort column(s).  Sort on whole num="W", sort on Vol+Num ="VN", etc.
    Rows: list[list[str]] = field(default_factory=list)


    #---------------------------------
    # Read an LST file, returning its contents as an LSTFile
    def Load(self, filename: str) -> None:

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
        for c in contents:
            if not c:   # If the current line is empty
                if output and output[-1]:   # Was the last line empty too?
                    continue        # Yes: Skip the current line
            output.append(c)
        contents=output
        if not contents:
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

        # The first non-empty line is the first line. (Since we've already collapsed runs of multiple empty lines to one, we only have to check the 1st line.)
        if not contents[0]:
            contents.pop(0)
        firstLine=contents.pop(0)
        # The Firstline is Name;Editor;Dates;Type, so parse it into fields
        parsed=firstLine.split(";")
        if len(parsed) > 0:
            self.FanzineName=parsed[0]
        if len(parsed) > 1:
            self.Editors=parsed[1]
        if len(parsed) > 2:
            self.Dates=parsed[2]
        if len(parsed) > 3:
            self.FanzineType=parsed[3]

        # Inline function to test if a line is a table row
        # Because we have already extracted the top line (which looks line a table line), we can use this function to detect the column headers
        def IsTableLine(s: str) -> bool:
            # Column header pattern is at least three repetitions of <a span of at least one character followed by a semicolon or '>'>
            # And there's also the messiness of the first column having an A>B structure
            return re.search(".+[>;].+;.+;", s) is not None

        # Go through the lines one-by-one, looking for a table line. Until that is found, accumulate toptext lines
        # Be on the lookout for Locale lines (bracketed by <<fanac-type>>)
        # Once we hit the table, we move to a new loop.
        self.TopComments=[]
        self.Locale=[]
        rowLines=[]     # This will accumulate the column header line and row lines
        colHeaderLine=""
        inFanacType=False
        while contents:
            line=contents.pop(0).strip()    # Grab the top line
            if not line:
                continue    # Skip blank lines
            if IsTableLine(line):   # If we come to a table line, we have found the colum headers (which must start the table). Save it and then drop down to table row processing.
                colHeaderLine=line
                break
            # Once we find a line that starts with <fanac-type>, we send the lines to local until we find a line that ends with </fanac-type>
            if inFanacType or line.startswith("<fanac-type>"):
                line=StripSpecificTag(StripSpecificTag(line, "fanac-type"), "h2")   # But we don't want to show the tags
                self.Locale.append(line)
                if not line.endswith("</fanac-type>"):
                    inFanacType=True
                    continue
                inFanacType=False
            else:
                self.TopComments.append(line)

        # Time to read the table header and rows
        while contents:
            line=contents.pop(0).strip()    # Grab the top line
            if not line:
                continue    # Skip blank lines
            if not IsTableLine(line):
                break       # If we hit a line that is not a table line, we must be past the table
            rowLines.append(line)

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
            if col1.find(">") == -1:    # If there's no ">" in col1, put it there.
                row=">"+row.strip() # Because there are some cases where there is no filename, the ">" is missing and we need to supply one
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

            # If the line has no content (other than ">" and ";" and whitespace, append an empty line
            if re.match("^[>;\s]*$", row):
                self.Rows.append([""]*len(self.ColumnHeaders))
                continue

            # Split the row on ";" and append it
            self.Rows.append([h.strip() for h in row.split(";")])

        # Define the grid's columns
        # First add the invisible column which is actually the link destination
        # It's the first part of the funny xxxxx>yyyyy thing in the LST file's 1st column
        self.ColumnHeaders=["Filename"]+self.ColumnHeaders

        # If any rows are shorter than the headers row, pad them with blanks
        for row in self.Rows:
            if len(row) < len(self.ColumnHeaders):
                row.extend([""]*(len(self.ColumnHeaders)-len(row)))

        # If there are any rows with a pdf we want to make sure they are listed as PDF in a PDF column
        # Add the PDF column if necessary

        # We only do this if there are pdf files
        if any([row[0].lower().endswith(".pdf") for row in self.Rows]):
            # Do we need to add a PDF column?
            if not any([(header.lower() == "pdf") for header in self.ColumnHeaders]):
                self.ColumnHeaders=self.ColumnHeaders[:2]+["PDF"]+self.ColumnHeaders[2:]         # Add the PDF column as the third column
                for i, row in enumerate(self.Rows):
                    self.Rows[i]=row[:2]+[""]+row[2:]
            # What is the PDF column's index?
            iPdf=[header.lower() for header in self.ColumnHeaders].index("pdf")
            # Go through all rows and make sure the PDF colum is set correctly
            for i, row in enumerate(self.Rows):
                if row[0].lower().endswith(".pdf"):
                    self.Rows[i][iPdf]="PDF"


    # ---------------------------------
    # Format the data and save it as an LST file on disk
    def Save(self, filename: str) -> bool:

        content=[f"{self.FanzineName};{self.Editors};{self.Dates};{self.FanzineType}", ""]

        if self.TopComments and "".join(self.TopComments):    # Only write these lines if there is at least one non-empty line
            for line in self.TopComments:
                content.append(line)
            content.append("")

        if self.Locale:
            for line in self.Locale:
                content.append(f"<fanac-type><h2>{line}</h2></fanac-type>")
            content.append("")

        # Go through the headers and rows and trim any trailing columns which are entirely empty.
        # First find the last non-empty column
        if not self.Rows:
            return False
        maxlen=max([len(row) for row in self.Rows])
        maxlen=max(maxlen, len(self.ColumnHeaders))
        lastNonEmptyColumn=maxlen-1     # lastNonEmptyColumn is an index, not a length
        while lastNonEmptyColumn > 0:
            if len(self.ColumnHeaders[lastNonEmptyColumn]) > 0:
                break
            found=False
            for row in self. Rows:
                if len(row[lastNonEmptyColumn]) > 0:
                    found=True
                    break
            if found:
                break
            lastNonEmptyColumn-=1

        # Do we need to trim?
        if lastNonEmptyColumn < maxlen-1:    # lastNonEmptyColumn is an index, not a length
            self.ColumnHeaders=self.ColumnHeaders[:lastNonEmptyColumn+1]
            self.Rows=[row[:lastNonEmptyColumn+1] for row in self.Rows]

        # Write out the column headers
        # Need to remove the "Filename" column which was added when the LST file was loaded.  It is the 1st col.
        content.append("; ".join(self.ColumnHeaders[1:]))

        # And the rows
        for row in self.Rows:
            if len(row) < 3:    # Smallest possible LST file
                continue

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
            content.append(out)

        # And write it out
        with open(filename, "w+") as f:
            f.writelines([c+"\n" for c in content])

        return True