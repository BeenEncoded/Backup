import os, queue
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, QRect, pyqtSlot
from PyQt5.QtGui import QFont

from data import BackupProfile
from globaldata import *
from errors import BackupProfileNotFoundError
from threads import BackupThread

class EditBackupProfileWidget(QWidget):
    def __init__(self, par, profile_id):
        '''
        Initializes this window to edit a backup profile.  Make sure that an
        ID
        '''
        global PDATA
        PDATA.load() #reload program data

        super(EditBackupProfileWidget, self).__init__(par)
        profiles = PDATA.profiles
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

        # Buttons to save, delete, and cancel the backup profile
        finalbuttons_layout = QHBoxLayout()
        self.finish_editing_button = QPushButton()
        self.delete_profile_button = QPushButton()
        self.cancel_edit_button = QPushButton("Cancel")
        self.finish_editing_button.setText("Finish Editing")
        self.delete_profile_button.setText("Delete Profile")
        finalbuttons_layout.addWidget(self.finish_editing_button)
        finalbuttons_layout.addWidget(self.cancel_edit_button)
        finalbuttons_layout.addWidget(self.delete_profile_button)
        mainlayout.addLayout(finalbuttons_layout)

        self.setLayout(mainlayout)
    
    def _apply_profile_to_fields(self):
        self.name_tbox.setText(self._profile.name)
        self.sources_listbox.clear()
        self.destinations_listbox.clear()
        self.sources_listbox.addItems(self._profile.sources)
        self.destinations_listbox.addItems(self._profile.destinations)

    def _connect_handlers(self):
        self.sources_add_button.clicked.connect(self._prompt_to_add_source_folders)
        self.destinations_add_button.clicked.connect(self._prompt_to_add_destination_folders)
        self.sources_del_button.clicked.connect(self._delete_selected_source)
        self.destinations_del_button.clicked.connect(self._delete_selected_destination)
        self.name_tbox.textChanged.connect(self._set_profile_name)
        self.finish_editing_button.clicked.connect(self._finish_editing_profile)
        self.cancel_edit_button.clicked.connect(self._cancel_edit)
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
        uiconfig = CONFIG.config['ui']
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
    
    @pyqtSlot()
    def _prompt_to_add_source_folders(self):
        self._add_to_list(self._profile.sources, self._directory_dialog("Select Sources to Backup"))
        self._apply_profile_to_fields()
    
    @pyqtSlot()
    def _prompt_to_add_destination_folders(self):
        self._add_to_list(self._profile.destinations, self._directory_dialog("Select Destinations to Target"))
        self._apply_profile_to_fields()
    
    @pyqtSlot()
    def _set_profile_name(self):
        self._profile.name = self.name_tbox.text()

    @pyqtSlot()
    def _delete_selected_source(self):
        self._remove_selected_item_from_list(self.sources_listbox, self._profile.getSources())
        self._apply_profile_to_fields()
    
    @pyqtSlot()
    def _delete_selected_destination(self):
        self._remove_selected_item_from_list(self.destinations_listbox, self._profile.destinations)
        self._apply_profile_to_fields()
    
    @pyqtSlot()
    def _delete_backup_profile(self):
        global PDATA
        profiles = PDATA.profiles
        if BackupProfile.getById(profiles, self._profile.ID) is not None:
            for x in range(0, len(profiles)):
                if profiles[x].ID == self._profile.ID:
                    profiles.pop(x)
                    PDATA.profiles = profiles
                    PDATA.save()
                    self.parent().setCentralWidget(ManageBackupsWidget(self.parent()))
                    break
        else:
            self.parent().setCentralWidget(ManageBackupsWidget(self.parent()))
    
    @pyqtSlot()
    def _finish_editing_profile(self):
        global PDATA
        profiles = PDATA.profiles
        backupfilename = CONFIG.config['DEFAULT']['profilepath']
        if BackupProfile.getById(profiles, self._profile.ID) is not None:
            for x in range(0, len(profiles)):
                if profiles[x].ID == self._profile.ID:
                    profiles[x] = self._profile
                    PDATA.profiles = profiles
                    PDATA.save()
                    self.parent().setCentralWidget(ManageBackupsWidget(self.parent()))
                    break
        else:
            self._profile.assignID(profiles)
            profiles.append(self._profile)
            PDATA.profiles = profiles
            PDATA.save()
            self.parent().setCentralWidget(ManageBackupsWidget(self.parent()))

    @pyqtSlot()
    def _cancel_edit(self):
        self.parent().setCentralWidget(ManageBackupsWidget(self.parent()))

    @pyqtSlot()
    def _set_enabled_buttons(self):
        self.sources_del_button.setEnabled(len(self.sources_listbox.selectedItems()) > 0)
        self.destinations_del_button.setEnabled(len(self.destinations_listbox.selectedItems()) > 0)
        self.delete_profile_button.setEnabled(BackupProfile.getById(PDATA.profiles, self._profile.ID) is not None)

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

class ManageBackupsWidget(QWidget):
    def __init__(self, parent):
        global PDATA

        super(ManageBackupsWidget, self).__init__(parent)
        self.parent().statusBar().showMessage("Loading Program Data...")
        PDATA.load()
        self.parent().statusBar().showMessage("Program Data Loaded.", 5000)
        self._profiles = PDATA.profiles

        self._init_layout()
        self._connect_handlers()
        self._set_enabled_buttons()
    
    def _init_layout(self):
        mainlayout = QVBoxLayout()

        self.newbackup_button = QPushButton("New Backup")
        mainlayout.addWidget(self.newbackup_button)

        # A labeled dropdown showing all the user's backups.  An edit button 
        # is next to it to allow editing the selected backup too.
        dropdownbox_layout = QHBoxLayout()
        self.backup_combobox = QComboBox()
        self.editbackup_button = QPushButton("<- Edit")
        backuplist_label = QLabel("Select a Backup: ")
        self.backup_combobox.addItems([p.name for p in self._profiles])
        dropdownbox_layout.addWidget(backuplist_label)
        dropdownbox_layout.addWidget(self.backup_combobox)
        dropdownbox_layout.addWidget(self.editbackup_button)
        mainlayout.addLayout(dropdownbox_layout)

        self.executebackup_button = QPushButton("Execute Selected Backup")
        mainlayout.addWidget(self.executebackup_button)

        self.setLayout(mainlayout)

    def _set_enabled_buttons(self):
        self.editbackup_button.setEnabled(len(self._profiles) > 0)
        self.executebackup_button.setEnabled((self.backup_combobox.currentIndex() >= 0) and (self.backup_combobox.currentIndex() < len(self._profiles)))

    def _connect_handlers(self):
        self.newbackup_button.clicked.connect(self._new_backup)
        self.editbackup_button.clicked.connect(self._edit_selected_backup)
        self.executebackup_button.clicked.connect(self._execute_backup)
    
    def _new_backup(self):
        self.parent().setCentralWidget(EditBackupProfileWidget(self.parent(), -1))
    
    def _execute_backup(self):
        i = self.backup_combobox.currentIndex()
        if i < 0:
            return
        if i < len(self._profiles):
            self.parent().setCentralWidget(ExecuteBackupWidget(self.parent(), self._profiles[i]))

    def _edit_selected_backup(self):
        i = self.backup_combobox.currentIndex()
        if i < 0:
            return
        if i < len(self._profiles):
            self.parent().setCentralWidget(EditBackupProfileWidget(self.parent(), self._profiles[i].ID))

class ExecuteBackupWidget(QWidget):
    def __init__(self, parent, backup):
        super(ExecuteBackupWidget, self).__init__(parent)
        self.parent().statusBar().showMessage("Execute: " + backup.name, 3000)
        self.backup = backup
        self.executions = []

        self._init_layout()
        self._connect_handlers()

    def _init_layout(self):
        mainlayout = QVBoxLayout()

        for entry in self.backup.sources:
            self.executions.append(QBackupExecution(None, self.backup, entry))
            mainlayout.addWidget(self.executions[(len(self.executions) - 1)])
        
        self.setLayout(mainlayout)
    
    def _connect_handlers(self):
        for e in self.executions:
            e.backupthread.show_error.connect(self._show_execution_error)
    
    def _show_execution_error(self, error):
        pass

class QBackupExecution(QWidget):
    def __init__(self, parent, backup, backup_source):
        super(QBackupExecution, self).__init__(parent)

        self.complete = False
        self.backup = backup
        self.source = backup_source
        self.backupthread = BackupThread()
        self.backupthread.backup = {"source": self.source, "destinations": self.backup.destinations}

        self._init_layout()
        self._connect_handlers()

    def _init_layout(self):
        mainlayout = QVBoxLayout()
        
        self.progressbar = QProgressBar()
        self.groupbox = QGroupBox(os.path.dirname(self.source))
        t = QVBoxLayout()
        t.addWidget(self.progressbar)
        self.groupbox.setLayout(t)
        
        mainlayout.addWidget(self.groupbox)
        self.setLayout(mainlayout)
    
    def _connect_handlers(self):
        self.backupthread.progress_update.connect(self._update_progress)
        self.backupthread.exec_finished.connect(self._backup_finished)

    @pyqtSlot(float)
    def _update_progress(self, percent):
        self.progressbar.setValue(percent)
    
    @pyqtSlot()
    def _backup_finished(self):
        self.backupthread.join()
        self.complete = True