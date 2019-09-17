import unittest, os, shutil
from filesystem.iterator import recursive, recursivecopy, ischild, split_path
from tqdm import tqdm

class IterationTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.iteration_path = os.path.abspath("../../..")
        self.iteration_path_count = 0

        self.backup_source = os.path.abspath("./test/test_source")
        self.backup_dest = os.path.abspath("./test/test_destination")

        for entry in recursive(self.iteration_path):
            self.iteration_path_count += 1

    def test_recursion(self):
        count = 0
        print("Testing Recursion: ")
        for entry in tqdm(recursive(self.iteration_path), total=self.iteration_path_count):
            self.assertEqual(os.path.exists(entry), True)
            count += 1
        self.assertEqual((count > 0), True)
    
    def test_split_path(self):
        print("Testing split_path")
        for entry in tqdm(recursive(self.iteration_path), total=self.iteration_path_count):
            if entry != IterationTestCase.iteration_path:
                self.assertEqual(entry, os.path.join(split_path(self.iteration_path, entry)[0], split_path(self.iteration_path, entry)[1]))

    def test_ischild(self):
        print("Testing ischild")
        for entry in tqdm(recursive(self.iteration_path), total=self.iteration_path_count):
            if entry != self.iteration_path:
                self.assertEqual(ischild(self.iteration_path, entry), True)

    def test_recursivecopy_initialization(self):
        print("testing recursive copy initialization")
        invalid_destinations = [os.path.abspath("../../../.."), \
                os.path.abspath("/q\\fwef/jo\nnat hanqe/  egibweff"), os.path.abspath("../../..")]
        
        dest_with_sourcepath = [os.path.abspath("../../../.."), \
                os.path.abspath(self.iteration_path), os.path.abspath("..")]

        # This test makes sure that the initialization using an invalid destination is safe and 
        # throws the appropriate error:
        try:
            a = recursivecopy(self.iteration_path, "/q\\fwef/jo\nnat hanqe/  egibweff")
            self.assertTrue(False)
        except NotADirectoryError:
            self.assertTrue(True)
        
        # Here we test that one of the destinations is an invalid path:
        try:
            b = recursivecopy(self.iteration_path, invalid_destinations)
            self.assertTrue(False)
        except NotADirectoryError:
            self.assertTrue(True)

        #here we test that both a source and destination are invalid
        try:
            c = recursivecopy("/wef/wef\\wefw\asocqoweijf", "/q\\fwef/jo\nnat hanqe/  egibweff")
            self.assertTrue(False)
        except NotADirectoryError:
            self.assertTrue(True)
        
        #test to make sure that passing the source path as one of the destinations
        # throws an exception.
        try:
            d = recursivecopy(self.iteration_path, dest_with_sourcepath)
            self.assertTrue(False)
        except shutil.SameFileError:
            self.assertTrue(True)

        #here we test that passing the wrong argument throws the appropriate error:
        try:
            e = recursivecopy(1, 2)
            self.assertTrue(False)
        except:
            self.assertTrue(True)
        
        #test that an invalid destination throws
        try:
            f = recursivecopy(self.iteration_path, 2)
            self.assertTrue(False)
        except:
            self.assertTrue(True)

        #and finally we make sure that passing a valid path is error-free
        try:
            z = recursivecopy(self.iteration_path, os.path.abspath("../../../.."))
            self.assertTrue(True)
        except:
            self.assertTrue(False)

    def test__copy_fsobject(self):
        print("Testing _copy_fsobject")

        self._mkdir(self.backup_dest)
        self._mkdir(self.backup_source)
        cpy = iter(recursivecopy(self.backup_source, self.backup_dest))
        try:
            for x in tqdm(range(100)):
                next(cpy)
        except StopIteration:
            pass

    def _mkdir(self, dir):
        try:
            os.makedirs(dir)
        except FileExistsError:
            pass