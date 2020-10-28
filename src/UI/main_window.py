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

from __future__ import annotations
import logging
from typing import List
from PyQt5.QtWidgets import QMainWindow, QShortcut, QMessageBox, QPlainTextEdit
from PyQt5.QtWidgets import QVBoxLayout, QWidget, QApplication
from PyQt5.QtCore import pyqtSlot, QObject, pyqtSignal
from PyQt5.QtGui import QFont, QKeySequence, QCloseEvent

from UI.main_window_widgets import ManageBackupsWidget, EditConfigurationWidget, ExecuteBackupWidget
from globaldata import CONFIG, VERSION

logger = logging.getLogger(__name__)

class MainWindow(QMainWindow):
    def __init__(self, parent: QWidget):
        logger.info("Initializing MainWindow")
        super().__init__(parent)
        self.statusBar().setEnabled(True)
        self._add_menubar()
        
        self.set_central_widget(ManageBackupsWidget(self))
        self._apply_configuration()
        self.log_shortcut = QShortcut(QKeySequence("Ctrl+L"), self)
        self.log_shortcut.activated.connect(self._show_log_window)
        self.logwindow = LogWindow()
        logger.info("Maindow set up.")
        self.show()
    
    def _apply_configuration(self):
        '''
        Applies the program's configuration to the UI.
        '''
        logger.info("Applying configuration to the main window.")
        uiconfig = CONFIG['ui']

        self.setFont(QFont(str(uiconfig['font']), int(uiconfig['font_size'])))

    @pyqtSlot()
    def _show_log_window(self):
        logger.debug("Ctrl+L pressed")
        self.logwindow.show()

    def closeEvent(self, event : QCloseEvent) -> None: # pylint: disable=unused-argument,invalid-name
        """ closeEvent(event : QCloseEvent) -> None

        Overrides QMainWindow.closeEvent, defining actions
        to be taken on the window's close.

        Parameters:
        -----------
        event : QCloseEvent
            The event... I think that triggers the close.
        """
        logger.debug("MainWindow closed.")
        self.logwindow.allowclose = True
        self.logwindow.close()

    def _add_menubar(self):
        self.menuBar().addAction('About', self._show_about)
        self.configbutton = self.menuBar().addAction('Configuration', self._edit_config)

    @pyqtSlot()
    def _edit_config(self):
        if type(self.centralWidget()) is not ExecuteBackupWidget:
            self.set_central_widget(EditConfigurationWidget(self))
        else:
            QMessageBox.warning(self, "Backup Running!", 
                "You currently have a backup running... Please " + 
                "cancel it or let it finish before you start fucking around.")

    @pyqtSlot()
    def _show_about(self):
        logger.info("showing about")
        QMessageBox.information(self, "GNU GPLv3:", """Backup backs up a user's computer to one or more disk drives or block devices.
        Copyright (C) 2019 Jonathan Whitlock

        This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

        This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.

        You should have received a copy of the GNU General Public License along with this program.  If not, see <https://www.gnu.org/licenses/>.
        
        Version: """ + str(VERSION))

    def set_central_widget(self, new_widget: QWidget) -> None:
        logger.debug("setCentralWidget overrided")
        self.configbutton.setEnabled(type(new_widget) is ManageBackupsWidget)

        super(MainWindow, self).setCentralWidget(new_widget)

class LogWindow(QWidget):
    '''
    LogWindow is a window that adds a handler to the root logger that prints
    to it.  Because the handler is added to the root logger, this object
    should exist until the program's termination and not be destroyed or
    the handler will be left referenced by the root logger.

    To that end, LogWindow.allowclose is provided, a boolean that when False
    hides the window when the closeEvent is intercepted.  Set it to true and
    call .close() to actually close it when the program terminates, or when 
    the parent window is closed.
    '''
    def __init__(self, parent=None):
        super(LogWindow, self).__init__(parent)
        self.log_handler = LogWindow.WindowLogHandler(self)

        self._layout()
        self._connect()

        logging.getLogger().addHandler(self.log_handler)
        self.setWindowTitle("LOGS")
        self.allowclose = False

    def _layout(self):
        mainlayout = QVBoxLayout()

        self.log_output = QPlainTextEdit()

        self.log_output.setReadOnly(True)
        self.log_output.setLineWrapMode(QPlainTextEdit.NoWrap)
        
        mainlayout.addWidget(self.log_output)
        self.setLayout(mainlayout)

        uiconfig = CONFIG.config['ui']

        self.setFont(QFont(str(uiconfig['font']), int(uiconfig['font_size'])))

    def _connect(self):
        self.log_handler.qcom.LOGTOWINDOW.connect(self._log_to_window)

    def closeEvent(self, event: QCloseEvent) -> None: # pylint: disable=unused-argument,invalid-name
        """ closeEvent(event : QCloseEvent) -> None
        """
        if self.allowclose:
            logger.debug("%s: closing log window", self.closeEvent.__qualname__)
            logging.getLogger().removeHandler(self.log_handler)
            self.close()
        else:
            logger.debug("%s: hiding log window", self.closeEvent.__qualname__)
            self.hide()

    @pyqtSlot(str)
    def _log_to_window(self, record: str=""):
        self.log_output.appendPlainText(record)

        #limit the size of the logfile to 300KB, minimum 100KB
        self._limit_size(minsize=((2**10) * 100), maxsize=((2**10) * 300))

    def _limit_size(self, minsize: int=((2**10) * 3), maxsize: int=((2**10) * 10)):
        '''
        limits the amount of information stored in the log window.
        This is a very inefficient operation to perform, so minsize and maxsize are
        provided so the user can define the smallest amount of information
        that should be immediately available, and the maximum amount of information
        that should be stored.

        When maxsize is reached (defaults to 10KB) the logwindow's QPlainTextEdit's
        plaintext is trimmed to just 3KB.
        '''
        length = len(self.log_output.toPlainText())

        if length > maxsize:
            self.log_output.setPlainText(self.log_output.toPlainText()[(length - minsize):length])

    class WindowLogHandler(logging.Handler):
        """ WindowLogHandler(logging.Handle)

        This log handler writes logs to a window.
        """

        class QComObject(QObject):
            """ A proxy object
            """
            LOGTOWINDOW = pyqtSignal(str)

        def __init__(self, window):
            super(LogWindow.WindowLogHandler, self).__init__()
            self.window = window
            f = "%(asctime)s [%(name)s] [%(levelname)s] -> %(message)s"
            self.setFormatter(logging.Formatter(f))
            self.qcom = LogWindow.WindowLogHandler.QComObject()

        def emit(self, record):
            self.qcom.LOGTOWINDOW.emit(self.format(record))

def display_gui(argv : List[str]):
    """ display_gui(argv: List[str]) -> int

    Display's the program's GUI using PyQt5.

    Parameters:
    -----------
    argv: List[str]
        The arguments passed to the program.

    Returns:
    --------
    int: 0 for normal termination.
    """
    logger.debug("display_gui called with args: %s", str(argv))
    app = QApplication(argv)
    window = MainWindow(None) # pylint: disable=unused-variable
    return app.exec()
