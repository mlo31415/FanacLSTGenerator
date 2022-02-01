from dataclasses import dataclass, field
import re

from HelpersPackage import CanonicizeColumnHeaders, Bailout


@dataclass(order=False)
class LSTFile:
    FirstLine: str=""
    TopTextLines: list[str] = field(default_factory=list)
    BottomTextLines: list[str] = field(default_factory=list)
    ColumnHeaders: list[str] = field(default_factory=list)        # The actual text of the column headers
    ColumnHeaderTypes: list[str] = field(default_factory=list)    # The single character types for the corresponding ColumnHeaders
    SortColumn: dict[str, float]   = field(default_factory=dict)# The single character type(s) of the sort column(s).  Sort on whole num="W", sort on Vol+Num ="VN", etc.
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
            # And there's also the messiness of the first column having an A>B structure
            return re.search(".+[>;].+;.+;", s) is not None

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
            if col1.find(">") == -1:    # If there's no ">" in col1, put it there.
                assert False    # What does this do???
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
            apas: list[str]=["FAPA", "SAPS", "OMPA", "ANZAPA", "VAPA", "FLAP"]
            mailing=[""]*len(self.Rows)
            found=False
            for i, row in enumerate(self.Rows):
                for apa in apas:
                    pat=f"(?:for|in|)[^a-zA-Z]+{apa}\s+([0-9]+)[,;]?"
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

        # Go through the headers and rows and trim any trailing columns which are entirely empty.
        # First find the last non-empty column
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
            if not re.match("^[>;\s]*$", out):  # Save only null rows
                content.append(out)

        if len(self.BottomTextLines) > 0:
            for line in self.BottomTextLines:
                content.append(line)
            content.append("")

        # And write it out
        with open(filename, "w+") as f:
            f.writelines([c+"\n" for c in content])
