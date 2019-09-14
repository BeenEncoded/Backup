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
    def __init__(self, root_path):
        self.iter = recursive(root_path)

    def __iter__(self):
        return self
    
    def __next__(self):
        return next(self.iter)