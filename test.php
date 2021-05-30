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

$dirreport = "";
foreach ($tests as $key => $value) {
    $passedTests = "";
    $failedTests = "";
    sort($value["passed"]);
    sort($value["failed"]);
    foreach ($value["passed"] as $pTests)
        $passedTests .= '<tr class="test-row"><td class="test-name">' . $pTests . '</td><td class="test-result green">Passed</td></tr>';
    foreach ($value["failed"] as $pFailed)
        $failedTests .= '<tr class="test-row"><td class="test-name">' . $pFailed . '</td><td class="test-result red">Failed</td></tr>';


    $allFailed = count($value["failed"]);
    $allPassed = count($value["passed"]);
    $allCount = $allFailed + $allPassed;

    $dirname = $key;
    if ($dirname == ".") $dirname = "Current directory";
    $report = '
        <div class="flex-item">
            <h2 class="dirname">' . $dirname . '</h2>
                <div class="report">
                    <h4>All: <span>' . $allCount . '</span></h4>
                    <h4>Passed: <span class="green">' . $allPassed . '</span></h4>
                    <h4>Failed: <span class="red">' . $allFailed . '</span></h4>
                </div>
                <table>
                    <tbody>
                        ' . $passedTests . '
                        ' . $failedTests . '
                    </tbody>
            </table>
        </div>
    ';
    if ($allCount != 0)
        $dirreport .= $report;
}

$mode = $interpretOnly ? "Interpret only" : ($parseOnly ? "Parse only" : "Both");

$doc =
    '
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta http-equiv="X-UA-Compatible" content="IE=edge" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>IPP21 TEST REPORT</title>

    <style>
      html {
        box-sizing: border-box;
      }
      *, *:before, *:after {
        box-sizing: inherit;
      }
      html {
        font-family: Arial, Helvetica, sans-serif;
        background-color: #f9f9f9;
      }
      h1,
      body {
        margin: 0;
      }
      h1 {
        font-family: "Courier New", monospace;
      }
      h2,
      h3 {
        font-weight: bold;
      }
      h4 {
        margin: 10px 0;
      }
      .content {
        padding: 2em;
      }
      .head {
        background-color: #ebebeb;
      }
      .green {
        color: #4cbb17;
      }
      .red {
        color: #ce1212;
      }
      .report {
        font-family: "Courier New", monospace;
      }
      .shadow {
        box-shadow: 0px 12px 18px -9px rgba(0, 0, 0, 0.3);
      }
      .flex {
        display: flex;
        flex-wrap: wrap;
        align-items: stretch;
      }
      .flex-item {
        width: 33%;
        padding-right: 2em;
      }
      .flex-item:last-child {
        padding-right: 0;
      }
      .test-result{
        text-align:right;
      }
      table {
        width: 100%;
        background-color: #ccc;
        border: 1px solid rgb(155, 155, 155);
      }
      td{
          border:1px solid #f9f9f9;
      }
    </style>
  </head>

  <body>
    <div class="content head shadow">
      <h1>IPP21 Tester report</h1>
      <p>
        Mode: <b>' . $mode . '</b>
      </p>
      <div class="report">
        <h2>All tests: <span id="all">' . $allTests . '</span></h2>
        <h3>Passed: <span id="passed" class="green">' . $passed . '</span></h3>
        <h3>Failed: <span id="failed" class="red">' . $failed . '</span></h3>
      </div>
    </div>

    <div class="content main">
      <h1>Report by directories</h1>
      <div id="dir-report">
        <div class="flex">
            ' . $dirreport . '
        </div>
      </div>
    </div>
  </body>
</html>
';

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
        exec("php7.4 $parseScript < $testSrc 2>/dev/null", $output, $retCode);
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
    echo ("Tester for interpret.py and parse.php, Version 1.0, Author: Peter Zdravecký\n");
    echo ("==========================================================\n");
    echo ("Usage: $name \n [ --help | --directory=dir | --recursive | --parse-script=script | --int-script=script | --parse-only | --int-only | --jexamxml=file | --jexamcfg=file | testliist=file | match=regex ]");

    echo ("    --directory    | Search directory for tests\n");
    echo ("    --recursive    | Search in directory recursivly in subdirectories\n");
    echo ("    --parse-script | Path to parse script\n");
    echo ("    --int-script   | Path to interpret script\n");
    echo ("    --parse-only   | Test only parse script\n");
    echo ("    --int-onl      | Test only interpret script\n");
    echo ("    --jexamxml     | Path to xml copmarator\n");
    echo ("    --jexamcfg     | Path to xml copmarator config\n");
    echo ("    --testliist    | File that contain directories to search for tests\n");
    echo ("    --match        | Do tests only match regex\n");


    echo ("\nExample usage: \n");
    echo ("       ./parse.php --help \n");
    echo ("       ./parse.php --directory=tests --parse-only --parse-script=./parse.php \n");
    echo ("       ./parse.php --recursive --int-only \n");
    echo ("==========================================================\n");
    exit(0);
}
