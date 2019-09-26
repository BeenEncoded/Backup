import os
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from data import BackupProfile
from globaldata import *
from errors import BackupProfileNotFoundError

class EditBackupProfileWidget(QWidget):
    def __init__(self, parent, profile_id):
        '''
        Initializes this window to edit a backup profile.  Make sure that an
        ID
        '''
        global PDATA
        PDATA.load() #reload program data

        super(EditBackupProfileWidget, self).__init__(parent)
        profiles = PDATA.getProfiles()
        if profile_id > -1:
            self._profile = BackupProfile.getById(profiles, profile_id)
            if self._profile is None:
                raise BackupProfileNotFoundError("Profile with id " + str(profile_id) + " could not be found!")
        else:
            self._profile = BackupProfile()
            self._profile.assignID(profiles)
        self._init_layout()
        self._apply_profile_to_fields()
        self._connect_handlers()
        self._set_enabled_buttons()
    
    def _init_layout(self):
        self.parent().setWindowTitle("Edit Backup")
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
        self.sources_del_button = QPushButton()
        self.sources_add_button.setText("Add")
        self.sources_del_button.setText("Delete")
        sources_buttons.addWidget(self.sources_add_button)
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

        # Buttons to save or completely delete the backup profile
        finalbuttons_layout = QHBoxLayout()
        self.finish_editing_button = QPushButton()
        self.delete_profile_button = QPushButton()
        self.finish_editing_button.setText("Finish Editing")
        self.delete_profile_button.setText("Delete Profile")
        finalbuttons_layout.addWidget(self.finish_editing_button)
        finalbuttons_layout.addWidget(self.delete_profile_button)
        mainlayout.addLayout(finalbuttons_layout)

        self.setLayout(mainlayout)
    
    def _apply_profile_to_fields(self):
        self.name_tbox.setText(self._profile.getName())
        self.sources_listbox.clear()
        self.destinations_listbox.clear()
        self.sources_listbox.addItems(self._profile.getSources())
        self.destinations_listbox.addItems(self._profile.getDestinations())

    def _connect_handlers(self):
        self.sources_add_button.clicked.connect(self._prompt_to_add_source_folders)
        self.destinations_add_button.clicked.connect(self._prompt_to_add_destination_folders)
        self.sources_del_button.clicked.connect(self._delete_selected_source)
        self.destinations_del_button.clicked.connect(self._delete_selected_destination)
        self.name_tbox.textChanged.connect(self._set_profile_name)
        self.finish_editing_button.clicked.connect(self._finish_editing_profile)
        self.delete_profile_button.clicked.connect(self._delete_backup_profile)

        #listbox: these signals are used to update whether buttons are enabled.
        self.destinations_listbox.itemSelectionChanged.connect(self._set_enabled_buttons)
        self.destinations_listbox.itemClicked.connect(self._set_enabled_buttons)
        self.destinations_listbox.currentRowChanged.connect(self._set_enabled_buttons)
        self.sources_listbox.itemSelectionChanged.connect(self._set_enabled_buttons)
        self.sources_listbox.itemClicked.connect(self._set_enabled_buttons)
        self.sources_listbox.currentRowChanged.connect(self._set_enabled_buttons)

    def _directory_dialog(self, title="Select a Directory"):
        global CONFIG
        uiconfig = CONFIG.getConfig()['ui']
        fdiag = QFileDialog(parent=self, caption=title)
        fdiag.setFileMode(QFileDialog.DirectoryOnly)
        fdiag.setDirectory(os.path.abspath("/"))
        fdiag.setAcceptDrops(False)
        fdiag.setFont(QFont(uiconfig['font'], int(uiconfig['font_size'])))
        fdiag.setWindowTitle(title)
        fdiag.setViewMode(QFileDialog.Detail)
        fdiag.setModal(True)

        if fdiag.exec():
            return fdiag.selectedFiles()
        return []
    
    def _prompt_to_add_source_folders(self):
        self._add_to_list(self._profile.getSources(), self._directory_dialog("Select Sources to Backup"))
        self._apply_profile_to_fields()
    
    def _prompt_to_add_destination_folders(self):
        self._add_to_list(self._profile.getDestinations(), self._directory_dialog("Select Destinations to Target"))
        self._apply_profile_to_fields()
    
    def _set_profile_name(self):
        self._profile.setName(self.name_tbox.text())

    def _delete_selected_source(self):
        self._remove_selected_item_from_list(self.sources_listbox, self._profile.getSources())
        self._apply_profile_to_fields()
    
    def _delete_selected_destination(self):
        self._remove_selected_item_from_list(self.destinations_listbox, self._profile.getDestinations())
        self._apply_profile_to_fields()
    
    def _delete_backup_profile(self):
        global PDATA
        profiles = PDATA.getProfiles()
        print("delete profile clicked")
        if BackupProfile.getById(profiles, self._profile.getID()) is not None:
            for x in range(0, len(profiles)):
                if profiles[x].getID() == self._profile.getID():
                    profiles.pop(x)
                    PDATA.setProfiles(profiles)
                    PDATA.save()
                    self.parent().setCentralWidget(ExecuteBackupProfileWidget(self.parent()))
                    break
        else:
            self.parent().setCentralWidget(ExecuteBackupProfileWidget(self.parent()))
    
    def _finish_editing_profile(self):
        global PDATA
        profiles = PDATA.getProfiles()
        print("finished editing clicked")
        backupfilename = CONFIG.getConfig()['DEFAULT']['profilepath']
        if BackupProfile.getById(profiles, self._profile.getID()) is not None:
            for x in range(0, len(profiles)):
                if profiles[x].getID() == self._profile.getID():
                    profiles[x] = self._profile
                    PDATA.setProfiles(profiles)
                    PDATA.save()
                    self.parent().setCentralWidget(ExecuteBackupProfileWidget(self.parent()))
                    break
        else:
            self._profile.assignID(profiles)
            profiles.append(self._profile)
            PDATA.setProfiles(profiles)
            PDATA.save()
            self.parent().setCentralWidget(ExecuteBackupProfileWidget(self.parent()))

    def _set_enabled_buttons(self):
        global PDATA

        self.sources_del_button.setEnabled(len(self.sources_listbox.selectedItems()) > 0)
        self.destinations_del_button.setEnabled(len(self.destinations_listbox.selectedItems()) > 0)
        self.delete_profile_button.setEnabled(BackupProfile.getById(PDATA.getProfiles(), self._profile.getID()) is not None)

    def _remove_selected_item_from_list(self, listwidget, listob):
        '''
        removes an item from the list widget and an associated list object.
        '''
        if len(listwidget.selectedItems()) > 0:
            listob.pop(listwidget.currentRow())

    def _add_to_list(self, ob, src):
        '''
        Adds objects in src to ob, but only if they do not exist in ob.
        '''
        if ob is not None and src is not None:
            if not isinstance(src, list):
                src = [src]
            for entry in src:
                if entry not in ob:
                    ob.append(entry)

class ExecuteBackupProfileWidget(QWidget):
    def __init__(self, parent):
        global PDATA

        super(ExecuteBackupProfileWidget, self).__init__(parent)
        self.parent().statusBar().showMessage("Loading Program Data...")
        PDATA.load()
        self.parent().statusBar().showMessage("Program Data Loaded.", 5000)
        self._profiles = PDATA.getProfiles()
        self._init_layout()
    
    def _init_layout(self):
        mainlayout = QVBoxLayout()

        dropdownbox_layout = QHBoxLayout()
        self.backup_combobox = QComboBox()
        backuplist_label = QLabel("Select a Backup: ")
        self.backup_combobox.addItems([p.getName() for p in self._profiles])
        dropdownbox_layout.addWidget(backuplist_label)
        dropdownbox_layout.addWidget(self.backup_combobox)
        mainlayout.addLayout(dropdownbox_layout)

        self.setLayout(mainlayout)