from dataclasses import dataclass, field
from Log import Log, LogError
import re
from urllib.parse import urlparse

from HelpersPackage import CanonicizeColumnHeaders, Bailout, StripSpecificTag, FindAnyBracketedText, RemoveHyperlink
from HelpersPackage import FindIndexOfStringInList, FanzineNameToDirName, ContainsBracketedText


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

        # Rummage through the whole file looking for fanac keywords
        # They are comments of the form: <!-- Fanac-keywords: Alphabetize individually-->
        for line in contents:
            if m:=re.search("<!-- Fanac-keywords: (.*)-->", line.strip()):
                # Now search a list of recognized keywords
                if "alphabetize individually" in m.groups()[0].lower():
                    self.AlphabetizeIndividually=True
                    break   # Since this is the one (and only) for now

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
            if m:=re.search("<!-- Fanac-keywords: (.*)-->", line.strip()):
                continue    # We ignore all Fanac-keywords lines as they are meant to be invisible and are handled elsewhere
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
        # We need to do some special processing on the first two columns.  In the LST file they are combined into a single columm,
        # and here we expand this to two for processing.  In all caases, the input is the 1st ;-separated group in a line of the LST file
        #
        # On display and for processing, Col 0 normally contains the link to the fanzine.  Col 1 normally contains the link text -- typically the fanzine's issue name
        #
        # There are four formats that I've found so far.
        # Case (0) is an empty line
        # Case (1) The most common format has (filename>displayname) in the input. We treat the ">" as a ";" for the purposes of the spreadsheet. (We'll undo this on save.)
        #   This format is to a specific issue of a fanzine.
        #   Output: Col 0 has the filename and Col 1 has the displayname
        # Case (2) An especially annoying one is where fanzine data has been entered, but there's no actual scan.  The input is just text.
        #   Output: Col 0 is blank and Col 1 has the fanzine name
        # Case (3) A less common format which has some sort of HTML or hyperlink in the input.  It comes in two flavors:
        #   Case (3a) "<a HREF="http://abc.bdc">xyz</a>" where abc is a URL and xyz is the display name.
        #   Output: col 0 will be abc.bdc and Col 1 will be xyz and this will turn into Case 1 on writing out
        #   Case (3b) "<a name="something">xyz</a>   This is to insert an anchor within the page.  The anchor is in col 0 and everything else in col 1
        #   Output: Col 0 will be <a name="something"> and Col 1 will be xyz
        # Case (4) is the case where there is no link at all in the input, but there *is* text containing HTML that is used for things like separation of different kinds of fanzines.
        #   This text may be decorated with html (e.g., <b>xx</b>) and the html must be preserved.
        #   Output: Col 0 will be the input (e.g., <b>xx</b>) and Col 0 will be blank
        #
        # Summary:
        # Case 0:   {blank}
        # Case 1:   {filename}>{text w/o HTML}
        # Case 2:   {text w/o HTML}
        # Case 3a   {<a href...>}>{text}     (There are multiple flavors depending on the details of the link)
        # Case 3b:  {<a name=..>}>{text}
        # Case 4:   {HTML}>{blank}  (Or, maybe, just {HTML})
        self.Rows=[]
        for row in rowLines:
            cols=[x.strip() for x in row.split(";")]
            lstrow=self.LSTToRow(cols[0])+cols[2:]
            self.Rows.append(lstrow)


        # Define the grid's columns
        # First add the invisible column which is actually the link destination
        # It's the first part of the funny xxxxx>yyyyy thing in the LST file's 1st column
        self.ColumnHeaders=["Filename"]+self.ColumnHeaders

        # If any rows are shorter than the headers row, pad them with blanks
        for row in self.Rows:
            if len(row) < len(self.ColumnHeaders):
                row.extend([""]*(len(self.ColumnHeaders)-len(row)))

        # The Mailings column probably contains HTML links to the APA mailings, but we only want to display the markup test (e.g., "FAPA 23A") to the user.
        # Strip away the html -- we'll add it back in on saving.
        # Note that some older LST files have variant headers.
        iMailings=FindIndexOfStringInList(self.ColumnHeaders, ["mailing", "mailings", "apa mailing", "apa mailings"], IgnoreCase=True)
        if iMailings is not None:
            for row in self.Rows:
                row[iMailings]=RemoveHyperlink(row[iMailings])


    def LSTToRow(self, col0: str) -> list[str, str]:
        # Case 0
        # If the line has no content (other than ">" and ";" and whitespace, append an empty line
        if re.match("^[>;\s]*$", col0):
            out=([""]*2)
            return out

        col0=col0.strip()

        # Case 1:   {filename}>{text w/o HTML}
        # Case 2:   {optional >}{text w/o HTML}     Input
        if not ContainsBracketedText(col0):
            # Look for case (2), and add the ">" to make it case (1)
            if ">" not in col0:
                col0=">"+col0.strip()  # Because there are some cases where there is no filename, the ">" is missing and we need to supply one
            # Apparently there may still be cases where the ">" was a ">>".  Fix this.
            col0=col0.replace(">>", ">")
            assert col0.count(">") == 1
            # Now we can handle them all as case (1)
            out=col0.split(">")
            return out

        # Case 4:   {HTML} (but not an href!)
        # Case (4) is the case where there is no link at all in the input, but there *is* text containing HTML that is used for things like separation of different kinds of fanzines.
        #   This text may be decorated with html (e.g., <b>xx</b>) and the html must be preserved.
        #   Output: Col 0 will be the input (e.g., <b>xx</b>) and Col 0 will be blank
        lead, brackets, bracketed, trail=FindAnyBracketedText(col0)
        # print(f"{lead=}  {brackets=}  {bracketed=}  {trail=}")
        # But remember that case (3) handles links in col 0, so we must ignore the case where we have an <a ...>...</a> and treat it normally.
        # Note that sometimes the LST files have case 3 (an anchor) band *also* HTML-decorated text, so we skip lines starting "<a< name="
        if len(brackets) > 0 and brackets.lower() != "a" and not lead.lower().startswith("<a name="):
            # Since this is of this special form, we save it as it is and don't process it further.
            # Split the row on ";" and append it
            out=["", col0]
            # print(f"Case 4: {[h.strip() for h in row.split(';')]}")
            return out

        # Case 3a   {<a href...>}>{text}     (There are multiple flavors depending on the details of the link)
        # This case is  <a href="http[s]//xxx.yyy/zzz/qqq.ext...>display text</a>  i.e., some sort of full hyperlink somewhere in fanac.org or elsewhere on the internet
        # There are several subcases:
        #       input LST file --> in display --> in output LST file
        #   3a1: Link away from fanac.org
        #       https://xyz.com/stuff/stuff --> xyz.com/stuff/stuff --> <a https://xyz.com/stuff/stuff
        #   3a2: Link to the index page of some other fanzines directory on fanac.org
        #       https//fanac.org/fanzines/abc/ --> ../abc/ --> <a https//fanac.org/fanzines/abc/
        #   3a3: Link a file in some other fanzines directory on fanac.org
        #       https//fanac.org/fanzines/abc/def.ext --> ../abc/def.ext --> <a https//fanac.org/fanzines/abc/def.ext
        #   3a4: Link using full url to the current directory or a file in it
        #       https://fanac.org/fanzines/curdir/stuff.ext --> stuff.ext --> stuff.ext

        # Case 3b:  {<a name=..>}>{text}   (an anchor)
        # This one is easy
        m=re.match("(<a\s+name=.*?>)(?:</a>|>)?(.*?)$", col0, re.IGNORECASE)  # Note that the 2d group is non-capturing
        if m is not None:
            out=[m.groups()[0], m.groups()[1]]
            return out

        # Does col 0 contain a full hyperlink?
        m=re.match("<a\s+href=\"?https?://(.*?/?)\"?>(.*?)(</a>)?$", col0, re.IGNORECASE)
        if m is not None:
            url=m.groups()[0]
            disptext=m.groups()[1]

            # Now which of the subcases is it?
            m=re.match("(www\.)?fanac\.org/(.*)", url, re.IGNORECASE)  # Does it refer to fanac.org?
            if m is not None:
                # Yes
                if url.lower().startswith("fanzines"):
                    out=[url, disptext]
                    return out
                # So we're going somewhere else in fanac.org.  Treat it the same as an outside URL

            # We're looking at a full URL
            out=[f"http://{url}"]+[disptext]
            return out
        print(f"Case 3a seems to be failing!: {input}")
        return ["", ""]


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

        # Turn any mailing info into hyperlinks to the mailing on fanac.org
        iMailings=FindIndexOfStringInList(self.ColumnHeaders, ["mailing", "mailings", "apa mailing", "apa mailings"], IgnoreCase=True)
        if iMailings is not None:
            self.ColumnHeaders[iMailings]="Mailing"     # Change header to standard
            for row in self.Rows:
                mailing=row[iMailings]
                row[iMailings]=""
                if len(mailing) > 0:
                    mailings=mailing.split(",")     # It may be of the form 'FAPA 103, OMPA 32'
                    first=True
                    for mailing in mailings:
                        mailing=mailing.strip()
                        if len(mailing) > 0:
                            if not first:
                                row[iMailings]=row[iMailings]=row[iMailings]=""+", "    # Add a comma before subsequent mailings
                            first=False
                            m=re.match("([a-zA-Z1-9_\- ]*)\s+([0-9]+[a-zA-Z]*)$", mailing)      # Split the FAPA 103A into an apa name and the mailing number (which may have trailing characters '30A')
                            if m is not None:
                                apa=m.groups()[0]
                                number=m.groups()[1]
                                row[iMailings]=f'<a href="https://fanac.org/fanzines/APA_Mailings/{FanzineNameToDirName(apa)}/{number}.html">{mailing}</a>'


        # Do not save trailing empty rows
        if len(self.Rows) > 1:
            lastNonEmptyRow=len(self.Rows)-1
            while lastNonEmptyRow > 0:
                if any([x.strip() != "" for x in self.Rows[lastNonEmptyRow]]):
                    break
            if lastNonEmptyRow < len(self.Rows)-1:
                self.Rows=self.Rows[:lastNonEmptyRow+1]

        # Now lst file can have fewer than three columns.
        if len(self.Rows[0]) < 3:  # Smallest possible LST file
            LogError(f"LSTfile.Save(): {filename} has {len(self.Rows)} columns which is too few. Not saved")
            return False

        # Now save the remaining rows.  Note that the list of rows is trimmed so that each has the same length
        # Convert each row in the GUI interface to a row in the LST file
        for row in self.Rows:
            row=[x.strip() for x in row]    # Remove any leading or traling blanks

            # The first two columns require special handing.
            cols01=self.RowToLST(row[0:1])
            if cols01 != "":
                # The later cols (#s 2-N) are just written out with semicolon separators
                content.append(cols01+'; '.join(row[2:]))

        # And write it out
        with open(filename, "w+") as f:
            f.writelines([c+"\n" for c in content])

        return True


    # Take the first two columns of the spreadsheet and generate the LST file string for them
    def RowToLST(self, row: list[str, str]) -> str:

        # The first two cases are easy, since there is nothing in col 0 and hence there is no possibility of a link of any sort.
        if row[0] == "":
            # Case (0): Both col0 and col1 are empty
            # Case (2):  Just col 0 is empty
            out=f"{row[1]};"
            # print(f"Case 0 or 2: {out}")
            return out

        # Case 1:   {filename}>{text w/o HTML}
        # There are no slashes or tags in filename; text does not contain HTML
        if "/" not in row[0] and '\\' not in row[0]:
            if not ContainsBracketedText(row[1]):
                out=f'{row[0]}>{row[1]};'
                # print(f"Case 0 or 2: {out}")
                return out

        # Now we know there is something in col 0.  It will most commonly be a filename in the current fanzine directory, but it may be header information or a hyperlink.
        # First, check to see if it's a hyperlink.  They can be in the forms:
        #   ../xxx/yyy/filename.ext          (A link into a different fanzine directory)
        #   a.b.com/xxx/yyy/filename.ext     (A link to another website)
        #   http[s]://.../filename.ext       (A link to *anywhere* that has been pasted in)

        # Case 3b:  {<a name=..>}>{text}   (an anchor)
        m=re.match("(<a\s+name=[^<>]+>)", row[0])
        if m is not None:
            out=m.groups()[0]+">"+row[1]+";"
            # print(f"Case 3b: {out}")
            return out

        # TODO: Isn't this really the case where col 0 has text that isn't a hyperlink and col 1 is empty?  Should this also include Case 3???
        # Case (4) is the case where there is no link in col 0, but there is text that is used for things like separation of different kinds of fanzines.
        #   This text may be decorated with html (e.g., <b>xx</b>) and the html must be preserved.
        #   Col 0 will be something like <b>xx</b> and Col 1 will be blank
        if re.search(r"<([b-zB-Z].*)>.*</\1>", row[0].lower().strip()):  # If there is a <xxx>...</xxx> in the 1st col and xxx does not start with A, we have a non-link
            out=f"{row[0]};"  # TODO what about col 2?
            # print(f"Case 4: {out}")
            return out
        # No look for the case where there is no <> delimited text at all.  That just gets put out as-is
        if not re.search(r"<(.*)>.*</\1>", row[0].lower().strip()):
            out=f"{row[0]};"  # TODO what about col 2?
            # print(f"Case 4: {out}")
            return out

        # Case 3a is <a href="http[s]//xxx.yyy/zzz/qqq.ext...>display text</a>  in col 0.  I.e., some sort of link to elsewhere in fanac.org or to elsewhere on the internet.
        # Col 1 is empty
        # There are several subcases:
        #       input LST file --> in display --> in output LST file
        #   3a: Link away from fanac.org
        #       https://xyz.com/stuff/stuff --> xyz.com/stuff/stuff --> <a https://xyz.com/stuff/stuff
        #   3b: Link to the index page of some other fanzines directory on fanac.org
        #       https//fanac.org/fanzines/abc/ --> ../abc/ --> <a https//fanac.org/fanzines/abc/
        #   3c: Link a file in some other fanzines directory on fanac.org
        #       https//fanac.org/fanzines/abc/def.ext --> ../abc/def.ext --> <a https//fanac.org/fanzines/abc/def.ext
        #   3d: Link using full url to the current directory or a file in it
        #       https://fanac.org/fanzines/curdir/stuff.ext --> stuff.ext --> stuff.ext

        # Case 3b or 3c
        if row[0].startswith("../"):
            col1=f"<a href=\"https://fanac.org/fanzines/{row[0].removeprefix('../')}\">{row[1]}"
            out=f"{col1};"
            # print(f":Case 3a2/3: {col1}")
            return out

        if row[0].startswith("<a "):
            try:
                m=re.match("<a href=(.*)>(.*)$", row[0].strip())
                if m is not None:
                    url=urlparse(m.groups()[0])
                    print(str(url))
                    # Case 3a
                    out=f"{row[0]}{row[1]}"f"<a href=\"https://{row[0]}\">{row[1]};"
                    # print(f":Case 3a1: {col1}")
                    return out

            except:
                pass

        #  Case (3??) "<a name="something">xyz</a>
        #   This is a reference to an anchor within the page.  It is also displayed without modification
        #   Col 0 will be <a name="something"> and Col 1 will be xyz
        if row[0].startswith("<a name="):
            out=f"{row[0]}{row[1]};"
            # print(f"Case 3b: {col1}")
            return out

        # Case (1): The most common format has (filename>displayname) in the first column of the LST file.
        #   This format is to a specific issue of a fanzine in the current directory.
        #   Col 0 has filename and Col 1 has displayname
        # This is also case 3a4!
        out=f"{row[0]}>{row[1]};"
        # print(f"Case 1: {out}")
        return out
