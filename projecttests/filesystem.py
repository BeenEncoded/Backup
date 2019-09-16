import unittest, os, shutil
from filesystem.iterator import recursive, recursivecopy, ischild, split_path

class IterationTestCase(unittest.TestCase):
    iteration_path = os.path.abspath("../../..")

    def test_recursion(self):
        count = 0
        for entry in recursive(IterationTestCase.iteration_path):
            self.assertEqual(os.path.exists(entry), True)
            count += 1
        self.assertEqual((count > 0), True)
    
    def test_split_path(self):
        for entry in recursive(IterationTestCase.iteration_path):
            if entry != IterationTestCase.iteration_path:
                self.assertEqual(entry, os.path.join(split_path(IterationTestCase.iteration_path, entry)[0], split_path(IterationTestCase.iteration_path, entry)[1]))

    def test_ischild(self):
        for entry in recursive(IterationTestCase.iteration_path):
            if entry != IterationTestCase.iteration_path:
                self.assertEqual(ischild(IterationTestCase.iteration_path, entry), True)

    def test_recursivecopy_initialization(self):
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
        test_backup_folder = os.path.abspath("./test_backup")

        try:
            os.mkdir(test_backup_folder)
        except FileExistsError:
            pass
        cpy = iter(recursivecopy(self.iteration_path, test_backup_folder))
        try:
            for x in range(100):
                next(cpy)
        except StopIteration:
            pass
        os.rmdir(test_backup_folder)