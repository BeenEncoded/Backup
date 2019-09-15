import os

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
        if (os.path.isfolder(root_path) != True):
            raise NotADirectoryError("recursivecopy: root_path argument not a folder")
        if isinstance(destination_folders, list) != True:
            raise AttributeError("recursivecopy: destination_folders is not an array!")
        for path in destination_folders:
            if os.path.isfolder(path) == False:
                raise NotADirectoryError("recursivecopy: one of the destination folders passed to the \
iterator is not a valid folder!")

        self.iter = recursive(root_path)

    def __iter__(self):
        return self
    
    def __next__(self):
        self.current = next(self.iter)

# /c/abc
# /c/abc/abc1/bac3
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