from dataclasses import dataclass, field
from enum import Enum
import re

from HelpersPackage import CanonicizeColumnHeaders, Bailout, StripSpecificTag, FindAnyBracketedText



@dataclass(order=False)
class LSTFile:
    FanzineName: str=""
    Editors: str=""
    Dates: str=""
    FanzineType: str=""

    TopComments: list[str] = field(default_factory=list)
    Locale: list[str] = field(default_factory=list)
    ColumnHeaders: list[str] = field(default_factory=list)        # The actual text of the column headers
    Rows: list[list[str]] = field(default_factory=list)

    Complete: bool=False
    AlphabetizeIndividually: bool=False


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
            self.FanzineType=parsed[3].strip()

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
            line=contents.pop(0).strip()    # Pop the first line from the list of likes
            if len(line) == 0:
                continue    # Skip blank lines
            if IsTableLine(line):   # If we come to a table line, we have found the column headers (which must start the table). Save it and then drop down to table row processing.
                colHeaderLine=line
                break
            # Once we find a line that starts with <fanac-type>, we append the lines to locale until we find a line that ends with </fanac-type>
            # We remove leading and trailing <fanac-type> and <h2>
            if inFanacType or line.lower().startswith("<fanac-type>"):
                while line.lower().startswith("<fanac-type>"):  # Must deal with duplicated HTML tags in some broken pages
                    line=StripSpecificTag(StripSpecificTag(line, "fanac-type"), "h2")   # Steip off the tags until there are none left
                self.Locale.append(line)
                if not line.lower().endswith("</fanac-type>"):
                    inFanacType=True
                    continue
                inFanacType=False
            else:
                self.TopComments.append(line.strip().removeprefix("<p>").removesuffix("</p>"))

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
        # We need to do some special processing on the first two columns
        # Col 1 (actually [0]) normally contains the link to the fanzine.  Col 2 normally contains the link text -- typically the fanzine's issue name
        # There are four formats that I've found so far.
        # Case (0) is an empty line
        # Case (1) The most common format has (filename>displayname) in the first column. We treat the ">" as a ";" for the purposes of the spreadsheet. (We'll undo this on save.)
        #   This format is to a specific issue of a fanzine.
        #   Col 1 has filename and Col 2 has displayname
        # Case (2) An especially annoying one is where fanzine data has been entered, but there's no actual scan.
        #   Col 1 is blank and Col 2 has the fanzine name
        # Case (3) A less common format which has some sort of HTML or hyperlink in column 1.  It comes in two flavors:
        #   Case (3a) "<a HREF="http://abc">xyz</a>" where abc is a URL and xyz is the display name.
        #   So col 1 will be abc and Col 2 will be xyz and this will turn into Case 1 on writing out
        #   Case (3b) "<a name="something">xyz</a>
        #   This is a reference to an anchor within the page.  It is also displayed without modification
        #   Col 1 will be <a name="something"> and Col 2 will be xyz
        # Case (4) is the case where there is no link at all in col 1, but there is text that is used for things like separation of different kinds of fanzines.
        #   This text may be decorated with html (e.g., <b>xx</b>) and the html must be preserved.
        #   Col 1 will be something like <b>xx</b> and Col 2 will be blank
        self.Rows=[]
        for row in rowLines:
            print(f"\n{row}")
            col1, colrest=row.split(";", 1)

            # Case 0
            # If the line has no content (other than ">" and ";" and whitespace, append an empty line
            if re.match("^[>;\s]*$", row):
                self.Rows.append([""]*len(self.ColumnHeaders))
                continue

            # First look for case (4) (nothing in col 1):
            lead, brackets, bracketed, trail=FindAnyBracketedText(col1)
            print(f"{lead=}  {brackets=}  {bracketed=}  {trail=}")
            # But remember that case (3) allows for links to be put in col 1, so we ignore the case where we have an <a ...>...</a> and treat it normally.
            if len(brackets) > 0 and brackets.lower() != "a":
                # Since this is of this special form, we save it as it is and don't process it further.
                # Split the row on ";" and append it
                self.Rows.append([h.strip() for h in row.split(";")])
                print(f"Case 4: {[h.strip() for h in row.split(';')]}")
                continue

            # Case 3a is <a href="http[s]//xxx.yyy/zzz/qqq.ext...>display text</a>  i.e., some sort of link elsewhere in fanac.org or elsewhere on the internet
            m=re.match("<a\s+href=\"+https+:\/\/(.*?)\/+\"+>(.*?)<\/a>$", col1, re.IGNORECASE)
            if m is not None:
                url=m.groups()[0].removeprefix("fanac.org/fanzines/")
                row=[url, m.groups()[1]]+[h.strip() for h in colrest.split(";")]
                self.Rows.append(row)
                print(f"Case 3a: {row}")
                continue

            # Case 3b is also left unchanged.
            m=re.match("(<a\s+name=.*?>)(.*?)<\/a>$", col1, re.IGNORECASE)
            if m is not None:
                row=[m.groups()[0], m.groups()[1]]+[h.strip() for h in colrest.split(";")]
                self.Rows.append(row)
                print(f"Case 3b: {row}")
                continue

            # Look for case (2), and add the ">" to make it case (1)
            case=None
            if col1.find(">") == -1:    # If there's no ">" in col1, put it there.
                row=">"+row.strip() # Because there are some cases where there is no filename, the ">" is missing and we need to supply one
                col1=row.split(";", 1)[0]

            # Now we can handle them all as case (1)
            if row.find(">>") != -1 and row.find(">>") < row.find(";"):
                row=row[:row.find(">>")]+">;"+row[row.find(">>")+2:]
            elif row.find(">") != -1 and row.find(">") < row.find(";"):
                row=row[:row.find(">")]+";"+row[row.find(">")+1:]
            print(f"Cases 1&2: {[h.strip() for h in row.split(';')]}")

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

        # Finally, rummage through the whole file looking for fanac keywords
        # They are comments of the form: <!-- Fanac-keywords: Alphabetize individually-->
        for row in rowLines:
            if m:=re.match("<!-- Fanac-keywords: (.*)-->", row.strip()):
                # Now search a list of recognized keywords
                if m.groups()[0] == "Alphabetize individually":
                    self.AlphabetizeIndividually=True
                    break   # Since this is the one (and only) for now



    # ---------------------------------
    # Format the data and save it as an LST file on disk
    def Save(self, filename: str) -> bool:

        content=[f"{self.FanzineName};{self.Editors};{self.Dates};{self.FanzineType}", ""]

        if self.TopComments and "".join(self.TopComments):    # Only write these lines if there is at least one non-empty line
            for line in self.TopComments:
                content.append(f"<p>{line}</p>")
            content.append("")

        if self.Locale:
            for line in self.Locale:
                content.append(f"<fanac-type><h2>{line}</h2></fanac-type>")
            content.append("")

        if self.AlphabetizeIndividually:
            content.append("<!-- Fanac-keywords: Alphabetize individually -->\n")

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

        # Do not save trailing empty rows
        lastrow=len(self.Rows)-1
        while lastrow > 0:
            if any([x.strip() != "" for x in self.Rows[lastrow]]):
                break
            lastrow-=1

        # And the rows
        for i, row in enumerate(self.Rows):
            if len(row) < 3:    # Smallest possible LST file
                continue    #TODO: Should this be a break?

            if i > lastrow:
                break   # Stop saving when we reach the last non-empty row

            # Now convert each row in the GUI interface to a row in the LST file
            # We need to figure out from what we see displayed when format to use on writing out
            # We don't do the cases in numnerical order as it's simpler to detect some cases

            col1=""
            # Case (0): An empty line
            if len("".join(row).strip()) == 0:
                col1=""

            # Case (2):  Col 1 is blank and Col 2 has the fanzine name
            elif len(row[0].strip()) == 0 and len(row[1].strip()) > 0:
                col1=f">{row[1]}"
                print(f"Case 2: {col1}")

            # Case (4) is the case where there is no link at all in col 1, but there is text that is used for things like separation of different kinds of fanzines.
            #   This text may be decorated with html (e.g., <b>xx</b>) and the html must be preserved.
            #   Col 1 will be something like <b>xx</b> and Col 2 will be blank
            elif re.search(r"<(.*)>.*</\1>", row[0].strip()) and not re.search(r"<(.*)>.*</\1>", row[0].strip()).groups()[0].lower().startswith("a"):
            #elif re.search("<(.*)>.*<\/\1>", row[0].strip()) and len(row[1].strip()) == 0:
                col1=row[0]
                print(f"Case 4: {col1}")

            # Case (3) A less common format which has some sort of HTML or hyperlink in column 1.  It comes in two flavors:
            #  Case (3a) "<a HREF="http://abc">xyz</a>" where abc is a URL and xyz is the display name.
            #   So col 1 will be abc and Col 2 will be xyz and this will turn into Case 1 on writing out
            elif ".com" in row[0] or ".org" in row[0]:
                col1=f'<a href="https://{row[0]}">{row[1]}</a>'
                print(f"Case 3a: {col1}")

            #  Case (3b) "<a name="something">xyz</a>
            #   This is a reference to an anchor within the page.  It is also displayed without modification
            #   Col 1 will be <a name="something"> and Col 2 will be xyz
            elif row[0].startswith("<a name="):
                col1=f"{row[0]}{row[1]}</a>"
                print(f"Case 3b: {col1}")

            # Case (1): The most common format has (filename>displayname) in the first column. We treat the ">" as a ";" for the purposes of the spreadsheet. (We'll undo this on save.)
            #   This format is to a specific issue of a fanzine.
            #   Col 1 has filename and Col 2 has displayname
            else:
                col1=row[0]+">"+row[1]
                print(f"Case 1: {col1}")


            # Now append the rest of the columns
            out=f"{col1}; {'; '.join(row[2:])}"
            content.append(out)

        # And write it out
        with open(filename, "w+") as f:
            f.writelines([c+"\n" for c in content])

        return True