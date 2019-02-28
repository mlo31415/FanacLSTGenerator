from dataclasses import dataclass

@dataclass(order=False)
class LSTFile:
    FirstLine: str=None
    TopTextLines: str=None
    ColumnHeaders: list=None
    Rows: list=None


# Read an LST file, returning its contents as an LSTFile
def ReadLstFile(filename):

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

    # Now parse the lines and put them into the LSTFile class structure
    lstFile=LSTFile()

    # The firstLine and the topTestLines are usable as-is, so we just store them
    lstFile.FirstLine=firstLine
    lstFile.TopTextLines=topTextLines

    # We need to parse the column headers
    lstFile.ColumnHeaders=[h.strip() for h in colHeaderLine.split(";")]

    # And likewise the rows
    # Note that we have the funny structure (filename>displayname) of the first column. We split that off
    lstFile.Rows=[]
    for row in rowLines:
        lstFile.Rows.append([h.strip() for h in row.split(";")])

    return lstFile


