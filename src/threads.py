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
from iterator import recursivecopy
from algorithms import ProcessStatus, Backup, prune_backup
from data import BackupProfile, BackupMapping

import threading, logging, queue, time

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

class BackupThread(threading.Thread):
    class QtComObject(QObject):
        progress_update = pyqtSignal(ProcessStatus)
        show_error = pyqtSignal(recursivecopy.UnexpectedError)
        exec_finished = pyqtSignal()

    def __init__(self, backup: dict={"source": "", "destinations": [], "newdest": None}):
        super(BackupThread, self).__init__()
        self.backup = backup
        self.algo = Backup(backup, 
            {"progressupdate": self.updateProgress, 
            "reporterror": self.showError, 
            "finished": self.raiseFinished})
        self.qcom = BackupThread.QtComObject()

    def run(self):
        logger.debug("BackupThread starting to run.")
        self.algo.execute()
    
    def cancelExec(self) -> None:
        self.algo.abort = True

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

class PruneBackupThread(QObject, threading.Thread):
    statusUpdated = pyqtSignal(ProcessStatus)
    finished = pyqtSignal()

    def __init__(self, backup: BackupProfile=None, mapping: BackupMapping=None):
        super(PruneBackupThread, self).__init__()
        self.backup = backup
        self.mapping = mapping
    
    def run(self)->None:
        logger.info("prune thread starting")
        prune_backup(self.backup, self.mapping, self.status)
        logger.info("pruning algorithm finished")
        self.rfinished()

    def status(self, ps: ProcessStatus=None)->None:
        logger.debug(f"{PruneBackupThread.status.__qualname__}: emitting status update")
        self.statusUpdated.emit(ps)

    def rfinished(self)->None:
        logger.debug(f"{PruneBackupThread.status.__qualname__}: Backup prune thread emmitting finished ")
        self.finished.emit()

class CoroutineThread(threading.Thread):
    def __init__(self, function, *args):
        super(CoroutineThread, self).__init__()
        self.function = function
        self.args = args
        self.value = None
        self.running = True
        self.start()

    def run(self)->None:
        try:
            self.value = self.function(*(self.args))
            self.running = False
        except:
            logger.exception(f"{CoroutineThread.run.__qualname__}: Exception occurred!")
            self.running = False
            raise

    def getReturnValue(self) -> any:
        while self.running: time.sleep(1 / 30) # wait for execution to end.
        self.running = True
        return self.value

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.join()

class Task:
    def __init__(self, function, *args):
        print(repr(args))
        self.crt = CoroutineThread(function, *args)
    
    def __del__(self):
        if self.crt.isAlive(): self.crt.join()
        self.crt = None

    def wait(self) -> any:
        if self.crt is not None:
            x = self.crt.getReturnValue()
            self.crt.join()
