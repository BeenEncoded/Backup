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
from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtGui import QFont

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
        logger.info("Maindow set up.")
        self.show()
    
    def _apply_configuration(self):
        '''
        Applies the program's configuration to the UI.
        '''
        logger.info("Applying configuration to the main window.")
        uiconfig = CONFIG.config['ui']

        self.setFont(QFont(str(uiconfig['font']), int(uiconfig['font_size'])))

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

def display_gui(argv):
    logger.debug("display_gui called with args: " + str(argv))
    app = QApplication(argv)
    window = MainWindow(None)
    return app.exec()