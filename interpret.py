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
exitBool = False
exitValue = 0
frames = {"GF": {}}
framesStack = []
callStack = []
dataStack = []
labels = {}

instCount = 0
inicializedMaxCount = 0
dataStackCount = 0
dataStackMaxCount = 0

statistic = False

# HELP FUNCTIONS FOR INSTRUCTION FUNCTIONS


def nothing(args):
    pass


def maxInicializedInFrame(frame):
    global inicializedMaxCount
    counter = 0
    for x in frame:
        if frame[x]["value"] != None:
            counter += 1

    if counter > inicializedMaxCount:
        inicializedMaxCount = counter


def getFrameAndName(var):
    return var["value"][0:2], var["value"][3:]


def frameExists(frame):
    if not frame in frames:
        print("{}: Frame doesn't exists".format(
            currentInstIndex), file=sys.stderr)
        exit(55)


def varExistsInFrame(frame, name):
    frameExists(frame)
    if not name in frames[frame]:
        print("{}: Undefiend variable".format(
            currentInstIndex), file=sys.stderr)
        exit(54)


def getVarValue(var):
    frame, name = getFrameAndName(var)
    varExistsInFrame(frame, name)

    value = frames[frame][name]["value"]
    if value == None:
        print("{}: Trying to get value from uninicialzated variable".format(
            currentInstIndex), file=sys.stderr)
        exit(56)
    return value


def getVarType(var):
    frame, name = getFrameAndName(var)
    varExistsInFrame(frame, name)
    return frames[frame][name]["type"]


def setVarValue(var, value):
    frame, name = getFrameAndName(var)
    varExistsInFrame(frame, name)
    frames[frame][name]["value"] = value


def setVarType(var, varType):
    frame, name = getFrameAndName(var)
    varExistsInFrame(frame, name)
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


def getLabel(var):
    if not var["value"] in labels:
        print("{}: Undefiend label".format(currentInstIndex), file=sys.stderr)
        exit(52)

    return var["value"]

# INSTRUCTION FUNCTIONS


def move(args):
    setVarValue(args[0], getVal(args[1]))
    setVarType(args[0], getType(args[1]))


def defvar(args):
    frame, name = getFrameAndName(args[0])
    if name in frames[frame]:
        print("{}: Redefinition of variable".format(
            currentInstIndex), file=sys.stderr)
        exit(52)

    frames[frame][name] = {"value": None, "type": "None"}


def write(args):
    if(getType(args[0]) == "nil"):
        print("", end="")
    elif(getType(args[0]) == "float"):
        print(float.hex(getVal(args[0])), end="")
    else:
        print(getVal(args[0]), end="")


def concat(args):
    if (getType(args[1]) != "string" or getType(args[2]) != "string"):
        print("{}: CONCAT variable types missmatch".format(
            currentInstIndex), file=sys.stderr)
        exit(53)
    setVarType(args[0], "string")
    setVarValue(args[0], getVal(args[1])+getVal(args[2]))


def jumpifeq(args):
    global currentInstIndex
    if((getType(args[1]) == "nil") ^ (getType(args[2]) == "nil")):
        return

    if(getType(args[1]) != getType(args[2])):
        print("{}: JUMPIFEQ not same types of variables".format(
            currentInstIndex), file=sys.stderr)
        exit(53)

    if(getVal(args[1]) == getVal(args[2])):
        currentInstIndex = labels[getLabel(args[0])]


def jumpifneq(args):
    global currentInstIndex
    if((getType(args[1]) == "nil") ^ (getType(args[2]) == "nil")):
        currentInstIndex = labels[getLabel(args[0])]
        return
    if(getType(args[1]) != getType(args[2])):
        print("{}: JUMPIFNEQ not same types of variables 1:{} 2:{}".format(
            currentInstIndex, getVal(args[1]), getType(args[2])), file=sys.stderr)
        exit(53)

    if(getVal(args[1]) != getVal(args[2])):
        currentInstIndex = labels[getLabel(args[0])]


def jump(args):
    global currentInstIndex
    currentInstIndex = labels[getLabel(args[0])]


def createframe(args):
    frames["TF"] = {}


def pushframe(args):
    frameExists("TF")
    maxInicializedInFrame(frames["TF"])
    framesStack.append(frames["TF"])
    frames.pop("TF")
    frames["LF"] = framesStack[len(framesStack)-1]


def popframe(args):
    frameExists("LF")
    maxInicializedInFrame(frames["LF"])
    frames["TF"] = frames["LF"]
    framesStack.pop()
    if len(framesStack) > 0:
        frames["LF"] = framesStack[len(framesStack)-1]
    else:
        frames.pop("LF")


def call(args):
    global currentInstIndex, callStack
    callStack.append(currentInstIndex)
    currentInstIndex = labels[getLabel(args[0])]


def ret(args):
    global currentInstIndex, callStack
    if len(callStack) == 0:
        print("{}: RETURN missing value at call stack".format(
            currentInstIndex), file=sys.stderr)
        exit(56)
    currentInstIndex = callStack.pop()


def pushs(args):
    global dataStack, dataStackCount, dataStackMaxCount
    dataStack.append({"value": getVal(args[0]), "type": getType(args[0])})
    dataStackCount += 1
    if dataStackCount > dataStackMaxCount:
        dataStackMaxCount = dataStackCount


def pops(args):
    global dataStack, dataStackCount
    if len(dataStack) == 0:
        print("{}: Data stack is empty cannot pop value".format(
            currentInstIndex), file=sys.stderr)
        exit(56)

    dataStackCount -= 1
    var = dataStack.pop()
    setVarValue(args[0], var["value"])
    setVarType(args[0], var["type"])


def add(args):
    if (not(getType(args[1]) == "int" and getType(args[2]) == "int") and not(getType(args[1]) == "float" and getType(args[2]) == "float")):
        print("{}: ADD variable types missmatch".format(
            currentInstIndex), file=sys.stderr)
        exit(53)

    setVarType(args[0], getType(args[1]))
    setVarValue(args[0], getVal(args[1]) + getVal(args[2]))


def sub(args):
    if (not(getType(args[1]) == "int" and getType(args[2]) == "int") and not(getType(args[1]) == "float" and getType(args[2]) == "float")):
        print("{}: SUB variable types missmatch".format(
            currentInstIndex), file=sys.stderr)
        exit(53)

    setVarType(args[0], getType(args[1]))
    setVarValue(args[0], getVal(args[1]) - getVal(args[2]))


def mul(args):
    if (not(getType(args[1]) == "int" and getType(args[2]) == "int") and not(getType(args[1]) == "float" and getType(args[2]) == "float")):
        print("{}: MUL variable types missmatch".format(
            currentInstIndex), file=sys.stderr)
        exit(53)

    setVarType(args[0], getType(args[1]))
    setVarValue(args[0], getVal(args[1]) * getVal(args[2]))


def idiv(args):
    if getVal(args[2]) == 0:
        exit(57)

    if (not(getType(args[1]) == "int" and getType(args[2]) == "int") and not(getType(args[1]) == "float" and getType(args[2]) == "float")):
        print("{}: IDIV variable types missmatch".format(
            currentInstIndex), file=sys.stderr)
        exit(53)

    setVarType(args[0], getType(args[1]))
    setVarValue(args[0], getVal(args[1]) // getVal(args[2]))


def div(args):
    if getVal(args[2]) == 0:
        exit(57)

    if (getType(args[1]) != "float" or getType(args[2]) != "float"):
        breakInterpret("")
        print("{}: DIV variable types missmatch".format(
            currentInstIndex), file=sys.stderr)
        exit(53)

    setVarType(args[0], "float")
    setVarValue(args[0], getVal(args[1]) / getVal(args[2]))


def lt(args):
    if(getType(args[1]) == "nil" or getType(args[2]) == "nil" or getType(args[1]) != getType(args[2])):
        print("{}: LT not same types of variables".format(
            currentInstIndex), file=sys.stderr)
        exit(53)

    setVarType(args[0], "bool")
    if getVal(args[1]) < getVal(args[2]):
        setVarValue(args[0], True)
    else:
        setVarValue(args[0], False)


def gt(args):
    if(getType(args[1]) == "nil" or getType(args[2]) == "nil" or getType(args[1]) != getType(args[2])):
        print("{}: GT not same types of variables".format(
            currentInstIndex), file=sys.stderr)
        exit(53)

    setVarType(args[0], "bool")
    if getVal(args[1]) > getVal(args[2]):
        setVarValue(args[0], True)
    else:
        setVarValue(args[0], False)


def eq(args):
    if((getType(args[1]) == "nil") ^ (getType(args[2]) == "nil")):
        setVarType(args[0], "bool")
        setVarValue(args[0], False)
        return

    if(getType(args[1]) != getType(args[2])):
        print("{}: EQ not same types of variables".format(
            currentInstIndex), file=sys.stderr)
        # breakInterpret("")
        exit(53)

    setVarType(args[0], "bool")
    if getVal(args[1]) == getVal(args[2]):
        setVarValue(args[0], True)
    else:
        setVarValue(args[0], False)


def logAnd(args):
    if (getType(args[1]) != "bool" or getType(args[2]) != "bool"):
        print("{}: AND not bool variables".format(
            currentInstIndex), file=sys.stderr)
        exit(53)

    setVarType(args[0], "bool")
    setVarValue(args[0], getVal(args[1]) and getVal(args[2]))


def logOr(args):
    if (getType(args[1]) != "bool" or getType(args[2]) != "bool"):
        print("{}: OR not bool variables".format(
            currentInstIndex), file=sys.stderr)
        exit(53)

    setVarType(args[0], "bool")
    setVarValue(args[0], getVal(args[1]) or getVal(args[2]))


def logNot(args):
    if (getType(args[1]) != "bool"):
        print("{}: NOT not bool variable".format(
            currentInstIndex), file=sys.stderr)
        exit(53)

    setVarType(args[0], "bool")
    setVarValue(args[0], not getVal(args[1]))


def int2char(args):
    if getType(args[1]) != "int":
        print("{}: INT2CHAR variable type missmatch".format(
            currentInstIndex), file=sys.stderr)
        exit(53)
    try:
        setVarValue(args[0], chr(getVal(args[1])))
        setVarType(args[0], "string")
    except:
        print("{}: INT2CHAR chr function failed".format(
            currentInstIndex), file=sys.stderr)
        exit(58)


def str2int(args):
    if getType(args[1]) != "string" or getType(args[2]) != "int":
        print("{}: STR2INT variable types missmatch".format(
            currentInstIndex), file=sys.stderr)
        exit(53)
    string = getVal(args[1])
    index = getVal(args[2])
    if index < 0:
        exit(58)
        print("{}: STR2INT index is < 0".format(
            currentInstIndex), file=sys.stderr)
    try:
        setVarValue(args[0], ord(string[index]))
        setVarType(args[0], "int")
    except:
        print("{}: STR2INT ord function failed , or index is out of boundries".format(
            currentInstIndex), file=sys.stderr)
        exit(58)


def read(args):
    val = inputFile.readline().strip()
    varType = getVal(args[1])
    setType = ""
    setValue = ""
    if varType == "bool":
        setType = "bool"
        if val == "true":
            setValue = True
        else:
            setValue = False
    elif varType == "int":
        setType = "bool"
        try:
            setValue = int(val)
        except:
            setType = "nil"
            setValue = "nil"
    elif varType == "string":
        setType = "string"
        setValue = val
    elif varType == "float":
        setType = "float"
        try:
            setValue = float.fromhex(val)
        except:
            setType = "nil"
            setValue = "nil"

    setVarType(args[0], setType)
    setVarValue(args[0], setValue)


def strlen(args):
    if (getType(args[1]) != "string"):
        print("{}: STRLEN variable type missmatch".format(
            currentInstIndex), file=sys.stderr)
        exit(53)
    setVarValue(args[0], len(getVal(args[1])))
    setVarType(args[0], "int")


def getchar(args):
    if getType(args[1]) != "string" or getType(args[2]) != "int":
        print("{}: GETCHAR variable types missmatch".format(
            currentInstIndex), file=sys.stderr)
        exit(53)
    string = getVal(args[1])
    index = getVal(args[2])
    if index < 0:
        exit(58)
        print("{}: GETCHAR index is < 0".format(
            currentInstIndex), file=sys.stderr)
    try:
        setVarValue(args[0], string[index])
        setVarType(args[0], "string")
    except:
        print("{}: GETCHAR index is out of boundries".format(
            currentInstIndex), file=sys.stderr)
        exit(58)


def setchar(args):
    if getType(args[0]) != "string" or getType(args[1]) != "int" or getType(args[2]) != "string":
        print("{}: SETCHAR variable types missmatch".format(
            currentInstIndex), file=sys.stderr)
        exit(53)
    index = getVal(args[1])
    if index < 0:
        exit(58)
        print("{}: SETCHAR index is < 0".format(
            currentInstIndex), file=sys.stderr)
    try:
        val = getVal(args[0])
        val[index] = getVal(args[2])[0]
        setVarValue(args[0], val)
    except:
        print("{}: SETCHAR index is out of boundries".format(
            currentInstIndex), file=sys.stderr)
        exit(58)


def typeFunc(args):
    varType = getType(args[1])
    val = varType
    if varType == "var":
        frame, name = getFrameAndName(args[1])
        if not name in frames[frame]:
            val = ""

    setVarType(args[0], "string")
    setVarValue(args[0], val)


def exitInterpret(args):
    global exitValue, exitBool
    if (getType(args[0]) != "int"):
        print("{}: EXIT variable types missmatch".format(
            currentInstIndex), file=sys.stderr)
        exit(53)
    val = getVal(args[0])
    if val < 0 or val > 49:
        print("{}: EXIT value out of <0,49>".format(
            currentInstIndex), file=sys.stderr)
        exit(57)

    exitBool = True
    exitValue = val


def dprint(args):
    print(getVal(args[0]), file=sys.stderr)


def breakInterpret(args):
    print("Current instruction executed index: {}".format(
        currentInstIndex), file=sys.stderr)
    print(frames, file=sys.stderr)


def float2int(args):
    if getType(args[1]) != "float":
        print("{}: FLOAT2INT variable type missmatch".format(
            currentInstIndex), file=sys.stderr)
        exit(53)
    try:
        setVarValue(args[0], int(getVal(args[1])))
        setVarType(args[0], "int")
    except:
        print("{}: FLOAT2INT cannot do operation".format(
            currentInstIndex), file=sys.stderr)
        exit(58)


def int2float(args):
    if getType(args[1]) != "int":
        print("{}: INT2FLOAT variable type missmatch".format(
            currentInstIndex), file=sys.stderr)
        exit(53)
    try:
        setVarValue(args[0], float(getVal(args[1])))
        setVarType(args[0], "float")
    except:
        print("{}: INT2FLOAT cannot do operation".format(
            currentInstIndex), file=sys.stderr)
        exit(58)


# STACK FUNCTIONS
def getValStack():
    global dataStack, dataStackCount
    if len(dataStack) == 0:
        exit(56)

    dataStackCount -= 1
    return dataStack.pop()


def setValStack(val, varType):
    global dataStack, dataStackCount, dataStackMaxCount
    dataStack.append({"value": val, "type": varType})
    dataStackCount += 1
    if dataStackCount > dataStackMaxCount:
        dataStackMaxCount = dataStackCount


def clears(args):
    dataStack = []


def adds(args):
    arg2 = getValStack()
    arg1 = getValStack()

    if (not(getType(arg1) == "int" and getType(arg2) == "int") and not(getType(arg1) == "float" and getType(arg2) == "float")):
        print("{}: ADDD variable types missmatch".format(
            currentInstIndex), file=sys.stderr)
        exit(53)

    setValStack(getVal(arg1) + getVal(arg2), getType(arg1))


def subs(args):
    arg2 = getValStack()
    arg1 = getValStack()

    if (not(getType(arg1) == "int" and getType(arg2) == "int") and not(getType(arg1) == "float" and getType(arg2) == "float")):
        print("{}: SUBS variable types missmatch".format(
            currentInstIndex), file=sys.stderr)
        exit(53)

    setValStack(getVal(arg1) - getVal(arg2), getType(arg1))


def muls(args):
    arg2 = getValStack()
    arg1 = getValStack()

    if (not(getType(arg1) == "int" and getType(arg2) == "int") and not(getType(arg1) == "float" and getType(arg2) == "float")):
        print("{}: MULS variable types missmatch".format(
            currentInstIndex), file=sys.stderr)
        exit(53)

    setValStack(getVal(arg1) * getVal(arg2), getType(arg1))


def idivs(args):
    arg2 = getValStack()
    arg1 = getValStack()

    if getVal(arg2) == 0:
        exit(57)

    if (not(getType(arg1) == "int" and getType(arg2) == "int") and not(getType(arg1) == "float" and getType(arg2) == "float")):
        print("{}: IDIVS variable types missmatch".format(
            currentInstIndex), file=sys.stderr)
        exit(53)

    setValStack(getVal(arg1) // getVal(arg2), getType(arg1))


def divs(args):
    arg2 = getValStack()
    arg1 = getValStack()

    if getVal(arg2) == 0:
        exit(57)

    if (getType(arg1) != "float" or getType(arg2) != "float"):
        print("{}: DIVS variable types missmatch".format(
            currentInstIndex), file=sys.stderr)
        exit(53)

    setValStack(getVal(arg1) / getVal(arg2), "float")


def lts(args):
    arg2 = getValStack()
    arg1 = getValStack()

    if(getType(arg1) == "nil" or getType(arg2) == "nil" or getType(arg1) != getType(arg2)):
        print("{}: LTS not same types of variables".format(
            currentInstIndex), file=sys.stderr)
        exit(53)

    if getVal(arg1) < getVal(arg2):
        setValStack(True, "bool")
    else:
        setValStack(False, "bool")


def gts(args):
    arg2 = getValStack()
    arg1 = getValStack()

    if(getType(arg1) == "nil" or getType(arg2) == "nil" or getType(arg1) != getType(arg2)):
        print("{}: GTS not same types of variables".format(
            currentInstIndex), file=sys.stderr)
        exit(53)

    if getVal(arg1) > getVal(arg2):
        setValStack(True, "bool")
    else:
        setValStack(False, "bool")


def eqs(args):
    arg2 = getValStack()
    arg1 = getValStack()

    if((getType(arg1) == "nil") ^ (getType(arg2) == "nil")):
        setValStack(False, "bool")
        return

    if(getType(arg1) != getType(arg2)):
        print("{}: EQS not same types of variables".format(
            currentInstIndex), file=sys.stderr)
        exit(53)

    if getVal(arg1) == getVal(arg2):
        setValStack(True, "bool")
    else:
        setValStack(False, "bool")


def logAnds(args):
    arg2 = getValStack()
    arg1 = getValStack()
    if (getType(arg1) != "bool" or getType(arg2) != "bool"):
        print("{}: ANDS not bool variables".format(
            currentInstIndex), file=sys.stderr)
        exit(53)

    setValStack(getVal(arg1) and getVal(arg2), "bool")


def logOrs(args):
    arg2 = getValStack()
    arg1 = getValStack()

    if (getType(arg1) != "bool" or getType(arg2) != "bool"):
        print("{}: ORS not bool variables".format(
            currentInstIndex), file=sys.stderr)
        exit(53)

    setValStack(getVal(arg1) or getVal(arg2), "bool")


def logNots(args):
    arg1 = getValStack()

    if (getType(arg1) != "bool"):
        print("{}: NOTS not bool variable".format(
            currentInstIndex), file=sys.stderr)
        exit(53)

    setValStack(not getVal(arg1), "bool")


def int2chars(args):
    arg1 = getValStack()

    if getType(arg1) != "int":
        print("{}: INT2CHARS variable type missmatch".format(
            currentInstIndex), file=sys.stderr)
        exit(53)
    try:
        setValStack(chr(getVal(arg1)), "string")
    except:
        print("{}: INT2CHARS chr function failed".format(
            currentInstIndex), file=sys.stderr)
        exit(58)


def str2ints(args):
    arg2 = getValStack()
    arg1 = getValStack()

    if getType(arg1) != "string" or getType(arg2) != "int":
        print("{}: STR2INTS variable types missmatch".format(
            currentInstIndex), file=sys.stderr)
        exit(53)
    string = getVal(arg1)
    index = getVal(arg2)
    if index < 0:
        exit(58)
        print("{}: STR2INTS index is < 0".format(
            currentInstIndex), file=sys.stderr)
    try:
        setValStack(ord(string[index]), "int")
    except:
        print("{}: STR2INTS ord function failed , or index is out of boundries".format(
            currentInstIndex), file=sys.stderr)
        exit(58)


def jumpifeqs(args):
    arg2 = getValStack()
    arg1 = getValStack()

    global currentInstIndex
    if((getType(arg1) == "nil") ^ (getType(arg2) == "nil")):
        return

    if(getType(arg1) != getType(arg2)):
        print("{}: JUMPIFEQS not same types of variables".format(
            currentInstIndex), file=sys.stderr)
        exit(53)

    if(getVal(arg1) == getVal(arg2)):
        currentInstIndex = labels[getLabel(args[0])]


def jumpifneqs(args):
    arg2 = getValStack()
    arg1 = getValStack()

    global currentInstIndex
    if((getType(arg1) == "nil") ^ (getType(arg2) == "nil")):
        currentInstIndex = labels[getLabel(args[0])]
        return
    if(getType(arg1) != getType(arg2)):
        print("{}: JUMPIFNEQS not same types of variables 1:{} 2:{}".format(
            currentInstIndex, getVal(args[1]), getType(args[2])), file=sys.stderr)
        exit(53)

    if(getVal(arg1) != getVal(arg2)):
        currentInstIndex = labels[getLabel(args[0])]


instructions = {
    # BASIC OPERATIONS
    "MOVE": {"args": ["var", "symb"], "func": move},
    "CREATEFRAME": {"args": [], "func": createframe},
    "PUSHFRAME": {"args": [], "func": pushframe},
    "POPFRAME": {"args": [], "func": popframe},
    "DEFVAR": {"args": ["var"], "func": defvar},
    "CALL": {"args": ["label"], "func": call},
    "RETURN": {"args": [], "func": ret},
    "PUSHS": {"args": ["symb"], "func": pushs},
    "POPS": {"args": ["var"], "func": pops},
    "ADD": {"args": ["var", "symb", "symb"], "func": add},
    "SUB": {"args": ["var", "symb", "symb"], "func": sub},
    "MUL": {"args": ["var", "symb", "symb"], "func": mul},
    "IDIV": {"args": ["var", "symb", "symb"], "func": idiv},
    "LT": {"args": ["var", "symb", "symb"], "func": lt},
    "GT": {"args": ["var", "symb", "symb"], "func": gt},
    "EQ": {"args": ["var", "symb", "symb"], "func": eq},
    "AND": {"args": ["var", "symb", "symb"], "func": logAnd},
    "OR": {"args": ["var", "symb", "symb"], "func": logOr},
    "NOT": {"args": ["var", "symb"], "func": logNot},
    "INT2CHAR": {"args": ["var", "symb"], "func": int2char},
    "STRI2INT": {"args": ["var", "symb", "symb"], "func": str2int},
    "READ":  {"args": ["var", "type"], "func": read},
    "WRITE": {"args": ["symb"], "func": write},
    "CONCAT": {"args": ["var", "symb", "symb"], "func": concat},
    "STRLEN": {"args": ["var", "symb"], "func": strlen},
    "GETCHAR": {"args": ["var", "symb", "symb"], "func": getchar},
    "SETCHAR": {"args": ["var", "symb", "symb"], "func": setchar},
    "TYPE": {"args": ["var", "symb"], "func": typeFunc},
    "LABEL": {"args": ["label"], "func": nothing},
    "JUMP": {"args": ["label"], "func": jump},
    "JUMPIFEQ": {"args": ["label", "symb", "symb"], "func": jumpifeq},
    "JUMPIFNEQ": {"args": ["label", "symb", "symb"], "func": jumpifneq},
    "EXIT": {"args": ["symb"], "func": exitInterpret},
    "DPRINT": {"args": ["symb"], "func": dprint},
    "BREAK":  {"args": [], "func": breakInterpret},

    # STACK OPERATIONS
    "CLEARS": {"args": [], "func": clears},
    "ADDS": {"args": [], "func": adds},
    "SUBS": {"args": [], "func": subs},
    "MULS": {"args": [], "func": muls},
    "DIVS": {"args": [], "func": divs},
    "IDIVS": {"args": [], "func": idivs},
    "LTS": {"args": [], "func": lts},
    "GTS": {"args": [], "func": gts},
    "EQS": {"args": [], "func": eqs},
    "ANDS": {"args": [], "func": logAnds},
    "ORS": {"args": [], "func": logOrs},
    "NOTS": {"args": [], "func": logNots},
    "INT2CHARS": {"args": [], "func": int2chars},
    "STRI2INTS ": {"args": [], "func": str2ints},
    "JUMPIFEQS": {"args": ["label"], "func": jumpifeqs},
    "JUMPIFNEQS": {"args": ["label"], "func": jumpifneqs},

    # FLOAT OPERATIONS
    "INT2FLOAT": {"args": ["var", "symb"], "func": int2float},
    "FLOAT2INT": {"args": ["var", "symb"], "func": float2int},
    "DIV": {"args": ["var", "symb", "symb"], "func": div},
}

# MAIN PROGRAM


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
            if not argumentTypeCheck(arg.text, arg.attrib["type"]):
                exit(32)

            argValue = decodeArgumentValue(arg.attrib["type"], arg.text)
            args.append({"type": arg.attrib["type"], "value": argValue})
            argumentCount += 1

        # INSTRUCTIONS WRITING TO STRUCTURTE AND CHCEKS
        global instructions

        # Instruction opcode check if exists
        if not instructionOpcode in instructions:
            exit(32)

        # Check if count of arguments mazch to instuction arguments count
        if len(instructions[instructionOpcode]["args"]) != len(args):
            exit(32)

        # Arguments check
        for i in range(0, len(args)):
            if instructions[instructionOpcode]["args"][i] == "symb":
                if args[i]["type"] in ["int", "string", "bool", "nil", "var", "float"]:
                    continue
            elif instructions[instructionOpcode]["args"][i] == args[i]["type"]:
                continue
            # If evrything okay continue. If not ... exit
            exit(32)

        # Add new record to parseTree
        parseTree[instLine] = {
            "instruction": instructionOpcode, "args": args, "order": order, "counter": 0}
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
        if not re.match('^[+-]?[\d]+$', value):
            return False
    elif(expectedType == "bool"):
        if not re.match('^true$|^false$', value):
            return False
    elif(expectedType == "nil"):
        if not re.match('^nil$', value):
            return False
    elif(expectedType == "var"):
        if not re.match('^(GF|TF|LF)@[a-z_\-$&%*!?A-Z][a-z_\-$&%*!?0-9A-Z]*', value):
            return False
    elif(expectedType == "type"):
        if not re.match('int$|^bool$|^string$|^nil$|^float$', value):
            return False
    elif(expectedType == "label"):
        if not re.match('(?i)^[a-z_\-$&%*!?][a-z_\-$&%*!?0-9]*', value):
            return False
    elif(expectedType == "float"):
        if not re.match('(?i)^0x([a-f]|[\d])(\.[\d|a-f]*)?p(\+|-)?[\d]*$', value):
            return False

    return True


def escapeSeqToAscii(match):
    seq = match.group(0).replace("\\", "")
    return str(chr(int(seq)))


def decodeArgumentValue(argType, value):
    decodedValue = value

    if(argType == "string"):
        # replace all \ sequences to ascii
        decodedValue = re.sub('\\\\[0-9]{3}', escapeSeqToAscii, value)
    elif(argType == "int"):
        decodedValue = int(value)
    elif(argType == "bool"):
        if value == "true":
            decodedValue = True
        else:
            decodedValue = False
    elif(argType == "float"):
        try:
            decodedValue = float.fromhex(value)
        except:
            print("{}: bad notation of float".format(
                currentInstIndex), file=sys.stderr)
            exit(32)

    return decodedValue


def getMostUsedOperation(tree):
    mostUsed = 0
    bestMatch = 0
    for x in tree:
        if tree[x]["counter"] > mostUsed:
            mostUsed = tree[x]["counter"]
            bestMatch = tree[x]["order"]

    return bestMatch


def interpreteCode(tree, lastIndex):
    global currentInstIndex, instCount
    while currentInstIndex <= lastIndex and not exitBool:
        instructions[tree[currentInstIndex]["instruction"]
                     ]["func"](tree[currentInstIndex]["args"])
        # STATS COUNTER
        if not re.match('^LABEL$|^DPRINT$|^BREAK$', tree[currentInstIndex]["instruction"]):
            tree[currentInstIndex]["counter"] += 1
            instCount += 1

        currentInstIndex += 1
    # Check GF frame for stats inicialized variables
    maxInicializedInFrame(frames["GF"])
    if "TF" in frames:
        maxInicializedInFrame(frames["TF"])
    if "LF" in frames:
        maxInicializedInFrame(frames["LF"])


sourceFile = sys.stdin
inputFile = sys.stdin

parser = argparse.ArgumentParser(add_help=False, prefix_chars="--")
parser.add_argument('--help', action='store_true')
parser.add_argument('--source', dest='source')
parser.add_argument('--input', dest='input')
parser.add_argument('--stats', dest='stats')
parser.add_argument('--insts', action='store_true')
parser.add_argument('--hot', action='store_true')
parser.add_argument('--vars', action='store_true')

try:
    args = parser.parse_args()
except:
    exit(10)


def processArguments():
    global sourceFile, inputFile, statistic
    if args.help:
        if len(sys.argv) == 2:
            help()
        else:
            exit(10)

    if (args.input == None and args.source == None):
        exit(10)

    if(args.input):
        try:
            inputFile = open(args.input)
        except:
            exit(10)

    if(args.source):
        try:
            sourceFile = open(args.source)
        except:
            exit(10)

    if args.insts or args.hot or args.vars:
        if not args.stats:
            exit(10)
    if args.stats:
        statistic = {"file": args.stats}
    if args.insts:
        statistic[sys.argv.index("--insts")] = "insts"
    if args.hot:
        statistic[sys.argv.index("--hot")] = "hot"
    if args.vars:
        statistic[sys.argv.index("--vars")] = "vars"


def writeStatsToFile(statistic, tree):
    try:
        statsFile = open(statistic["file"], "w")
        statistic.pop('file', None)
    except:
        exit(10)

    first = True
    statistic = sorted(statistic.items())
    for x in statistic:
        if first:
            first = False
        else:
            statsFile.write("\n")
        if "vars" in x[1]:
            statsFile.write(str(max(inicializedMaxCount, dataStackMaxCount)))
        elif "insts" in x[1]:
            statsFile.write(str(instCount))
        elif "hot" in x[1]:
            statsFile.write(str(getMostUsedOperation(tree)))


def help():
    print("HELP", file=sys.stderr)


def main():
    global exitValue, statistic
    processArguments()
    tree = checkXMLandSave()
    lastInstruction = int(list(tree)[-1])
    interpreteCode(tree, lastInstruction)
    if statistic != False:
        writeStatsToFile(statistic, tree)

    exit(exitValue)


if __name__ == '__main__':
    main()
