

class CopyPathError(Exception):
    def __init__(self, message, errors = []):
        super(CopyPathError, self).__init__(message)
        self.errors = errors
    
    def __str__(self):
        return "CopyPathError(\"" + self.message + "\"  errors: " + str(self.errors) + ")"

class IncompleteCopyError(Exception):
    def __init__(self, message, errors):
        super(IncompleteCopyError, self).__init__(message)
        self.errors = errors
    
    def __str__(self):
        return "IncompleteCopyError(\"" + self.message + "\"  errors: " + str(self.errors) + ")"

class CopyFolderError(Exception):
    def __init__(self, message, errors):
        super(CopyFolderError, self).__init__(message)
        self.errors = errors
    
    def __str__(self):
        return "CopyFolderError(\"" + self.message + "\"  errors: " + str(self.errors) + ")"

class WrongArgumentTypeError(Exception):
    def __init__(self, message, errors):
        super(CopyFolderError, self).__init__(message)
        self.errors = errors

class BackupProfileNotFoundError(Exception):
    def __init__(self, message, errors):
        super(CopyFolderError, self).__init__(message)
        self.errors = errors
    
    def __str__(self):
        return "BackupProfileNotFoundError: " + self.message