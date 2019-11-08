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

from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, pyqtSlot, QRect, QObject, pyqtSignal
from PyQt5.QtGui import QFont, QKeySequence

from UI.MainWindowWidgets import EditBackupProfileWidget, ManageBackupsWidget
from globaldata import *
import logging

logger = logging.getLogger("UI.MainWindow")

class MainWindow(QMainWindow):
    def __init__(self, parent):
        logger.info("Initializing MainWindow")
        super(MainWindow, self).__init__(parent)
        self.statusBar().setEnabled(True)
        self._add_menubar()
        
        self.setCentralWidget(ManageBackupsWidget(self))
        self._apply_configuration()
        self.logShortcut = QShortcut(QKeySequence("Ctrl+L"), self)
        self.logShortcut.activated.connect(self._show_log_window)
        self.logwindow = LogWindow()
        logger.info("Maindow set up.")
        self.show()
    
    def _apply_configuration(self):
        '''
        Applies the program's configuration to the UI.
        '''
        logger.info("Applying configuration to the main window.")
        uiconfig = CONFIG.config['ui']

        self.setFont(QFont(str(uiconfig['font']), int(uiconfig['font_size'])))

    @pyqtSlot()
    def _show_log_window(self):
        logger.debug("Ctrl+L pressed")
        self.logwindow.show()

    def closeEvent(self, event):
        logger.debug("MainWindow closed.")
        self.logwindow.close()

    def _add_menubar(self):
        self.menuBar().addAction('About', self._show_about)

    @pyqtSlot()
    def _show_about(self):
        logger.info("showing about")
        QMessageBox.information(self, "GNU GPLv3:", """Backup backs up a user's computer to one or more disk drives or block devices.
        Copyright (C) 2019 Jonathan Whitlock

        This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

        This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.

        You should have received a copy of the GNU General Public License along with this program.  If not, see <https://www.gnu.org/licenses/>.
        
        Version: """ + str(VERSION))

class LogWindow(QWidget):
    def __init__(self, parent=None):
        super(LogWindow, self).__init__(parent)
        self.log_handler = LogWindow.WindowLogHandler(self)

        self._layout()
        self._connect()

        logging.getLogger().addHandler(self.log_handler)
        self.setWindowTitle("LOGS")
    
    def _layout(self):
        self.setWindowFlag(Qt.WindowCloseButtonHint, False)
        mainlayout = QVBoxLayout()

        self.log_output = QPlainTextEdit()
        self.closebutton = QPushButton("Close")

        self.log_output.setReadOnly(True)
        self.log_output.setLineWrapMode(QPlainTextEdit.NoWrap)
        
        mainlayout.addWidget(self.log_output)
        closelayout = QHBoxLayout()
        closelayout.addWidget(self.closebutton)
        mainlayout.addLayout(closelayout)
        self.setLayout(mainlayout)

        uiconfig = CONFIG.config['ui']

        self.setFont(QFont(str(uiconfig['font']), int(uiconfig['font_size'])))
    
    def _connect(self):
        self.closebutton.clicked.connect(self._close_logwindow)
        self.log_handler.qcom.logtowindow.connect(self._log_to_window)
    
    @pyqtSlot()
    def _close_logwindow(self):
        self.hide()

    @pyqtSlot(str)
    def _log_to_window(self, record: str=""):
        self.log_output.appendPlainText(record)
        self._limit_size((2**10) * 100)

    def _limit_size(self, maxsize: int=((2**10) * 3)):
        length = len(self.log_output.toPlainText())

        if length > maxsize:
            self.log_output.setPlainText(self.log_output.toPlainText()[(length - maxsize):length])

    class WindowLogHandler(logging.Handler):
        class QComObject(QObject):
            logtowindow = pyqtSignal(str)

        def __init__(self, window):
            super(LogWindow.WindowLogHandler, self).__init__()
            self.window = window
            self.setFormatter(logging.Formatter("%(asctime)s [%(name)s] [%(levelname)s] -> %(message)s"))
            self.qcom = LogWindow.WindowLogHandler.QComObject()

        def emit(self, record):
            self.qcom.logtowindow.emit(self.format(record))

def display_gui(argv):
    logger.debug("display_gui called with args: " + str(argv))
    app = QApplication(argv)
    window = MainWindow(None)
    return app.exec()