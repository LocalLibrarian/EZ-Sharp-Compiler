#Constants
OUTFILE = 'outputSemantic.txt'
ERRORFILE = 'errorLogSemantic.txt'
LEXICAL = 'outputLexical.txt'

#Lists used to determine when to create new scope/exit current one
newTables = ['if', 'while', 'def', 'else']
endTables = ['fi', 'od', 'fed']

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

class Literal:
    def __init__(self, line, lexeme, token, type):
        self.line = line
        self.lexeme = lexeme
        self.token = token
        self.type = type

class IDVariable:
    def __init__(self, line, lexeme, token, type):
        self.line = line
        self.lexeme = lexeme
        self.token = token
        self.type = type

class IDFunction:
    def __init__(self, line, lexeme, token, type, paramTypes):
        self.line = line
        self.lexeme = lexeme
        self.token = token
        self.type = type
        self.paramTypes = paramTypes

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

#Makes symbol class from params and returns it.
def buildSymbol(kind, line, lexeme, token, type, paramTypes):
    if kind == 'Keyword':
        return
    elif kind == "Literal":
        return
    elif kind == 'IDVariable':
        return
    elif kind == 'IDFunction':
        return

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
    print(text)
    stack = [[]] #Stack of symbol tables, first/bottom element is global
    skipMode = 0 #For handling what is in what scope, skipping things
    prev = [] #Holds previous lineSplit for getting types
    lineSplit = []
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
        print(stack[0])
        if skipMode == 1: #Skip until ( encountered
            if lineSplit[1] == '(':
                skipMode = 0
                stack.insert(0, [])
            stack[0].append(lineSplit[1])
        elif skipMode == 2: #Skip until then encountered
            stack[0].append(lineSplit[1])
            if lineSplit[1] == 'then':
                skipMode = 0
                stack.insert(0, [])
        elif skipMode == 3: #Skip until do encountered
            stack[0].append(lineSplit[1])
            if lineSplit[1] == 'do':
                skipMode = 0
                stack.insert(0, [])
        else:
            if lineSplit[1] in newTables: #Create new table on stack
                if lineSplit[1] == 'def':
                    stack[0].append(lineSplit[1])
                    skipMode = 1 #Skip until (
                elif lineSplit[1] == 'if':
                    stack[0].append(lineSplit[1])
                    skipMode = 2 #Skip until then
                elif lineSplit[1] == 'while':
                    stack[0].append(lineSplit[1])
                    skipMode = 3 #Skip until do
                #'else' does not require any skipping before new stack
                #However it can delete previous 'if' stack
                elif lineSplit[1] == 'else':
                    del stack[0]
                    stack[0].append(lineSplit[1])
                    stack.insert(0, [])
            elif lineSplit[1] in endTables: #Exit current table
                del stack[0]
                stack[0].append(lineSplit[1])
            else: #Add to current table on stack
                stack[0].append(lineSplit[1])
    print(stack[0])

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