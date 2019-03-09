from dataclasses import dataclass


# -------------------------------------------------------------
def CanonicizeColumnHeaders(header):
    # 2nd item is the canonical form
    translationTable={
        "published": "date",
        "editors": "editor",
        "zine": "W",
        "fanzine": "W",
        "mo.": "M",
        "mon": "M",
        "month": "M",
        "notes": "notes",
        "no.": "N",
        "no,": "N",
        "num": "N",
        "#": "N",
        "page": "P",
        "pages": "P",
        "pp,": "P",
        "pub": "publisher",
        "vol": "V",
        "volume": "V",
        "wholenum": "W",
        "year": "Y",
        "day": "D",
    }
    try:
        return translationTable[header.replace(" ", "").replace("/", "").lower()]
    except:
        return header.lower()


@dataclass(order=False)
class LSTFile:
    FirstLine: str=None
    TopTextLines: str=None
    ColumnHeaders: list=None        # The actual text of the column headers
    ColumnHeaderTypes: list=None    # The single character types for the corresponding ColumnHeaders
    Rows: list=None

    def IdentifyColumnHeaders(self):

        # The trick here is that "Number" (in its various forms) is used vaguely: Sometimes it means whole number and sometimes volume number
        # First identify all the easy ones
        self.ColumnHeaderTypes=[]
        for header in self.ColumnHeaders:
            cHeader=CanonicizeColumnHeaders(header)
            if len(cHeader) == 1 and cHeader.isupper():
                self.ColumnHeaderTypes.append(cHeader)
            else:
                self.ColumnHeaderTypes.append(header)

        # In cases where we have a num *and* a vol, the num is treated as the issue's volume number; else its treated as the issue's whole number
        if "V" not in self.ColumnHeaderTypes:
            for i in range(0, len(self.ColumnHeaderTypes)):
                if self.ColumnHeaderTypes[i] == "N":
                    self.ColumnHeaderTypes[i]="W"

        return

    # Read an LST file, returning its contents as an LSTFile
    def Read(self, filename):

        # Open the file, read the lines in it and strip leading and trailing whitespace (including '\n')
        contents=list(open(filename))
        contents=[l.strip() for l in contents]

        if contents is None or len(contents) == 0:
            return None

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
        topTextLines=[]
        while contents[0].lower().startswith("<p>"):
            while True:
                topTextLines.append(contents[0])
                contents=contents[1:]
                if topTextLines[-1:][0].lower().endswith(r"</p>") or topTextLines[-1:][0].lower().endswith(r"<p>"):
                    break


        colHeaderLine=contents[0]
        contents=contents[1:]
        rowLines=[]
        while len(contents)>0:
            rowLines.append(contents[0])
            contents=contents[1:]

        # The firstLine and the topTestLines are usable as-is, so we just store them
        self.FirstLine=firstLine
        self.TopTextLines=topTextLines

        # We need to parse the column headers
        self.ColumnHeaders=[h.strip() for h in colHeaderLine.split(";")]

        # And likewise the rows
        # Note that we have the funny structure (filename>displayname) of the first column. We split that off
        self.Rows=[]
        for row in rowLines:
            self.Rows.append([h.strip() for h in row.split(";")])


