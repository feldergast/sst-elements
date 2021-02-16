# -*- coding: utf-8 -*-

from sst_unittest import *
from sst_unittest_support import *
from sst_unittest_parameterized import parameterized

import hashlib
#import os

dirpath = os.path.dirname(sys.modules[__name__].__file__)

module_init = 0
module_sema = threading.Semaphore()
dir3levelsweep_test_matrix = []

################################################################################
# NOTES:
# This is a parameterized test, we setup the dir3levelsweep test matrix ahead of time and
# then use the sst_unittest_parameterized module to load the list of testcases.
#
# There are a lot of environment options that can be set by exporting a env variable
# that will affect testing operations:
#
#
#
################################################################################

def build_dir3levelsweep_test_matrix():
    global dir3levelsweep_test_matrix
    dir3levelsweep_test_matrix = []
    testlist = []
    testnum = 1

    # L1 Cache Options
    L1_cache_size_list = ["8 KB", "32 KB"]
    L1_replacement_policy_list = ["random", "mru"]
    L1_associativity_list = ["2", "4"]

    # L2 Cache Options
    L2_cache_size_list = ["32 KB", "128 KB"]
    L2_replacement_policy_list = ["random", "mru"]
    L2_associativity_list = ["8", "16"]
    L2_mshr_size_list = ["8", "64"]

    # L3 Cache Options
    L3_cache_size_list = ["32 KB", "128 KB"]
    L3_replacement_policy_list = ["random", "mru"]
    L3_associativity_list = ["8", "16"]
    L3_mshr_size_list = ["8", "64"]

    # Test type options
    test_type_list = ["MSI", "MESI"]

    # Now loop through the options
    log_debug("*** BUILDING THE TEST MATRIX")
    for L1_size in L1_cache_size_list:
        if L1_size == "8 KB":
            L1_repl = "mru"
            L1_asso = "2"
        else:
            L1_repl = "random"
            L1_asso = "4"
        for L2_size in L2_cache_size_list:
            for L3_size in L3_cache_size_list:
                for L2_repl in L2_replacement_policy_list:
                    for L3_repl in L3_replacement_policy_list:
                        for L2_asso in L2_associativity_list:
                            for L3_asso in L3_associativity_list:
                                for L2_mshr in L2_mshr_size_list:
                                    for L3_mshr in L3_mshr_size_list:
                                        for test_type in test_type_list:
                                            # NOW POPULATE THE Test Matrix
#                                            log_debug("dir3levelsweep Test Matrix:TestNum={0:04}; L1:size={1}; repl={2}; asso={3}; L2:size={4}; repl={5}; asso={6}; mshr={7}; L3:size={8}; repl={9}; asso={10}; mshr={11}; test_type={12}".format(testnum, L1_size, L1_repl, L1_asso, L2_size, L2_repl, L2_asso, L2_mshr, L3_size, L3_repl, L3_asso, L3_mshr, test_type))
                                            test_data = (testnum, L1_size, L1_repl, L1_asso, L2_size, L2_repl, L2_asso, L2_mshr, L3_size, L3_repl, L3_asso, L3_mshr, test_type)
                                            dir3levelsweep_test_matrix.append(test_data)
                                            testnum += 1


################################################################################

# At startup, build the test matrix
build_dir3levelsweep_test_matrix()

def gen_custom_name(testcase_func, param_num, param):
# Full TestCaseName
#    testcasename = "{0}_{1:03}".format(testcase_func.__name__,
#        parameterized.to_safe_name("_".join(str(x) for x in param.args)))
# Abbreviated TestCaseName
    testcasename = "{0}_{1:04}_L1:{2}-{3}-{4}_L2:{5}-{6}-{7}-{8}_L3:{9}-{10}-{11}-{12}_Type:{13}".format(
        testcase_func.__name__,                                   # Test Name
        int(parameterized.to_safe_name(str(param.args[0]))),      # Test Num

        parameterized.to_safe_name(str(param.args[1])),           # L1 Cache
        parameterized.to_safe_name(str(param.args[2])),
        parameterized.to_safe_name(str(param.args[3])),

        parameterized.to_safe_name(str(param.args[4])),           # L2 Cache
        parameterized.to_safe_name(str(param.args[5])),
        parameterized.to_safe_name(str(param.args[6])),
        parameterized.to_safe_name(str(param.args[7])),

        parameterized.to_safe_name(str(param.args[8])),           # L3 Cache
        parameterized.to_safe_name(str(param.args[9])),
        parameterized.to_safe_name(str(param.args[10])),
        parameterized.to_safe_name(str(param.args[11])),

        parameterized.to_safe_name(str(param.args[12]))           # Test Type
        )
    return testcasename

################################################################################
# Code to support a single instance module initialize, must be called setUp method

def initializeTestModule_SingleInstance(class_inst):
    global module_init
    global module_sema

    module_sema.acquire()
    if module_init != 1:
        try:
            # Put your single instance Init Code Here
            class_inst._setupdir3LevelSweepTestFiles()
        except:
            pass
        module_init = 1
    module_sema.release()

################################################################################

class testcase_memH_sweep_dir3levelsweep(SSTTestCase):

    def initializeClass(self, testName):
        super(type(self), self).initializeClass(testName)
        # Put test based setup code here. it is called before testing starts
        # NOTE: This method is called once for every test

    def setUp(self):
        super(type(self), self).setUp()
        initializeTestModule_SingleInstance(self)

    def tearDown(self):
        # Put test based teardown code here. it is called once after every test
        super(type(self), self).tearDown()

####

    @parameterized.expand(dir3levelsweep_test_matrix, name_func=gen_custom_name)
    def test_memH_dir3levelsweep(self, testnum, L1_size, L1_repl, L1_asso, L2_size, L2_repl, L2_asso, L2_mshr, L3_size, L3_repl, L3_asso, L3_mshr, test_type):
        self._checkSkipConditions(testnum)

        log_debug("Running memH dir3levelsweep #{0:04}; L1:size={1}; repl={2}; asso={3}; L2:size={4}; repl={5}; asso={6}; mshr={7}; L3:size={8}; repl={9}; asso={10}; mshr={11}; test_type={12}".format(testnum, L1_size, L1_repl, L1_asso, L2_size, L2_repl, L2_asso, L2_mshr, L3_size, L3_repl, L3_asso, L3_mshr, test_type))
        self.memH_dir3levelsweek_test_template(testnum, L1_size, L1_repl, L1_asso, L2_size, L2_repl, L2_asso, L2_mshr, L3_size, L3_repl, L3_asso, L3_mshr, test_type)

####

    def memH_dir3levelsweek_test_template(self, testnum, L1_size, L1_repl, L1_asso, L2_size, L2_repl, L2_asso, L2_mshr, L3_size, L3_repl, L3_asso, L3_mshr, test_type):

        # Get the path to the test files
        test_path = self.get_testsuite_dir()
        outdir = self.get_test_output_run_dir()
        tmpdir = self.get_test_output_tmp_dir()

#        self.ember_ESshmem_Folder = "{0}/ember_ESshmem_folder".format(tmpdir)
#        self.emberelement_testdir = "{0}/../test/".format(test_path)
#
#        # Set the various file paths
#        testDataFileName="{0}".format("testESshmem_{0:03}".format(testnum))
#
#        reffile = "{0}/refFiles/ESshmem_cumulative.out".format(test_path)
#        outfile = "{0}/{1}.out".format(outdir, testDataFileName)
#        errfile = "{0}/{1}.err".format(outdir, testDataFileName)
#        mpioutfiles = "{0}/{1}.testfile".format(outdir, testDataFileName)
#        sdlfile = "{0}/../test/{1}".format(test_path, sdlfile)
#        testtimeout = 120
#
#        otherargs = modelstr
#
#        # Run SST
#        self.run_sst(sdlfile, outfile, errfile, other_args=otherargs, set_cwd=self.ember_ESshmem_Folder, mpi_out_files=mpioutfiles, timeout_sec=testtimeout)
#
#        # NOTE: THE PASS / FAIL EVALUATIONS ARE PORTED FROM THE SQE BAMBOO
#        #       BASED testSuite_XXX.sh THESE SHOULD BE RE-EVALUATED BY THE
#        #       DEVELOPER AGAINST THE LATEST VERSION OF SST TO SEE IF THE
#        #       TESTS & RESULT FILES ARE STILL VALID
#
#        self.assertFalse(os_test_file(errfile, "-s"), "Ember Test Test {0} has Non-empty Error File {1}".format(testnum, errfile))
#
#        # Dig through the output file looking for "Simulation is complete"
#        outfoundline = ""
#        grepstr = 'Simulation is complete'
#        with open(outfile, 'r') as f:
#            for line in f.readlines():
#                if grepstr in line:
#                    outfoundline = line
#
#        outtestresult = outfoundline != ""
#        self.assertTrue(outtestresult, "Ember Test Test {0} - Cannot find string \"{1}\" in output file {2}".format(testnum, grepstr, outfile))
#
#        reffoundline = ""
#        grepstr = '{0} {1}'.format(hash_str, outfoundline)
#        with open(reffile, 'r') as f:
#            for line in f.readlines():
#                if grepstr in line:
#                    reffoundline = line
#
#        reftestresult = reffoundline != ""
#        self.assertTrue(reftestresult, "Ember Test Test {0} - Cannot find string \"{1}\" in reference file {2}".format(testnum, grepstr, reffile))
#
#        log_debug("Ember Test Test {0} - PASSED\n--------".format(testnum))

###############################################

    def _checkSkipConditions(self, testindex):
        # Check to see if Env Var SST_TEST_dir3levelsweep_LIST is set limiting which tests to run
        #   An inclusive sub-list may be specified as "first-last"  (e.g. 7-10)
        env_var = 'SST_TEST_dir3levelsweep_LIST'
#        try:
#            testlist = os.environ[env_var]
#            log_debug("SST_TEST_dir3levelsweep_LIST = {0}; type = {1}".format(testlist, type(testlist)))
#            index = testlist.find('-')
#            if index > 0 and len(testlist) >= 3:
#                startnumstr = int(testlist[0:index])
#                stopnumstr = int(testlist[index+1:])
#                try:
#                    startnum = int(startnumstr)
#                    stopnum = int(stopnumstr)
#                except ValueError:
#                    log_debug("Cannot decode start/stop index strings: startstr = {0}; stopstr = {1}".format(startnumstr, stopnumstr))
#                    return
#                log_debug("Current Test Index = {0}; Skip Number: startnum = {1}; stopnum = {2}".format(testindex, startnum, stopnum))
#                if testindex < startnum or testindex > stopnum:
#                    self.skipTest("Skipping Test #{0} - Per {1} = {2}".format(testindex, env_var, testlist))
#            else:
#                log_debug("Env Var {0} - not formatted correctly = {1}".format(env_var, testlist))
#                return
#        except KeyError:
#            return

###

    def _setupdir3LevelSweepTestFiles(self):
        log_debug("_setupdir3LevelSweepTestFiles() Running")
        test_path = self.get_testsuite_dir()
        outdir = self.get_test_output_run_dir()
        tmpdir = self.get_test_output_tmp_dir()

#        self.ember_ESshmem_Folder = "{0}/ember_ESshmem_folder".format(tmpdir)
#        self.emberelement_testdir = "{0}/../test/".format(test_path)
#
#        # Create a clean version of the ember_ESshmem_folder Directory
#        if os.path.isdir(self.ember_ESshmem_Folder):
#            shutil.rmtree(self.ember_ESshmem_Folder, True)
#        os.makedirs(self.ember_ESshmem_Folder)
#
#        # Create a simlink of each file in the ember/test directory
#        for f in os.listdir(self.emberelement_testdir):
#            filename, ext = os.path.splitext(f)
#            if ext == ".py":
#                os_symlink_file(self.emberelement_testdir, self.ember_ESshmem_Folder, f)

###############################################################################
