#Constants
TABLEFILE = 'table.csv' #CSV file for LL(1) table
ERRORFILE = 'errorLogSyntax.txt'
OUTFILE = 'outputSyntax.txt'
INFILE = 'outputLexical.txt' #From lexicalAnalyzer.py
EPSILON = 'EPSILON'
SEP = '|'
FAIL = 'FAIL'
START = '<program>'
END = '$'

'''
Reads TABLEFILE and puts the LL(1) parser table in memory.
Returns the table.

TABLEFILE is a .csv file which is seperated by SEP.
'''
def readTable():
    tableFile = open(TABLEFILE, 'r')
    #Table is a dict, format is:
    #table[column (terminal)][row (symbol)] = transition
    table = {}
    headers = tableFile.readline().removesuffix('\n').split(SEP)
    #Skip first header since it is just a label, not a column header
    for header in headers[1:]:
        table[header] = {}
    for line in tableFile:
        row = line.removesuffix('\n').split(SEP)
        #Again, skip first column, as it is a label
        i = 1
        for col in row[1:]:
            if col != '': table[headers[i]][row[0]] = col
            else: table[headers[i]][row[0]] = FAIL #For invalid state checks
            i += 1
    return table

#Writes errors to log file
def throwError(errorToken, errorTokenNum, errorType, resolution):
    part1 = f'Error on token {errorToken}'
    part2 = f'token number {errorTokenNum}'
    part3 = f'[{errorType}]\nProceeding via {resolution}'
    errorFile.write(f'{part1} ({part2}) {part3}\n')

#Returns true if token is a symbol of the format <text>, false otherwise
def isSymbol(token):
    return len(token) > 2 and token[0] == '<' and token[-1] == '>'

#Syntax analysis of INFILE
def Parse():
    #Stack is list of elements on top of stack
    stack = [START, END]
    

#Start of program
#Put the parsing table in memory
table = readTable()

#Open input file, create output file and error file
inFile = open(INFILE, 'r')
outFile = open(OUTFILE, 'w')
errorFile = open(ERRORFILE, 'w')

#Start parsing
Parse()
#https://web.stanford.edu/class/archive/cs/cs143/cs143.1128/lectures/03/Slides03.pdf
