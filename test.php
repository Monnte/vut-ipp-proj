<?php
# ----------------------------
# Author: Peter Zdravecký
# Date: 16.2.2021
# Description: Tester for IPPcode21
# Name: test.php
# Version: 1.0
# PHP 7.4
# ----------------------------
ini_set("display_errors", "stderr");


/* Vars */
$dirs = [];
$directory = ".";
$recursive = false;
$parseScript = "parse.php";
$interpretScript = "interpret.py";
$parseOnly = false;
$interpretOnly = false;
$jexamxml = "/pub/courses/ipp/jexamxml/jexamxml.jar";
$jexamcfg = "/pub/courses/ipp/jexamxml/options";
$testlist = ".";
$match = "/^.*$/";
$opts = ["help", "directory:", "recursive", "parse-script:", "int-script:", "parse-only", "int-only", "jexamxml:", "jexamcfg:", "testlist:", "match:"];
$options = getopt("", $opts);
$diffScript = "diff";

/* Arguments check */

if (array_key_exists("help", $options)) {
    if ($argc === 2)
        printHelp($argv[0]);
    else
        exit(10);
}

if (array_key_exists("directory", $options)) {
    if (!is_readable($options["directory"]))
        exit(41);
    $directory = $options["directory"];
}
array_push($dirs, $directory);

if (array_key_exists("recursive", $options)) {
    $recursive = true;
    $dirs = array_merge(scanDirRecursive($directory), $dirs);
}

if (array_key_exists("parse-script", $options)) {
    if (!is_readable($options["parse-script"]))
        exit(41);
    $parseScript = $options["parse-script"];
}
if (array_key_exists("int-script", $options)) {
    if (!is_readable($options["int-script"]))
        exit(41);
    $interpretScript = $options["int-script"];
}

if (array_key_exists("int-only", $options)) {
    $interpretOnly = true;
}

if (array_key_exists("jexamxml", $options)) {
    if (!is_readable($options["jexamxml"]))
        exit(41);
    $jexamxml = $options["jexamxml"];
}

if (array_key_exists("jexamcfg", $options)) {
    if (!is_readable($options["jexamcfg"]))
        exit(41);
    $jexamcfg = $options["jexamcfg"];
}

if (array_key_exists("testlist", $options)) {
    $testlist = $options["testlist"];
    if (array_key_exists("directory", $options))
        exit(10);

    $dirs = [];
    $myfile = fopen($testlist, "r") or exit(11);
    while (($line = fgets($myfile)) != false) {
        $line = trim($line);
        if (is_dir($line)) {
            array_push($dirs, $line);
            if ($recursive)
                $dirs = array_merge(scanDirRecursive($line), $dirs);
        }
    }
    fclose($myfile);
}

if (array_key_exists("match", $options)) {
    $match = $options["match"];
}

if (array_key_exists("parse-only", $options)) {
    $parseOnly = true;
    $diffScript = "java -jar " . $jexamxml;
}

if ($parseOnly && (array_key_exists("int-script", $options) || $interpretOnly)) {
    exit(10);
}
if ($interpretOnly && (array_key_exists("parse-script", $options) || $parseOnly)) {
    exit(10);
}

# ----------------------------------------------------

/* 
    Scanning for tests and executing them 
*/
$allTests = 0;
$passed = 0;
$failed = 0;
$tests = [];

$tmpFile = tempnam($directory, "ipp_");

foreach ($dirs as $dir) {
    $tests[$dir]["passed"] = [];
    $tests[$dir]["failed"] = [];
    $testInDir = glob($dir . "/*.src");
    foreach ($testInDir as $testSrc) {
        $testName = basename($testSrc, ".src");

        if (preg_match($match, $testName) === false) {
            unlink($tmpFile);
            exit(11);
        }
        if (!preg_match($match, $testName))
            continue;


        $testIn = $dir . "/" . $testName . ".in";
        $testOut = $dir . "/" . $testName . ".out";
        $testRc = $dir . "/" . $testName . ".rc";
        if (!file_exists($testIn))
            WriteToFile($testIn, "");
        if (!file_exists($testOut))
            WriteToFile($testOut, "");
        if (!file_exists($testRc))
            WriteToFile($testRc, "0");

        if (doTest($testSrc, $testIn, $testOut, $testRc)) {
            array_push($tests[$dir]["passed"], $testName);
            $passed++;
        } else {
            array_push($tests[$dir]["failed"], $testName);
            $failed++;
        }
        $allTests++;
    }
}

unlink($tmpFile);

# ----------------------------------------------------

/* 
    Creating html website.
*/
$dirTests = "";
foreach ($tests as $key => $value) {
    $passedTests = "";
    $failedTests = "";
    sort($value["passed"]);
    sort($value["failed"]);
    foreach ($value["passed"] as $pTests)
        $passedTests .= "<div class='grid-item greenItem'>$pTests</div>";
    foreach ($value["failed"] as $pFailed)
        $failedTests .= "<div class='grid-item redItem'>$pFailed</div>";

    $allFailed = count($value["failed"]);
    $allPassed = count($value["passed"]);
    $allCount = $allFailed + $allPassed;
    if ($allCount != 0)
        $dirTests .= "
            <div style='margin:1em 0 0 0.5em;'>    
                <h2 onclick='toggleShow(\"$key\")' style='margin:0.1em 0;display:inline-block;' class='directoryInfo'>$key</h2>
                <div id='$key' style='display:none;'>
                    <p  style='margin:0.1em 0'> <b>PASSED: <span style='color:green'> $allPassed / $allCount </span></b><br><div class='grid-container greenContainer'>$passedTests</div></p>
                    <p  style='margin:0.1em 0'> <b>FAILED: <span style='color:red'> $allFailed / $allCount </span></b><br><div class='grid-container redContainer'>$failedTests</div></p>
                </div>
            </div>
            ";
}

$doc = "
<style>
   body {margin:1em;}
   h2   {text-decoration:underline;}
   .directoryInfo:hover {color:blue;cursor:pointer;}
   .grid-container {
   display: grid;
   grid-template-columns: auto auto auto;
   padding: 10px;
   }
   .grid-item {
   border: 1px solid #000;
   padding: 0.1em;
   text-align: center;
   }
   .greenContainer{background-color: #90ee90;}
   .greenItem{background-color: #64e764;}
   .redContainer{background-color: #ff9a9a;}
   .redItem{background-color: #ff6868;}
</style>
<html>
   <head>
      <meta charset='UTF-8'>
      <meta author='Peter Zdravecký'>
      <title>IPPcode21 Tester</title>
   </head>
   <body>
      <h1 style='border-bottom:2px solid black'>IPP tests</h1>
      <div style='margin-top:1em;font-weight:bold;'>
         <h2 style=''>Summary all tests</h2>
         <p>PASSED: <span style='color:green'> $passed / $allTests </span> </p>
         <p>FAILED: <span style='color:red'> $failed / $allTests </span> </p>
      </div>
      <div stlye='margin:1em 0'>
         <h2 style=''>Tests by directories</h2>
         $dirTests
      </div>
   </body>
</html>
<script>
   function toggleShow(key) {
       var div = document.getElementById(key);
       if (div.style.display === 'none') {
         div.style.display = 'block';
       } else {
         div.style.display = 'none';
       }
   } 
</script>\n
";

/* Program Output */
echo $doc;

# ----------------------------------------------------

/* 
    Recursive scan in directory.
    Return array of all subdirectories.
*/
function scanDirRecursive($directory)
{
    $dirs = [];
    foreach (glob($directory . "/*", GLOB_ONLYDIR) as $dir) {
        $dirs = array_merge(scanDirRecursive($dir), $dirs);
        array_push($dirs, $dir);
    }
    return $dirs;
}

function WriteToFile($file, $write)
{
    $myfile = fopen($file, "w") or exit(12);
    fwrite($myfile, $write);
    fclose($myfile);
}

function CheckRetValue($testRc, $retCode)
{
    $myfile = fopen($testRc, "r") or exit(11);
    $rc = fgets($myfile);
    if ($rc == $retCode)
        return true;
    else
        return false;
}


/* 
    Execute one test and checks output.
*/
function doTest($testSrc, $testIn, $testOut, $testRc)
{
    global $parseScript, $interpretScript, $diffScript, $parseOnly, $interpretOnly, $tmpFile, $jexamcfg;
    if ($parseOnly) {
        exec("timeout 10s php7.4 $parseScript < $testSrc 2>/dev/null", $output, $retCode);
    } else if ($interpretOnly) {
        exec("timeout 10s python3.8 $interpretScript --source=$testSrc --input=$testIn 2>/dev/null", $output, $retCode);
    } else {
        exec("php7.4 $parseScript < $testSrc", $output, $retCode);
        if ($retCode != 0) {
            if (CheckRetValue($testRc, $retCode))
                return true;
            else
                return false;
        }
        WriteToFile($tmpFile, implode("\n", $output));
        $output = [];
        exec("timeout 10s python3.8 $interpretScript --source=$tmpFile --input=$testIn 2>/dev/null", $output, $retCode);
    }

    if (CheckRetValue($testRc, $retCode)) {
        if ($retCode == 0) {
            WriteToFile($tmpFile, implode("\n", $output));
            if ($parseOnly) {
                exec("$diffScript $testOut $tmpFile /dev/null $jexamcfg 2>/dev/null", $none, $retCode);
            } else {
                exec("$diffScript $testOut $tmpFile 2>/dev/null", $none, $retCode);
            }
            if ($retCode == 0)
                return true;
        } else {
            return true;
        }
    }
    return false;
}

function printHelp($name)
{
    fprintf(STDERR, "Tester for interpret.py and parse.php, Version 1.0, Author: Peter Zdravecký\n");
    fprintf(STDERR, "==========================================================\n");
    fprintf(STDERR, "Usage: $name \n [ --help | --directory=dir | --recursive | --parse-script=script | --int-script=script | --parse-only | --int-only | --jexamxml=file | --jexamcfg=file | testliist=file | match=regex ]");

    fprintf(STDERR, "    --directory    | Search directory for tests\n");
    fprintf(STDERR, "    --recursive    | Search in directory recursivly in subdirectories\n");
    fprintf(STDERR, "    --parse-script | Path to parse script\n");
    fprintf(STDERR, "    --int-script   | Path to interpret script\n");
    fprintf(STDERR, "    --parse-only   | Test only parse script\n");
    fprintf(STDERR, "    --int-onl      | Test only interpret script\n");
    fprintf(STDERR, "    --jexamxml     | Path to xml copmarator\n");
    fprintf(STDERR, "    --jexamcfg     | Path to xml copmarator config\n");
    fprintf(STDERR, "    --testliist    | File that contain directories to search for tests\n");
    fprintf(STDERR, "    --match        | Do tests only match regex\n");


    fprintf(STDERR, "\nExample usage: \n");
    fprintf(STDERR, "       ./parse.php --help \n");
    fprintf(STDERR, "       ./parse.php --directory=tests --parse-only --parse-script=./parse.php \n");
    fprintf(STDERR, "       ./parse.php --recursive --int-only \n");
    fprintf(STDERR, "==========================================================\n");
    exit(0);
}
