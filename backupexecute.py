from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

from data import BackupProfile
from filesystem.iterator import recursive, recursivecopy, copypredicate
from errors import *

import threading

class ProcessStatus:
    def __init__(self, percent_complete=0.0, mess=""):
        self.message = mess
        self.percent = percent_complete
    
    def getMessage(self):
        return self.message
    
    def setMessage(self, m):
        self.message = m
    
    def getPercent(self):
        return self.percent

    def setPercent(self, p):
        self.percent = p

class BackupThread(threading.Thread):
    progress_update = pyqtSignal(status=ProcessStatus())
    show_error = pyqtSignal(error=Exception("What?  I didn't do anything...  -- whistles nonchalantly  --"))

    def run(self):
        self._init_vars()
        l = threading.local()
        l.sources = self.data.backup.getSources()
        l.destinations = self.data.backup.getDestinations()
        l.sources_count = 0
        l.sources_copied = 0
        l.status = ProcessStatus(0.0, "Counting stuff...")

        self.updateProgress(l.status)
        for x in range(0, l.sources):
            for entry in recursive(l.sources[x]):
                l.sources_count += 1
            l.status.setPercent((x * 100) / len(l.sources))
            self.updateProgress(l.status)
        
        l.status.setMessage("Copying sources...")
        l.status.setPercent(0.0)
        for entry in l.sources:
            for results in recursivecopy(entry, l.destinations):
                for result in results:
                    if not result[0]:
                        #TODO: show error...
                        pass
                l.sources_copied += 1
                l.status.setPercent((l.sources_copied * 100) / l.sources_count)
                self.updateProgress(l.status)
        return

    def _init_vars(self):
        if not hasattr(self, "data"):
            self.data = threading.local()
            self.data.backup = BackupProfile()
            self.data.progress_id = 0 #referrs to the progress bar that this process is associated with.
    
    @property
    def backup(self):
        self._init_vars()
        return self.data.backup

    @backup.setter
    def backup(self, value):
        self._init_vars()
        self.data.backup = value

    def setProgressID(self, id):
        self._init_vars()
        self.data.progress_id = id

    def updateProgress(self, status):
        '''
        ##pyqtSignal: Emits a signal to update progress of the backup's process.
        '''
        self.progress_update.emit(status)
    
    def showError(self, error):
        '''
        pyqtSignal: Shows an exception to the user. 
        '''
        self.show_error.emit(error)
