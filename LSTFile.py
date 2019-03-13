from dataclasses import dataclass
import math
import re

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


# ====================================================================================
# Convert a text month to integer
# (Borrowed from FanacAnalyzer -- consider taking more)
def MonthToInt(text):
    monthConversionTable={"jan": 1, "january": 1, "1": 1,
                          "feb": 2, "february": 2, "feburary": 2, "2": 2,
                          "mar": 3, "march": 3, "3": 3,
                          "apr": 4, "april": 4, "4": 4,
                          "may": 5, "5": 5,
                          "jun": 6, "june": 6, "6": 6,
                          "jul": 7, "july": 7, "7": 7,
                          "aug": 8, "august": 8, "8": 8,
                          "sep": 9, "sept": 9, "september": 9, "9": 9,
                          "oct": 10, "october": 10, "10": 10,
                          "nov": 11, "november": 11, "11": 11,
                          "dec": 12, "december": 12, "12": 12,
                          "1q": 1, "q1": 1,
                          "4q": 4, "q2": 4,
                          "7q": 7, "q3": 7,
                          "10q": 10, "q4": 10,
                          "spring": 4, "spr": 4,
                          "summer": 7, "sum": 7,
                          "fall": 10, "autumn": 10, "fal": 10,
                          "winter": 1, "win": 1,
                          "xmas": 12, "christmas": 12}

    text=text.replace(" ", "").lower()

    # First look to see if the input is two month names separated by a non-alphabetic character (e.g., "September-November"
    m=re.compile("^([a-zA-Z]+)[-/]([a-zA-Z]+)$").match(text)
    if m is not None and len(m.groups()) == 2 and len(m.groups()[0]) > 0:
        m1=MonthToInt(m.groups()[0])
        m2=MonthToInt(m.groups()[1])
        if m1 is not None and m2 is not None:
            return math.ceil((m1+m2)/2)

    try:
        return monthConversionTable[text]
    except:
        return None


@dataclass(order=False)
class LSTFile:
    FirstLine: str=None
    TopTextLines: str=None
    ColumnHeaders: list=None        # The actual text of the column headers
    ColumnHeaderTypes: list=None    # The single character types for the corresponding ColumnHeaders
    SortColumn: dict=None           # The single character type(s) of the sort column(s).  Sort on whole num="W", sort on Vol+Num ="VN", etc.
    Rows: list=None



    # Simple method to turn a year/month pair into a float which can be sorted
    def YMtoInt(self, year, month):
        if year is None or year == "":
            return 0

        try:
            year=int(year)
        except:
            return 0
        if year < 30:
            year+=2000
        if year < 100:
            year+=1900

        if month is None or month == "":
            return year

        try:
            month=int(month)
        except:
            month=MonthToInt(month)
            if month == None:
                month=0

        return year+month/100


    #--------------------------------
    # Using the columns specified, find the best location to insert the row
    # In all cases we assume that the LST file is sorted in increasing order, so we stop the first time we hit a larger value
    # Note that we may return a negative index, which means to prepend the row.
    def GetBestRowIndex(self, bestCols, newRow):
        # The choices are
        #   YM -- use year and month
        #   VN -- use volume and number
        #   W -- use whole number
        #   "" -- use the title
        if bestCols == "W":
            if "W" not in self.ColumnHeaderTypes:
                raise ValueError("LSTFile: GetBestRowIndex - can't find columnheader="+bestCols)
            col=self.ColumnHeaderTypes.index("W")
            for i in range(0, len(self.Rows)):
                if int(self.Rows[i][col]) > int(newRow[col]):
                    return i-0.5
            return len(self.Rows)

        if bestCols == "VN":
            if "V" not in self.ColumnHeaderTypes or "N" not in self.ColumnHeaderTypes:
                raise ValueError("LSTFile: GetBestRowIndex - can't find columnheader="+bestCols)
            colV=self.ColumnHeaderTypes.index("V")
            colN=self.ColumnHeaderTypes.index("N")
            for i in range(0, len(self.Rows)):
                if int(self.Rows[i][colV]) > int(newRow[colV]):
                    return i-0.5
                if int(self.Rows[i][colV]) == int(newRow[colV]) and int(self.Rows[i][colN]) == int(newRow[colN]):
                    return i-0.5
            return len(self.Rows)

        if bestCols == "YM":
            if "Y" not in self.ColumnHeaderTypes:   # We don't actually need a month in every column for this to be useful
                raise ValueError("LSTFile: GetBestRowIndex - can't find columnheader="+bestCols)
            colY=self.ColumnHeaderTypes.index("Y")
            colM=self.ColumnHeaderTypes.index("M")
            val=self.YMtoInt(newRow[colY], newRow[colM])
            for i in range(0, len(self.Rows)):
                if self.YMtoInt(self.Rows[i][colY], self.Rows[i][colM]) > val:
                    return i-0.5
            return len(self.Rows)

        # OK, try to sort of title which is always col 1
        for i in range(0, len(self.Rows)):
            if int(self.Rows[i][1]) > int(newRow[1]):
                return i-0.5
        return len(self.Rows)



    #--------------------------------
    # Figure out what the column headers are (they frequently have variant names)
    # Get some statistics on which columns have info in them, also.
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

        # Now cather statistics on what columns have data.  This will be needed to determine the best colums to use for inserting new data
        self.MeasureSortColumns()


    #---------------------------------
    # take the supplied header types and use the row statistics to determine what column to use to do an insertion.
    def GetInsertCol(self):
        if self.SortColumn is None:
            raise ValueError("class LSTFile: GetInsertCol called while SortColumn is None")

        # ColumnHeaderTypes is a list of the type letters for which this issue has data.
        possibleCols={}
        if "W" in self.ColumnHeaderTypes and self.SortColumn["W"] > .75:
            possibleCols["W"]=self.SortColumn["W"]
        if "V" and self.ColumnHeaderTypes and "N" and self.ColumnHeaderTypes and self.SortColumn["VN"] > .75:
            possibleCols["VN"]=self.SortColumn["VN"]
        if "Y" in self.ColumnHeaderTypes and "M" in self.ColumnHeaderTypes and self.SortColumn["YM"] > .75:
            possibleCols["YM"]=self.SortColumn["YM"]

        if len(possibleCols) == 0:
            return -1
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
    def MeasureSortColumns(self):
        # A sort column must either be the title or have a type code
        # Start by looking through the columns that have a type code and seeing which are mostly or completely filled.  Do it in order of perceived importance.
        fW=self.CountFilledCells("W")
        fV=self.CountFilledCells("V")
        fN=self.CountFilledCells("N")
        fY=self.CountFilledCells("Y")
        fM=self.CountFilledCells("M")

        self.SortColumn={}
        self.SortColumn["W"]=fW
        self.SortColumn["VN"]=fV*fN
        self.SortColumn["YM"]=fY*fM


    #---------------------------------
    # Count the number of filled cells in the column with the specified type code
    # Returns a floating point fraction between 0 and 1
    def CountFilledCells(self, type):
        try:
            index=self.ColumnHeaderTypes.index(type)
        except:
            return 0

        # Count the number of filled-in values for this type
        num=0
        for row in self.Rows:
            if row[index] is not None and len(row[index]) > 0:
                num+=1
        return num/len(self.Rows)


    #---------------------------------
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


