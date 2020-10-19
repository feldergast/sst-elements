# -*- coding: utf-8 -*-

from sst_unittest import *
from sst_unittest_support import *

################################################################################
# Code to support a single instance module initialize, must be called setUp method

module_init = 0
module_sema = threading.Semaphore()

def initializeTestModule_SingleInstance(class_inst):
    global module_init
    global module_sema

    module_sema.acquire()
    if module_init != 1:
        # Put your single instance Init Code Here
        module_init = 1
    module_sema.release()

################################################################################

class testcase_cacheTracer_Component(SSTTestCase):

    def initializeClass(self, testName):
        super(type(self), self).initializeClass(testName)
        # Put test based setup code here. it is called before testing starts
        # NOTE: This method is called once for every test

    def setUp(self):
        super(type(self), self).setUp()
        initializeTestModule_SingleInstance(self)
        # Put test based setup code here. it is called once before every test

    def tearDown(self):
        # Put test based teardown code here. it is called once after every test
        super(type(self), self).tearDown()

#####

    def test_cacheTracer_1(self):
        self.cacheTracer_test_template_1()

    @unittest.skipIf(testing_check_get_num_ranks() > 1, "CacheTracer: test_cacheTracer_2 skipped if ranks > 1")
    def test_cacheTracer_2(self):
        self.cacheTracer_test_template_2()

#####

    def cacheTracer_test_template_1(self):
        # Get the path to the test files
        test_path = self.get_testsuite_dir()
        outdir = self.get_test_output_run_dir()
        tmpdir = self.get_test_output_tmp_dir()

        # Set the various file paths
        testDataFileName="test_cacheTracer_1"

        sdlfile = "{0}/{1}.py".format(test_path, testDataFileName)
        reffile = "{0}/refFiles/{1}.out".format(test_path, testDataFileName)
        outfile = "{0}/{1}.out".format(outdir, testDataFileName)
        errfile = "{0}/{1}.err".format(outdir, testDataFileName)
        mpioutfiles = "{0}/{1}.testfile".format(outdir, testDataFileName)

        self.run_sst(sdlfile, outfile, errfile, mpi_out_files=mpioutfiles)

        # NOTE: THE PASS / FAIL EVALUATIONS ARE PORTED FROM THE SQE BAMBOO
        #       BASED testSuite_XXX.sh THESE SHOULD BE RE-EVALUATED BY THE
        #       DEVELOPER AGAINST THE LATEST VERSION OF SST TO SEE IF THE
        #       TESTS & RESULT FILES ARE STILL VALID

        # Perform the test
        cmp_result = testing_compare_sorted_diff(testDataFileName, outfile, reffile)
        self.assertTrue(cmp_result, "Sorted Output file {0} does not match sorted Reference File {1}".format(outfile, reffile))

###

    def cacheTracer_test_template_2(self):
        # Get the path to the test files
        test_path = self.get_testsuite_dir()
        outdir = self.get_test_output_run_dir()
        tmpdir = self.get_test_output_tmp_dir()

        # Set the various file paths
        testDataFileName="test_cacheTracer_2"

        sdlfile = "{0}/{1}.py".format(test_path, testDataFileName)
        reffile = "{0}/refFiles/{1}_memRef.out".format(test_path, testDataFileName)
        outfile = "{0}/{1}.out".format(outdir, testDataFileName)
        errfile = "{0}/{1}.err".format(outdir, testDataFileName)
        mpioutfiles = "{0}/{1}.testfile".format(outdir, testDataFileName)
        out_memRefFile = "{0}/{1}_memRef.out".format(outdir, testDataFileName)

        self.run_sst(sdlfile, outfile, errfile, mpi_out_files=mpioutfiles)

        # Cat the files together normally (OpenMPI V2)
        cmd = "cat {0} {1} > {2}".format("{0}/test_cacheTracer_2_mem_ref_trace.txt".format(outdir),
                                         "{0}/test_cacheTracer_2_mem_ref_stats.txt".format(outdir),
                                         out_memRefFile)
        os.system(cmd)

        # NOTE: THE PASS / FAIL EVALUATIONS ARE PORTED FROM THE SQE BAMBOO
        #       BASED testSuite_XXX.sh THESE SHOULD BE RE-EVALUATED BY THE
        #       DEVELOPER AGAINST THE LATEST VERSION OF SST TO SEE IF THE
        #       TESTS & RESULT FILES ARE STILL VALID

        # Perform the test
        cmp_result = testing_compare_diff(out_memRefFile, reffile, ignore_ws=True)
        self.assertTrue(cmp_result, "File {0} does not match Reference File {1} ignoring whitespace".format(out_memRefFile, reffile))
