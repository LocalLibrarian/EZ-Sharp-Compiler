'''
NOTES
1. For if... then... fi perhaps make a label at every fi so stuff after an if
    can jump back to the end of the if? ex.:
    if x == 0 then
        x = 3
    fi
    print(x)
    would become
    cmp x, 0
    jumpEqual place0
    place1:
    print(x)
    ...
    place0:
    x = 3
    jump place1
2. Similar thing for else with above:
    if... then
    ...
    else
    y = 5
    print(x + y)
    becomes
    cmp...
    (jumps for cmp)
    jump place3 (3 is example number)
    place4:
    print(x + y)
    ...
    place3:
    y = 5
    jump place4
3. To fix issues where we have example:
    x = 1 + 2 * y
    will have to use parse tree to get order of ops right and divide up the
    parts into segments of 2. The above may become for example:
    _temp0 = 2 * y
    x = _temp0 + 1

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

#Globals
output = [["jump", "main"], [], []] #List of lists of words for each line
jumps = 0
temps = 0

#Holds data about number of parameters (count) for a function
class Function:
    def __init__(self, name, count):
        self.name = name
        self.count = count

    def __str__(self):
        return f"FUNCTION: {self.name}, count: {self.count}"
    
#Binary tree for parsing BEDMAS of expressions and making sure they are in
#right order when reduced to TAC
class ParseTree:
    def __init__(self, data):
        self.data = data
        self.left = NULL
        self.right = NULL

    def __str__(self):
        return f"PARSETREE: {self.data}, left: {str(self.left)}, right: " + (
            f"{str(self.right)}")

#Breaks output lines of lexicalAnalyzer up to make them easier to deal with.
#First element is type of token, second element is token
def parseLexicalOutput(line) -> list[str]:
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
def countElements(tokens: list[str]) -> int:
    #Assume that tokens is in lineSplit format: [[tokenType, token], etc...]
    count = 0
    for elem in tokens:
        if elem[0] in [IDENTIFIER, INTEGER, DOUBLE]:
            count += 1
    return count

#Returns the index of two (different) IDs in tokens
def findIDLiteralIndex(tokens: list[str]) -> tuple[int, int]:
    index1 = -1
    index2 = -1
    for x in range(len(tokens)):
        if tokens[x][0] in [IDENTIFIER, INTEGER, DOUBLE]:
            if index1 == -1: index1 = x
            else: index2 = x
    return (index1, index2)

#Checks counts of elements in tokens and updates the output as needed
def checkCount(tokens: list[str], currentName: str) -> None:
    global output, jumps
    index = 0
    foundAssign = False
    foundCompare = False
    foundReturn = False
    for token in tokens:
        if token[1] == '=': foundAssign = True
        elif token[1] in comparators: foundCompare = True
        elif token[1] == 'return': foundReturn = True
        if not foundAssign and not foundCompare: index += 1
    ending = JUMPLABEL + str(jumps)
    if foundCompare:
        #a == b for example in this case
        type = comparators[comparators.index(tokens[index][1])]
        if countElements(tokens[:index]) == 1 and (
            countElements(tokens[index + 1:]) == 1):
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
    elif foundReturn:
        #return (a) for example in this case
        if countElements(tokens) == 1:
            index1, index2 = findIDLiteralIndex(tokens) #Can ignore index2 here
            output.append(["fp", "-", "4", "=", tokens[index1][1]])
            output.append(["jump", "exit" + currentName])
        else:
            #TODO
            print("TODO: HANDLE INCORRECT NUMBERS WITH PARSE TREE?")

#Main work function
def TACGeneration() -> None:
    funcData = [] #Holds Function classes that contain param counts
    global output
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
            if countCheck or lineSplit[1] == 'return':
                checker.append(lineSplit)
        #Entering function declaration
        if lineSplit[1] == "def": 
            waitForFunc = True
            possiblyAtMain = False
        #Saving function name and doing general init stuff
        elif waitForFunc and lineSplit[0] == IDENTIFIER:
            output[-1].append(lineSplit[1] + ":")
            output.append(["begin", SIZEPLACEHOLDER])
            output.append(["push", "{LR}"])
            output.append(["push", "{FP}"])
            waitForFunc = False
            currentName = lineSplit[1]
            getFuncData = True
        #Doing main/global init stuff
        elif not inMain and possiblyAtMain and lineSplit[1] != "def":
            output.append(["main:"])
            output.append(["begin", SIZEPLACEHOLDER])
            inMain = True
        #Exiting function
        elif lineSplit[1] == "fed": 
            possiblyAtMain = True
            output.append(["exit" + currentName + ":"])
            output.append(["pop", "{FP}"])
            output.append(["pop", "{PC}"])
            currentName = NULL
        #Done function defs, just doing global statements or inits
        elif inMain:
            #TODO
            print('TODO: Main Handling')
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