from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from UI.MainWindowWidgets import EditBackupProfileWidget, ExecuteBackupProfileWidget
from globaldata import *

class MainWindow(QMainWindow):
    def __init__(self, parent):
        super(MainWindow, self).__init__(parent)
        self.setCentralWidget(ExecuteBackupProfileWidget(self))
        self._apply_configuration()
    
    def _apply_configuration(self):
        '''
        Applies the program's configuration to the UI.
        '''
        global CONFIG
        uiconfig = CONFIG.getConfig()['ui']

        self.setFont(QFont(str(uiconfig['font']), int(uiconfig['font_size'])))

def display_gui(argv):
    app = QApplication(argv)
    window = MainWindow(None)
    window.show()
    return app.exec()