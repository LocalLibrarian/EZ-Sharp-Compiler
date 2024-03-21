#Constants
OUTFILE = "outputTAC.txt"
LEXICAL = "outputLexical.txt"
IDENTIFIER = 'identifier'
SIZEPLACEHOLDER = "INSERTSIZEHERE"
NULL = "NULL"
FUNCTION = "FUNCTION"
INTEGER = "integer"
DOUBLE = "double"
JUMPLABEL = "place"
TEMPLABEL = "_temp"
BEGIN = "begin"
VARSIZE = 4

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
varsUsed = 0 #Holds number of vars used in a function/main
lastID = NULL #Holds last ID name
whileJumpBack = NULL #Used to jump back to a while condition check
seenVars = []

#Holds data about number of parameters (count) for a function
class Function:
    def __init__(self, name, count, numVars = 0, paramNames = []):
        self.name = name
        self.count = count
        self.numVars = numVars
        self.paramNames = paramNames.copy()

    def __str__(self):
        return f"FUNCTION: [{self.name}, count: {self.count}, names: " + (
            f"{self.paramNames}, needed vars: {self.numVars}]")
    
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
def getFuncData(func: str) -> Function:
    for funcName in funcData:
        if funcName.name == func: return funcName
    return Function(NULL, NULL)

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
    paramTokens = tokens[startI + 1: endI]
    stack = 0
    maybeFunc = False
    atFunc = False
    while x < len(paramTokens): #Splitting params
        if paramTokens[x][0] == IDENTIFIER:
            maybeFunc = True
        elif paramTokens[x][1] == "(" and maybeFunc:
            atFunc = True
            stack += 1
            maybeFunc = False
        elif paramTokens[x][1] == ")" and atFunc: stack -= 1
        if stack == 0: atFunc = False
        if paramTokens[x][1] == "," and not atFunc:
            temp = paramTokens[beginI:x]
            temp = removeUnmatchedBrackets(temp)
            params.append(temp)
            beginI = x + 1
        x += 1
    if getFuncData(name).count > 0:
        temp = paramTokens[beginI:x]
        temp = removeUnmatchedBrackets(temp)
        params.append(temp)
    return tokens[0:startI] + tokens[endI:], params

#Builds a parse tree from an expression in tokens and returns the name of the
#temp variable that the tree results in
def buildParseTree(tokens: list[list[str]]) -> str:
    global temps, output, funcData, varsUsed, seenVars
    foundFunc = False #Check if there is a function in tokens
    maybeFunc = False
    for token in tokens:
        if token[0] == IDENTIFIER: maybeFunc = True
        elif token[1] == "(" and maybeFunc: foundFunc = True
        else: maybeFunc = False
    root = ParseTree(NULL)
    current = root
    if foundFunc: #Push params and finish actual tree
        holder = removeFunctionParams(tokens)
        for param in holder[1]:
            output.append(["push", "{" + buildParseTree(param) + "}"])
        return buildParseTree(holder[0])
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
                else:
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
                        current.parent = ParseTree(token[1], right=current)
                        root = current.parent
                        current.parent.left = ParseTree(NULL, 
                                                         parent=current.parent)
                        current = current.parent.left
            elif token[0] in [INTEGER, DOUBLE, IDENTIFIER]:
                current.data = token[1]
                if current.parent == NULL: #Root node
                    current.parent = ParseTree(NULL, left=current)
                    root = current.parent
                current = current.parent
        #End of for loop, done making tree
        if root.data == NULL: #Simplest case, only 1 value as the left child
            if getFuncData(root.left.data).name != NULL:
                output.append([TEMPLABEL + str(temps), "=", "jumpLink",
                                       root.left.data])
                temps += 1
                varsUsed += 1
                holder = getFuncData(root.left.data)
                x = 0
                while x < len(holder.paramNames):
                    output.append(["pop", "{" + TEMPLABEL + str(temps - (x + 2)) + "}"])
                    x += 1
            else:
                output.append([TEMPLABEL + str(temps), "=", root.left.data])
                temps += 1
                varsUsed += 1
            return TEMPLABEL + str(temps - 1)
        #Something like -a, for example
        elif root.left == NULL and root.right.data != NULL:
            if getFuncData(root.right.data).name != NULL:
                output.append([TEMPLABEL + str(temps), "=", "jumpLink",
                                       root.right.data])
                temps += 1
                varsUsed += 1
                holder = getFuncData(root.right.data)
                x = 0
                while x < len(holder.paramNames):
                    output.append(["pop", "{" + TEMPLABEL + str(temps - (x + 2)) + "}"])
                    x += 1
                output.append([TEMPLABEL + str(temps), "=", "-1", "*",
                                TEMPLABEL + str(temps - 1)])
                temps += 1
                varsUsed += 1
            else:
                output.append([TEMPLABEL + str(temps), "=", "-1", "*", 
                               root.right.data])
                temps += 1
                varsUsed += 1
            return TEMPLABEL + str(temps - 1)
        else: #Trees have at least 3 nodes otherwise
            node = root
            while node.right != NULL:
                node = node.right
            while node.parent != NULL:
                node = node.parent
                #Check if have any functions to jumpLink to
                if getFuncData(node.left.data).name != NULL or (
                    getFuncData(node.right.data).name != NULL):
                    #Left is function only
                    if getFuncData(node.left.data).name != NULL and (
                        getFuncData(node.right.data).name == NULL
                    ):
                        output.append([TEMPLABEL + str(temps), "=", "jumpLink",
                                       node.left.data])
                        temps += 1
                        varsUsed += 1
                        holder = getFuncData(node.left.data)
                        x = 0
                        while x < len(holder.paramNames):
                            output.append(["pop", "{" + TEMPLABEL + str(temps - (x + 2)) + "}"])
                            x += 1
                        output.append([TEMPLABEL + str(temps), "=", 
                                       TEMPLABEL + str(temps - 1), node.data,
                                       node.right.data])
                        temps += 1
                        varsUsed += 1
                    #Right is function only
                    elif getFuncData(node.right.data).name != NULL and (
                        getFuncData(node.left.data).name == NULL
                    ):
                        output.append([TEMPLABEL + str(temps), "=", "jumpLink",
                                       node.right.data])
                        temps += 1
                        varsUsed += 1
                        holder = getFuncData(node.right.data)
                        x = 0
                        while x < len(holder.paramNames):
                            output.append(["pop", "{" + TEMPLABEL + str(temps - (x + 2)) + "}"])
                            x += 1
                        output.append([TEMPLABEL + str(temps), "=", 
                                       node.left.data, node.data,
                                       TEMPLABEL + str(temps - 1)])
                        temps += 1
                        varsUsed += 1
                    #Both are functions
                    else:
                        output.append([TEMPLABEL + str(temps), "=", "jumpLink",
                                       node.left.data])
                        temps += 1
                        varsUsed += 1
                        holder = getFuncData(node.left.data)
                        x = 0
                        while x < len(holder.paramNames):
                            output.append(["pop", "{" + TEMPLABEL + str(temps - (x + 2)) + "}"])
                            x += 1
                        output.append([TEMPLABEL + str(temps), "=", "jumpLink",
                                       node.right.data])
                        temps += 1
                        varsUsed += 1
                        holder = getFuncData(node.right.data)
                        x = 0
                        while x < len(holder.paramNames):
                            output.append(["pop", "{" + TEMPLABEL + str(temps - (x + 2)) + "}"])
                            x += 1
                        output.append([TEMPLABEL + str(temps), "=",
                                       TEMPLABEL + str(temps - 2),
                                       TEMPLABEL + str(temps - 1)])
                        temps += 1
                        varsUsed += 1
                elif node.right.data in operators:
                    output.append([TEMPLABEL + str(temps), "=", 
                                   TEMPLABEL + str(temps - 1),
                                   node.data, node.left.data])
                    temps += 1
                    varsUsed += 1
                else:
                    output.append([TEMPLABEL + str(temps), "=", node.left.data,
                                   node.data, node.right.data])
                    temps += 1
                    varsUsed += 1
            return TEMPLABEL + str(temps - 1)

#Checks counts of elements in tokens and updates the output as needed
def checkCount(tokens: list[list[str]], currentName: str) -> None:
    global output, jumps, stackJumpReturn, whileJumpBack, varsUsed, seenVars
    index = 0
    foundAssign = False
    foundCompare = False
    foundReturn = False
    foundPrint = False
    foundWhile = False
    for token in tokens:
        if token[1] == '=': foundAssign = True
        elif token[1] in comparators: foundCompare = True
        elif token[1] == 'return': foundReturn = True
        elif token[1] == "print": foundPrint = True
        elif token[1] == "while": foundWhile = True
        if not foundAssign and not foundCompare: index += 1
    ending = JUMPLABEL + str(jumps)
    if foundCompare:
        type = comparators[comparators.index(tokens[index][1])]
        left = buildParseTree(tokens[:index])
        right = buildParseTree(tokens[index + 1:])
        if foundWhile:
            output.append([])
            output.append([ending + ":"])
            whileJumpBack = ending
            jumps += 1
            ending = JUMPLABEL + str(jumps)
        output.append(["cmp", left + ",", right])
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
        output.append(["fp", "-", str(VARSIZE), "=", buildParseTree(tokens)]) 
        output.append(["jump", "exit" + currentName])
    elif foundAssign:
        output.append([lastID, "=", buildParseTree(tokens[index + 1:])])
        holder = getFuncData(currentName)
        if holder.name != NULL:
            if lastID not in holder.paramNames and lastID not in seenVars:
                varsUsed += 1
                seenVars.append(lastID)
        else: #In main
            if lastID not in seenVars:
                varsUsed += 1
                seenVars.append(lastID)
    elif foundPrint:
        output.append(["print", "(" + buildParseTree(tokens) + ")"])

#Fixes output to have the correct size for each function and main
def fixSizes() -> None:
    global output
    x = 0
    while x < len(output):
        #Check if we are at a BEGIN statement
        if len(output[x]) > 1 and output[x][1] == SIZEPLACEHOLDER:
            holder = getFuncData(output[x - 1][0][:-1])
            if holder.name != NULL:
                output[x][1] = str(holder.numVars * VARSIZE)
            else: #Main
                output[x][1] = str(varsUsed * VARSIZE)
        x += 1

#Main work function
def TACGeneration() -> None:
    global output, jumps, stackJumpReturn, funcData, varsUsed, lastID
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
    paramNames = [] #Holds parameter names for a function
    for line in lexicalFile:
        prev = lineSplit
        lineSplit = parseLexicalOutput(line)
        #Save count, name of params
        if getFuncData:
            if lineSplit[0] == IDENTIFIER:
                count += 1
                paramNames.append(lineSplit[1])
            #Add data to list of function info
            elif lineSplit[1] == ")":
                funcData.append(Function(currentName, count, 0,
                                         paramNames))
                getFuncData = False
                count = 0
                paramNames.clear()
                pOffset = 8
                for param in reversed(funcData[-1].paramNames):
                    output.append([param, "=", "fp", "+", str(pOffset)])
                    pOffset += VARSIZE
                varsUsed += funcData[-1].count
                output.append([])
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
                lineSplit[1] == ';' or lineSplit[0] == "programEnder"):
                countCheck = False
                checkCount(checker, currentName)
                checker.clear()
            if countCheck or lineSplit[1] in ['return', "print", "while"]:
                checker.append(lineSplit)
            if countCheck and len(prev) > 0 and prev[0] == IDENTIFIER and (
                lineSplit[1] == "="
            ):
                lastID = prev[1]
        #Entering function declaration
        if lineSplit[1] == "def": 
            waitForFunc = True
            possiblyAtMain = False
        #Saving function name and doing general init stuff
        elif waitForFunc and lineSplit[0] == IDENTIFIER:
            output.append([lineSplit[1] + ":"])
            output.append([BEGIN, SIZEPLACEHOLDER])
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
            output.append([BEGIN, SIZEPLACEHOLDER])
            inMain = True
        #Exiting function
        elif lineSplit[1] == "fed": 
            possiblyAtMain = True
            output.append([])
            output.append(["exit" + currentName + ":"])
            output.append(["pop", "{FP}"])
            output.append(["pop", "{PC}"])
            currentName = NULL
            funcData[-1].numVars = varsUsed
            varsUsed = 0
            seenVars.clear()
        #Unconditional jump to new scope
        if lineSplit[1] == "else":
            output.append(["jump", JUMPLABEL + str(jumps)])
            stackJumpReturn.append(JUMPLABEL + str(jumps))
            jumps += 1
            output.append([])
            output.append([stackJumpReturn[-2] + ":"])
            del stackJumpReturn[-2]
        #Exit if, may need a label if no elses were present
        elif lineSplit[1] == "fi":
            if len(stackJumpReturn) > 0:
                output.append([])
                output.append([stackJumpReturn[-1] + ":"])
                del stackJumpReturn[-1]
                jumps += 1
        #End a while loop
        elif lineSplit[1] == "od":
            output.append(["jump", whileJumpBack])
            output.append([])
            output.append([stackJumpReturn[-1] + ":"])
            del stackJumpReturn[-1]
    fixSizes()
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
