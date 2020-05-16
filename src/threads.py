# Backup backs up a user's computer to one or more disk drives or block devices.
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

from PyQt5.QtCore import pyqtSignal, QObject
from iterator import recursive, recursivecopy, copypredicate, recursiveprune

import dataclasses, threading, logging, queue, time, shutil, os

logger = logging.getLogger("threads")


class Worker(threading.Thread):
    '''
    An arbitrary worker thread.
    '''
    def __init__(self, functor):
        '''
        functor: the function to execute on each iteration.  Takes no arguments.

        If the functor is None, Worker.doWork will be the function used for implimentation,
        allowing for polymorphic implimentation much like threading.Thread, where doWork is the
        implemented function instead of run.
        '''
        super(Worker, self).__init__()
        self.throttle = 30 #iterates 30 times per second
        self._running = False #True when the thread is running
        self._stopthread = False #True when the caller wants the thread to stop
        self._functor = functor
    
    def halt_thread(self) -> None:
        '''
        Stops this worker thread.
        '''
        if not self.isAlive():
            return
        self._stopthread = True
        self.join()
        if self._running:
            raise RuntimeError("Failed to stop thread")
    
    def doWork(self) -> None:
        '''
        Impliment this in a subclass.  This is the only function you /need/ for function.
        '''
        raise NotImplementedError(Worker.doWork.__qualname__ + ": Not implemented.")

    def tryLog(self, message) -> bool:
        try:
            logger.debug(message)
            return True
        except: # noqa: E722
            return False

    def run(self):
        self._running = True
        while(not self._stopthread):
            if self._functor is not None:
                self._functor()
            else:
                self.doWork()
            time.sleep(1 / self.throttle)
        self._running = False

class ThreadPool:
    '''
    A ThreadPool for asynchronous tasks.
    '''

    def __init__(self, maxcount: int=0):
        self.threadqueue = queue.Queue(0)
        self.runningthreads = set()
        self.maxcount = maxcount
        self.noadd = False #when true, disabled the addition and starting of more threads.

    def addThread(self, t: threading.Thread=None) -> None:
        if not self.noadd:
            self.threadqueue.put(t)
    
    def startAll(self) -> bool:
        '''
        Starts all threads.  Limit number of threads to self.maxthreads.
        Returns true if threads were started, false otherwise.
        '''
        if self.threadqueue.empty():
            return False
        tstarted = False
        scount = (self.maxcount - len(self.runningthreads))
        if scount <= 0:
            return tstarted
        for x in range(0, scount):
            if self._runthread():
                tstarted = True
            else:
                break
        return tstarted

    def canStart(self) -> bool:
        '''
        returns true if there are still threads in this pool waiting to be started
        '''
        return not self.threadqueue.empty()

    def joinAll(self) -> bool:
        '''
        Joins all threads that are not alive.
        returns True if any threads were joined.
        '''
        toremove = [t for t in self.runningthreads if not t.is_alive()]
        self.runningthreads.difference_update(toremove)
        for t in toremove: t.join()
        return (len(toremove) > 0)

    def terminateAll(self) -> None:
        '''
        Attempts to join everything.  First joins threads that are not alive, then
        it will blocking join all the rest.
        '''
        self.noadd = True
        self.joinAll()
        for t in self.runningthreads: t.join()
        self.runningthreads.clear()

    def _runthread(self) -> bool:
        '''
        Attempts to run a thread.  Returns True if a thread was started and moved to the
        list of running threads.
        '''
        if len(self.runningthreads) < self.maxcount and not self.threadqueue.empty():
            if not self.noadd:
                t = self.threadqueue.get(block=True)
                t.start()
                self.runningthreads.update([t])
                return True
        return False

class ThreadManager(Worker):
    '''
    A worker thread that manages the threads a user gives it.  When starting a large number of
    threads, it can be helpful to limit their number if they used a 
    shared resource.  This worker helps to mitigate resource hogging
    by limiting the number of threads that can start, and joins them when 
    they have completed whatever they were doing.
    '''
    def __init__(self, maxcount: int=3):
        super(ThreadManager, self).__init__(functor=None)
        self.toadd = queue.Queue(0)
        self.pool = ThreadPool(maxcount)
    
    def addThread(self, t: threading.Thread=None) -> None:
        self.toadd.put(t)

    def doWork(self) -> None:
        while not self.toadd.empty():
            try:
                self.pool.addThread(self.toadd.get(block=False, timeout=0.5))
            except queue.Empty:
                break
        self.pool.startAll()
        self.pool.joinAll()

    def halt_thread(self) -> None:
        self.pool.terminateAll()
        super(ThreadManager, self).halt_thread()

@dataclasses.dataclass
class ProcessStatus:
    percent: float = 0.0
    message: str = str()

class BackupThread(threading.Thread):
    class QtComObject(QObject):
        progress_update = pyqtSignal(ProcessStatus)
        show_error = pyqtSignal(recursivecopy.UnexpectedError)
        exec_finished = pyqtSignal()

    def __init__(self, backup: dict={"source": "", "destinations": []}):
        super(BackupThread, self).__init__()
        self.backup = backup
        self.qcom = BackupThread.QtComObject()
        self.stop = False

    def run(self):
        logger.debug("BackupThread starting to run.")
        try:
            self.stop = False
            if len(self.backup["destinations"]) == 0:
                self.raiseFinished()
                logger.warning("No destination folders, doing nothing.  Backup thread terminating.")
                return
            l = threading.local()
            l.source = self.backup["source"]
            l.destinations = self.backup["destinations"]
            l.sources_count = 0
            l.sources_copied = 0
            l.status = ProcessStatus(0.0, "Counting stuff...")

            self.updateProgress(l.status)
            for entry in recursive(l.source):
                l.sources_count += 1
            
            l.status.message = "Copying..."
            l.status.percent = 0.0
            logger.info(f"Executing copy on \"{l.source}\"")
            iterator = iter(recursivecopy(l.source, l.destinations, predicate=copypredicate.if_source_was_modified_more_recently))
            while not self.stop:
                try:
                    errors = next(iterator)
                except StopIteration:
                    break
                if errors is not None:
                    for error in errors:
                        self.showError(error)
                l.sources_copied += 1
                l.status.message = self._display_string(iterator.current)
                l.status.percent = ((l.sources_copied * 100) / l.sources_count)
                self.updateProgress(l.status)
            
            logger.info(f"Executing pruneing algorithm.")
            for dest in l.destinations:
                l.status.message = f"Pruning \"{dest}\""
                logger.info(f"Pruning \"{dest}\"")
                self.updateProgress(l.status)
                self._pruneDestination(l.source, dest)
            
            logger.info(f"Pruning finished.")
            self.raiseFinished()
        except: # noqa E722
            logger.critical("Uncaught exception in a backup thread!")
            logger.exception("CRITICAL EXCEPTION; " + str(self.backup))
            self.raiseFinished()
    
    def _pruneDestination(self, source: str="", destination: str="") -> int:
        '''
        Prunes the destination.
        Returns the number of file objects a delete was executed on successfully.
        Folders count as 1.  rmtree is used on those.
        '''
        logger.debug(f"{BackupThread._pruneDestination.__qualname__}: called")
        deletecount = 0
        if self.stop:
            return 0
        for element in recursiveprune(source, destination):
            if self.stop:
                break
            if not self._deletePath(element):
                logger.error(f"Prune: could not delete \"{element}\"")
            else:
                self.updateProgress(ProcessStatus(percent=100, message=f"Deleted \"{element}\""))
                logger.warning(f"Deleted while pruning: \"{element}\"")
                deletecount += 1
            if self.stop:
                break
        return deletecount
    
    def _deletePath(self, path: str="") -> bool:
        if not os.path.exists(path):
            return True
        if os.path.islink(path) or os.path.isfile(path):
            os.remove(path)
        elif os.path.isdir(path):
            shutil.rmtree(path, onerror=self.rmtree_onError)
        return not os.path.exists(path)

    def rmtree_onError(self, function, path, excinfo) -> None:
        errormessage = ("rmtree: I don't know what heppened... Here's some data:" + os.linesep + 
            f"function: {str(function)}" + os.linesep + 
            f"path: \"{path}\"" + os.linesep + 
            f"excinfo: {str(excinfo)}")
        self.showError(recursivecopy.UnexpectedError(message=errormessage))
        logger.error(errormessage)

    def updateProgress(self, status: ProcessStatus):
        '''
        ##pyqtSignal: Emits a signal to update progress of the backup's process.
        '''
        self.qcom.progress_update.emit(status)
    
    def raiseFinished(self):
        logger.debug(self.raiseFinished.__qualname__ + ": backup thread is saying it's finished.")
        self.qcom.exec_finished.emit()

    def showError(self, error):
        '''
        pyqtSignal: Shows an exception to the user. 
        '''
        self.qcom.show_error.emit(error)

    def _display_string(self, s: str="", length: int=100) -> str:
        if len(s) > length:
            s = (s[:int((length / 2) - 3)] + "..." + s[len(s) - int(length / 2 + 1):])
        return s
