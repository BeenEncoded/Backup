import os, shutil, io

from errors import *

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
        self.current = next(self.iter)
        return self._copy_fsobject(self.current, self._destinations)
    
    def getCurrentPath(self):
        return self.current

    # copies a filesystem object
    # errors are returned as an array of exceptions
    # Returns:
    # [[bool: success, str: failure reason]]
    # None if nothing was copied at all.  This can happen if the predicate returns false, or
    #      No destinations are specified.
    def _copy_fsobject(self, source_path, destination_folders):
        #first if the predicate is set, filter our destinations so that we are only going 
        #to copy what we want.
        if self._predicate != None:
            tempdlist = []
            for x in destination_folders:
                if self._predicate(source_path, os.path.join(x, split_path(self._source, source_path)[1])):
                    tempdlist.append(x)
            destination_folders = tempdlist
        
        #return if we aren't going to copy anything.
        if len(destination_folders) == 0:
            return None

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
                        operation_results.append(CopyPathError(r"""_copy_fsobject: on attempt of removing a destination
                        target path, I could not determine if it was a folder or a file.""", 
                        errors=[self._source, source_path, destination]))
                        continue
            if os.path.isfile(source_path):
                results = self._copy_file(source_path, new_dests)
                for r in results:
                    if r[0] == False:
                        operation_results.append([False, [IncompleteCopyError("Incomplete copy operation", r[1])]])
            if os.path.isdir(source_path):
                r = self._copy_folder(source_path, new_dests)
                for result in r:
                    if not result[0]:
                        operation_results.append([False, [CopyFolderError("Unable to copy folder!", [result[1]])]])
        else:
            operation_results.append([False, [r"""Could not copy path because it was not a file or a folder!""", self._source, source_path]])
        return operation_results
    
    #Copies a file from source, to destination.
    #If the file exists at the destination it is overwritten.
    #
    # Returns: an array containing [bool: success, str: failure reason] that is the length
    # of the number of destinations.  Each element represents one of the copy operations 
    # that took place.
    def _copy_file(self, source, destinations=[]):
        if (source is None) or (destinations is None):
            return [[False, "one of the arguments to the function is None!"]]
        if (isinstance(destinations, list) == False) and (isinstance(destinations, str) == False):
            return [[False, "destinations argument is not a list or a string!"]]
        if os.path.isfile(source) == False:
            return [[False, "The source path argument is not a file!"]]
        for destination in destinations:
            if os.path.basename(source) != os.path.basename(destination):
                return [[False, ("The path arguments don't look right...  Here they are: \n" + source + "\n" + destination)]]
        if destinations is str:
            destinations = [destinations]
        
        #create results to store the results of the operation and 
        #initialize it to nothing.
        results = []
        for x in range(0, len(destinations)):
            results.append([False, "Nothing has been done yet."])

        #perform the copy operation.
        with open(source, 'rb') as sourcefile:
            #here we have a list of destination streams:
            dest_files = []
            for destination in destinations:
                dest_files.append(open(destination, 'wb'))
            
            while True:
                #read once from the source, and write that data to each destination stream.
                #this should ease the stress of the operation on the drive.
                data = sourcefile.read()
                if len(data) == 0:
                    break  # <-- at EOF

                #Attempt to write the read data to each target destination:
                for x in range(0, len(dest_files)):
                    if dest_files[x].write(data) == len(data):
                        results[x][0] = True
                        results[x][1] = "A write operation succeeded."
                    else:
                        results[x][0] = False
                        results[x][1] = ("Failed to write all the data to the destination file: " + destinations[x])
            
            #the write operations are complete.  Close all the destination
            # streams:
            for f in dest_files:
                f.close()
            
            #cleanup results information:
            for result in results:
                if result[0] == True:
                    result[1] = ""
        #now we need to copy over all the attributes:
        for x in range(0, len(destinations)):
            if os.path.isfile(destinations[x]):
                shutil.copystat(source, destinations[x])
        return results
    
    def _copy_folder(self, source, destinations=[]):
        results = []
        for x in range(0, len(destinations)):
            results.append([False, "Nothing was done."])
        if isinstance(destinations, str):
            destinations = [destinations]
        for x in range(0, len(destinations)):
            if destinations[x] != source:
                if not os.path.exists(destinations[x]):
                    os.mkdir(destinations[x])
                results[x][0] = os.path.exists(destinations[x])
                if results[x][0]:
                    shutil.copystat(source, destinations[x], follow_symlinks=False)
                    results[x][1] = ""
                else:
                    results[x][1] = "Could not mkdir!"
            else:
                results[x] = [False, "Destination is the source!"]
        return results

    @staticmethod
    def resultstr(error):
        '''
        Takes a result from an iteration and formats it for 
        nice display.  Returns a string that can be printed.
        '''
        disp = ""
        if error[0]:
            disp += "Copy success.\n"
        else:
            disp += ("Copy failed!" + os.linesep)
            if isinstance(error[1], list):
                for element in error:
                    disp += (str(element) + os.linesep)
            elif isinstance(error[1], Exception):
                disp += (str(error[1]) + os.linesep + "Errors:  " + str([err for err in error[1].errors]) + os.linesep)
            else:
                disp += (str(error[1]) + os.linesep)
        return disp

class copypredicate:
    @staticmethod
    def if_source_was_modified_more_recently(source, destination=""):
        if os.path.exists(source) and os.path.exists(destination):
            return os.path.getmtime(source) > os.path.getmtime(destination)
        return True

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