import os
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt

from data import BackupProfile
from globaldata import *

class EditBackupProfileWidget(QWidget):
    def __init__(self, parent):
        super(EditBackupProfileWidget, self).__init__(parent)
        self._init_layout()
    
    def _init_layout(self):
        mainlayout = QVBoxLayout()
        label = QLabel("Hello World!")
        label.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)

        mainlayout.addWidget(label)
        self.setLayout(mainlayout)