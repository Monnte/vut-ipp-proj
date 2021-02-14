# ----------------------------
# Author: Peter Zdravecký
# Date: 13.2.2021
# Description: Interpreter for IPPcode21
# Name: interpret.py
# Version: 1.0
# Python 3.8
# ----------------------------
import argparse
import sys
import re
import xml.etree.ElementTree as ET

currentInstIndex = 0
frames = {"GF":{},"LF":{},"TF":{}}
currentLF = -1
labels = {}

# HELP FUNCTIONS FOR INSTRUCTION FUNCTIONS
def nothing(args):
    pass

def getFrameAndName(var):
    return var["value"][0:2],var["value"][3:]

def getVarValue(var):
    frame,name = getFrameAndName(var)
    if not name in frames[frame]:
        exit(54)
    value = frames[frame][name]["value"]
    if not value:
        exit(56)
    return value

def getVarType(var):
    frame,name = getFrameAndName(var)
    if not name in frames[frame]:
        exit(54)
    return frames[frame][name]["type"]

def setVarValue(var,value):
    frame,name = getFrameAndName(var)
    if not name in frames[frame]:
        exit(54)
    frames[frame][name]["value"] = value

def setVarType(var,varType):
    frame,name = getFrameAndName(var)
    if not name in frames[frame]:
        exit(54)
    frames[frame][name]["type"] = varType

def getVal(arg):
    if arg["type"] == "var":
        return getVarValue(arg)
    else:
        return arg["value"]
def getType(arg):
    if arg["type"] == "var":
        return getVarType(arg)
    else:
        return arg["type"]

# INSTRUCTION FUNCTIONS 
def move(args):
        setVarValue(args[0],getVal(args[1]))
        setVarType(args[0],getType(args[1]))

def defvar(args):
    frame,name = getFrameAndName(args[0])
    if name in frames[frame] :
        exit(52)

    frames[frame][name] = {"value":None,"type":"None"}

def write(args):
        print(getVal(args[0]),end="")

def concat(args):
    if (getType(args[1]) != "string" or getType(args[2]) != "string"):
        exit(53)
    setVarValue(args[0],getVal(args[1])+getVal(args[2]))   


instructions = {
    "MOVE" : {"args":["var", "symb"],"func":move},
    "CREATEFRAME" : {"args":[],"func":nothing},
    "PUSHFRAME" : {"args":[],"func":nothing},
    "POPFRAME" : {"args":[],"func":nothing},
    "DEFVAR" : {"args":["var"],"func":defvar},
    "CALL" : {"args":["label"],"func":nothing},
    "RETURN" : {"args":[],"func":nothing},
    "PUSHS"  : {"args":["symb"],"func":nothing},
    "POPS"  : {"args":["var"],"func":nothing},
    "ADD"  : {"args":["var", "symb", "symb"],"func":nothing},
    "SUB"  : {"args":["var", "symb", "symb"],"func":nothing},
    "MUL"  : {"args":["var", "symb", "symb"],"func":nothing},
    "IDIV"  : {"args":["var", "symb", "symb"],"func":nothing},
    "LT"  : {"args":["var", "symb", "symb"],"func":nothing},
    "GT"  : {"args":["var", "symb", "symb"],"func":nothing},
    "EQ"  : {"args":["var", "symb", "symb"],"func":nothing},
    "AND"  : {"args":["var", "symb", "symb"],"func":nothing},
    "OR"  : {"args":["var", "symb", "symb"],"func":nothing},
    "NOT"  : {"args":["var", "symb"],"func":nothing},
    "INT2CHAR"  : {"args":["var", "symb"],"func":nothing},
    "STRI2INT"  : {"args":["var", "symb", "symb"],"func":nothing},
    "READ"  :  {"args":["var", "type"],"func":nothing},
    "WRITE" : {"args":["symb"],"func":write},
    "CONCAT"  : {"args":["var", "symb", "symb"],"func":concat},
    "STRLEN"  : {"args":["var", "symb"],"func":nothing},
    "GETCHAR"  : {"args":["var", "symb", "symb"],"func":nothing},
    "SETCHAR"  : {"args":["var", "symb", "symb"],"func":nothing},
    "TYPE"  : {"args":["var", "symb"],"func":nothing},
    "LABEL" : {"args":["label"],"func":nothing},
    "JUMP" : {"args":["label"],"func":nothing},
    "JUMPIFEQ" : {"args":["label", "symb", "symb"],"func":nothing},
    "JUMPIFNEQ" : {"args":["label", "symb", "symb"],"func":nothing},
    "EXIT" : {"args":["symb"],"func":nothing},
    "DPRINT" : {"args":["symb"],"func":nothing},
    "BREAK" :  {"args":[],"func":nothing},
    "CLEARS": {"args":[],"func":nothing},
    "ADDS": {"args":[],"func":nothing},
    "SUBS": {"args":[],"func":nothing},
    "MULS": {"args":[],"func":nothing},
    "IDIVS": {"args":[],"func":nothing},
    "LTS": {"args":[],"func":nothing},
    "GTS": {"args":[],"func":nothing},
    "EQS": {"args":[],"func":nothing},
    "ANDS": {"args":[],"func":nothing},
    "ORS": {"args":[],"func":nothing},
    "NOTS": {"args":[],"func":nothing},
    "INT2CHARS": {"args":[],"func":nothing},
    "STRI2INTS ": {"args":[],"func":nothing},
    "JUMPIFEQS": {"args":[],"func":nothing},
    "JUMPIFNEQS": {"args":[],"func":nothing},
}


sourceFile = sys.stdin
inputFile = sys.stdin

parser = argparse.ArgumentParser(add_help=False)
parser.add_argument('--help', action='store_true')
parser.add_argument('--source', dest='source')
parser.add_argument('--input', dest='input')

args = parser.parse_args()


## FIX LATER
def help():
    print("HELP")


def processArguments():
    global sourceFile,inputFile
    if args.help:
        if len(sys.argv) == 2:
            help()
        else:
            exit(10)
            
    if (args.input == None and args.source == None):
        exit(10)

    if(args.input):
        inputFile = args.input

    if(args.source):
        sourceFile = args.source


def checkXMLandSave():
    parseTree = {}
    try:
        tree = ET.parse(sourceFile)
        root = tree.getroot()
    except:
        exit(31) 

    if root.tag != "program" or not("language" in root.attrib):
        exit(32)

    if root.attrib["language"] != "IPPcode21":
        exit(32)

    # Sort instruction by opcode , if opcode attrib not exists exit with error code
    try:
        root[:] = sorted(root, key=lambda child: int(child.attrib["order"]))
    except:
        exit(32)

    # XML READING AND CHCEKS
    instLine = 0
    for instruction in root:
        # Check xml instruction tag
        if not re.match("^instruction$", instruction.tag):
            exit(32)

        # Check for correct attributes and count of them
        if not("opcode" in instruction.attrib) or len(instruction.attrib) != 2:
            exit(32)
            
        order = instruction.attrib["order"]
        instructionOpcode = instruction.attrib["opcode"]

        # Check for duplicit order in instructions or order is below 0 value
        if order in parseTree or int(order) < 0:
            exit(32)

        # Sort arguments to be in right order ( from 1 to max )
        instruction[:] = sorted(instruction, key=lambda child: child.tag)

        args = []
        argumentCount = 1
        for arg in instruction:
            # Check xml arg tag
            if arg.tag != ("arg" + str(argumentCount)):
                exit(32)

            # Check for correct attributes and count of them
            if not("type" in arg.attrib) or len(arg.attrib) != 1:
                exit(32)

            # Default set arguemnt value if empty from xml
            if arg.text == None: 
                arg.text = ""

            # Check if given type is correct to the given value
            if not argumentTypeCheck(arg.text,arg.attrib["type"]):
                exit(32)

            argValue = decodeArgumentValue(arg.attrib["type"],arg.text)
            args.append({"type":arg.attrib["type"],"value":argValue})
            argumentCount +=1

        # INSTRUCTIONS WRITING TO STRUCTURTE AND CHCEKS
        global instructions

        # Instruction opcode check if exists
        if not instructionOpcode in instructions:
            exit(32)

        # Check if count of arguments mazch to instuction arguments count
        if len(instructions[instructionOpcode]["args"]) != len(args):
            exit(32)

        # Arguments check
        for i in range(0,len(args)):
            if instructions[instructionOpcode]["args"][i] == "symb":
                if args[i]["type"] in ["int","string","bool","nil","var","float"]:
                    continue
            elif instructions[instructionOpcode]["args"][i] == args[i]["type"]:
                continue       
            # If evrything okay continue. If not ... exit
            exit(32)
        
        # Add new record to parseTree
        parseTree[instLine] = {"instruction":instructionOpcode,"args":args}
        # Add label if opcode LABEL / better do there
        if instructionOpcode == "LABEL":
            if args[0]["value"] in labels:
                exit(52)
            labels[args[0]["value"]] = instLine
        # --------------------------------------
        instLine += 1

    return parseTree


# Check if given type is correct to the given value
# Return: True if types match , false if not
def argumentTypeCheck(value, expectedType):
    if(expectedType == "int"):
        if not re.match('^[+-]?[\d]+$',value):
            return False
    elif(expectedType == "bool"):
        if not re.match('^true$|^false$',value):
            return False
    elif(expectedType == "nil"):
        if not re.match('^nil$',value):
            return False
    elif(expectedType == "var"):
        if not re.match('^(GF|TF|LF)@[a-z_\-$&%*!?A-Z][a-z_\-$&%*!?0-9A-Z]*',value):
            return False
    elif(expectedType == "type"):
        if not re.match('int$|^bool$|^string$|^nil$|^float$',value):
            return False
    elif(expectedType == "label"):
        if not re.match('(?i)^[a-z_\-$&%*!?][a-z_\-$&%*!?0-9]*',value):
            return False
    elif(expectedType == "float"):
        if not re.match('(?i)^0x([a-f]|[\d])(\.[\d|a-f]*)?p(\+|-)?[\d]*$',value):
            return False

    return True


def escapeSeqToAscii(match):
    seq = match.group(0).replace("\\","")
    return str(chr(int(seq)))

def decodeArgumentValue(argType,value):
    decodedValue = value

    if(argType == "string"):
        decodedValue = re.sub('\\\\[0-9]{3}', escapeSeqToAscii, value) # replace all \ sequences to ascii
    elif(argType == "int"):
        decodedValue = int(value)
    elif(argType == "float"):
        try:
            decodedValue = float.fromhex(value)
        except:
            exit(32)

    return decodedValue

def interpreteCode(tree,lastIndex):  
    global currentInstIndex
    while currentInstIndex <= lastIndex:
        instructions[tree[currentInstIndex]["instruction"]]["func"](tree[currentInstIndex]["args"])
        currentInstIndex +=1

def main():
    processArguments()
    tree = checkXMLandSave()
    lastInstruction = int(list(tree)[-1])
    interpreteCode(tree,lastInstruction)
    print("============================")
    print(labels)
    print(frames)

if __name__ == '__main__':
    main()