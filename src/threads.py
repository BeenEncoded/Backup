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
from iterator import recursive, recursivecopy, copypredicate

import dataclasses, threading, logging

logger = logging.getLogger("threads")

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
            self.raiseFinished()
        except: # noqa E722
            logger.critical("Uncaught exception in a backup thread!")
            logger.exception("CRITICAL EXCEPTION; " + str(self.backup))
            self.raiseFinished()
    
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
