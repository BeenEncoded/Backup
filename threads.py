from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, pyqtSignal, QObject
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
    class QtComObject(QObject):
        progress_update = pyqtSignal(ProcessStatus)
        show_error = pyqtSignal(recursivecopy.UnexpectedError)
        exec_finished = pyqtSignal()

    def run(self):
        if not hasattr(self, "qcom"):
            self.qcom = BackupThread.QtComObject()
        self.stop = False
        if len(self.backup["destinations"]) == 0:
            self.raiseFinished()
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
        iterator = iter(recursivecopy(l.source, l.destinations, predicate=copypredicate.if_source_was_modified_more_recently))
        print("thread beginning iteration")
        while True and not self.stop:
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
        print("thread raising finished")
        self.raiseFinished()
    
    def updateProgress(self, status):
        '''
        ##pyqtSignal: Emits a signal to update progress of the backup's process.
        '''
        self.qcom.progress_update.emit(status)
    
    def raiseFinished(self):
        self.qcom.exec_finished.emit()

    def showError(self, error):
        '''
        pyqtSignal: Shows an exception to the user. 
        '''
        self.qcom.show_error.emit(error)

    def _display_string(self, s):
        if len(s) > 50:
            s = (s[:int((50 / 2) - 3)] + "..." + s[len(s) - int(50 / 2 + 1):])
        return s
