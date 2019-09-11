import unittest

#Here we will define our test suites
#test-cases are packaged into the testcases package

if __name__ == "__main__":
    runner = unittest.TextTestRunner()
    runner.run(unittest.TestSuite())