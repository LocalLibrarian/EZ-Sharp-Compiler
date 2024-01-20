#Constants
ERRORFILE = 'errorLog.txt'
OUTFILE = 'output.txt'
BUFFERLENGTH = 2048
FAILSTATE = 'FAIL'

#Valid alphabet/characters, if a char isn't in this list or separators, immediately throw an error
alphabet = []
for c in 'qwertyuiopasdfghjklzxcvbnm1234567890':
    alphabet.append(c)
    
#Token separators. Used for error handling and alphabet checking
separators = ['\n']
for c in '.()+=-/%*;<>, 	':
    separators.append(c)
    
#Whitespace, can ignore for token generation
whitespaces = [' ', '	', '\n']

#Comparators, require special handling due to being compound
comparators = ['<', '>', '=']

#Operators for doing math
operators = ['+', '-', '/', '*', '%']
    
#Valid keywords
keywords = ['def', 'fed', 'int', 'double', 'if', 'fi', 'then', 'else', 'while', 'do', 'od', 'print', 'return']

#Code-defined identifiers, i.e., func and var names, list is updated during compilation
identifiers = []

#Writes errors to error log file
def throwError(lineNum, colNum, errorChar, line, errorType):
    errorFile.write(f'Error on line {lineNum}, column {colNum}, at character ({errorChar}) [{errorType}]:\n--> {lineNum} {line[0:colNum]}\n')

#Writes tokens to output file
def writeToken(tokenType, token):
    outFile.write(f'<{tokenType}, {token}>\n')

#Determines the type of the given token and outputs it
def findTokenType(token, lineNum, colNum, line):
    typed = 'null'
    #Empty token given, this is an error
    if not token:
        typed = FAILSTATE
    #Check alphabet validity of each char in token
    i = 0
    for c in token:
        if c not in alphabet and c not in separators: 
            throwError(lineNum, colNum - len(token) + i, c, line, 'Invalid Character')
            typed = FAILSTATE
        i += 1
    #Fail means invalid character or other error, DO NOT write the token to output
    if typed != FAILSTATE:
        #Token is a keyword
        if token in keywords:
            typed = 'keyword'
        #Comparators/assignment
        elif token in comparators:
            if token != '=':
                typed = 'comparator'
            else:
                typed = 'assignment'
        #Operators
        elif token in operators:
            typed = 'operator'
        #Seperators
        elif token in separators:
            typed = 'seperator'
        #Programmer-made identifiers
        elif token in identifiers:
            typed = 'identifier'
        #Don't know token type yet, need to check states to determine
        if(typed == 'null'):
            writeToken('ERROR', token)
        #Already determined token type, can write to output
        else:
            writeToken(typed, token)

"""
Actually does all the token finding.

For error handling, on an error, we throw the error, then skip all the next 
characters until the next token separator (found in the separators list).
This is Panic Mode implementation, it is implemented in findTokenType().
"""
def getNextToken(lineNum, line):
    """TODO:
    Handle doubles: x.y format, rn seperates them as '.' is a sep
    Obviously get states correctly lol
    """
    token = ''
    panic = False
    skip = False
    colNum = 1
    for c in line:
        if not skip:
            if c in separators:
                #End of previous token OR multiple separators/whitespace in a row
                #OR comparator, i.e. ==/<>/>=/<=
                if token != '':
                    findTokenType(token, lineNum, colNum, line)
                if c not in whitespaces:
                    if c in comparators:
                        if colNum < len(line):
                            compound = False
                            #Checking if we have a compound comparator, i.e. ==, <=, >=, <>
                            if c == '<':
                                if line[colNum] in ['>', '=']: compound = True
                            elif c == '>':
                                if line[colNum] == '=': compound = True
                            elif line[colNum] == '=': compound = True #c == '='
                            if compound:
                                writeToken('comparator', c + line[colNum])
                                skip = True
                            else:
                                findTokenType(c, lineNum, colNum, line)
                        else:
                            """
                            Edge-case: a comparator (<, >, =) at the end of input.
                            In this case, just write that the token is a comparator, DO
                            NOT access line[colNum], as that would be out of list bounds.
                            """
                            findTokenType(c, lineNum, colNum, line)
                    else:
                        findTokenType(c, lineNum, colNum, line)
                token = ''
            else:
                token += c
            colNum += 1
        else:
            skip = False

#Uses getNextToken to do real work, this just passes it lines and line numbers
def lexicalAnalysis(inFile):
    #Variable declarations
    lineNum = 1
    lined = ''
    c1 = ''
    c2 = ''
    buffer1 = 'null'
    buffer2 = 'null'
    while(buffer2 != '' and buffer2!= ''):
        #Add to buffers
        buffer1 = inFile.read(BUFFERLENGTH)
        buffer2 = inFile.read(BUFFERLENGTH)
        #Consume buffer 1
        for c1 in buffer1:
            lined += c1
            if(c1 == '\n'):
                getNextToken(lineNum, lined)
                lined = ''
                lineNum += 1
        #Consume buffer 2
        for c2 in buffer2:
            lined += c2
            if(c2 == '\n'):
                getNextToken(lineNum, lined)
                lined = ''
                lineNum += 1
    #Gets last line of input
    getNextToken(lineNum, lined)

    #Closing resources
    inFile.close()
    outFile.close()
    errorFile.close()
    
#Get input file name and open
inFileStr = str(input('Enter input file name: '))
try:
    inFile = open(inFileStr, 'r')
except:
    print(f'Failed to open file {inFileStr}!')

#Create error log file and output file
outFile = open(OUTFILE, 'w')
errorFile = open(ERRORFILE, 'w')

#Actual start of real work
lexicalAnalysis(inFile)
