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

from __future__ import annotations
import os
import shutil
import typing
import logging
import enum
import re
import sys
import io
from typing import Tuple

logger = logging.getLogger("filesystem.iterator")


class OsType(enum.IntFlag):
    '''
    Operating system support bitmask.
    '''
    NO_SUPPORT = 0
    WINDOWS = enum.auto()
    LINUX = enum.auto()
    OSX = enum.auto()

def current_os() -> OsType:
    '''
    Returns the OsType corresponding to the platform currently being used.
    '''
    systems = { #expressions paired with each platform type
        r"([Ww][Ii][Nn])": OsType.WINDOWS,
        r"([Ll]inux)": OsType.LINUX,
        r"([Dd]arwin)|(osx)|(OSX)": OsType.OSX
    }
    plat = sys.platform

    for expression in systems:
        if re.match(expression, plat):
            return systems[expression]
    return OsType.NO_SUPPORT


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
        if not self.returned_parent:
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
    It returns a [recursivecopy.UnexpectedError] upon __next__(), which represents
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
    def __init__(self, root_path, destination_folders, predicate=None, newdestname: str=None):
        '''
        Initializes the copy iterator.

        ### Paraeters
            :param root_path (string):                 the folder you want to copy.  Also called the "source" folder.
            :param destination_folders (list<string>): a list of destination folders (or a string representing the 
                                                       path to a single destination)
            :param predicate:                          A function with the signature
                                                       predicate(str: sourcePath, str: sourceDestination)
        
        ### Exceptions
            :raises AttributeError:              when an argument passed does not conform to what was expected.
            :raises NotADirectoryError:          When an argument passed is not a directory.  All arguments are expected to be directories.
            :raises ValueError:                  When the typing of an argument to this function is not an array of strings or a snigle string.
            :raises shutil.SameFileError:        When any of the arguments are duplicates.

        '''
        if (root_path is None) or (destination_folders is None):
            raise AttributeError("recursivecopy: invalid arguments")
        if not os.path.isdir(root_path):
            raise NotADirectoryError(
                "recursivecopy: source directory ('root_path') argument not a folder")
        if not isinstance(destination_folders, list) and not isinstance(destination_folders, str):
            raise ValueError(
                "recursivecopy: destination_folders is not an array or a string!")
        if isinstance(destination_folders, str):
            destination_folders = [destination_folders]
        if isinstance(destination_folders, list):
            for path in destination_folders:
                if not os.path.isdir(path):
                    raise NotADirectoryError("""recursivecopy: one of the destination folders passed to the 
                    iterator is not a valid folder!""")
                if path == root_path:
                    raise shutil.SameFileError("""recursivecopy: one of the 
                    destinations given is the same as the source.""")
                if ischild(root_path, path) or ischild(path, root_path):
                    raise shutil.SameFileError("""recursivecopy: one of the 
                    destinations given is a path under the source.""")
        self._source = root_path
        self._destinations = [os.path.join(d, os.path.basename(self._source) if newdestname is None else newdestname) for d in destination_folders]
        self.iter = recursive(self._source)
        self._predicate = predicate

        # log the type of predicate used
        if predicate is not None:
            logger.warning("conditional predicate passed to recursivecopy: " + self._predicate.__qualname__)

    def __iter__(self):
        return self

    def __next__(self):
        if len(self._destinations) == 0:
            raise StopIteration()
        self.current = next(self.iter)
        return self._copy_fsobject(self.current, self._destinations)

    def getCurrentPath(self):
        '''
        # getCurrentPath
            :returns: the current path being iterated over.  Set after a call to __next__
        '''
        return self.current

    # copies a filesystem object
    # errors are returned as an array of errors.
    # Returns:
    # [UnexpectedError]
    def _copy_fsobject(self, source_path: str, destination_folders: list):
        '''
        ### _copy_fsobject(self, source_path: str, destination_folders: list) -> List[recursivecopy.UnexpectedError]
            :param source_path: A fully qualified path to the source
            :param List[destination_folders]: A list of fully qualified paths representing destination directories that the source will be copied into.

            :returns List[recursivecopy.UnexpectedError]: A list of any errors that occured during the operation(s).
        '''
        #      Here be dragons:
        #                                            _   __,----'~~~~~~~~~`-----.__
        #                                     .  .    `//====-              ____,-'~`
        #                     -.            \_|// .   /||\\  `~~~~`---.___./
        #               ______-==.       _-~o  `\/    |||  \\           _,'`
        #         __,--'   ,=='||\=_    ;_,_,/ _-'|-   |`\   \\        ,'
        #      _-'      ,='    | \\`.    '',/~7  /-   /  ||   `\.     /
        #    .'       ,'       |  \\  \_  "  /  /-   /   ||      \   /
        #   / _____  /         |     \\.`-_/  /|- _/   ,||       \ /
        #  ,-'     `-|--'~~`--_ \     `==-/  `| \'--===-'       _/`
        #            '         `-|      /|    )-'\~'      _,--"'
        #                        '-~^\_/ |    |   `\_   ,^             /\
        #                             /  \     \__   \/~               `\__
        #                         _,-' _/'\ ,-'~____-'`-/                 ``===\
        #                        ((->/'    \|||' `.     `\.  ,                _||
        #          ./                       \_     `\      `~---|__i__i__\--~'_/
        #         <_n_                     __-^-_    `)  \-.______________,-~'
        #          `B'\)                  ///,-'~`__--^-  |-------~~~~^'
        #          /^>                           ///,--~`-\
        #         `  `                                       
        if len(destination_folders) == 0:
            return [recursivecopy.NothingWasDoneError("Destination folders had a length of zero.  Returned from \
                copy immediately.")]
        
        # first if the predicate is set, filter our destinations so that we are only going
        # to copy what we want.
        if self._predicate is not None:
            tempdlist = [x for x in destination_folders if self._predicate(source_path, 
                os.path.join(x, split_path(self._source, source_path)[1]))]
            
            destination_folders = tempdlist #we'll need this (tempdlist) if we need to log what we are not backup up

            # purely for logging purposes, we gather information on what paths were removed from the
            # list of destinations and log that.  That's good info... yum yum
            if logging.getLogger().level == logging.DEBUG: # do this only if the log level is debug
                excluded = [ex for ex in destination_folders if ex not in tempdlist]
                if len(excluded) > 0:
                    logger.debug(self._predicate.__qualname__ +
                                " ruled out operations for source[\"" + source_path + "\"] to " +
                                "destinations " + str(excluded))

        # return if we aren't going to copy anything.
        if len(destination_folders) == 0:
            return []

        new_dests = destination_folders
        operation_results = []

        # we construct the new destination path if the source currently being iterated over is not the same
        # as the root source path.
        if source_path != self._source:
            new_dests = [os.path.join(d, split_path(self._source, source_path)[1]) for d in destination_folders]
        
        #now we make sure that the source path is somthing we are programmed to copy:
        if os.path.isdir(source_path) or os.path.isfile(source_path) or os.path.islink(source_path):

            # Make sure that if the parent directory of our destination doesn't exist, 
            # that we create it and all intermediate directories.
            for dest in new_dests: self._make_parent_folders(dest)
            
            #next copy them.
            if os.path.isfile(source_path) or os.path.islink(source_path):
                operation_results.extend(self._copy_file(source_path, new_dests))
            elif os.path.isdir(source_path):
                operation_results.extend(self._copy_folder(source_path, new_dests))
        else:
            logger.error(f"{self._copy_fsobject.__qualname__}: Source is neither " + 
                f"a file nor a folder.  Source = [\"{source_path}\"]")
            
            operation_results.append(recursivecopy.PathNotWorkingError(
                "Could not copy path because it was not a file or a folder!",  path=source_path))
        
        return operation_results

    # Copies a file from source, to destination.
    # If the file exists at the destination it is overwritten.
    # 
    # Returns: an array containing recursivecopy.UnexpectedErrors that contains
    # all errors that occured.
    def _copy_file(self, source: str, destinations: list = []):
        '''
        ### _copy_file(self, source: str, destinations: list = []) -> [[bool, recursivecopy.UnexpectedError]]
            :param source: the source path.  A fully qualified path.
            :param destinations: fully qualified destinations.  (representing the new filenames)

            :returns [recursivecopy.UnexpectedError]: an array of results.
        '''
        if isinstance(destinations, str):
            destinations = [destinations]
        if not os.path.isfile(source):
            logger.error(f"{recursivecopy._copy_file.__qualname__}: [\"{source}\"] path is not a file.")
            return [recursivecopy.PathNotWorkingError("The source path argument is not a file!", source)]
        
        checkresult = self._check_dest_rectified(source, destinations)
        if len(checkresult) > 0:
            logger.error(f"{recursivecopy._copy_file.__qualname__}: a check for destination rectification to the new path's destination failed.")
            return checkresult


        #----------------------------
        # perform the copy operation.
        #----------------------------
        do_continue = False
        
        # open the source file
        ophandle, opsuccess, opresult = self._open_file(source, 'rb')
        sourcefile = None
        if not opsuccess:
            return [opresult]
        sourcefile = ophandle

        #Open all the destination files.
        dest_files = []
        for dest in destinations:
            try:
                dhandle, dsuccess, dresult = self._open_file(dest, 'wb')
                dest_files.append(tuple(((dhandle if dsuccess else None), (None if dsuccess else dresult), dest)))
                if dsuccess:
                    do_continue = True #set the write loop to run if we have a handle to write to
            except:
                for d,_,_ in dest_files:
                    if d is not None:
                        d.close()
                sourcefile.close()
                raise

        #dest_files -> [tuple(fileHandle, error, pathstring)]

        # perform the writing operation.
        haveread = False
        logger.debug("Copying [\"%s\"] -> %s", source, destinations)

        sourcesize = os.stat(source).st_size
        read_blocksize = ((2**20) * 10) # 10 megabytes
        if sourcesize > (2**30): #greater than 1GB
            logger.warning("Largefile, will take some time.")

        while do_continue:
            # read once from the source, and write that data to each destination stream.
            # this should ease the stress of the operation on the source drive.

            try:
                rateof, data, rerror = self._read_file(sourcefile, read_blocksize)
                if rerror is not None:
                    logger.error("READ ERROR OCCURRED!")
                    for d,_,_ in dest_files:
                        if d is not None:
                            d.close() #sourcefile is already closed by _read_file

                    #return the error(s).  We can't do anything now.
                    return ([error for _,error,_ in dest_files if error is not None] + [rerror])

                if rateof:
                    break
                if not haveread:
                    haveread = True
            except: # noqa E722
                #the sourcefile will be closed if an exception is raised from _read_file
                for d,_,_ in dest_files:
                    if d is not None:
                        d.close()
                raise

            # Attempt to write the read data to each target destination:
            for dest in dest_files:
                if dest[0] is not None:
                    if not dest[0].closed:
                        try:
                            werror = self._write_file(dest[0], data)
                            if werror is not None:
                                werror.path = dest[2] #set the error's path vairable so we have that information
                                dest[1] = werror
                                dest[0].close()
                        except: # noqa E722
                            for d,_,_ in dest_files:
                                if d is not None:
                                    d.close()
                            sourcefile.close()
                            raise

            #if we have a large file, log the progress
            if (sourcesize > 2**30) and ((int((sourcefile.tell() / sourcesize) * 100) % 10) == 0):
                logger.warning("Largefile copy: %" + str((sourcefile.tell() / sourcesize) * 100))

            # if for any reason all our destination streams were closed, 
            # we need to break out of the write operation and halt the process.
            do_continue = False
            for handle ,error,_ in dest_files:
                if error is None and handle is not None:
                    if not handle.closed:
                        do_continue = True

        # the write operations are complete.  Close all the destination
        # streams:
        for dest in dest_files:
            if dest[0] is not None:
                dest[0].close()

        sourcefile.close()

        logger.debug(f"Copying stat info for source [\"{source}\"] to destinations: {str(destinations)}")
        # now we need to copy over all the attributes:
        for x in range(0, len(destinations)):
            if os.path.isfile(destinations[x]):
                try:
                    shutil.copystat(source, destinations[x], follow_symlinks=False)
                except: # noqa E722
                    logger.exception(f"\n\n\n{recursivecopy._copy_file.__qualname__}: UNHANDLED EXCEPTION!\n\n\n")
                    raise
        return [error for _,error,_ in dest_files if error is not None]

    def _copy_folder(self, source: str, destinations: list = []):
        '''
        ### _copy_folder(self, source: str, destinations: list = []): -> [[bool, recursivecopy.UnexpectedError]]
            :param source: the source path.  A fully qualified path.
            :param destinations: fully qualified destinations.  (representing the new filenames)

            :returns [[bool, recursivecopy.UnexpectedError]]: an array of results.
        '''

        results = []
        if isinstance(destinations, str):
            destinations = [destinations]
        for dest in destinations:
            if dest != source:
                if not os.path.exists(dest):
                    try:
                        os.mkdir(dest)
                    except FileNotFoundError:
                        continue
                    except OSError as e:
                        logger.exception("recursivecopy._copy_folder")
                        results.append(recursivecopy.UnexpectedError("Can't make directory!", exception=e))
                        continue
                    if not os.path.exists(dest):
                        logger.warning(f"destination [\"{dest}\"] does not exist even after an attempt to create it.")
                        results.append(recursivecopy.PathOperationFailedError(message="Could not mkdir!", path=dest))
            else:
                logger.error(f"{recursivecopy._copy_folder.__qualname__}: arguments invalid; SOURCE == DESTINATION   " + 
                    f"source: [\"{source}\"]  destinations: {str(destinations)}")
                
                results.append(recursivecopy.WrongArgumentValueError(
                    "Destination is the source!", argvalue=dest, expectedvalue=("Anything but " + source)))
        return results

    def _check_dest_rectified(self, source: str="", dests: list=[]) -> list:
        '''
        ### _check_dest_rectified(self, source: str="", dests: list=[]) -> bool
        performs a check on the source a destinations.  Makes sure that destinations 
        represents a fully qualified destination path under the destination root.

            :param source: The source path.  Must be a fully qualified path.
            :param dests:  The destinations.  Must respresent fully qualified destinations.
        
            :returns [[bool, resursivecopy.UnexpectedError]]: A list of errors if it did not succeed.
        '''

        #here we expect the destinations to be rectified.  What this means
        #is that /a/b/c -> /d yeilds the following destination /d/c which
        #is a folder or file under the root destination folder (/d, in this case)
        results = []
        for destination in dests:
            if os.path.basename(source) != os.path.basename(destination):
                logger.warning("recursivecopy._copy_file: Arguments invalid: " +
                               "source: [\"" + source + "\"] destiations: [\"" + destination + "\"]")
                results.append(recursivecopy.PathNotWorkingError(("The path arguments don't look right...  Here they are: \n" + source + "\n" + destination), destination))
        
        #return the results if there was a problem, otherwise just return None
        return results

    def _open_file(self, path: str, access: str='wrb') -> Tuple[io.IOBase, bool, recursivecopy.UnexpectedError]:
        '''
        ### _open_file(self, path: str, access: str='wrb') -> tuple
            :param path: a fully qualified path to open.
            :param access: the type of access.  Same as the read/write string for standard open()

            :returns (handle, bool, recursivecopy.UnexpectedError): whether or not the operation succeeded, and
                                                            an error if there was one.
        '''
        handle = None
        success = False
        result = None
        try:
            handle = open(path, access)
            success = True
        except FileNotFoundError as e:
            #on windows this exception is thrown when a pathtoolong error
            #is encountered.  It's generally just a nuisance, but we need to make
            #sure that we don't cause problems on mac or linux:
            if current_os() == OsType.WINDOWS:
                #on windows, we will ignore this if it's actually a path-too-long
                if len(path) < 256:
                    logger.exception(f"{recursivecopy._open_file.__qualname__}")
                    result = recursivecopy.UnexpectedError("File not found.", e)
                else:
                    result = recursivecopy.PathTooLongError(e=e, path=path)
                    logger.info(str(result))
            else: #for mac and linux, we simply revert to reporting the error (they don't have path-length limits):
                logger.exception(f"{recursivecopy._open_file.__qualname__}")
                result = recursivecopy.UnexpectedError(f"File not found. (\"{path}\")", e)
        except PermissionError as e:
            logger.exception(f"{recursivecopy._open_file.__qualname__}")
            result = recursivecopy.AccessDeniedError(f"{recursivecopy._open_file.__qualname__}: Failed to open \"{path}\"!", e=e, path=path)
        except OSError as e:
            logger.exception(f"{recursivecopy._open_file.__qualname__}")
            result = recursivecopy.CantOpenFileError(f"Error on opening \"{path}\".", exception=e, filename=path)
        except: # noqa E722
            #we should have caught everything, but in case we havn't, we 
            #need to know about it.  Log it and pass the exception on.
            logger.exception(f"\n\n\nUNHANDLED EXCEPTION: {recursivecopy._open_file.__qualname__}\n\n\n")
            raise
        finally:
            if not success and handle is not None:
                handle.close()
                handle = None
        return handle, success, result

    def _read_file(self, filehandle: io.BytesIO=None, blocksize:int = -1):
        '''
        ### _read_file(self, filehandle: HANDLE, blocksize: int = -1)
        Reads a block from the file.  File must have been open with 'rb'.

            :param filehandle: the handle to read
            :param blocksize:  the number of bytes to read from the file.  if unspecified
                               reads the entire file.

            :returns (bool, bytes, error): true if the file is at end.  The bytes read.  An error if there was one, or None.
        '''
        if filehandle is None:
            raise Exception(f"{recursivecopy._read_file.__qualname__}: filehandle is none!")
        success = False

        ateof = False
        data = b''
        error = None
        try:
            data = filehandle.read(blocksize)
            success = True
        except PermissionError as e:
            logger.exception()
            error = recursivecopy.AccessDeniedError(f"Permission error encountered while reading from source \"{self.current}\"", e, self.current)
            return ateof, data, error
        except OSError as e:
            if current_os() is OsType.WINDOWS:
                if e.errno == 22 and e.strerror == "Invalid argument":
                    logger.warning(
                        "Attempted to read a file that is probably%s",
                        " in the cloud on windows.  Run OneDrive to fix this.")
                    error = recursivecopy.CantOpenFileError("Attempted to read a file that is probably " +
                        "in the cloud on windows.  Run OneDrive to fix this.", e)
                    return ateof, data, error
            logger.exception("Operating System Error... This should not happen!")
            raise
        except: # noqa E722
            #we should have caught everything, but in case we havn't, we
            #need to know about it.  Log it and pass the exception on.
            logger.exception(
                "\n\n\nUNHANDLED EXCEPTION: %s\nblocksize=%i\ndata:%s\n\n\n",
                recursivecopy._read_file.__qualname__,
                blocksize,
                data)
            raise
        finally:
            if not success and filehandle is not None:
                filehandle.close()

        ateof = (len(data) == 0)
        return ateof, data, error

    def _write_file(self, filehandle, data):
        '''
        ### _write_file(self, filehandle, blocksize: int = -1):
        Writes a block to the file.  File must have been open with 'wb'.
        So far I know of no exceptions that can be raised from this operation, however
        a log is in place for such an occurance.

            :param filehandle: the handle to write to.
            :param data:      bytes to write to the file.
            
            :returns (bool, recursivecopy.FileWriteFailure): True if the write operation succeeded.
        '''
        written = 0
        success = False
        try:
            written = filehandle.write(data)
            success = True
        except BlockingIOError:
            logger.exception(f"\n\n\n{recursivecopy._write_file.__qualname__}: Blocking IO error on write!\n\n\n")
            raise
        except: # noqa E722
            logger.exception(f"\n\n\n{recursivecopy._write_file.__qualname__}:  UNHANDLED EXCEPTION!\n\n\n")
            raise
        finally:
            if not success and filehandle is not None: filehandle.close()
        
        #success currently defined as there being no exception thrown, and
        #all bytes were written.
        if len(data) == written:
            return None
        
        return recursivecopy.FileWriteFailure(message="Failed to write all the bytes!", e=None)

    def _remove(self, path: str):
        '''
        ### _remove(self, path: str) -> recursivecopy.UnexpectedError
        Removes a path.  Refer to documentation of _remove_file and _remove_folder.

            :param path: string representing the filesystem object to delete

            :returns recursivecopy.UnexpectedError: An error if an error occured, or None if successful.
        '''
        logger.debug(f"Deleting path \"{path}\"")
        if os.path.islink(path) or os.path.isfile(path):
            return self._remove_file(path)
        elif os.path.isdir(path):
            return self._remove_folder(path)
        return recursivecopy.PathNotWorkingError(message="Path doesn't register as a symlink, directory, or file!", path=path)

    def _remove_folder(self, path: str):
        '''
        ### _remove_folder(self, path: str) -> recursivecopy.UnexpectedError
        Removes a folder.
            :param path: string representing the path to the folder to be deleted.
            :param predicate(str): a callback that returns true on some given 
                                   condition.  Takes the path parameter as its argument.

            :returns recursivecopy.UnexpectedError: an error if it failed, otherwise None.
        '''
        try:
            os.rmdir(path)
        except FileNotFoundError as e:
            return recursivecopy.PathNotThereError(exception=e, path=path)
        except OSError as e:
            return recursivecopy.DirectoryNotEmptyError(exception=e, path=path)
        except: # noqa E722
            logger.exception(f"\n\n\n{recursivecopy._remove_folder.__qualname__}: UNHANDLED EXCEPTION!\n\n\n")
            raise
        return None

    def _remove_file(self, path: str):
        '''
        ### _remove_file(self, path: str) -> recursivecopy.UnexpectedError
        Removes a file.
            :param path: the path to the file to be removed.
            
            :returns UnexpectedError: An error if an error occured, or None if successful.
        '''
        try:
            os.remove(path)
        except IsADirectoryError:
            #the path is a folder, not a file:
            return self._remove_folder(path)
        except PermissionError as e:
            return recursivecopy.AccessDeniedError(message="Access Denied", e=e, path=path)
        except: # noqa E722
            logger.exception(f"\n\n\n{recursivecopy._remove_file.__qualname__}: UNHANDLED EXCEPTION!\n\n\n")
            raise
        return None

    def _make_parent_folders(self, path: str="") -> bool:
        if len(path) == 0:
            return False

        if not os.path.isabs(path):
            path = os.path.abspath(path)
        folder = os.path.dirname(path)

        if not os.path.isdir(folder):
            try:
                os.makedirs(folder)
            except FileExistsError:
                return True
            except OSError:
                logger.exception("%s: Error creating parent folders.", recursivecopy._make_parent_folders.__qualname__)
                return False
        
        return os.path.isdir(folder)

    # -------------------------------------------------------------------------------------------\
    # Below is a family of errors.  When dealing with system calls (especially                   |
    # calls that deal with asynchronous operations that can result in race conditions)           |
    # a better option to exceptions is returning values and letting the                          |
    # caller deal with the error instead of throwing an exception and breaking the               |
    # call stack.  This is generally more complicated but much more robust.  All uncaught        |
    # exceptions should be programming errors or unrecoverable errors.                           |
    #                                                                                            |
    # Because all errors inherit from UnexpectedError it will be easier to extend its            |
    # functionality in the future by adding things like error codes and the like if we need to.  |
    #                                                                                            |
    # Each error returned by a copy operation inherits from UnexpectedError and implements       |
    # its __str__ function so the user can simply call str() on each error returned to           |
    # tell the user about it.                                                                    |
    # -------------------------------------------------------------------------------------------/
    class UnexpectedError:
        '''
        An unexpected error...  This is not an exception class.  It represents data returned after an operation
        fails with unexpected results.
        '''

        def __init__(self, message: str = "No message set.", exception: Exception = None):
            self.message = message
            self.exception = exception

        def __str__(self) -> str:
            return f"[{recursivecopy.UnexpectedError.__name__}]{self.message}{os.linesep}{str(self.exception)}"

    class DirectoryNotEmptyError(UnexpectedError):
        def __init__(self, message: str="", exception: Exception=None, path: str=""):
            super(recursivecopy.DirectoryNotEmptyError, self).__init__(message, exception)
            self.path = path
        
        def __str__(self) -> str:
            return (f"[{recursivecopy.DirectoryNotEmptyError.__name__}]  " + 
                f"Directory is not empty: \"{self.path}\"{os.linesep}Message: {self.message}{os.linesep}" + 
                f"Exception: {str(self.exception)}")

    class PathTooLongError(UnexpectedError):
        def __init__(self, message:str="", e:Exception=None, path:str=""):
            super(recursivecopy.PathTooLongError, self).__init__(message, e)
            self.path = path
        
        def __str__(self) -> str:
            return (f"[{recursivecopy.PathTooLongError.__name__}] Path too long: " + 
                f"\"{self.path}\"{os.linesep}Message: {self.message}{os.linesep}Exception: {str(self.exception)}")

    class PathNotThereError(UnexpectedError):
        def __init__(self, message: str="", exception: Exception = None, path: str=""):
            super(recursivecopy.PathNotThereError, self).__init__(message,exception)
            self.path = path
        
        def __str__(self) -> str:
            return f"[{recursivecopy.PathNotThereError.__name__}] Path does not exist: \"{self.path}\"{os.linesep}{self.message}{os.linesep}{str(self.exception)}"

    class PathNotWorkingError(UnexpectedError):
        '''
        This error refers to whenever a path registers as not existing, or not referring to
        an expected object (for instance, it's not a folder even though it was expected to be)
        '''

        def __init__(self, message: str = "No message set", path: str = ""):
            super(recursivecopy.PathNotWorkingError,
                  self).__init__(message, None)
            self.path = path

        def __str__(self) -> str:
            return f"[{recursivecopy.PathNotWorkingError.__name__}]:  {self.message}{os.linesep}Path: {self.path}"

    class PathOperationFailedError(UnexpectedError):
        def __init__(self, message: str = "No Message Set", exception: Exception = None, path: str = None):
            super(recursivecopy.PathOperationFailedError, self).__init__(message, exception)
            self.path = path

        def __str__(self) -> str:
            return f"[{recursivecopy.PathOperationFailedError.__name__}]{self.message}{os.linesep}{self.path}{os.linesep}{str(self.exception)}"

    class WrongArgumentTypeError(UnexpectedError):
        def __init__(self, message: str = "No message set.", argtype: type = type(None), expectedtype: type = type(None)):
            super(recursivecopy.WrongArgumentTypeError,
                  self).__init__(message, None)
            self.argument_type = argtype
            self.expected_type = expectedtype

        def __str__(self) -> str:
            return f"[{recursivecopy.WrongArgumentTypeError.__name__}]{self.message}{os.linesep}Expected type {str(self.expected_type)} but instead got {str(self.argument_type)}"

    class WrongArgumentValueError(UnexpectedError):
        def __init__(self, message: str = None, argvalue=None, expectedvalue=None):
            super(recursivecopy.WrongArgumentValueError,
                  self).__init__(message, None)
            self.argument = argvalue
            self.expected_argument = expectedvalue

        def __str__(self) -> str:
            return (f"[{recursivecopy.WrongArgumentValueError.__name__}] {self.message}" + 
                f"{os.linesep}Expected {str(self.argument)} but got {str(self.expected_argument)}")

    class CantOpenFileError(UnexpectedError):
        def __init__(self, message: str, exception: Exception = None, filename: str = ""):
            super(recursivecopy.CantOpenFileError,
                  self).__init__(message, exception)
            self.filename = filename

        def __str__(self):
            temps = (f"[{recursivecopy.CantOpenFileError.__name__}] Exception: " +
                f"{str(self.exception)}{os.linesep}File: {self.filename}")
            if self.message is not None and len(self.message) > 0:
                temps += f"{os.linesep}Message: {self.message}"
            return temps

    class NothingWasDoneError(UnexpectedError):
        def __init__(self, message: str = None, exception: Exception = None):
            super(recursivecopy.NothingWasDoneError, self).__init__(
                "Nothing was done.", None)

        def __str__(self) -> str:
            return f"[{recursivecopy.NothingWasDoneError.__name__}] {self.message}"

    class AccessDeniedError(UnexpectedError):
        def __init__(self, message: str="", e: Exception=None, path: str=""):
            super(recursivecopy.AccessDeniedError, self).__init__(message, e)
            self.path = path
        
        def __str__(self) -> str:
            return (f"[{recursivecopy.AccessDeniedError.__name__}] {self.message}{os.linesep}Permission Denied Exception" + 
                f" while attempting to overwrite \"{self.path}\": {str(self.exception)}")

    class FileWriteFailure(UnexpectedError):
        def __init__(self, message: str="", e: Exception=None, path: str=""):
            super(recursivecopy.UnexpectedError, self).__init__(message, e)
            self.path = path
        
        def __str__(self) -> str:
            return f"[{recursivecopy.FileWriteFailure.__name__}] {self.message}{os.linesep}Failed to write to {self.path}."

    # this map is used to map error names with their types.  This can be used, for example, 
    # in a configuration file where the user can list types of errors they want or don't want to see.
    ERROR_TYPES = {
        DirectoryNotEmptyError.__name__: DirectoryNotEmptyError,
        PathTooLongError.__name__:PathTooLongError,
        PathNotThereError.__name__:PathNotThereError,
        PathNotWorkingError.__name__:PathNotWorkingError,
        PathOperationFailedError.__name__:PathOperationFailedError,
        WrongArgumentTypeError.__name__:WrongArgumentTypeError,
        WrongArgumentValueError.__name__:WrongArgumentValueError,
        CantOpenFileError.__name__:CantOpenFileError,
        NothingWasDoneError.__name__:NothingWasDoneError,
        AccessDeniedError.__name__:AccessDeniedError,
        FileWriteFailure.__name__:FileWriteFailure
    }

class copypredicate:
    @staticmethod
    def if_source_was_modified_more_recently(source: str = "", destination: str = "") -> bool:
        if os.path.exists(destination):
            return os.path.getmtime(source) > os.path.getmtime(destination)
        return True

class recursiveprune:
    '''
    An iterator that can be used to prune a destination directory after a recursive copy.
    This is important because there can be files left over after repeated copies
    that don't exist in the source anymore.

    This iterator ONLY iterates over paths that exist in the destination, but not in
    the source.  It does not do any deleting.  Moreover, it does not get invalidated
    when a path is removed.  It gathers all paths to delete on construction,
    so iteration happens without a dependency on filesystem state.
    '''
    def __init__(self, source, destination, newdestname: str=None):
        self.source = source
        self.destination = destination
        self.current = None
        self.destination = os.path.join(self.destination, os.path.basename(source)) if newdestname is None else os.path.join(self.destination, newdestname)
        self.todelete = set([element for element in recursive(self.destination) if not self._dest_in_source(element)])
        self.iter = iter(self.todelete)
    
    def __iter__(self):
        return self
    
    def __next__(self):
        self.current = next(self.iter)
        return self.current
    
    def _dest_in_source(self, subdir) -> bool:
        if subdir == self.destination: return True
        newsource = os.path.join(self.source, split_path(self.destination, subdir)[1])
        if os.path.islink(subdir):
            return os.path.islink(newsource)
        if os.path.isfile(subdir):
            return (os.path.isfile(newsource) and not os.path.islink(newsource))
        if os.path.isdir(subdir):
            return (os.path.isdir(newsource) and not os.path.islink(newsource))
        return False

# /c/abc
# /c/abc/abc1/bac3
#  V
# ['/c/abc', 'abc1/bac3']

def split_path(parent: str, child: str) -> typing.Tuple[str, str]:
    if not os.path.isabs(parent): parent = os.path.abspath(parent)
    if not os.path.isabs(child): child = os.path.abspath(child)
    if ischild(parent, child): return parent, child[(len(parent) + 1):]
    return parent, ""

def ischild(parent: str, child: str) -> bool:
    if len(parent) <= len(child):
        return (parent == child[:len(parent)])
    return False
