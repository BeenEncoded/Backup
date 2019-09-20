import unittest
from projecttests.filesystem import IterationTestCase

#Here we will define our test suites
#test-cases are packaged into the testcases package

no_tests = unittest.TestSuite() #an empty test suite is no tests

def defaultTests():
    s = unittest.TestSuite()
    s.addTest(IterationTestCase('test_recursion'))
    s.addTest(IterationTestCase('test_split_path'))
    s.addTest(IterationTestCase('test_ischild'))
    s.addTest(IterationTestCase('test_recursivecopy_initialization'))
    s.addTest(IterationTestCase('test__copy_fsobject'))
    return s

if __name__ == "__main__":
    runner = unittest.TextTestRunner()
    runner.run(defaultTests())
    # unittest.main()