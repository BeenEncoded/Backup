import logging, os, shutil, dataclasses

from iterator import recursivecopy, recursiveprune, copypredicate
from data import BackupProfile, BackupMapping
from globaldata import CONFIG


logger = logging.getLogger(__name__)


@dataclasses.dataclass
class ProcessStatus:
    percent: float = 0.0
    message: str = str()


class Backup:
    '''
    This object encapsulates the backup algorithm in a portable way.  It backs up a single source
    to any number of destinations.  Using the com argument you can pass callbacks that can
    update another thread on what is happening or provide progress updates throughout the process.
    '''

    def __init__(self,
        data: dict={"source": "", "destinations": [], "newdest": None},
        com: dict={"progressupdate": None, "reporterror": None, "finished": None}):
        '''
        Creates a Backup object containing all the information needed to move forward with the backup.
        data:  a dictionary containing a single source and an array of destinations.
            source: str()
            destinations: [str]
            newdestname: str

        com: callbacks that can be passed in order to recieve updates as the process progresses.
            progressupdate(ProcessStatus)
            reporterror(recursivecopy.UnexpectedError)
            finished()
        '''

        self.source = data["source"]
        self.destinations = data["destinations"]
        self.newdestname = data["newdest"]
        self.update_progress = com["progressupdate"]
        self.report_error = com["reporterror"]
        self.finishedcallback = com["finished"]
        self.abort = False
        self.status = ProcessStatus(0.0, "Nothing is happening yet...")
        
        self.ignored_errors = [recursivecopy.ERROR_TYPES[key] for key in recursivecopy.ERROR_TYPES.keys() if key in CONFIG["DEFAULT"]["ignorederrors"]]
        if len(self.ignored_errors) > 0:
            logger.info("Ignoring error types: %s", repr(self.ignored_errors))
        else: logger.info("All errors will be shown.")
    
    def execute(self):
        logger.debug("BackupThread starting to run.")
        try:
            self.abort = False
            if len(self.destinations) == 0:
                self.raise_finished()
                logger.warning("No destination folders, doing nothing.  Backup aborting.")
                return
            sources_copied = 0

            self.status = ProcessStatus(0.0, "Perparing...")
            self.update_status(self.status)
            sources_count = sum((len(files) + len(dirs)) for _, dirs, files in os.walk(self.source))

            self.status.message = "Copying..."
            self.status.percent = 0.0
            logger.info("Executing copy on \"%s\"", self.source)

            #initialize the iterator.
            iterator = None
            if self.newdestname is None:
                iterator = iter(recursivecopy(self.source, self.destinations, predicate=copypredicate.if_source_was_modified_more_recently))
            else:
                iterator = iter(recursivecopy(self.source, self.destinations, 
                    predicate=copypredicate.if_source_was_modified_more_recently,
                    newdestname=self.newdestname))
            
            while not self.abort:
                try:
                    errors = next(iterator)
                except StopIteration:
                    break
                if errors is not None:
                    for error in errors:
                        if type(error) not in self.ignored_errors: 
                            self.report_error(error)
                sources_copied += 1
                self.status.message = self._display_string(iterator.current)
                if sources_count > 0: self.status.percent = ((sources_copied * 100) / sources_count)
                self.update_status(self.status)
            
            self.status.percent = 100
            self.update_status(self.status)

            logger.info("Executing pruneing algorithm.")
            if not self.abort:
                for dest in self.destinations:
                    self.status.message = f"Pruning \"{dest}\""
                    logger.info("Pruning \"%s\"", dest)
                    self.update_status(self.status)
                    self._prune_destination(self.source, dest)
            
            logger.info("Pruning finished.")
            self.raise_finished()
        except: # noqa E722
            logger.critical("Uncaught exception in a backup algorithm!")
            logger.exception("CRITICAL EXCEPTION; " + str({"source": self.source, "destinations": self.destinations}))
            self.raise_finished()
    
    def _prune_destination(self, source: str="", destination: str="") -> int:
        '''
        Prunes the destination.
        Returns the number of file objects a delete was executed on successfully.
        Folders count as 1.  rmtree is used on those.
        '''
        logger.debug(f"{Backup._prune_destination.__qualname__}: called")
        deletecount = 0
        if self.abort:
            return 0
        for element in recursiveprune(source, destination, self.newdestname):
            if self.abort: break
            if not self._delete_path(element):
                logger.error(f"Prune: could not delete \"{element}\"")
            else:
                self.update_status(ProcessStatus(percent=100, message=f"Deleted \"{element}\""))
                logger.warning(f"Deleted while pruning: \"{element}\"")
                deletecount += 1
            if self.abort: break
        return deletecount
    
    def _delete_path(self, path: str="") -> bool:
        if not os.path.exists(path):
            return True
        if os.path.islink(path) or os.path.isfile(path):
            os.remove(path)
        elif os.path.isdir(path):
            shutil.rmtree(path, onerror=self.rmtree_onerror)
        return not os.path.exists(path)
    
    def rmtree_onerror(self, function, path, excinfo) -> None:
        errormessage = ("rmtree: I don't know what heppened... Here's some data:" + os.linesep + 
            f"function: {str(function)}" + os.linesep + 
            f"path: \"{path}\"" + os.linesep + 
            f"excinfo: {str(excinfo)}")
        self.report_error(recursivecopy.UnexpectedError(message=errormessage))
        logger.error(errormessage)

    def raise_finished(self) -> None:
        if self.finishedcallback is not None:
            self.finishedcallback()

    def report_error(self, error: recursivecopy.UnexpectedError = None) -> None:
        if self.report_error is not None:
            self.report_error(error)
    
    def update_status(self, status: ProcessStatus=ProcessStatus(0.0, "DEFAULT STATUS")) -> None:
        if self.update_progress is not None:
            self.update_progress(status)

    def _display_string(self, s: str="", length: int=100) -> str:
        if len(s) > length: s = (s[:int((length / 2) - 3)] + "..." + s[len(s) - int(length / 2 + 1):])
        return s

def prune_backup(backup: BackupProfile=None, mapping: BackupMapping=None, updateStatus=None, finished=None) -> None:
    def _tdelete_path(path: str="") -> bool:
        def rmtree_onerror(function, path, excinfo) -> None:
            errormessage = ("rmtree: I don't know what heppened... Here's some data:" + os.linesep + 
                f"function: {str(function)}" + os.linesep + 
                f"path: \"{path}\"" + os.linesep + 
                f"excinfo: {str(excinfo)}")
            logger.error(errormessage)

        if not os.path.exists(path):
            return True
        if os.path.islink(path) or os.path.isfile(path):
            os.remove(path)
        elif os.path.isdir(path):
            shutil.rmtree(path, onerror=rmtree_onerror)
        return not os.path.exists(path)
    
    if len(backup.destinations) == 0:
        logger.info(f"{prune_backup.__qualname__}: no destinations in the backup.  Returing immediately.")
        updateStatus(ProcessStatus(100.00, "Didn't find anything"))
        return
    
    todel = []
    destinations = None
    valid_dests = set([d for d in backup.destinations if os.path.isdir(d)])
    invalid_dests = set(backup.destinations).difference_update(valid_dests)

    if len(valid_dests) == 0:
        logger.error(f"{prune_backup.__qualname__}:  No viable destinations to prune!  They do not exist.")
    
    if len(valid_dests) < len(backup.destinations):
        logger.warning(f"{prune_backup.__qualname__}: did not find all the destinations.  " + 
            f"Executing on destinations: {repr(valid_dests)}    Skipping invalids: {repr(invalid_dests)}")

    if updateStatus is not None: updateStatus(ProcessStatus(0.0, "Pruning Backup"))
    for dest in valid_dests:
        with os.scandir(dest) as it:
            destinations = [folder.name for folder in it if os.path.isdir(folder.path)]
        sourcenames = [mapping[s] for s in backup.sources]
        for dname in destinations:
            if dname not in sourcenames:
                todel.append(dest + os.path.sep + dname)
    
    if len(todel) == 0:
        if updateStatus is not None: updateStatus(ProcessStatus(100.00, "Nothing was pruned."))
    
    x = 0
    for d in todel:
        logger.warning(f"Pruning algorithm deleteing path: \"{d}\"")
        _tdelete_path(d)
        x += 1
        if updateStatus is not None: updateStatus(ProcessStatus((x / len(todel) * 100), "Pruning Backup"))

