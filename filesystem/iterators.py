import os

class CopyIterator:
    def __init__(self, root_path):
        self.iter = os.walk(root_path)
    
    def __iter__(self):
        return self
    
    def __next__(self):
        return next(self.iter)[0]