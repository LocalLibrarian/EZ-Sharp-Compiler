'''
NOTES
1. To fix issues where we have example:
    x = 1 + 2 * y
    will have to use parse tree to get order of ops right and divide up the
    parts into segments of 2. The above may become for example:
    _temp0 = 2 * y
    x = _temp0 + 1
2. Need to figure out how to do a parse tree when there is a function call in
    the tokens. Probably needs its own tree for each parameter, then ignore the
    parameters in the original tree after the parameters are resolved.
3. To continue, need to make parse tree builder return what it says in its
    describing comment, and also make it write to output
'''

#Constants
OUTFILE = "outputTAC.txt"
SEMANTIC = "outputSemantic.txt"
LEXICAL = "outputLexical.txt"
IDENTIFIER = 'identifier'
SIZEPLACEHOLDER = "INSERTSIZEHERE"
NULL = "NULL"
FUNCTION = "FUNCTION"
INTEGER = "integer"
DOUBLE = "double"
JUMPLABEL = "place"
TEMPLABEL = "_temp"

#Comparators
comparators = ['<>', '<', '>', '==', '>=', '<=']

#Operators
operators = ['+', '-', '/', '*', '%']

#Globals
output = [["jump", "main"], []] #List of lists of words for each line
jumps = 0 #Counts number of jump labels
temps = 0 #Counts number of temporary variables
stackJumpReturn = [] #Stack of next jump label to place for sub-scopes
funcData = [] #Holds Function classes that contain param counts

#Holds data about number of parameters (count) for a function
class Function:
    def __init__(self, name, count, numVars = 0):
        self.name = name
        self.count = count
        self.numVars = numVars

    def __str__(self):
        return f"FUNCTION: [{self.name}, count: {self.count}, needed vars: ]" +(
            f"{self.numVars}")
    
#Binary tree for parsing BEDMAS of expressions and making sure they are in
#right order when reduced to TAC
class ParseTree:
    def __init__(self, data, left = NULL, right = NULL, parent = NULL):
        self.data = data
        self.left = left
        self.right = right
        self.parent = parent

    def __str__(self):
        return f"{self.data}"

#Breaks output lines of lexicalAnalyzer up to make them easier to deal with.
#First element is type of token, second element is token
def parseLexicalOutput(line: str) -> list[str]:
    splitter = line.find(',')
    lineSplit = []
    lineSplit.append(line[1:splitter])
    lineSplit.append(line[splitter + 2:-2])
    return lineSplit

#Writes the contents of output to a file, word by word and line by line
def writeOutput() -> None:
    for line in output:
        for word in line:
            outFile.write(word + " ")
        outFile.write("\n")

#Counts and returns the number of literals + IDs in tokens, used to check if
#have a legal amount for TAC in many scenarios
def countElements(tokens: list[list[str]]) -> int:
    #Assume that tokens is in lineSplit format: [[tokenType, token], etc...]
    count = 0
    for elem in tokens:
        if elem[0] in [IDENTIFIER, INTEGER, DOUBLE]:
            count += 1
    return count

#Returns the index of two (different) IDs in tokens
def findIDLiteralIndex(tokens: list[list[str]]) -> tuple[int, int]:
    index1 = -1
    index2 = -1
    for x in range(len(tokens)):
        if tokens[x][0] in [IDENTIFIER, INTEGER, DOUBLE]:
            if index1 == -1: index1 = x
            else: index2 = x
    return (index1, index2)

'''
Checks order of precedence for operators and returns value relating to that.
Return values:
0 means operator 1 is higher precedence
1 means operator 2 is higher precedence
2 means they are equal
'''
def checkPrecedence(operator1: str, operator2: str) -> int:
    class1 = ["+", "-"]
    class2 = ["/", "*", "%"]
    if operator1 in class1 and operator2 in class2:
        return 1
    elif operator1 in class2 and operator2 in class1:
        return 0
    else:
        return 2

#Returns func data class in funcData
def getFuncData(func: str) -> bool:
    for funcName in funcData:
        if funcName.name == func: return funcName

#Removes unmatched brackets in tokens and returns result
def removeUnmatchedBrackets(tokens: list[list[str]]) -> list[list[str]]:
    opens = 0
    closes = 0
    for token in tokens:
        if token[1] == "(": opens += 1
        elif token[1] == ")": closes += 1
    z = 0
    if opens > closes:
        while z < len(tokens):
            if tokens[z][1] == "(": 
                del tokens[z]
                z -= 1
            z += 1
    elif closes > opens:
        z = len(tokens) - 1
        while z > -1:
            if tokens[z][1] == ")": 
                del tokens[z]
            z -= 1
    return tokens

#Finds the first index of a function in tokens and removes its parameters, so as
#to return them in a seperate list for processing in a ParseTree
def removeFunctionParams(tokens: list[list[str]]) -> tuple[list[list[str]], ]:
    stack = 0
    atFunc = False #Check if found a function
    maybeFunc = False
    startI = 0
    endI = 0
    x = 0
    name = NULL
    while x < (len(tokens)):
        if (tokens[x][0] == IDENTIFIER): 
            maybeFunc = True
            if not atFunc: name = tokens[x][1]
        elif tokens[x][1] == "(" and maybeFunc:
            atFunc = True
            stack += 1
            if startI == 0: startI = x
        elif tokens[x][1] == ")" and atFunc:
            stack -=1
            if stack == 0:
                endI = x + 1
                x = len(tokens) #Break the loop at first occurrence
        else: maybeFunc = False
        x += 1
    beginI = 0
    params = [] #List of params split at commas
    x = 0
    paramTokens = tokens[startI: endI]
    while x < len(paramTokens): #Splitting params
        if paramTokens[x][1] == ",":
            temp = paramTokens[beginI:x]
            temp = removeUnmatchedBrackets(temp)
            params.append(temp)
            beginI = x + 1
        x += 1
    if getFuncData(name).count > 0:
        temp = paramTokens[beginI:x]
        temp = removeUnmatchedBrackets(temp)
        params.append(temp)
    print(params)
    return tokens[0:startI] + tokens[endI:], params

#Builds a parse tree from an expression in tokens and returns the name of the
#temp variable that the tree results in
def buildParseTree(tokens: list[list[str]]) -> str:
    foundFunc = False #Check if there is a function in tokens
    maybeFunc = False
    for token in tokens:
        if token[0] == IDENTIFIER: maybeFunc = True
        elif token[1] == "(" and maybeFunc: foundFunc = True
        else: maybeFunc = False
    root = ParseTree(NULL)
    current = root
    if foundFunc: #TODO
        holder = removeFunctionParams(tokens)
        for param in holder[1]:
            buildParseTree(param)
        buildParseTree(holder[0])
    else: #No function, easier
        for token in tokens:
            if token[1] == "(":
                current.left = ParseTree(NULL, NULL, NULL, current)
                current = current.left
            elif token[1] in operators:
                if current.data == NULL:
                    current.data = token[1]
                    current.right = ParseTree(NULL, NULL, NULL, current)
                    current = current.right
                else: #TODO handle accidentally deleting data??
                    prec = checkPrecedence(current.data, token[1])
                    #token[1] is higher precedence
                    if prec == 1:
                        current.right.left = ParseTree(current.right.data,
                                                       current.right.left,
                                                       current.right.right,
                                                       current.right)
                        current.right.right = ParseTree(NULL, 
                                                        parent=current.right)
                        current.right.data = token[1]
                        current = current.right.right
                    else: #token[1] is equal or lower precedence
                        current.parent = ParseTree(token[1], current)
                        root = current.parent
                        current.parent.right = ParseTree(NULL, 
                                                         parent=current.parent)
                        current = current.parent.right
            elif token[0] in [INTEGER, DOUBLE, IDENTIFIER]:
                current.data = token[1]
                if current.parent == NULL: #Root node
                    current.parent = ParseTree(NULL, left=current)
                    root = current.parent
                current = current.parent

#Checks counts of elements in tokens and updates the output as needed
def checkCount(tokens: list[list[str]], currentName: str) -> None:
    global output, jumps, stackJumpReturn
    index = 0
    foundAssign = False
    foundCompare = False
    foundReturn = False
    foundPrint = False
    for token in tokens:
        if token[1] == '=': foundAssign = True
        elif token[1] in comparators: foundCompare = True
        elif token[1] == 'return': foundReturn = True
        elif token[1] == "print": foundPrint = True
        if not foundAssign and not foundCompare: index += 1
    ending = JUMPLABEL + str(jumps)
    if foundCompare:
        #a == b for example in this case
        type = comparators[comparators.index(tokens[index][1])]
        count1 = countElements(tokens[:index])
        count2 = countElements(tokens[index + 1:])
        if count1 == 1 and (
            count2 == 1):
            index1, index2 = findIDLiteralIndex(tokens)
            output.append(["cmp", tokens[index1][1] + ",", tokens[index2][1]])
        else:
            #TODO
            print("TODO: HANDLE INCORRECT NUMBERS WITH PARSE TREE?")
        if type == "<>": 
            output.append(["jumpNotEqual", ending])
        elif type == "<":
            output.append(["jumpLess", ending])
        elif type == ">":
            output.append(["jumpGreater", ending])
        elif type == "==":
            output.append(["jumpEqual", ending])
        elif type == ">=":
            output.append(["jumpGreaterEqual", ending])
        elif type == "<=":
            output.append(["jumpLessEqual", ending])
        jumps += 1
        output.append(["jump", JUMPLABEL + str(jumps)])
        stackJumpReturn.append(JUMPLABEL + str(jumps))
        output.append([])
        output.append([JUMPLABEL + str(jumps - 1) + ":"])
        jumps += 1
    elif foundReturn:
        #return (a) for example in this case
        if countElements(tokens) == 1:
            index1, index2 = findIDLiteralIndex(tokens) #Can ignore index2 here
            output.append(["fp", "-", "4", "=", tokens[index1][1]])
        else:
            #TODO
            print("TODO: HANDLE INCORRECT NUMBERS WITH PARSE TREE?")
            output.append(["improper", "return"])
        output.append(["jump", "exit" + currentName])
    elif foundAssign:
        #TODO
        print("TODO (assignment)")
    elif foundPrint:
        #Something like print 10 for example
        if countElements(tokens) == 1:
            retVal = []
            for token in tokens:
                retVal.append(token[1])
                if token[1] == "print": retVal.append("(")
            retVal.append(")")
            output.append(retVal)
        else:
            #TODO
            print("TODO IMPROPER PRINTS")
            output.append(["improper", "print"])

#Main work function
def TACGeneration() -> None:
    global output, jumps, stackJumpReturn, funcData
    waitForFunc = False #Check if waiting for function name
    possiblyAtMain = True #Check if done doing function defs
    inMain = False #Check if in main
    getFuncData = False #Check if getting func param count
    currentName = NULL #Current name of a function we are inside
    count = 0 #Count of params for function data
    lineSplit = []
    prev = [] #Holds previous lineSplit
    countCheck = False #Check for if need to check number of elements
    checker = [] #Holds lineSplits to check counts on
    for line in lexicalFile:
        prev = lineSplit
        lineSplit = parseLexicalOutput(line)
        #Save count of params
        if getFuncData:
            if lineSplit[0] == IDENTIFIER:
                count += 1
            #Add data to list of function info
            elif lineSplit[1] == ")":
                funcData.append(Function(currentName, count))
                getFuncData = False
                count = 0
        #Check if need to check number of elements
        elif lineSplit[1] in ['return', 'if', 'while', 'print'] or (len(prev) 
                                                                    > 0 and 
                                                prev[0] == IDENTIFIER and 
                                                lineSplit[1] == '='): 
            countCheck = True
        #Check count of elements
        if countCheck:
            if (lineSplit[0] == 'keyword' and lineSplit[1] not in 
                ['return', 'if', 'while', 'print']) or (
                lineSplit[1] == ';'):
                countCheck = False
                checkCount(checker, currentName)
                checker.clear()
            if countCheck or lineSplit[1] in ['return', "print"]:
                checker.append(lineSplit)
        #Entering function declaration
        if lineSplit[1] == "def": 
            waitForFunc = True
            possiblyAtMain = False
        #Saving function name and doing general init stuff
        elif waitForFunc and lineSplit[0] == IDENTIFIER:
            output.append([lineSplit[1] + ":"])
            output.append(["begin", SIZEPLACEHOLDER])
            output.append(["push", "{LR}"])
            output.append(["push", "{FP}"])
            output.append([])
            waitForFunc = False
            currentName = lineSplit[1]
            getFuncData = True
        #Doing main/global init stuff
        elif not inMain and possiblyAtMain and lineSplit[1] != "def":
            output.append([])
            output.append(["main:"])
            output.append(["begin", SIZEPLACEHOLDER])
            inMain = True
        #Exiting function
        elif lineSplit[1] == "fed": 
            possiblyAtMain = True
            output.append([])
            output.append(["exit" + currentName + ":"])
            output.append(["pop", "{FP}"])
            output.append(["pop", "{PC}"])
            currentName = NULL
        #Unconditional jump to new scope
        if lineSplit[1] == "else":
            output.append([])
            output.append([stackJumpReturn[-1] + ":"])
            del stackJumpReturn[-1]
        #Exit if, may need a label if no elses were present
        elif lineSplit[1] == "fi":
            if len(stackJumpReturn) > 0:
                output.append([])
                output.append([stackJumpReturn[-1] + ":"])
                del stackJumpReturn[-1]
                jumps += 1
        elif inMain:
            '''
            Done function defs. Not an else/fi. General other statements then,
            like inits or prints, go here.
            TODO check for while loops (do/od)
            '''
            #TODO
            print("IN MAIN, TODO")
    writeOutput()
    
#Get input file name and open
print("Please ensure the input file is error free from the other phases, " +
      "and that the output from those phases is in the same directory.")
inFileStr = str(input('Enter input file name: '))
fail = False
try:
    inFile = open(inFileStr, 'r')
    checker = inFileStr.split('.')
    if checker[1] != 'cp':
        fail = True
        print(f'File extension .{checker[1]} is not supported!')
    try: #Open other required output files from previous phases
        semanticFile = open(SEMANTIC, "r")
        lexicalFile = open(LEXICAL, "r")
    except:
        fail = True
        print("Could not open other required files!")
except:
    fail = True
    print(f'Failed to open file {inFileStr}!')

#Create output file
outFile = open(OUTFILE, 'w')

#Actual start of real work
if not fail:
    TACGeneration()
    print(f'TAC generation on file {inFileStr} completed.')
    text = [[IDENTIFIER, "gcd"],["sep", "("],["sep", "("],[IDENTIFIER, "a"],["operator", "-"],[IDENTIFIER,"b"], ["sep", ","], [IDENTIFIER, "b"], ["sep", ")"], ["sep", ")"],["operator", "-"], ["integer", 3]]
    x = buildParseTree(text)
