#Constants
ERRORFILE = 'errorLog.txt'
OUTFILE = 'output.txt'

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
    
#Valid keywords
keywords = ['def', 'fed', 'int', 'double', 'if', 'fi', 'then', 'else', 'while', 'do', 'od', 'print', 'return']

#Code-defined identifiers, i.e., func and var names, list is updated during compilation
identifiers = []

#Writes errors to error log file
def throwError(lineNum, colNum, errorChar, line, errorType):
    errorFile.write(f'Error on line {lineNum}, column {colNum}, at character ({errorChar}) [{errorType}]:\n--> {lineNum} {line[0:colNum]}\n')

#Writes tokens to output file
def writeToken(tokenType, token):
    OUTFILE.write(f'<{tokenType}> {token}\n')

"""
Actually does all the token finding.

For error handling, on an error, we throw the error, then skip all the next 
characters until the next token separator (found in the separators list).
This is Panic Mode implementation.
"""
def getNextToken(lineNum, line):
    panic = False
    colNum = 1
    for c in line:
        if(panic): #Panic Mode/error handling #TODO
            if c in separators:
                panic = False
        else:
            #Check if char in alphabet at all, error if not
            if c not in alphabet and c not in separators: 
                throwError(lineNum, colNum, c, line, 'Invalid Character')
                panic = True
                if(debug): print(f'Errored on line {lineNum} with char ({c})')
        if(debug): print(f'{colNum} {c}')
        colNum += 1


#Uses getNextToken to do real work, this just passes it lines and line numbers
def lexicalAnalysis(inFile):
    lineNum = 1
    for line in inFile:
        getNextToken(lineNum, line)
        lineNum += 1
    
    #Closing resources
    inFile.close()
    outFile.close()
    errorFile.close()
    
#Get input file name and open
inFileStr = str(input('Enter input file name: '))
inFileInput = inFileStr.split(' ') 
inFile = open(inFileInput[0], 'r')

#Debug mode enabler
if len(inFileInput) > 2:
    debug = True
    print('DEBUG ON, SEE README FOR HOW TO NOT ENABLE THIS ON RUN')

#Create error log file and output file
outFile = open(OUTFILE, 'w')
errorFile = open(ERRORFILE, 'w')

#Actual start of real work
lexicalAnalysis(inFile)