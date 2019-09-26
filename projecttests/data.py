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