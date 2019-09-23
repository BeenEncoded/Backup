import unittest
from projecttests.filesystem import IterationTestCase
from projecttests.data import DataTestCase

#Here we will define our test suites
#test-cases are packaged into the testcases package

no_tests = unittest.TestSuite() #an empty test suite is no tests

def addIterationTestCase(suite):
    suite.addTest(IterationTestCase('test_recursion'))
    suite.addTest(IterationTestCase('test_split_path'))
    suite.addTest(IterationTestCase('test_ischild'))
    suite.addTest(IterationTestCase('test_recursivecopy_initialization'))
    # suite.addTest(IterationTestCase('test__copy_fsobject'))
    # suite.addTest(IterationTestCase('test_backup_potential'))

def addDataTestCase(suite):
    suite.addTest(DataTestCase('test_jsonification'))

def defaultTests():
    suite = unittest.TestSuite()
    addIterationTestCase(suite)
    addDataTestCase(suite)
    return suite

if __name__ == "__main__":
    runner = unittest.TextTestRunner()
    runner.run(defaultTests())
    # unittest.main()