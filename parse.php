<?php
# ----------------------------
# Author: Peter Zdravecký
# Date: 13.2.2021
# Description: Parser for IPPcode21
# Name: parse.php
# Version: 1.0
# PHP 7.4
# ----------------------------
ini_set('display_errors', 'stderr');

# INSTRUCTION SET
$instructionList = array(
    "MOVE" => array("var", "symb"),
    "CREATEFRAME" => array(),
    "PUSHFRAME" => array(),
    "POPFRAME" => array(),
    "DEFVAR" => array("var"),
    "CALL" => array("label"),
    "RETURN" => array(),
    "PUSHS"  => array("symb"),
    "POPS"  => array("var"),
    "ADD"  => array("var", "symb", "symb"),
    "SUB"  => array("var", "symb", "symb"),
    "MUL"  => array("var", "symb", "symb"),
    "IDIV"  => array("var", "symb", "symb"),
    "LT"  => array("var", "symb", "symb"),
    "GT"  => array("var", "symb", "symb"),
    "EQ"  => array("var", "symb", "symb"),
    "AND"  => array("var", "symb", "symb"),
    "OR"  => array("var", "symb", "symb"),
    "NOT"  => array("var", "symb"),
    "INT2CHAR"  => array("var", "symb"),
    "STRI2INT"  => array("var", "symb", "symb"),
    "READ"  => array("var", "type"),
    "WRITE" => array("symb"),
    "CONCAT"  => array("var", "symb", "symb"),
    "STRLEN"  => array("var", "symb"),
    "GETCHAR"  => array("var", "symb", "symb"),
    "SETCHAR"  => array("var", "symb", "symb"),
    "TYPE"  => array("var", "symb"),
    "LABEL" => array("label"),
    "JUMP" => array("label"),
    "JUMPIFEQ" => array("label", "symb", "symb"),
    "JUMPIFNEQ" => array("label", "symb", "symb"),
    "EXIT" => array("symb"),
    "DPRINT" => array("symb"),
    "BREAK" => array(),
    "CLEARS" => array(),
    "ADDS" => array(),
    "SUBS" => array(),
    "MULS" => array(),
    "IDIVS" => array(),
    "LTS" => array(),
    "GTS" => array(),
    "EQS" => array(),
    "ANDS" => array(),
    "ORS" => array(),
    "NOTS" => array(),
    "INT2CHARS" => array(),
    "STRI2INTS " => array(),
    "JUMPIFEQS" => array("label"),
    "JUMPIFNEQS" => array("label"),
    "DIV" => array("var", "symb", "symb"),
    "INT2FLOAT" => array("var", "symb"),
    "FLOAT2INT" => array("var", "symb"),

);

# VARIABLES
$commentCount = 0;
$locCount = 0;
$labelCount = 0;
$jumpCount = 0;
$fwJumpsCount = 0;
$backJumpsCount = 0;
$badJumpsCount = 0;
$labels = array();
$jumpInstructions = array();
$options = getopt("", ["help", "stats:", "loc", "comments", "labels", "jumps", "fwjumps", "backjumps", "badjumps"]);
$longOptions = ["help", "stats", "loc", "comments", "labels", "jumps", "fwjumps", "backjumps", "badjumps"];

# ARGUMENT CHECKS
if (array_key_exists("help", $options)) {
    if ($argc === 2)
        printHelp($argv[0]);
    else
        exit(10);
}

if (array_key_exists("stats", $options) && is_array(($options["stats"]))) {
    if (count($options["stats"]) !== count(array_unique($options["stats"])))
        exit(12);
}

for ($i = 1; $i < $argc; $i++) {
    if (!preg_match('/^--/', $argv[$i])) {
        exit(10);
    }
    $argv[$i] = str_replace("-", "", $argv[$i]);
    $argv[$i] = preg_replace('/=.*$/', '', $argv[$i]);
    if (!in_array($argv[$i], $longOptions)) {
        exit(10);
    }
}

# HEADER CHECK
do {
    $line = fgets(STDIN);
    if (preg_match('/#/', $line))
        $commentCount++;
} while (!feof(STDIN) && preg_match("/^\s*$|^\s*#.*$/", $line));

$line = preg_replace('/#.*$/', '', $line);
if (strtolower(trim($line)) !== ".ippcode21") {
    print($line);
    fprintf(STDERR, "Header .IPPcode21 nout found\n");
    exit(21);
}


# XML GENERATION | SYN and LEN checks
$xmlOut = new DOMDocument('1.0', "UTF-8");
$xmlOut->formatOutput = true;

$root = $xmlOut->createElement('program');
$root = $xmlOut->appendChild($root);
$root->setAttribute("language", "IPPcode21");

$order = 1;
while ($line = fgets(STDIN)) {
    $line = trim($line);
    if (preg_match('/#/', $line))
        $commentCount++;
    $line = preg_replace('/#.*$/', '', $line); //remove comments

    if (!empty($line)) {
        $parts = array();
        preg_match_all('/\S+/', $line, $parts);
        $parts = $parts[0];
        $instruction = strtoupper($parts[0]);
        unset($parts[0]);

        $parts = array_values(array_filter($parts));
        processLine($instruction, $parts);
        $locCount++;
    }
}

# STATS BONUS 
$labelCount = count(array_unique($labels));
foreach ($jumpInstructions as $key => $jump) {
    if (!array_key_exists($jump[1], $labels)) {
        $badJumpsCount++;
        continue;
    }
    if ($key < $labels[$jump[1]])
        $fwJumpsCount++;
    else
        $backJumpsCount++;
}

$file = null;
$hasFile = false;
$fileCount = 0;
$stats = array();
for ($i = 1; $i < $argc; $i++) {
    if ($hasFile) {
        # check for next file
        if ($argv[$i] === "stats") {
            printStatsToFile($file, $stats); # write to current file
            $stats = array();
            $file = $options["stats"][$fileCount]; # assign new file
            $fileCount++;
        } else {
            switch ($argv[$i]) {
                case "loc":
                    $stats["loc"] = $locCount;
                    break;
                case "comments":
                    $stats["comments"] = $commentCount;
                    break;
                case "labels":
                    $stats["labels"] = $labelCount;
                    break;
                case "jumps":
                    $stats["jumps"] = $jumpCount;
                    break;
                case "fwjumps":
                    $stats["fwjumps"] = $fwJumpsCount;
                    break;
                case "backjumps":
                    $stats["backjumps"] = $backJumpsCount;
                    break;
                case "badjumps":
                    $stats["badjumps"] = $badJumpsCount;
                    break;
            }
        }
    } else {
        # Check for first file. If another option before file exists exit with error
        if ($argv[$i] === "stats") {
            $hasFile = true;
            if (is_array(($options["stats"])))
                $file = $options["stats"][$fileCount];
            else
                $file = $options["stats"];
            $fileCount++;
        } else {
            exit(10);
        }
    }
}

# Write stats to last assigned file
if ($hasFile)
    printStatsToFile($file, $stats);

# MAIN OUTPUT
echo $xmlOut->saveXML();
# -----------------------------------------------------------------------------------


# FUNCTIONS

# PRINT BONUS STATS TO FILE
function printStatsToFile($file, $stats)
{
    if (count($stats) === 0)
        return;

    $first = true;
    $myfile = fopen($file, "w") or exit(12);
    foreach ($stats as $s) {
        if (!$first)
            fwrite($myfile, "\n");

        fwrite($myfile, $s);
        $first = false;
    }
    fclose($myfile);
}

# PROCESS INSTRUCTION NAME AND ARGUMENTS
function processLine($instruction, $arguments)
{
    global $root, $order, $labels, $jumpCount, $labels, $jumpInstructions, $xmlOut, $instructionList;

    if (!array_key_exists($instruction, $instructionList)) {
        fprintf(STDERR, "$order: LEX ERROR in name of instruction\n");
        exit(22);
    }

    if (count($instructionList[$instruction]) != (count($arguments))) {
        fprintf(STDERR, "$order: $instruction , missmatch in number of arguments\n");
        exit(23);
    }

    if ($instruction === "LABEL")
        if (count($arguments) > 0)
            $labels[$arguments[0]] = $order;

    if (preg_match('/^CALL$|^JUMP$|^JUMPIFEQ$|^JUMPIFNEQ$/', $instruction)) {
        $jumpCount++;
        if (count($arguments) > 0) {
            $jumpInstructions[$order] = [$instruction, $arguments[0]];
        }
    }

    $inst = $xmlOut->createElement('instruction');
    $inst->setAttribute("order", $order++);
    $inst->setAttribute("opcode", $instruction);
    for ($j = 0; $j < count($arguments); $j++) {
        [$type, $value] = parseArgument($arguments[$j], $instructionList[$instruction][$j]);
        $arg = $xmlOut->createElement('arg' . ($j + 1), $value);
        $arg->setAttribute("type", $type);
        $inst->appendChild($arg);
    }
    $root->appendChild($inst);
}

# SYNTAX CHECK AND PARSING ARGUMENTS
function parseArgument($arg, $expectedType)
{
    $type = "";
    $value = $arg;

    switch ($expectedType) {
        case "symb":
            if (preg_match('/^int@[+-]?[\d]+$/', $arg)) {
                $type = "int";
                $value = substr($arg, 4, strlen($arg));
                break;
            }
            if (preg_match('/^string@/', $arg)) {
                $type = "string";
                $value = substr($arg, 7, strlen($arg));
                if (preg_match_all('/\\\\[0-9]{3}/', $value) !== preg_match_all('/\\\\/', $value))
                    exit(23);
                break;
            }
            if (preg_match('/^bool@(true|false)$/', $arg)) {
                $type = "bool";
                $value = substr($arg, 5, strlen($arg));
                break;
            }
            if (preg_match('/^float@0x([a-f]|[\d])(\.[\d|a-f]*)?p(\+|-)?[\d]*$/i', $arg)) {
                $type = "float";
                $value = substr($arg, 6, strlen($arg));
                break;
            }
            if (preg_match('/^nil@nil$/', $arg)) {
                $type = "nil";
                $value = "nil";
                break;
            }

        case "var":
            if (preg_match('/^(GF|TF|LF)@[a-z_\-$&%*!?A-Z][a-z_\-$&%*!?0-9A-Z]*$/', $arg)) {
                $type = "var";
                break;
            }
            fprintf(STDERR, "Expected type VAR or SYMBOL, got input: $arg\n");
            exit(23);

        case "type":
            if (preg_match('/^int$|^bool$|^string$|^nil$|^float$/', $arg)) {
                $type = "type";
                break;
            }
            fprintf(STDERR, "Expected type TYPE, got input: $arg\n");
            exit(23);

        case "label":
            if (preg_match('/^[a-z_\-$&%*!?A-Z][a-z_\-$&%*!?0-9A-Z]*$/', $arg)) {
                $type = "label";
                break;
            }
            fprintf(STDERR, "Expected type LABEL, got input: $arg\n");
            exit(23);
    }

    $value =  preg_replace(["/&/", "/>/", "/</", '/\'/', "/\"/"], ["&amp;", "&gt;", "&lt;", "&apos;", "&quot;"], $value);
    return [$type, $value];
}

# PRINT HELP
function printHelp($scriptName)
{
    fprintf(STDERR, "Parser for IPPcode21, Version 1.0, Author: Peter Zdravecký\n");
    fprintf(STDERR, "==========================================================\n");
    fprintf(STDERR, "Usage: $scriptName \n");
    fprintf(STDERR, "- Accepts input from STDIN \n");

    fprintf(STDERR, "\nOptional parameters:\n");
    fprintf(STDERR, "[ help | stats ]\n");
    fprintf(STDERR, "   --help        | Prints help. No other arguments accepted with these option\n");
    fprintf(STDERR, "   --stats=file  | Sets the file that the statistics will be written to.\n");

    fprintf(STDERR, "\nTo use these parameters, --stats has to be already set!\n");
    fprintf(STDERR, "[ loc | comments | labels | jumps | fwjumps | backjumps | badjumps ]\n");
    fprintf(STDERR, "    --loc        | Count lines where occurs instructions in the code\n");
    fprintf(STDERR, "    --comments   | Count number of comments\n");
    fprintf(STDERR, "    --labels     | Count uniqe labels\n");
    fprintf(STDERR, "    --jumps      | Count instructions which provides jump in the program\n");
    fprintf(STDERR, "    --fwjumps    | Count forward jumps\n");
    fprintf(STDERR, "    --backjumps  | Count backwards jumps\n");
    fprintf(STDERR, "    --badjumps   | Count jumps which refers to a non-existent labels\n");
    fprintf(STDERR, "Statistics are logged in the order that they were written in arguments.\n");

    fprintf(STDERR, "\nExample usage: \n");
    fprintf(STDERR, "       ./parse.php --help \n");
    fprintf(STDERR, "       ./parse.php --stats=file1 --loc\n");
    fprintf(STDERR, "       ./parse.php --stats=file1 --comment --loc --badjumps \n");
    fprintf(STDERR, "       ./parse.php --stats=file1 --loc --stats=file2 --comments \n");
    fprintf(STDERR, "==========================================================\n");
    exit(0);
}
