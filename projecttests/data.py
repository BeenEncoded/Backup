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

import unittest, os

from tqdm import tqdm
from data import BackupProfile
from projecttests.randomstuff import randomBackupProfile

class DataTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        super(DataTestCase, self).setUpClass()

    @classmethod
    def tearDownClass(self):
        return super(DataTestCase, self).tearDownClass()
    
    def test_jsonification(self):
        print("Testing jsonification of BackupProfile")
        random_stuff = []
        filename = os.path.abspath("./jsonification_test.json")

        for x in tqdm(range(0, 30)):
            random_stuff.clear()
            for i in range(0, 10):
                random_stuff.append(randomBackupProfile())
            
            BackupProfile.writejson(random_stuff, filename)
            loaded = BackupProfile.readjson(filename)
            self.assertTrue(loaded == random_stuff)
        os.remove(filename)