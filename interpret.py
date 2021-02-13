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
from xml.dom.minidom import parse
import xml.etree.ElementTree as ET

instructions = {
    "MOVE" : ["var", "symb"],
    "CREATEFRAME" : [],
    "PUSHFRAME" : [],
    "POPFRAME" : [],
    "DEFVAR" : ["var"],
    "CALL" : ["label"],
    "RETURN" : [],
    "PUSHS"  : ["symb"],
    "POPS"  : ["var"],
    "ADD"  : ["var", "symb", "symb"],
    "SUB"  : ["var", "symb", "symb"],
    "MUL"  : ["var", "symb", "symb"],
    "IDIV"  : ["var", "symb", "symb"],
    "LT"  : ["var", "symb", "symb"],
    "GT"  : ["var", "symb", "symb"],
    "EQ"  : ["var", "symb", "symb"],
    "AND"  : ["var", "symb", "symb"],
    "OR"  : ["var", "symb", "symb"],
    "NOT"  : ["var", "symb"],
    "INT2CHAR"  : ["var", "symb"],
    "STRI2INT"  : ["var", "symb", "symb"],
    "READ"  : ["var", "type"],
    "WRITE" : ["symb"],
    "CONCAT"  : ["var", "symb", "symb"],
    "STRLEN"  : ["var", "symb"],
    "GETCHAR"  : ["var", "symb", "symb"],
    "SETCHAR"  : ["var", "symb", "symb"],
    "TYPE"  : ["var", "symb"],
    "LABEL" : ["label"],
    "JUMP" : ["label"],
    "JUMPIFEQ" : ["label", "symb", "symb"],
    "JUMPIFNEQ" : ["label", "symb", "symb"],
    "EXIT" : ["symb"],
    "DPRINT" : ["symb"],
    "BREAK" : [],
    "CLEARS":[],
    "ADDS":[],
    "SUBS":[],
    "MULS":[],
    "IDIVS":[],
    "LTS":[],
    "GTS":[],
    "EQS":[],
    "ANDS":[],
    "ORS":[],
    "NOTS":[],
    "INT2CHARS":[],
    "STRI2INTS ":[],
    "JUMPIFEQS":[],
    "JUMPIFNEQS":[],
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
                
            args.append({"type":arg.attrib["type"],"value":arg.text})
            argumentCount +=1

        # INSTRUCTIONS WRITING TO STRUCTURTE AND CHCEKS
        global instructions

        # Instruction opcode check if exists
        if not instructionOpcode in instructions:
            exit(32)

        # Check if count of arguments mazch to instuction arguments count
        if len(instructions[instructionOpcode]) != len(args):
            exit(32)

        # Arguments check
        for i in range(0,len(args)):
            if instructions[instructionOpcode][i] == "symb":
                if args[i]["type"] in ["int","string","bool","nil","var","float"]:
                    continue
            elif instructions[instructionOpcode][i] == args[i]["type"]:
                continue       
            # If evrything okay continue. If not ... exit
            exit(32)
        
        # Add new record to parseTree
        parseTree[order] = {"inst":instructionOpcode,"args":args}

    return parseTree


# Check if given type is correct to the given value
# Return: True if types match , false if not
def argumentTypeCheck(value, expectedType):
    if(expectedType == "int"):
        if not re.match('^[+-]?[\d]+$',value):
            return False
    elif(expectedType == "string"):
        if len(re.findall('\\\\[0-9]{3}',value)) != len(re.findall('\\\\',value)):
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


def main():
    processArguments()
    tree = checkXMLandSave()

if __name__ == '__main__':
    main()


