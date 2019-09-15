import unittest, os

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

    # def iterators(self):
    #     print("\n\n\n\n\nSTARTING ITERATION: \n")
    #     p = os.path.abspath(".")
    #     count = 0
    #     errors = list()
    #     for entry in recursive(p):
    #         count += 1
    #         print(split_path(p, entry))
    #         if p != entry:
    #             ic = ischild(p, os.path.join(split_path(p, entry)[0], split_path(p, entry)[1]))
    #             print("second is child: " + str(ic))
    #             if ic != True:
    #                 errors.append([entry, split_path(p, entry)])
    #     if len(errors) > 0:
    #         print("\n\n\n\nErrors: " + str(len(errors)))
    #     else:
    #         print("\n\n\n\nNo errors")
    #     for e in errors:
    #         print("Path: " + e[0])
    #         print("split_path: " + e[1])
    #     print("\n\nDone iterating over " + str(count) + " paths under " + p)
    #     print("Destinations: " + str(iter(recursivecopy(p, ['/sys', '/home/jonathan']))._destinations))