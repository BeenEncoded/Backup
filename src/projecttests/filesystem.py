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

import unittest, os, shutil
from iterator import recursive, recursivecopy, ischild, split_path, copypredicate, recursiveprune
from tqdm import tqdm
from algorithms import prune_backup
import data


class IterationTestCase(unittest.TestCase):
    '''
    Tests a bunch of stuff in filesystem.iterator to make sure it works.
    '''

    @classmethod
    def setUpClass(cls):
        cls.iteration_path = os.path.abspath("../../..")
        cls.iteration_path_count = 0

        cls.backup_source = os.path.abspath("./test/test_source")
        cls.backup_dest = os.path.abspath("./test/test_destination")

        cls.iteration_path_count = sum((len(files) + len(dirs)) for _, dirs, files in os.walk(cls.iteration_path))

    @unittest.skip("skipping")
    def test_pruneiterator(self):
        for i in recursiveprune(r"D:\beene", r"G:\legion\03152020\d\beene"):
            print(i)

    @unittest.skip("skipping")
    def test_recursion(self):
        count = 0
        print("Testing Recursion: ")
        for entry in tqdm(recursive(self.iteration_path), total=self.iteration_path_count):
            count += 1
        self.assertEqual((count > 0), True)

    @unittest.skip("skipping")
    def test_split_path(self):
        print("Testing split_path")
        for entry in tqdm(recursive(self.iteration_path), total=self.iteration_path_count):
            if entry != IterationTestCase.iteration_path:
                self.assertEqual(entry, os.path.join(split_path(self.iteration_path, entry)[
                                 0], split_path(self.iteration_path, entry)[1]))

    @unittest.skip("skipping")
    def test_ischild(self):
        print("Testing ischild")
        for entry in tqdm(recursive(self.iteration_path), total=self.iteration_path_count):
            if entry != self.iteration_path:
                self.assertEqual(ischild(self.iteration_path, entry), True)

    @unittest.skip("skipping")
    def test_recursivecopy_initialization(self):
        print("testing recursive copy initialization")
        invalid_destinations = [os.path.abspath("../../../.."),
                                os.path.abspath("/q\\fwef/jo\nnat hanqe/  egibweff"), os.path.abspath("../../..")]

        dest_with_sourcepath = [os.path.abspath("../../../.."),
                                os.path.abspath(self.iteration_path), os.path.abspath("..")]

        # This test makes sure that the initialization using an invalid destination is safe and
        # throws the appropriate error:
        try:
            a = recursivecopy(self.iteration_path, # noqa F841
                              "/q\\fwef/jo\nnat hanqe/  egibweff")
            self.assertTrue(False)
        except NotADirectoryError:
            self.assertTrue(True)

        # Here we test that one of the destinations is an invalid path:
        try:
            b = recursivecopy(self.iteration_path, invalid_destinations) # noqa F841
            self.assertTrue(False)
        except NotADirectoryError:
            self.assertTrue(True)

        # here we test that both a source and destination are invalid
        try:
            c = recursivecopy("/wef/wef\\wefw\asocqoweijf", # noqa F841
                              "/q\\fwef/jo\nnat hanqe/  egibweff")
            self.assertTrue(False)
        except NotADirectoryError:
            self.assertTrue(True)

        # test to make sure that passing the source path as one of the destinations
        # throws an exception.
        try:
            d = recursivecopy(self.iteration_path, dest_with_sourcepath) # noqa F841
            self.assertTrue(False)
        except shutil.SameFileError:
            self.assertTrue(True)

        # here we test that passing the wrong argument throws the appropriate error:
        try:
            e = recursivecopy(1, 2) # noqa F841
            self.assertTrue(False)
        except: # noqa E722
            self.assertTrue(True)

        # test that an invalid destination throws
        try:
            f = recursivecopy(self.iteration_path, 2) # noqa F841
            self.assertTrue(False)
        except: # noqa E722
            self.assertTrue(True)

        # and finally we make sure that passing a valid path is error-free
        try:
            z = recursivecopy(self.iteration_path, # noqa F841
                              os.path.abspath("../../../.."))
            self.assertTrue(True)
        except: # noqa E722
            self.assertTrue(False)

    @unittest.skip("Problematic")
    def test__copy_fsobject(self):
        print("Testing _copy_fsobject")

        self._mkdir(self.backup_dest)
        self._mkdir(self.backup_source)
        count = 0
        for entry in recursive(self.backup_source):
            count += 1
        for result in tqdm(recursivecopy(self.backup_source, self.backup_dest), total=count):
            if len(result) > 1:
                print("Copy fail!")
                print(result[1].message)
                print(result[1].errors)

                self.assertTrue(False)
        shutil.rmtree(self.backup_dest)

    @unittest.skip("Problematic")
    def test_backup_potential(self):
        bsource = os.path.abspath("D:\\beene")
        bdest = [
            os.path.abspath("E:\\testbackup"),
            os.path.abspath("F:\\testbackup")
        ]
        count = 0
        print("Loading...")
        for entry in tqdm(recursive(bsource)):
            count += 1
        print("Starting backup:")
        print("Source: " + bsource)
        print("Destination: " + str(bdest))
        for results in tqdm(recursivecopy(bsource, bdest, copypredicate.if_source_was_modified_more_recently), total=count):
            if results is not None:
                for result in results:
                    print("Error: " + str(result))

    @unittest.skip("skipping")
    def test_backup_prune(self):
        prune_backup(data._profile_from_dict({
            "destinations": [
                "G:/legion/05172020/c",
                "E:/legiony530/05172020/c"
                ],
            "id": 1,
            "name": "Weekly C Backup",
            "sources": [
                "C:/Users/beene/Documents",
                "C:/Users/beene/.config",
                "C:/Users/beene/.ssh",
                "C:/Users/beene/source",
                "C:/Users/beene/Videos",
                "C:/Users/beene/.backup",
                "C:/Users/beene/.omnisharp",
                "C:/Users/beene/.dotnet",
                "C:/Users/beene/3D Objects",
                "C:/Users/beene/bash",
                "C:/Users/beene/Contacts",
                "C:/Users/beene/Desktop",
                "C:/Users/beene/Music",
                "C:/Users/beene/Pictures"
                ]
            }))

    # Helper functions:
    def _mkdir(self, dir):
        try:
            os.makedirs(dir)
        except FileExistsError:
            pass

