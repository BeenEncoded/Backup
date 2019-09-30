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

class BackupThread(threading.Thread):
    progress_update = pyqtSignal(ProcessStatus)
    show_error = pyqtSignal(recursivecopy.UnexpectedError)
    exec_finished = pyqtSignal()

    def run(self):
        self._init_vars()
        l = threading.local()
        l.source = self.backup["source"]
        l.destinations = self.data.backup["destinations"]
        l.sources_count = 0
        l.sources_copied = 0
        l.status = ProcessStatus(0.0, "Counting stuff...")

        self.updateProgress(l.status)
        for entry in recursive(l.source):
            l.sources_count += 1
        
        l.status.message = "Copying..."
        l.status.percent = 0.0
        for errors in recursivecopy(l.source, l.destinations):
            for error in errors:
                if not error[0]:
                    self.showError(error[1])
            l.sources_copied += 1
            l.status.percent = ((l.sources_copied * 100) / l.sources_count)
            self.updateProgress(l.status)
        self.raiseFinished()
        return

    def _init_vars(self):
        if not hasattr(self, "data"):
            self.data = threading.local()
            self.data.backup = {"source": None, "destinations": []}
    
    @property
    def backup(self):
        '''
        Thread-local property representing the backup
        It should be a dictionary with the following elements:
        {"source": source, "destinations": []}
        '''
        self._init_vars()
        return self.data.backup

    @backup.setter
    def backup(self, value):
        self._init_vars()
        self.data.backup = value

    def updateProgress(self, status):
        '''
        ##pyqtSignal: Emits a signal to update progress of the backup's process.
        '''
        self.progress_update.emit(status)
    
    def raiseFinished(self):
        self.exec_finished.emit()

    def showError(self, error):
        '''
        pyqtSignal: Shows an exception to the user. 
        '''
        self.show_error.emit(error)
