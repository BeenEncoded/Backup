

class CopyPathError(Exception):
    def __init__(self, message, errors = []):
        super(CopyPathError, self).__init__(message)
        self.errors = errors

class IncompleteCopyError(Exception):
    def __init__(self, message, errors):
        super(IncompleteCopyError, self).__init__(message)
        self.errors = errors

class CopyFolderError(Exception):
    def __init__(self, message, errors):
        super(CopyFolderError, self).__init__(message)
        self.errors = errors

class WrongArgumentTypeError(Exception):
    def __init__(self, message, errors):
        super(CopyFolderError, self).__init__(message)
        self.errors = errors