#Constants
ERRORFILE = 'errorLog.txt'
OUTFILE = 'output.txt'
BUFFERLENGTH = 2048

#Global vars
debug = False

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

#Determines the type of the given token
#using a list of states given and returns it
def findTokenType(states, token):
    #No states given, this is an error
    if not states:
        return 'ERROR'
    #Token is a keyword
    if token in keywords:
        return 'keyword'
    #Comparators/assignment
    if token in comparators:
        if token != '=':
            return 'comparator'
        return 'assignment'
    if token in operators:
        return 'operator'
    #Seperators
    if token in separators:
        return 'seperator'
    #Fail state
    return 'ERROR'

"""
Actually does all the token finding.

For error handling, on an error, we throw the error, then skip all the next 
characters until the next token separator (found in the separators list).
This is Panic Mode implementation.
"""
def getNextToken(lineNum, line):
    """TODO:
    Handle doubles: x.y format, rn seperates them as '.' is a sep
    Obviously get states correctly lol
    Panic mode implementation
    Make it so can error on wrong states with correct column num
    """
    token = ''
    panic = False
    skip = False
    colNum = 1
    states = ['TEMP']
    for c in line:
        if not skip:
            if(panic): #Panic Mode/error handling #TODO
                if c in separators:
                    panic = False
            else:
                if(debug): print(f'{colNum} {c}')
                #Check if char in alphabet at all, error if not
                if c not in alphabet and c not in separators: 
                    throwError(lineNum, colNum, c, line, 'Invalid Character')
                    panic = True
                    if(debug): print(f'Errored on line {lineNum} with char ({c})')
                elif c in separators:
                    #End of previous token OR multiple separators/whitespace in a row
                    #OR comparator, i.e. ==/<>/>=/<=
                    if token != '':
                        writeToken(findTokenType(states, token), token)
                        if(debug): print(f'Read token {token}')
                    if c not in whitespaces:
                        if c in comparators:
                            if colNum < len(line):
                                compound = False
                                if c == '<':
                                    if line[colNum] in ['>', '=']: compound = True
                                elif c == '>':
                                    if line[colNum] == '=': compound = True
                                elif line[colNum] == '=': compound = True #c == '='
                                if compound:
                                    writeToken('comparator', c + line[colNum])
                                    skip = True
                                    if(debug): print(f'Read token {c}{line[colNum]}')
                                else:
                                    writeToken(findTokenType(states, c), c)
                                    if(debug): print(f'Read token {c}')
                        else:
                            writeToken(findTokenType(states, c), c)
                            if(debug): print(f'Read token {c}')
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
inFileInput = inFileStr.split(' ')
try:
    inFile = open(inFileInput[0], 'r')
except:
    print(f'Failed to open file {inFileInput[0]}!')

#Debug mode enabler
if len(inFileInput) > 2:
    debug = True
    print('DEBUG ON, SEE README FOR HOW TO NOT ENABLE THIS ON RUN')

#Create error log file and output file
outFile = open(OUTFILE, 'w')
errorFile = open(ERRORFILE, 'w')

#Actual start of real work
lexicalAnalysis(inFile)
