import os, shutil

# This is basically just a wrapper class around os.walk, but it actually
# iterates over everything.
class recursive:
    def __init__(self, root_path):
        self.iter = os.walk(root_path)
        self.returned_parent = False
        self.files = None
        self.files_pos = 0
        self.dirs = None
        self.path = None
    
    def __iter__(self):
        return self
    
    def __next__(self):
        if self.files is not None:
            if self.files_pos >= len(self.files):
                self.returned_parent = False
        if self.returned_parent == False:
            self.path, self.dirs, self.files = next(self.iter)
            if self.files is not None:
                self.returned_parent = True
                self.files_pos = 0
            return self.path
        elif self.files is not None:
            if self.files_pos < len(self.files):
                s = os.path.join(self.path, self.files[self.files_pos])
                self.files_pos += 1
                return s

class recursivecopy:
    def __init__(self, root_path, destination_folders):
        if (root_path is None) or (destination_folders is None):
            raise AttributeError("recursivecopy: invalid arguments")
        if (os.path.isdir(root_path) == False):
            raise NotADirectoryError("recursivecopy: source directory ('root_path') argument not a folder")
        if (isinstance(destination_folders, list) == False) and (isinstance(destination_folders, str) == False):
            raise ValueError("recursivecopy: destination_folders is not an array or a string!")
        if isinstance(destination_folders, str):
            destination_folders = [destination_folders]
        if isinstance(destination_folders, list):
            for path in destination_folders:
                if os.path.isdir(path) == False:
                    raise NotADirectoryError("recursivecopy: one of the destination folders passed to the \
iterator is not a valid folder!")
                if path == root_path:
                    raise shutil.SameFileError("recursivecopy: one of the  \
destinations given is the same as the source.")
        self._source = root_path
        self._destinations = [os.path.join(d, os.path.basename(self._source)) for d in destination_folders]
        self.iter = recursive(self._source)

    def __iter__(self):
        return self
    
    def __next__(self):
        self.current = next(self.iter)
        return self._copy_fsobject(self.current, self._destinations)
    
    def _copy_fsobject(self, source_path, destination_folders):
        new_dests = destination_folders
        if source_path != self._source:
            new_dests = [os.path.join(d, split_path(self._source, source_path)[1]) for d in destination_folders]
        if os.path.isdir(source_path):
            pass
        elif os.path.isfile(source_path):
            pass
        else:
            pass
        return self.current

# /c/abc
# /c/abc/abc1/bac3
#  V 
# ['/c/abc', 'abc1/bac3']
def split_path(parent, child):
    if os.path.isabs(parent) == False:
        parent = os.path.abspath(parent)
    if os.path.isabs(child) == False:
        child = os.path.abspath(child)
    if ischild(parent, child):
        return parent, child[(len(parent) + 1):]
    return parent, ""

def ischild(parent, child):
    if len(parent) <= len(child):
        return (parent == child[:len(parent)])
    return False