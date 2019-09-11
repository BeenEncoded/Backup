import unittest

#Here we will define our test suites
#test-cases are packaged into the testcases package

no_tests = unittest.TestSuite() #an empty test suite is no tests

if __name__ == "__main__":
    runner = unittest.TextTestRunner()

    runner.run(no_tests)