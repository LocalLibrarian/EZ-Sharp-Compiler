#Constants
TABLEFILE = 'table.csv' #CSV file for LL(1) table
ERRORFILE = 'errorLogSyntax.txt'
INFILE = 'outputLexical.txt' #From lexicalAnalyzer.py
EPSILON = 'EPSILON'
SEP = '|'
FAIL = 'FAIL'
START = '<program>'
END = '$'
PRODSTART = '::='

#List of direct lookup terminals in LL(1) table, i.e., don't need special
#handling to access associated productions
directLook = ['keyword', 'seperator', 'operator', 'programEnder',
              'statementEnder', 'comparator', 'assignment']

#List of number lookups
numbers = ['integer', 'double']

#List of recognized identifier names to print
variables = []

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

#Breaks output lines of lexicalAnalyzer up to make them easier to deal with.
#First element is type of token, second element is token
def parseLexicalOutput(line):
    splitter = line.find(',')
    lineSplit = []
    lineSplit.append(line[1:splitter])
    lineSplit.append(line[splitter + 2:-2])
    return lineSplit

#Replaces the first element of list with newItem and returns the resulting list
def replace1st(list, newItem):
    if type(newItem) == type(['list']):
        return newItem + list[1:]
    else:
        temp = []
        temp.append(newItem)
        for item in list[1:]:
            temp.append(item)
        return temp

#Breaks a production from the LL(1) Parsing Table into a list of elements in the
#production and returns it
def parseLL1Output(production):
    if production == FAIL:
        return production
    prod = production[production.find(PRODSTART) + len(PRODSTART) + 1:]
    return prod.split(' ')

#Syntax analysis of INFILE
def Parse():
    DELETEME = 0
    tokenNum = 0
    #Stack is list of elements on top of stack
    stack = [START, END]
    while len(stack) > 0:
        line = inFile.readline()
        tokenNum += 1
        #Break line into 2 element list detailing contents
        lineInfo = parseLexicalOutput(line)
        cont = True
        while cont:
            #While top of stack (leftmost item) is a symbol, keep doing prods
            while isSymbol(stack[0]):
                #Directly access table elements with token type
                if lineInfo[0] in directLook:
                    stack = replace1st(stack, parseLL1Output(
                        table[lineInfo[1]][stack[0]]))
                #Access table elements via [a-z] since identifiers always start
                #with that
                elif lineInfo[0] == 'identifier':
                    stack = replace1st(stack, parseLL1Output(
                        table['[a-z]'][stack[0]]))
                #Access table elements with [0-9] since numbers always start
                #with that
                elif lineInfo[0] in numbers:
                    stack = replace1st(stack, parseLL1Output(
                        table['[0-9]'][stack[0]]))
            #Check if terminal matches top of stack, error if not
            if stack[0] == lineInfo[1] or stack[0] == EPSILON or (
                stack[0] == '[a-z]' and lineInfo[0] == 'identifier') or (
                    stack[0] == '[0-9]' and lineInfo[0] in numbers) or (
                        line == '' and stack[0] == END):
                '''Terminal matched stack, successful parse for this token OR
                terminal nulls top of stack item, del stack item and move to 
                next stack item OR end of input reached, done parsing.
                '''
                if stack[0] == lineInfo[1] or (
                stack[0] == '[a-z]' and lineInfo[0] == 'identifier') or (
                    stack[0] == '[0-9]' and lineInfo[0] in numbers) or (
                        line == '' and stack[0] == END):
                    cont = False #Go to next line in input
                    if stack[0] == '[a-z]' and lineInfo[0] == 'identifier' and (
                        lineInfo[1] not in variables):
                        variables.append(lineInfo[1])
                del stack[0]
            else:
                #Terminal did not match expected parse, throw error and delete
                #so can continue parsing rest of input
                cont = False #Go to next line in input
                throwError(lineInfo[1], tokenNum, 'Unexpected Token', 
                           'deleting token')
                del stack[0]

#Start of program
#Put the parsing table in memory
table = readTable()

#Open input file, create error file
inFile = open(INFILE, 'r')
errorFile = open(ERRORFILE, 'w')

#Start parsing
Parse()
print('Syntax analysis completed. Recognized identifiers:')
if len(variables) == 0: print("None parsed")
else: 
    for v in variables: print(v)
