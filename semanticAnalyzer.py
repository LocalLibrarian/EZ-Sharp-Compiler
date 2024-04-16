#Constants
OUTFILE = 'outputSemantic.txt'
ERRORFILE = 'errorLogSemantic.txt'
LEXICAL = 'outputLexical.txt'
IDENTIFIER = 'identifier'
ASSIGNMENT = 'assignment'
NULL = 'NULL'
MAXLINES = 100000 #Maximum lines in a code file

#Lists used to determine when to create new scope/exit current one
newTables = ['if', 'while', 'def', 'else']
endTables = ['fi', 'od', 'fed']

#List used for valid types
types = ['int', 'double', 'integer']

#Comparators
comparators = ['<>', '<', '>', '==', '>=', '<=']

#Current table link ID index to use
linkNum = 0

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
        self.link = linkNum

    def __str__(self):
        #return f'KEYWORD: {self.line}, {self.lexeme}, {self.token}'
        #Properly return linkID to scope this token created on the stack
        if self.lexeme in newTables:
            return (f'KEYWORD [line: {self.line}, lexeme: {self.lexeme}, ' +
                    f'token: {self.token}, link: {self.link + 1}]')
        return (f'KEYWORD [line: {self.line}, lexeme: {self.lexeme}, token:' +
                     f' {self.token}]')

class Literal:
    def __init__(self, line, lexeme, token, type):
        self.line = line
        self.lexeme = lexeme
        self.token = token
        self.type = type
        self.link = linkNum

    def __str__(self):
        return (f'LITERAL [line: {self.line}, lexeme: {self.lexeme},' + 
                f' token: {self.token}, type: {self.type}]')

class IDVariable:
    def __init__(self, line, lexeme, token, type):
        self.line = line
        self.lexeme = lexeme
        self.token = token
        self.type = type
        self.link = linkNum

    def __str__(self):
        return (f'VARIABLE [line: {self.line}, lexeme: {self.lexeme}' + 
                f' token: {self.token}, type: {self.type}]')

class IDFunction:
    def __init__(self, line, lexeme, token, type, paramTypes):
        self.line = line
        self.lexeme = lexeme
        self.token = token
        self.type = type
        self.paramTypes = paramTypes
        self.link = linkNum

    def __str__(self):
        return (f'FUNCTION [line: {self.line}, lexeme: {self.lexeme}' + 
                f' token: {self.token}, type: {self.type}, parameter types:'+
                f' {self.paramTypes}]')

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
    level = 0
    for item in stack[0]:
        if type(item).__name__ == 'Keyword':
            level = item.link
            break
    outFile.write(str(level).ljust(3))
    outFile.write((len(stack) - 1) * '    ')
    for item in stack[0]:
        outFile.write(str(item) + ', ')
    outFile.write('\n')

'''
Returns type of tokens (that have a function call in them).
Checks function parameters for valid types as well.
Helper function for getType()
'''
def checkFunctionType(tokens, stack):
    i = 0
    types = []
    for token in tokens:
        split = parseLexicalOutput(token)
        if split[1] in seenFuncs:
            index = findScope(stack, split[1])
            if index != NULL:
                valid = True
                for t in stack[index[0]][index[1]].paramTypes:
                    type2 = getType(tokens[i + 1:], stack)
                    if t in ['int', 'integer'] and (type2 in 
                                                    ['int', 'integer']):
                        valid = True
                    elif t == type2: valid = True
                    else: valid = False
                if not valid: #Invalid parameter types
                    return NULL
                else:
                    types.append(stack[index[0]][index[1]].type)
            else: #Error, wrong types, let calling function throw the error
                return NULL
        else:
            if split[0] == IDENTIFIER:
                index = findScope(stack, split[1])
                if index != NULL:
                    if (stack[index[0]][index[1]].type not in 
                    ['int', 'integer']):
                        types.append('double')
                else: #Error, let calling func throw error
                    return NULL
        i += 1
    for entry in types:
        if entry == 'double': return entry
    return 'integer'

'''
Returns the type of the tokens passed to it.
Tokens will represent expressions like 3+x or 9/5-1 for example, and are thus
simple to handle.
This func can return NULL if an error occurs during type getting for IDs.
'''
def getType(tokens, stack):
    foundID = False
    foundFunc = False
    #Check if func or var in tokens
    for token in tokens:
        split = parseLexicalOutput(token)
        if split[0] == IDENTIFIER: 
            foundID = True
            if split[1] in seenFuncs: foundFunc = True
    if not foundID: #No IDs in expression, simpler
        #Check if we have division, it is a double always unless typecast to an
        #int which is handled in the else block
        for token in tokens:
            split = parseLexicalOutput(token)
            if split[1] == '/': return 'double'
        for token in tokens:
            split = parseLexicalOutput(token)
            if split[0] in types and split[0] != 'integer': return 'double'
        return 'integer'
    else: #IDs in expression, harder
        #Follows same rules as above EXCEPT that division can be made to be
        #integer division if all IDs present are integer types
        if foundFunc:
            typed = checkFunctionType(tokens, stack)
            if typed != NULL:
                return typed
            else: #Error, let calling function figure it out
                return NULL
        else: #Return double if we have any double type IDs, else int
            for token in tokens:
                split = parseLexicalOutput(token)
                if split[0] == IDENTIFIER:
                    index = findScope(stack, split[1])
                    if index != NULL:
                        if (stack[index[0]][index[1]].type not in 
                        ['int', 'integer']):
                            return 'double'
                    else: #Error, let calling func throw error
                        return NULL
            return 'integer'

'''
Returns true if tokens passed to it is valid for type checking, false otherwise.
Splits type checking lines and checks each side.
For assignments: declaration, expression
For comparisons: left side, right side
For returns: return, expression
'''
def checkType(tokens, stack):
    index = 0
    foundAssign = False
    foundCompare = False
    foundReturn = False
    for token in tokens:
        split = parseLexicalOutput(token)
        if split[1] == '=': foundAssign = True
        elif split[1] in comparators: foundCompare = True
        elif split[1] == 'return': foundReturn = True
        if not foundAssign and not foundCompare: index += 1
    if foundAssign or foundCompare:
        type1 = getType(tokens[:index], stack)
        type2 = getType(tokens[index + 1:], stack)
        if type1 == type2: return True
        elif type1 in ['int', 'integer'] and type2 in ['int', 'integer']:
            return True
        return False
    elif foundReturn:
        type1 = stack[-1][-1].type
        type2 = getType(tokens[1:], stack)
        if type1 == type2: return True
        elif type1 in ['int', 'integer'] and type2 in ['int', 'integer']:
            return True
        return False
    return True

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
    checker = [] #List of checking type validity
    typeCheck = False
    varlist = [False, 'int']
    global linkNum
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
            if lineNum > len(text):
                throwError(lineNum, lineSplit[1], 'Could Not Find Token in ' +
                           'Code File', 'crashing parser')
                break
        #Now we have the correct line number for output, proceed with analysis
        if lineSplit[1] in ['return', 'if', 'while', 'print'] or (len(prev) > 0 
                                                                  and 
                                                prev[0] == IDENTIFIER and 
                                                lineSplit[1] == '='): 
            typeCheck = True
        if typeCheck:
            if (lineSplit[0] == 'keyword' and lineSplit[1] not in 
                ['return', 'if', 'while', 'print']) or (
                lineSplit[1] == ';'):
                typeCheck = False
                if not checkType(checker, stack):
                    throwError(lineNum, 'BEFORE ' + lineSplit[1], 
                               'Invalid Type', 'ignoring error')
                checker.clear()
            if typeCheck or lineSplit[1] == 'return':
                checker.append(line)
        if varlist[0]:
            if lineSplit[0] not in ['seperator', IDENTIFIER]:
                varlist = [False, 'int']
            elif lineSplit[0] == IDENTIFIER:
                seenIDs.append(lineSplit[1])
                stack[0].append(buildSymbol(lineNum, lineSplit[1],
                                                lineSplit[0], varlist[1],
                                                [NULL]))
        elif lineSplit[0] == IDENTIFIER and lineSplit[1] not in seenIDs:
            if prev[1] not in types:
                throwError(lineNum, lineSplit[1], 
                    'Undeclared Identifier/Inaccessible Identifier in Scope',
                    'ignoring error')
            else:
                seenIDs.append(lineSplit[1])
                #Declaring new variable(s)
                if skipMode != 1 and skipMode != 4:
                    stack[0].append(buildSymbol(lineNum, lineSplit[1],
                                                lineSplit[0], prev[1],
                                                [NULL]))
                    varlist = [True, prev[1]]
        elif lineSplit[0] == IDENTIFIER and lineSplit[1] in seenIDs and (
            prev[1] in types):
                throwError(lineNum, lineSplit[1], 
                    'Variable Already Defined',
                    'ignoring error')
        if skipMode == 1: #Skip until ( encountered
            if lineSplit[1] == '(':
                skipMode = 4
                stack.insert(0, [])
                linkNum += 1
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
                    temp = stack[index[0]][index[1]]
                    try:
                        stack[0].append(buildSymbol(lineNum, temp.lexeme,
                                                    temp.token, temp.type,
                                                    temp.paramTypes))
                    except:
                        stack[0].append(buildSymbol(lineNum, temp.lexeme,
                                                    temp.token, temp.type,
                                                    NULL))
                else:
                    #Error, variable isn't declared or can't be accessed in this
                    #scope
                    throwError(lineNum, lineSplit[1], 
                    'Undeclared Identifier/Inaccessible Identifier in Scope',
                    'ignoring error')
            elif lineSplit[1] == 'then':
                skipMode = 0
                stack[0].append(buildSymbol(lineNum, lineSplit[1], lineSplit[0],
                                            NULL, [NULL]))
                stack.insert(0, [])
                linkNum += 1
            else:
                stack[0].append(buildSymbol(lineNum, lineSplit[1], lineSplit[0],
                                            NULL, [NULL]))
        elif skipMode == 3: #Skip until do encountered
            if lineSplit[1] in seenIDs:
                index = findScope(stack, lineSplit[1]) 
                if index != NULL:
                    temp = stack[index[0]][index[1]]
                    try:
                        stack[0].append(buildSymbol(lineNum, temp.lexeme,
                                                    temp.token, temp.type,
                                                    temp.paramTypes))
                    except:
                        stack[0].append(buildSymbol(lineNum, temp.lexeme,
                                                    temp.token, temp.type,
                                                    NULL))
                else:
                    #Error, variable isn't declared or can't be accessed in this
                    #scope
                    throwError(lineNum, lineSplit[1], 
                    'Undeclared Identifier/Inaccessible Identifier in Scope',
                    'ignoring error')
            elif lineSplit[1] == 'do':
                skipMode = 0
                stack[0].append(buildSymbol(lineNum, lineSplit[1], lineSplit[0],
                                            NULL, [NULL]))
                stack.insert(0, [])
                linkNum += 1
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
                if funcData[2] in seenFuncs:
                    throwError(lineNum, lineSplit[1], 
                    'Function Already Defined',
                    'ignoring error')
                else:
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
                    linkNum += 1
            elif lineSplit[1] in endTables: #Exit current table
                writeStack(stack)
                del stack[0]
                stack[0].append(buildSymbol(lineNum, lineSplit[1],
                                                lineSplit[0], NULL, [NULL]))
            else: #Add to current table on stack
                if lineSplit[1] in seenFuncs:
                    index = findScope(stack, lineSplit[1])
                    if index == NULL:
                        throwError(lineNum, lineSplit[1], 
                    'Undeclared Identifier/Inaccessible Identifier in Scope',
                    'ignoring error')
                    else:
                        temp = stack[index[0]][index[1]]
                        try:
                            stack[0].append(buildSymbol(lineNum, temp.lexeme,
                                                    temp.token, temp.type,
                                                    temp.paramTypes))
                        except:
                            stack[0].append(buildSymbol(lineNum, temp.lexeme,
                                                    temp.token, temp.type,
                                                    NULL))
                elif lineSplit[1] in seenIDs:
                    index = findScope(stack, lineSplit[1])
                    if index == NULL:
                        throwError(lineNum, lineSplit[1], 
                    'Undeclared Identifier/Inaccessible Identifier in Scope',
                    'ignoring error')
                    else:
                        if not varlist[0]:
                            temp = stack[index[0]][index[1]]
                            try:
                                stack[0].append(buildSymbol(lineNum, temp.lexeme,
                                                    temp.token, temp.type,
                                                    temp.paramTypes))
                            except:
                                stack[0].append(buildSymbol(lineNum, temp.lexeme,
                                                    temp.token, temp.type,
                                                    NULL))
                else:
                    stack[0].append(buildSymbol(lineNum, lineSplit[1], 
                                                lineSplit[0], lineSplit[0], 
                                                [NULL]))
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
