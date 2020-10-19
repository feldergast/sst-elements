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

class testcase_Samba_Component(SSTTestCase):

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

    @unittest.skipIf(testing_check_get_num_ranks() > 2, "Samba: test_Samba_gupsgen_mmu skipped if ranks > 2")
    def test_Samba_gupsgen_mmu(self):
        self.Samba_test_template("gupsgen_mmu")

    @unittest.skipIf(testing_check_get_num_ranks() > 2, "Samba: test_Samba_gupsgen_mmu_4KB skipped if ranks > 2")
    def test_Samba_gupsgen_mmu_4KB(self):
        self.Samba_test_template("gupsgen_mmu_4KB")

    @unittest.skipIf(testing_check_get_num_ranks() > 2, "Samba: test_Samba_gupsgen_mmu_three_levels skipped if ranks > 2")
    def test_Samba_gupsgen_mmu_three_levels(self):
        self.Samba_test_template("gupsgen_mmu_three_levels")

    @unittest.skipIf(testing_check_get_num_ranks() > 2, "Samba: test_Samba_stencil3dbench_mmu skipped if ranks > 2")
    def test_Samba_stencil3dbench_mmu(self):
        self.Samba_test_template("stencil3dbench_mmu")

    @unittest.skipIf(testing_check_get_num_ranks() > 2, "Samba: test_Samba_streambench_mmu skipped if ranks > 2")
    def test_Samba_streambench_mmu(self):
        self.Samba_test_template("streambench_mmu")

#####

    def Samba_test_template(self, testcase):
        # Get the path to the test files
        test_path = self.get_testsuite_dir()
        outdir = self.get_test_output_run_dir()
        tmpdir = self.get_test_output_tmp_dir()

        # Set the various file paths
        testDataFileName="test_Samba_{0}".format(testcase)
        sdlfile = "{0}/{1}.py".format(test_path, testcase)
        reffile = "{0}/refFiles/{1}.out".format(test_path, testDataFileName)
        outfile = "{0}/{1}.out".format(outdir, testDataFileName)
        errfile = "{0}/{1}.err".format(outdir, testDataFileName)
        tmpfile = "{0}/{1}.tmp".format(tmpdir, testDataFileName)
        self.tmp_file = tmpfile
        mpioutfiles = "{0}/{1}.testfile".format(outdir, testDataFileName)
        newoutfile = "{0}/{1}.newout".format(outdir, testDataFileName)
        newreffile = "{0}/{1}.newref".format(outdir, testDataFileName)

        self.run_sst(sdlfile, outfile, errfile, mpi_out_files=mpioutfiles)

#        # This may be needed in the future
#        remove_component_warning()

        # NOTE: THE PASS / FAIL EVALUATIONS ARE PORTED FROM THE SQE BAMBOO
        #       BASED testSuite_XXX.sh THESE SHOULD BE RE-EVALUATED BY THE
        #       DEVELOPER AGAINST THE LATEST VERSION OF SST TO SEE IF THE
        #       TESTS & RESULT FILES ARE STILL VALID

        cmp_result = testing_compare_diff(outfile, reffile)
        if cmp_result != True:
            # We need to use some bailing wire to allow serialization
            # branch to work with same reference files
            cmd = "sed s/' (.*)'// {0} > {1}".format(reffile, newreffile)
            os.system(cmd)
            ref_wc_data = self._get_file_data_counts(newreffile)

            cmd = "sed s/' (.*)'// {0} > {1}".format(outfile, newoutfile)
            os.system(cmd)
            out_wc_data = self._get_file_data_counts(newoutfile)

            cmp_result = ref_wc_data == out_wc_data
            self.assertTrue(cmp_result, "Output file {0} word/line count does NOT match Reference file {1} word/line count".format(outfile, reffile))

        else:
            self.assertTrue(cmp_result, "Diffed compared Output file {0} does not match Reference File {1}".format(outfile, reffile))

###

    def _get_file_data_counts(self, in_file):
        cmd = "wc {0} | awk '{{print $1, $2}}' > {1}".format(in_file, self.tmp_file)
        os.system(cmd)
        cmd = "cat {0}".format(self.tmp_file)
        cmd_rtn = os_simple_command(cmd)
        cat_out = cmd_rtn[1]
        return cat_out