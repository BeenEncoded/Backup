import unittest, json, random, os, sys

from data import BackupProfile
from projecttests.randomstuff import randomstring, randomBackupProfile

class DataTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        super(DataTestCase, self).setUpClass()

    @classmethod
    def tearDownClass(self):
        return super(DataTestCase, self).tearDownClass()
    
    def test_jsonification(self):
        random_stuff = []
        for x in range(0, 10):
            random_stuff.append(randomBackupProfile())
        
        with open(os.path.abspath("./jsonification_test.json"), 'w') as file:
            file.write(BackupProfile.json(random_stuff))