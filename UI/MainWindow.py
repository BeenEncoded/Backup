from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt

from UI.MainWindowWidgets import EditBackupProfileWidget

class MainWindow(QMainWindow):
    def __init__(self, parent):
        super(MainWindow, self).__init__(parent)
        self.setCentralWidget(EditBackupProfileWidget(self))

def display_gui(argv):
    app = QApplication(argv)
    window = MainWindow(None)
    window.show()
    return app.exec()