# Backup backs up a user's computer to one or more disk drives or block devices.
# Copyright (C) 2019 Jonathan Whitlock

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

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