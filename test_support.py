# -*- coding: utf-8 -*-

import os
import time
import subprocess
import threading
import traceback
import shlex

import unittest
import test_globals

###################################################

""" This class the the SST Unittest class """
class SSTUnitTest(unittest.TestCase):

    def __init__(self, methodName):
        super(SSTUnitTest, self).__init__(methodName)

### Logging Commands

    def log(self, logstr):
        log(logstr)

    def logDebug(self, logstr):
        logDebug(logstr)

### Path Information

    def isTestingInDebugMode(self):
        return test_globals.debugMode

    def getTestSuiteDir(self):
        return os.path.dirname(test_globals.testSuiteFilePath)

    def getTestOutputRunDir(self):
        return test_globals.testOutputRunDirPath

    def getTestOutputTmpDir(self):
        return test_globals.testOutputTmpDirPath

### OS Basic Commands

    def os_ls(self, directory = "."):
        cmd = "ls -lia {0}".format(directory)
        rtn = OSCommand(cmd).run()
        logDebug("{0}".format(rtn.output()))

    def os_cat(self, filepath):
        cmd = "cat {0}".format(filepath)
        rtn = OSCommand(cmd).run()
        logDebug("{0}".format(rtn.output()))

################################################################################

def initTestSuite(testSuiteFilePath):
    test_globals.testSuiteFilePath = testSuiteFilePath

###################################################

def log(logstr):
    print("\n{0}".format(logstr))

def logDebug(logstr):
    if test_globals.debugMode:
        log(logstr)

###################################################

class OSCommand(object):
    """
    Enables to run subprocess commands in a different thread with TIMEOUT option.
    This will return a OSCommandResult object

    Based on a modified version of jcollado's solution:
    http://stackoverflow.com/questions/1191374/subprocess-with-timeout/4825933#4825933
    """
    _outputfilepath = None
    _command        = None
    _process        = None
    _timeout        = 60
    _run_status     = None
    _run_output     = ''
    _run_error      = ''
    _run_timeout    = False

    def __init__(self, command, outputfilepath=None):
        if isinstance(command, basestring):
            if command != "":
                command = shlex.split(command)
            else:
                raise ValueError("ERROR: Command must not be empty")
        else:
            raise ValueError("ERROR: Command must be a string")
        self._command = command

        if outputfilepath != None:
            dirpath = os.path.abspath(os.path.dirname(outputfilepath))
            if not os.path.exists(dirpath):
                raise ValueError("ERROR: Path to outputfile {0} is not valid".format(outputfilepath))
        self._outputfilepath = outputfilepath

    def run(self, timeout=60, **kwargs):
        """ Run a command then return and OSCmdRtn object. """
        def target(**kwargs):
            try:
                if self._outputfilepath != None:
                    with open(self._outputfilepath, 'w+') as f:
                        self._process = subprocess.Popen(self._command, stdout=f, **kwargs)
                        self._run_output, self._run_error = self._process.communicate()
                        self._run_status = self._process.returncode
                else:
                        self._process = subprocess.Popen(self._command, **kwargs)
                        self._run_output, self._run_error = self._process.communicate()
                        self._run_status = self._process.returncode

                if self._run_output == None:
                    self._run_output = ""

                if self._run_error == None:
                    self._run_error = ""

            except:
                self._run_error = traceback.format_exc()
                self._run_status = -1

        if not (isinstance(self._timeout, (int, float)) and not isinstance(self._timeout, bool)):
            raise ValueError("ERROR: Timeout must be an int or a float")

        self._timeout = timeout

        # default stdout and stderr
        if 'stdout' not in kwargs and self._outputfilepath == None:
            kwargs['stdout'] = subprocess.PIPE
        if 'stderr' not in kwargs:
            kwargs['stderr'] = subprocess.PIPE

        # thread
        thread = threading.Thread(target=target, kwargs=kwargs)
        thread.start()
        thread.join(self._timeout)
        if thread.is_alive():
            self._run_timeout = True
            self._process.terminate()
            thread.join()

        # Build a results cpass
        rtn = OSCommandResult(self._command, self._run_status, self._run_output,
                              self._run_error, self._run_timeout)
        return rtn

class OSCommandResult():
    _run_cmd        = ''
    _run_status     = None
    _run_output     = ''
    _run_error      = ''
    _run_timeout    = False

    def __init__(self, cmd, status, output, error, timeout):
        self._run_cmd        = cmd
        self._run_status     = status
        self._run_output     = output
        self._run_error      = error
        self._run_timeout    = timeout

    def __repr__(self):
        return "Cmd = {0}; Status = {1}; Timeout = {2}; Error = {3}; Output = {4}".format(
        self._run_cmd, self._run_status, self._run_timeout, self._run_error, self._run_output)

    def __str__(self):
        return self.__repr__()

    def cmd(self):
        return self._run_cmd

    def result(self):
        return self._run_status

#    @property
    def output(self):
        return self._run_output

    def error(self):
        return self._run_error

    def timeout(self):
        return self._run_timeout





