# Recursive Filesystem Iterators (filesystem.iterator) makes it easy to recursively
#   iterate over a directory tree.
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

import os, shutil, io, typing, logging

logger = logging.getLogger("filesystem.iterator")

# This is basically just a wrapper class around os.walk, but it actually
# iterates over everything.
class recursive:
    '''
    A recursive directory iterator, the first element of which is the root_path
    being iterated over.
    '''
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
    '''
    A recursive directory iterator that also copies the elements being iterated.
    It returns a [[bool: success, any_type: failure_reason]] upon __next__(), which represents
    an array of results.  These results correspond to each copy operation, since
    recursivecopy can also copy to multiple destinations.  When copying to
    multiple destinations recursivecopy only reads the source a single time.

    It is expected that if /a/b/c is copied into /z, then the result should
    be /z/c/*, where * represents the contents of /a/b/c.

    An optional argument <code>predicate(str: source_path, str: source_destination)</code> can 
    be used to define the condition under which a copy operation proceeds.
    By applying a predicate you can do things like skip files that have not 
    changed, or only copy a specific type of file.

    Occassionally a path will be skipped.  This can happend when the predicate returns False or
    when no destinations are specified.  In this case the iterator will return None.
    '''

    def __init__(self, root_path, destination_folders, predicate=None):
        '''
        root_path: the folder you want to copy.

        destination_folders: a list of folders (or a string representing the 
        path to a single destination)
        '''
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
                    raise NotADirectoryError("""recursivecopy: one of the destination folders passed to the 
                    iterator is not a valid folder!""")
                if path == root_path:
                    raise shutil.SameFileError("""recursivecopy: one of the 
                    destinations given is the same as the source.""")
        self._source = root_path
        self._destinations = [os.path.join(d, os.path.basename(self._source)) for d in destination_folders]
        self.iter = recursive(self._source)
        self._predicate = predicate

    def __iter__(self):
        return self
    
    def __next__(self):
        if len(self._destinations) == 0:
            raise StopIteration()
        self.current = next(self.iter)
        return self._copy_fsobject(self.current, self._destinations)
    
    def getCurrentPath(self):
        return self.current

    # copies a filesystem object
    # errors are returned as an array of exceptions
    # Returns:
    # [UnexpectedError]
    # None if nothing was copied at all.  This can happen if the predicate returns false, or
    #      No destinations are specified.
    def _copy_fsobject(self, source_path: str, destination_folders: list):
        if len(destination_folders) == 0:
            return [recursivecopy.NothingWasDoneError("Destination folders had a length of zero.  Returned from \
                copy immediately.")]
        #first if the predicate is set, filter our destinations so that we are only going 
        #to copy what we want.
        if self._predicate != None:
            tempdlist = []
            for x in destination_folders:
                if self._predicate(source_path, os.path.join(x, split_path(self._source, source_path)[1])):
                    tempdlist.append(x)

            #purely for logging purposes, we gather information on what paths were removed from the 
            #list of destinations and log that.  That's good info... yum yum
            excluded = [ex for ex in destination_folders if ex not in tempdlist]
            if len(excluded) > 0:
                logger.warning("predicate ruled out operations for source[\"" + source_path + "\"] to " + \
                    "destinations " + str(excluded))
            
            destination_folders = tempdlist
        
        #return if we aren't going to copy anything.
        if len(destination_folders) == 0:
            return []

        new_dests = destination_folders
        success = False
        removeddest = False
        operation_results = []
        number_of_copied_paths = 0

        if source_path != self._source:
            new_dests = [os.path.join(d, split_path(self._source, source_path)[1]) for d in destination_folders]
        if os.path.isdir(source_path) or os.path.isfile(source_path):

            # Removing the destination targets if they exist.
            for destination in new_dests:
                if os.path.exists(destination):
                    if os.path.isfile(destination):
                        os.remove(destination)
                        removeddest = (os.path.exists(destination) == False)
                    elif os.path.isdir(destination):
                        if os.listdir(destination) == []:
                            os.rmdir(destination)
                            removeddest = (os.path.exists(destination) == False)
                    else:
                        operation_results.append(recursivecopy.PathNotWorkingError(message=r"""_copy_fsobject: on attempt of removing a destination
                        target path, I could not determine if it was a folder or a file.""", path=destination))
                        continue
            if os.path.isfile(source_path):
                results = self._copy_file(source_path, new_dests)
                for r in results:
                    if not r[0]:
                        operation_results.append(r[1])
            if os.path.isdir(source_path):
                r = self._copy_folder(source_path, new_dests)
                for result in r:
                    if not result[0]:
                        operation_results.append(result[1])
        else:
            operation_results.append(recursivecopy.PathNotWorkingError("Could not copy path because it was not a file or a folder!",  path=source_path))
        return operation_results
    
    #Copies a file from source, to destination.
    #If the file exists at the destination it is overwritten.
    #
    # Returns: an array containing [bool: success, recursivecopy.UnexpectedError: error data] that is the length
    # of the number of destinations.  Each element represents one of the copy operations 
    # that took place.
    def _copy_file(self, source: str, destinations: list=[]):
        if isinstance(destinations, str):
            destinations = [destinations]
        if not os.path.isfile(source):
            logger.warning("recursivecopy._copy_file: [\"" + source + "\"] path is not a file.")
            return [[False, PathNotWorkingError("The source path argument is not a file!", source)]]
        for destination in destinations:
            if os.path.basename(source) != os.path.basename(destination):
                logger.warning("recursivecopy._copy_file: Arguments invalid: " + \
                    "source: [\"" + source + "\"] destiations: [\"" + destination + "\"]")
                return [[False, PathNotWorkingError(("The path arguments don't look right...  Here they are: \n" + source + "\n" + destination), destination)]]
        
        #create results to store the results of the operation and 
        #initialize it to nothing.
        results = []
        for x in range(0, len(destinations)):
            results.append([False, recursivecopy.NothingWasDoneError()])

        #open the source file
        try:
            sourcefile = open(source, 'rb')
        except PermissionError as e:
            logger.exception("recursivecopy._copy_file")
            for r in results:
                r[0] = False
                r[1] = recursivecopy.CantOpenFileError("Source: Permission denied.", exception=e, filename=source)
            return results

        #perform the copy operation.
        #here we have a list of destination streams:
        dest_files = []
        for x in range(0, len(destinations)):
            try:
                dest_files.append(open(destinations[x], 'wb'))
            except FileNotFoundError as e:
                logger.exception("recursivecopy._copy_file")
                results[x][0] = False
                results[x][1] = recursivecopy.UnexpectedError("File not found.", e)
            except OSError as e:
                logger.exception("recursivecopy._copy_file")
                results[x][0] = False
                results[x][1] = recursivecopy.CantOpenFileError("Error on opening destination path.", \
                    exception=e, filename=destinations[x])
        
        #perform the writing operation.
        haveread = False
        logger.info("Copying [\"" + source + "\"] -> " + str(destinations))
        while len(dest_files) > 0:
            #read once from the source, and write that data to each destination stream.
            #this should ease the stress of the operation on the drive.

            try:
                data = sourcefile.read()
            except PermissionError as e:
                logger.exception("PermissionError; source=\"" + source + "\"")
                for result in results:
                    result[0] = False
                    result[1] = recursivecopy.UnexpectedError(("Error reading source: [\"" + \
                        source + "\"]"), e)
                break
            if len(data) == 0:
                break  # <-- at EOF

            if not haveread:
                haveread = True

            #Attempt to write the read data to each target destination:
            for x in range(0, len(dest_files)):
                if dest_files[x].write(data) == len(data):
                    results[x][0] = True
                    results[x][1] = None
                else:
                    logger.error("Failed to write all the data.  Length of data: " + str(len(data)) + ", " + \
                        "destination: [\"" + destinations[x] + "\"]  Source: [\"" + source + "\"]")
                    results[x][0] = False
                    results[x][1] = recursivecopy.PathOperationFailedError("Failed to write all the data to the destination file!", path=destinations[x])
        
        # here, we address the issue where the length of data read was zero on the first read.
        # this can mean a couple things, but we add this primarily to address files with nothing
        # in them.
        # We assume that in this case if the file being opened was successful, so was the write(s)
        if not haveread and (len(dest_files) > 0):
            for r in results:
                #make sure that the error wasn't overridden by an exception during
                #opening the destination filehandles
                if type(r[1]) is recursivecopy.NothingWasDoneError:
                    r[0] = True
                    r[1] = None

        #the write operations are complete.  Close all the destination
        # streams:
        for f in dest_files:
            f.close()
        sourcefile.close()
        
        logger.debug("Copying stat info for source [\"" + source + "\"] to destinations: " + str(destinations))
        #now we need to copy over all the attributes:
        for x in range(0, len(destinations)):
            if os.path.isfile(destinations[x]):
                shutil.copystat(source, destinations[x])
        return results
    
    def _copy_folder(self, source: str, destinations: list=[]):
        results = []
        for x in range(0, len(destinations)):
            results.append([False, recursivecopy.NothingWasDoneError()])
        if isinstance(destinations, str):
            destinations = [destinations]
        for x in range(0, len(destinations)):
            if destinations[x] != source:
                if not os.path.exists(destinations[x]):
                    try:
                        os.mkdir(destinations[x])
                    except OSError as e:
                        logger.exception("recursivecopy._copy_folder")
                        results[x][0] = False
                        results[x][1] = recursivecopy.UnexpectedError("Can't make directory!", exception=e)
                        continue
                results[x][0] = os.path.exists(destinations[x])
                if results[x][0]:
                    shutil.copystat(source, destinations[x], follow_symlinks=False)
                    results[x][1] = None
                else:
                    logger.warning("destination [\"" + destinations[x] + "\"] does not exist even after an attempt to create it.")
                    results[x][1] = recursivecopy.PathOperationFailedError(message="Could not mkdir!", path=destinations[x])
            else:
                logger.error("recursivecopy._copy_folder: arguments invalid; SOURCE == DESTINATIONS   source: [\"" + \
                    source + "\"]  destinations: " + str(destinations))
                results[x] = [False, recursivecopy.WrongArgumentValueError("Destination is the source!", argvalue=destinations[x], expectedvalue=("Anything but " + source))]
        return results
    
    class UnexpectedError:
        '''
        An unexpected error...  This is no an exception class.  It represents data returned after an operation
        fails with unexpected results.
        '''
        def __init__(self, message: str="No message set.", exception: Exception=None):
            self.message = message
            self.exception = exception
        
        def __str__(self) -> str:
                return self.message + os.linesep + str(self.exception)

    class PathNotWorkingError(UnexpectedError):
        '''
        This error refers to whenever a path registers as not existing, or not referring to
        an expected object (for instance, it's not a folder even though it was expected to be)
        '''
        def __init__(self, message: str="No message set", path: str=""):
            super(recursivecopy.PathNotWorkingError, self).__init__(message, None)
            self.path = path
        
        def __str__(self) -> str:
            return self.message + os.linesep + "Path: " + self.path

    class PathOperationFailedError(UnexpectedError):
        def __init__(self, message: str="No Message Set", exception: Exception=None, path: str=None):
            super(recursivecopy.PathOperationFailedError, self).__init__(message, exception)
            self.path=path
        
        def __str__(self) -> str:
            return self.message + os.linesep + self.path + os.linesep + str(self.exception)

    class WrongArgumentTypeError(UnexpectedError):
        def __init__(self, message: str="No message set.", argtype: type=type(None), expectedtype: type=type(None)):
            super(recursivecopy.WrongArgumentTypeError, self).__init__(message, None)
            self.argument_type = argtype
            self.expected_type = expectedtype
        
        def __str__(self) -> str:
                return self.message + os.linesep + "Expected type " + str(self.expected_type) + " but instead got " + str(self.argument_type)

    class WrongArgumentValueError(UnexpectedError):
        def __init__(self, message: str=None, argvalue=None, expectedvalue=None):
            super(recursivecopy.WrongArgumentValueError, self).__init__(message, None)
            self.argument = argvalue
            self.expected_argument = expectedvalue

        def __str__(self) -> str:
                return self.message + os.linesep + "Expected " + str(self.argument) + " but got " + str(self.expected_argument)

    class CantOpenFileError(UnexpectedError):
        def __init__(self, message: str, exception: Exception=None, filename: str=""):
            super(recursivecopy.CantOpenFileError, self).__init__(message, exception)
            self.filename = filename
        
        def __str__(self):
                return "Exception: " + str(self.exception) + os.linesep + "File: " + self.filename

    class NothingWasDoneError(UnexpectedError):
        def __init__(self, message: str=None, exception: Exception=None):
            super(recursivecopy.NothingWasDoneError, self).__init__("Nothing was done.", None)
        
        def __str__(self) -> str:
                return self.message

class copypredicate:
    @staticmethod
    def if_source_was_modified_more_recently(source: str="", destination: str="") -> bool:
        if os.path.exists(destination):
            return os.path.getmtime(source) > os.path.getmtime(destination)
        return True

# /c/abc
# /c/abc/abc1/bac3
#  V 
# ['/c/abc', 'abc1/bac3']
def split_path(parent: str, child: str) -> typing.Tuple[str, str]:
    if os.path.isabs(parent) == False:
        parent = os.path.abspath(parent)
    if os.path.isabs(child) == False:
        child = os.path.abspath(child)
    if ischild(parent, child):
        return parent, child[(len(parent) + 1):]
    return parent, ""

def ischild(parent: str, child: str) -> bool:
    if len(parent) <= len(child):
        return (parent == child[:len(parent)])
    return False