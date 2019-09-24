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
        self.setWindowTitle("Edit Backup")
        mainlayout = QVBoxLayout()

        # A labeled text box:
        temp_hbox = QHBoxLayout()
        self.name_tbox = QLineEdit()
        self.namelabel = QLabel("Backup Name:  ")
        temp_hbox.addWidget(self.namelabel)
        temp_hbox.addWidget(self.name_tbox)
        mainlayout.addLayout(temp_hbox)

        #A list box labeled with a groupbox for editing the list of source folders
        self.sources_groupbox = QGroupBox("Source Folders:")
        sources_gbox_layout = QVBoxLayout()
        self.sources_listbox = QListWidget()
        sources_gbox_layout.addWidget(self.sources_listbox)
        sources_buttons = QHBoxLayout()
        self.sources_add_button = QPushButton()
        self.sources_add_button.setText("Add")
        sources_buttons.addWidget(self.sources_add_button)
        self.sources_del_button = QPushButton()
        self.sources_del_button.setText("Delete")
        sources_buttons.addWidget(self.sources_del_button)
        sources_gbox_layout.addLayout(sources_buttons)
        self.sources_groupbox.setLayout(sources_gbox_layout)
        mainlayout.addWidget(self.sources_groupbox)

        #a list box labeled with a groupbox for editing the list of destination folders.
        self.destinations_groupbox = QGroupBox("Destination Folders:")
        dests_gbox_layout = QVBoxLayout()
        self.destinations_listbox = QListWidget()
        dests_gbox_layout.addWidget(self.destinations_listbox)
        self.destinations_add_button = QPushButton()
        self.destinations_del_button = QPushButton()
        self.destinations_add_button.setText("Add")
        self.destinations_del_button.setText("Delete")
        dbuttons_layout = QHBoxLayout()
        dbuttons_layout.addWidget(self.destinations_add_button)
        dbuttons_layout.addWidget(self.destinations_del_button)
        dests_gbox_layout.addLayout(dbuttons_layout)
        self.destinations_groupbox.setLayout(dests_gbox_layout)
        mainlayout.addWidget(self.destinations_groupbox)

        self.setLayout(mainlayout)