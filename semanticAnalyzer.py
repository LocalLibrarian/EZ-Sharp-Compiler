'''
TODO LIST
1. Check variable references, see if they in a scope yet
2. Check each side of comparisons and assignments to make sure the types are
equivalent
3. Check return types of functions
'''

#Constants
OUTFILE = 'outputSemantic.txt'
ERRORFILE = 'errorLogSemantic.txt'
LEXICAL = 'outputLexical.txt'
IDENTIFIER = 'identifier'
NULL = 'NULL'

#Lists used to determine when to create new scope/exit current one
newTables = ['if', 'while', 'def', 'else']
endTables = ['fi', 'od', 'fed']

#List used for valid types
types = ['int', 'double', 'integer']

#List of ALL seen identifiers
seenIDs = []
seenFuncs = []

'''
All these classes are used to hold symbol table data in stack of scopes (symbol
tables). Some are identical in initialization but still used since they should
print differently.
'''
class Keyword:
    def __init__(self, line, lexeme, token):
        self.line = line
        self.lexeme = lexeme
        self.token = token

    def __str__(self):
        #return f'KEYWORD: {self.line}, {self.lexeme}, {self.token}'
        return f'KEYWORD, {self.lexeme}'

class Literal:
    def __init__(self, line, lexeme, token, type):
        self.line = line
        self.lexeme = lexeme
        self.token = token
        self.type = type

    def __str__(self):
        #return f'LITERAL: {self.line}, {self.lexeme}, {self.token}, {self.type}'
        return f'LITERAL, {self.lexeme}'

class IDVariable:
    def __init__(self, line, lexeme, token, type):
        self.line = line
        self.lexeme = lexeme
        self.token = token
        self.type = type

    def __str__(self):
        #return f'IDENTIFIER (FUNCTION): {self.line}, {self.lexeme}, ' + (
        #f'{self.token}, {self.type}')
        return f'VARIABLE, {self.lexeme}'

class IDFunction:
    def __init__(self, line, lexeme, token, type, paramTypes):
        self.line = line
        self.lexeme = lexeme
        self.token = token
        self.type = type
        self.paramTypes = paramTypes

    def __str__(self):
        #return f'IDENTIFIER (FUNCTION): {self.line}, {self.lexeme}, ' + (
        #f'{self.token}, {self.type}, {self.paramTypes}')
        return f'FUNCTION, {self.lexeme}'

#Breaks output lines of lexicalAnalyzer up to make them easier to deal with.
#First element is type of token, second element is token
def parseLexicalOutput(line):
    splitter = line.find(',')
    lineSplit = []
    lineSplit.append(line[1:splitter])
    lineSplit.append(line[splitter + 2:-2])
    return lineSplit

#Separates inFile into a list of list of elements on each line that are
#separated by spaces/tabs and returns it for getting line numbers of tokens
def sepInput(inFile):
    output = []
    for line in inFile:
        lineStrip = line
        token = ''
        newLine = []
        for c in lineStrip:
            if c != ' ' and c != '	':
                token += c
            if (c == ' ' or c == '	' and token != '') or c == '\n':
                newLine.append(token.removesuffix('\n'))
                token = ''
        output.append(newLine)
    output[-1].append(token) #Add token that has '.' at end of itself and no \n
    return output

#Makes symbol class based on and from params passed and returns it.
def buildSymbol(line, lexeme, token, type, paramTypes):
    #Determine which symbol we have from the params passed
    if token == IDENTIFIER:
        if paramTypes[0] != NULL: kind = 'IDFunction'
        else: kind = 'IDVariable'
    elif type == NULL or type not in types: kind = 'Keyword'
    else: kind = 'Literal'
    #Now build the symbol class from the params
    if kind == 'Keyword':
        return Keyword(line, lexeme, token)
    elif kind == "Literal":
        return Literal(line, lexeme, token, type)
    elif kind == 'IDVariable':
        return IDVariable(line, lexeme, token, type)
    elif kind == 'IDFunction':
        return IDFunction(line, lexeme, token, type, paramTypes)

#Tries to find variable/function id in stack and returns stack position it is at
#if found or NULL if not found
def findScope(stack, id):
    for i in range(len(stack)):
        for j in range(len(stack[i])):
            if stack[i][j].lexeme == id:
                return (i, j)
    return NULL

#Writes errors to error log file
def throwError(lineNum, lexeme, errorType, resolution):
    part1 = f'Error on line {lineNum}'
    part2 = f'lexeme {lexeme}'
    part3 = f'[{errorType}]\nProceeding via {resolution}'
    errorFile.write(f'{part1} ({part2}) {part3}\n')

#Writes top of stack to outFile
def writeStack(stack):
    outFile.write((len(stack) - 1) * '    ')
    for item in stack[0]:
        outFile.write(str(item) + ' ')
    outFile.write('\n')

#Analyzes semantics of the inFile and outputs symbol table to OUTFILE
def AnalyseSemantics(inFile):
    #Need to open LEXICAL so can figure out types of tokens and when they occur
    try:
        lexicalFile = open(LEXICAL, 'r')
    except:
        print(f'Could not open {LEXICAL}, aborting analysis...')
        return
    #Was able to open file correctly, may proceed
    text = sepInput(inFile) #Used to get line numbers of tokens
    lineNum = 1
    tokenNum = 0
    stack = [[]] #Stack of symbol tables, first/bottom element is global
    skipMode = 0 #For handling what is in what scope, skipping things
    prev = [] #Holds previous lineSplit for getting types
    lineSplit = [] #Holds data for a line in LEXICAL
    funcData = [] #Holds function data, format is [type, lineNum, name,
    #paramTypes...]
    for line in lexicalFile:
        prev = lineSplit
        lineSplit = parseLexicalOutput(line)
        #Current token is not in current line
        while(not (lineSplit[1] in text[lineNum - 1][tokenNum])):
            if tokenNum + 1 < len(text[lineNum - 1]): #Move to next 'token'
                tokenNum += 1
            else: #Move to next line
                lineNum += 1
                tokenNum = 0
        #Now we have the correct line number for output, proceed with analysis
        if lineSplit[0] == IDENTIFIER and lineSplit[1] not in seenIDs:
            seenIDs.append(lineSplit[1])
        if skipMode == 1: #Skip until ( encountered
            if lineSplit[1] == '(':
                skipMode = 4
                stack.insert(0, [])
                stack[0].append(buildSymbol(lineNum, lineSplit[1], 
                                            lineSplit[0], NULL,
                                            [NULL]))
            else:
                if lineSplit[1] in types: 
                    funcData.clear() #Reset for new func
                    stack[0].append(buildSymbol(lineNum, lineSplit[1], 
                                                lineSplit[0], NULL, [NULL]))
                else: funcData.append(lineNum)
                funcData.append(lineSplit[1])
        elif skipMode == 2: #Skip until then encountered
            if lineSplit[1] in seenIDs:
                index = findScope(stack, lineSplit[1]) 
                if index != NULL:
                    stack[0].append(stack[index[0]][index[1]])
                else:
                    #Error, variable isn't declared or can't be accessed in this
                    #scope
                    throwError(lineNum, lineSplit[1], 
                    'Undeclared Identifier/Inaccessible Identifier in Scope',
                    'ignoring lexeme')
            elif lineSplit[1] == 'then':
                skipMode = 0
                stack[0].append(buildSymbol(lineNum, lineSplit[1], lineSplit[0],
                                            NULL, [NULL]))
                stack.insert(0, [])
            else:
                stack[0].append(buildSymbol(lineNum, lineSplit[1], lineSplit[0],
                                            NULL, [NULL]))
        elif skipMode == 3: #Skip until do encountered
            if lineSplit[1] in seenIDs:
                index = findScope(stack, lineSplit[1]) 
                if index != NULL:
                    stack[0].append(stack[index[0]][index[1]])
                else:
                    #Error, variable isn't declared or can't be accessed in this
                    #scope
                    throwError(lineNum, lineSplit[1], 
                    'Undeclared Identifier/Inaccessible Identifier in Scope',
                    'ignoring lexeme')
            elif lineSplit[1] == 'do':
                skipMode = 0
                stack[0].append(buildSymbol(lineNum, lineSplit[1], lineSplit[0],
                                            NULL, [NULL]))
                stack.insert(0, [])
            else:
                stack[0].append(buildSymbol(lineNum, lineSplit[1], lineSplit[0],
                                            NULL, [NULL]))
        elif skipMode == 4: #Skip until done getting function params
            if lineSplit[1] == ')':
                skipMode = 0
                stack[0].append(buildSymbol(lineNum, lineSplit[1], lineSplit[0],
                                            NULL, [NULL]))
                stack[1].append(buildSymbol(funcData[1], funcData[2], 
                                            IDENTIFIER, funcData[0], 
                                            funcData[3:]))
                seenFuncs.append(funcData[2])
            #Add to types list
            elif lineSplit[1] in types:
                funcData.append(lineSplit[1])
                stack[0].append(buildSymbol(lineNum, lineSplit[1], lineSplit[0],
                                            NULL, [NULL]))
            else: #Local vars
                stack[0].append(buildSymbol(lineNum, lineSplit[1], lineSplit[0],
                                            prev[1], [NULL]))
        else:
            if lineSplit[1] in newTables: #Create new table on stack
                if lineSplit[1] == 'def':
                    stack[0].append(buildSymbol(lineNum, lineSplit[1],
                                                lineSplit[0], NULL, [NULL]))
                    skipMode = 1 #Skip until (
                elif lineSplit[1] == 'if':
                    stack[0].append(buildSymbol(lineNum, lineSplit[1],
                                                lineSplit[0], NULL, [NULL]))
                    skipMode = 2 #Skip until then
                elif lineSplit[1] == 'while':
                    stack[0].append(buildSymbol(lineNum, lineSplit[1],
                                                lineSplit[0], NULL, [NULL]))
                    skipMode = 3 #Skip until do
                #'else' does not require any skipping before new stack
                #However it does delete previous 'if' stack
                elif lineSplit[1] == 'else':
                    writeStack(stack)
                    del stack[0]
                    stack[0].append(buildSymbol(lineNum, lineSplit[1],
                                                lineSplit[0], NULL, [NULL]))
                    stack.insert(0, [])
            elif lineSplit[1] in endTables: #Exit current table
                writeStack(stack)
                del stack[0]
                stack[0].append(buildSymbol(lineNum, lineSplit[1],
                                                lineSplit[0], NULL, [NULL]))
            else: #Add to current table on stack
                if lineSplit[1] in seenFuncs:
                    index = findScope(stack, lineSplit[1])
                    stack[0].append(stack[index[0]][index[1]])
                elif lineSplit[1] in seenIDs:
                    index = findScope(stack, lineSplit[1])
                    stack[0].append(stack[index[0]][index[1]])
                else:
                    stack[0].append(buildSymbol(lineNum, lineSplit[1], 
                                                lineSplit[0], lineSplit[0], [NULL]))
    writeStack(stack)

#Get input file name and open
print("Please ensure the input file has already had lexical analysis " +
      "completed, and that the output for it is in the current directory.")
inFileStr = str(input('Enter input file name: '))
fail = False
try:
    inFile = open(inFileStr, 'r')
    checker = inFileStr.split('.')
    if checker[1] != 'cp':
        fail = True
        print(f'File extension .{checker[1]} is not supported!')
except:
    fail = True
    print(f'Failed to open file {inFileStr}!')

#Create error log file and output file
outFile = open(OUTFILE, 'w')
errorFile = open(ERRORFILE, 'w')

#Actual start of real work
if not fail: 
    AnalyseSemantics(inFile)
    print(f'Semantic analysis on file {inFileStr} completed')
