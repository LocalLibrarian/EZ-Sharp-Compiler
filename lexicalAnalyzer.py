#Constants
ERRORFILE = 'errorLog.txt'
OUTFILE = 'output.txt'
BUFFERLENGTH = 2048
FAILSTATE = 'FAIL'
INVALIDCHAR = 'Invalid Character'
INVALIDID = 'Invalid Identifier'
INVALIDDOUBLE = 'Invalid Double'
INVALIDTEXT = 'Invalid Text'

#Valid alphabet/characters, if a char isn't in this list or separators,
#immediately throw an error
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

#List of all valid numbers
numbers = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0']

#List of all valid letters
letters = []
for c in 'qwertyuiopasdfghjklzxcvbnm':
    letters.append(c)
    
#Valid keywords
keywords = ['def', 'fed', 'int', 'double', 'if', 'fi', 'then', 'else', 'while',
            'do', 'od', 'print', 'return']

#Code-defined identifiers, i.e., func and var names, list is updated
#during compilation
identifiers = []

#Writes errors to error log file
def throwError(lineNum, colNum, errorChar, line, errorType):
    part1 = f'Error on line {lineNum}'
    part2 = f'column {colNum}'
    part3 = f'at character ({errorChar}) [{errorType}]'
    part4 = f'--> {lineNum} {line[0:colNum]}'
    errorFile.write(f'{part1}, {part2}, {part3}:\n{part4}\n')

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
            throwError(lineNum, colNum - len(token) + i, c, line, 
                       INVALIDCHAR)
            typed = FAILSTATE
        i += 1
    #Fail means invalid character or other error, DO NOT write the 
    #token to output
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
            #Change semi-colons to statement enders as that is what they are
            if token == ';': typed = 'statementEnder'
            else: typed = 'seperator'
        #Programmer-made identifiers
        elif token in identifiers:
            typed = 'identifier'
        #Don't know token type yet, need to check states to determine
        if(typed == 'null'):
            """
            Iterate through each char and treat it as a state.
            We are only checking for (identifier, integer, double) validity
            because everything else is already covered above. We reject anything
            else by throwing an error and not writing it to the output
            (Panic Mode).

            Identifier = start with letter, then anything other than a seperator
                         is valid
            Integer = only numbers, nothing else
            Double = x.y(e)(-)x.y, where x and y are integers, e is optional, -
                     is optional if e has already appeared but cannot appear
                     otherwise
            """
            #Immediately classify as identifier if passes the criteria above
            if token[0] in letters:
                if '.' not in token and '-' not in token:
                    #Can ignore other seperators above as the tokenizer won't
                    #allow them into tokens, just the 2 above
                    typed = 'identifier'
                    identifiers.append(token)
                    writeToken(typed, token)
                #This is an invalid identifier, it starts with a letter but has
                #seperators in it
                else:
                    i1 = token.find('.')
                    i2 = token.find('-')
                    i3 = 0
                    #Found no periods, so found a minus sign
                    if i1 < 0:
                        i3 = i2
                    #Found no minus signs, so found a period
                    elif i2 < 0:
                        i3 = i1
                    #Found both, go with whatever is first
                    elif i1 < i2:
                        i3 = i1
                    else:
                        i3 = i2
                    throwError(lineNum, colNum - len(token) + i3, token[i3],
                               line, INVALIDID)
            #Only need to classify integers, doubles, and fail states for them
            else:
                eFound = False #True if 'e' has been found for a double
                numDecimalsBefore = 0 #Counts number of decimals before e
                numDecimalsAfter = 0 #Counts number of decimals after e
                i = 0
                errored = False #True if threw an error, end checking
                while(i < len(token) and errored == False):
                    state = token[i]
                    if state in letters:
                        if state == 'e':
                            #Already have an e, can't have more OR char before
                            #this wasn't a number, also fail
                            if eFound or token[i - 1] not in numbers:
                                throwError(lineNum, colNum - len(token) + i,
                                        state, line, INVALIDDOUBLE)
                                errored = True
                            else:
                                eFound = True
                        else:
                            throwError(lineNum, colNum - len(token) + i,
                                        state, line, INVALIDTEXT)
                            errored = True
                    #Fail on too many decimals, too many decimals in a row
                    if state == '.':
                        if eFound:
                            if numDecimalsAfter == 0: numDecimalsAfter += 1
                            else:
                                throwError(lineNum, colNum - len(token) + i,
                                       state, line, INVALIDDOUBLE)
                                errored = True
                        else:
                            if numDecimalsBefore == 0: numDecimalsBefore += 1
                            else:
                                throwError(lineNum, colNum - len(token) + i,
                                       state, line, INVALIDDOUBLE)
                                errored = True
                    i += 1
                #Didn't encounter any errors, can now classify token
                if not errored:
                    #No decimals or 'e's, token is an integer
                    if (not eFound and numDecimalsBefore == 0 and 
                        numDecimalsAfter == 0): typed = 'integer'
                    #At least 1 decimal or 'e', token is a double
                    else: typed = 'double'
                    writeToken(typed, token)
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
    token = ''
    dub = False #Used to determine if parsing a double
    #Skip is used when a compound comparator is made to skip the next char 
    #since it's been used already
    skip = False
    colNum = 1
    for c in line:
        if not skip:
            dub = False
            if c in separators:
                """
                Checking for doubles:
                First part checks for decimals and if there is a number before 
                and after it. This covers things in the form x.yez, even with 
                omitting the 'e' and 'z' parts. Second part checks for a
                negative sign and if there is an e before it and number after
                it. This covers x.ye-z.
                """
                if (c == '.' and len(token) > 0 and token[len(token) - 1] 
                    in numbers 
                    and colNum < len(line) and line[colNum] in numbers) or (
                    c == '-' and len(token) > 0 and token[len(token) - 1] == 'e'
                    and colNum < len(line) and line[colNum] in numbers):
                    token += c
                    dub = True
                """
                End of previous token OR multiple separators/whitespace in a row
                OR comparator, i.e. ==/<>/>=/<=
                """
                if token != '' and not dub:
                    findTokenType(token, lineNum, colNum, line)
                if c not in whitespaces and not dub:
                    if c in comparators:
                        if colNum < len(line):
                            compound = False
                            #Checking if we have a compound comparator, i.e.
                            #==, <=, >=, <>
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
                            Edge-case: a comparator (<, >, =) at the end of
                            input. In this case, just write that the token is a
                            comparator, DO NOT access line[colNum], as that
                            would be out of list bounds.
                            """
                            findTokenType(c, lineNum, colNum, line)
                    else:
                        #Check if we are at end of program
                        if c == '.': writeToken('programEnder', c)
                        else: findTokenType(c, lineNum, colNum, line)
                #Don't reset doubles
                if not dub:
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
if not fail: lexicalAnalysis(inFile)
