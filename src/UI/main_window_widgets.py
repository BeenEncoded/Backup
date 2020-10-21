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

import os, typing, logging

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QPushButton
from PyQt5.QtWidgets import QLineEdit, QGroupBox, QLabel, QFileDialog, QAbstractItemView
from PyQt5.QtWidgets import QTreeView, QListView, QFileSystemModel, QComboBox, QPlainTextEdit
from PyQt5.QtWidgets import QMessageBox, QScrollArea, QProgressBar, QFontDialog, QSpinBox
from PyQt5.QtCore import Qt, pyqtSlot, pyqtSignal
from PyQt5.QtGui import QFont

from data import BackupProfile, BackupMapping
from globaldata import PDATA, CONFIG
from errors import BackupProfileNotFoundError
from threads import BackupThread, ThreadManager, PruneBackupThread
from iterator import recursivecopy
from algorithms import ProcessStatus

logger = logging.getLogger("UI.MainWindowWidgets")

def add_to_list(ob, src):
    '''
    Adds objects in src to ob, but only if they do not exist in ob.
    '''
    if ob is not None and src is not None:
        if not isinstance(src, list):
            src = [src]
        for entry in src:
            if entry not in ob:
                ob.append(entry)

class EditBackupProfileWidget(QWidget):
    '''
    EditBackupProfileWidget:
        Edits a backup profile.
    '''
    def __init__(self, par, profile_id):
        '''
        Initializes this window to edit a backup profile.  Make sure that an
        ID
        '''
        global PDATA

        super(EditBackupProfileWidget, self).__init__(par)
        profiles = PDATA.profiles
        if profile_id > -1:
            self._profile = BackupProfile.get_by_id(profiles, profile_id)
            if self._profile is None:
                raise BackupProfileNotFoundError("Profile with id " + str(profile_id) + " could not be found!")
        else:
            self._profile = BackupProfile()
            self._profile.assign_id(profiles)
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

        #source and destination editing:
        listeditlayout = QHBoxLayout()
        listeditlayout.addWidget(EditPathListWidget(self._profile.sources, "Source Folders", self))
        listeditlayout.addWidget(EditPathListWidget(self._profile.destinations, "Destination Folders", self))
        mainlayout.addLayout(listeditlayout)

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

    def _connect_handlers(self):
        self.name_tbox.textChanged.connect(self._set_profile_name)
        self.finish_editing_button.clicked.connect(self._finish_editing_profile)
        self.cancel_edit_button.clicked.connect(self._cancel_edit)
        self.delete_profile_button.clicked.connect(self._delete_backup_profile)

    @pyqtSlot()
    def _set_profile_name(self):
        self._profile.name = self.name_tbox.text()

    @pyqtSlot()
    def _delete_backup_profile(self):
        logger.warning("delete button clicked")
        global PDATA
        profiles = PDATA.profiles
        if BackupProfile.get_by_id(profiles, self._profile.ID) is not None:
            for x in range(0, len(profiles)):
                if profiles[x].ID == self._profile.ID:
                    logger.warning("Deleted profile " + str(profiles[x]))
                    profiles.pop(x)
                    PDATA.save()
                    self.parent().setCentralWidget(ManageBackupsWidget(self.parent()))
                    break
        else:
            self.parent().setCentralWidget(ManageBackupsWidget(self.parent()))
    
    @pyqtSlot()
    def _finish_editing_profile(self):
        global PDATA
        profiles = PDATA.profiles
        if BackupProfile.get_by_id(profiles, self._profile.ID) is not None:
            for x in range(0, len(profiles)):
                if profiles[x].ID == self._profile.ID:
                    profiles[x] = self._profile
                    PDATA.save()
                    self.parent().setCentralWidget(ManageBackupsWidget(self.parent()))
                    break
        else:
            self._profile.assign_id(profiles)
            profiles.append(self._profile)
            PDATA.profiles = profiles
            PDATA.save()
            self.parent().setCentralWidget(ManageBackupsWidget(self.parent()))

    @pyqtSlot()
    def _cancel_edit(self):
        logger.warning("Cancel button clicked.  Canceled edit")
        self.parent().setCentralWidget(ManageBackupsWidget(self.parent()))

    @pyqtSlot()
    def _set_enabled_buttons(self):
        self.delete_profile_button.setEnabled(BackupProfile.get_by_id(PDATA.profiles, self._profile.ID) is not None)


class EditConfigurationWidget(QWidget):
    _loglevels = {
            "critical": logging.CRITICAL,
            "error":    logging.ERROR,
            "warning":  logging.WARNING,
            "info":     logging.INFO,
            "debug":    logging.DEBUG}

    def __init__(self, parent):
        super(EditConfigurationWidget, self).__init__(parent)
        self._layout()
        self._connectHandlers()

        self.newfont = None
        self._update_inputs()

    def __del__(self):
        pass

    def _layout(self) -> None:
        mainlayout = QVBoxLayout()

        title = QLabel("Configuration")
        title.setAlignment(Qt.AlignHCenter)
        mainlayout.addWidget(title)

        settinggroup = QGroupBox("Settings")
        gboxlayout = QVBoxLayout()
        self.loglevel_box = QComboBox()
        self.loglevel_box.addItems(EditConfigurationWidget._loglevels.keys())
        self.loglevel_box.setToolTip("While debug will show the most information, it " + 
            "can have a large performance impact.  Warning is the recommended level.")
        gboxlayout.addLayout(self._hlayout(QLabel("Log Level: "), self.loglevel_box))

        self.fonteditbutton = QPushButton("")
        gboxlayout.addWidget(self.fonteditbutton)

        self.threadbox = QSpinBox()
        self.threadbox.setToolTip("This is the max number of threads that will " + 
            "be used to run your backup.  Note that 1 thread per folder will be used.  If you're running linux " + 
            "and just back up /home, then this will probably have negligible effect.")
        gboxlayout.addLayout(self._hlayout(QLabel("Max threads: "), self.threadbox))

        settinggroup.setLayout(gboxlayout)
        mainlayout.addWidget(settinggroup)
        mainlayout.addStretch()

        self.done_button = QPushButton("Save")
        self.cancel_button = QPushButton("Cancel")
        mainlayout.addLayout(self._hlayout(self.done_button, self.cancel_button))

        self.setLayout(mainlayout)

    def _connectHandlers(self) -> None:
        self.done_button.clicked.connect(self.save_and_quit)
        self.cancel_button.clicked.connect(self.cancelAndQuit)
        self.fonteditbutton.clicked.connect(self.setFont)

    @pyqtSlot()
    def save_and_quit(self) -> None:
        logger.info("Saving configuration and quitting the config edit menu.")
        self._apply_changes()
        CONFIG.save()
        self.parent().setCentralWidget(ManageBackupsWidget(self.parent()))

    @pyqtSlot()
    def cancelAndQuit(self) -> None:
        logger.info("Quitting the configuration menu without saving.")
        self.parent().setCentralWidget(ManageBackupsWidget(self.parent()))

        #when we change the font, it will set the window's current font to
        # give the user a preview.  Reset this change:
        self.parent().setFont(QFont(str(CONFIG['ui']['font']), int(CONFIG['ui']['font_size'])))

    @pyqtSlot()
    def setFont(self) -> None:
        self.newfont, ok = QFontDialog.getFont(self.newfont if self.newfont else QFont(str(CONFIG['ui']['font']), int(CONFIG['ui']['font_size'])), self)
        if ok:
            self.parent().setFont(self.newfont)
            self.fonteditbutton.setText(f"Font: {self.newfont.family()} {str(self.newfont.pointSize())}")

    def _update_inputs(self) -> None:
        self.loglevel_box.setCurrentText(CONFIG["DEFAULT"]["loglevel"])
        self.fonteditbutton.setText(f"Font: {CONFIG['ui']['font']} {CONFIG['ui']['font_size']}")
        self.threadbox.setValue(int(CONFIG['BackupBehavior']['threadcount']))
        if self.newfont is not None:
            self.parent().setFont(self.newfont)

    def _apply_changes(self) -> None:
        global CONFIG
        CONFIG["DEFAULT"]["loglevel"] = self.loglevel_box.currentText()
        logging.getLogger().setLevel(EditConfigurationWidget._loglevels[CONFIG["DEFAULT"]["loglevel"]])
        if self.newfont is not None:
            CONFIG['ui']['font'] = self.newfont.family()
            CONFIG['ui']['font_size'] = str(self.newfont.pointSize())
            self.parent().setFont(QFont(str(CONFIG['ui']['font']), int(CONFIG['ui']['font_size'])))
        CONFIG['BackupBehavior']['threadcount'] = str(self.threadbox.value())

    def _hlayout(self, *objects) -> QHBoxLayout:
        layout = QHBoxLayout()
        for o in objects: layout.addWidget(o)
        return layout
    
    def _vlayout(self, *objects) -> QVBoxLayout:
        layout = QVBoxLayout()
        for o in objects: layout.addWidget(o)
        return layout


class EditPathListWidget(QWidget):
    '''
    Sub-widget
    Allows a user to edit a list of paths.  They can add, delete, and edit with a textbox.
    '''
    def __init__(self, pathlist: list=None, listname: str="Paths", parent=None):
        super(EditPathListWidget, self).__init__(parent)
        self.listname = listname
        self._data = pathlist
        self._layout()
        self._handlers()
        self._applyfields()
    
    def _layout(self) -> None:
        self.mainlayout = QVBoxLayout()

        #a list box labeled with a groupbox for editing the list of destination folders.
        self.destinations_groupbox = QGroupBox(self.listname + ":")
        dests_gbox_layout = QVBoxLayout()

        textboxlayout = QHBoxLayout()
        self.directorytextbox = QLineEdit()
        self.entertextbutton = QPushButton("Apply")
        textboxlayout.addWidget(self.directorytextbox)
        textboxlayout.addWidget(self.entertextbutton)
        dests_gbox_layout.addLayout(textboxlayout)

        self.listbox = QListWidget()
        dests_gbox_layout.addWidget(self.listbox)
        self.add_button = QPushButton("Add")
        self.del_button = QPushButton("Delete")
        dbuttons_layout = QHBoxLayout()
        dbuttons_layout.addWidget(self.add_button)
        dbuttons_layout.addWidget(self.del_button)
        dests_gbox_layout.addLayout(dbuttons_layout)
        self.destinations_groupbox.setLayout(dests_gbox_layout)
        self.mainlayout.addWidget(self.destinations_groupbox)
        self.setLayout(self.mainlayout)

    def _handlers(self) -> None:
        self.listbox.itemSelectionChanged.connect(self._set_enabled_buttons)
        self.listbox.itemClicked.connect(self._set_enabled_buttons)
        self.listbox.currentRowChanged.connect(self._set_enabled_buttons)

        self.directorytextbox.textEdited.connect(self._editdirectory)
        self.directorytextbox.returnPressed.connect(self._apply_edit)
        self.entertextbutton.clicked.connect(self._apply_edit)

        self.add_button.clicked.connect(self._add_paths)
        self.del_button.clicked.connect(self._remove_selected_path)

    def _applyfields(self) -> None:
        '''
        Updates the UI to reflect changes to the data being stored.
        Usually performed after a change (edit from a textbox is 'applied', etc...)
        '''
        self.listbox.clear()
        self.listbox.addItems(self._data)
        self._set_enabled_buttons()

    def _directory_dialog(self, title="Select Paths:"):
        uiconfig = CONFIG.config['ui']
        fdiag = QFileDialog(parent=self, caption=title)
        fdiag.setFileMode(QFileDialog.DirectoryOnly)
        fdiag.setDirectory(os.path.abspath("/"))
        fdiag.setAcceptDrops(False)
        fdiag.setFont(QFont(uiconfig['font'], int(uiconfig['font_size'])))
        fdiag.setWindowTitle(title)
        fdiag.setViewMode(QFileDialog.Detail)
        fdiag.setModal(True)
        fdiag.setOption(QFileDialog.DontUseNativeDialog, True)

        for v in fdiag.findChildren((QListView, QTreeView)):
            if isinstance(v.model(), QFileSystemModel):
                v.setSelectionMode(QAbstractItemView.MultiSelection)

        if fdiag.exec():
            return fdiag.selectedFiles()
        return []

    @pyqtSlot()
    def _apply_edit(self) -> None:
        if len(self.listbox.selectedItems()) > 0:
            if self.listbox.currentRow() < len(self._data):
                self._data[self.listbox.currentRow()] = self.directorytextbox.text()
                self._applyfields()
            else:
                row = self.listbox.currentRow() # noqa: F841
                size = len(self._data) # noqa: F841
                logger.error("listbox.currentRow >= len(self._data)!!  Currentrow: {row} size of _data (pathlist): {size}")
        else:
            logger.warning("{EditPathListWidget._apply_edit.__qualname__}: called with nothing selected in the list!!  WHY?!?!?!")

    @pyqtSlot(str)
    def _editdirectory(self, text: str="") -> None:
        if len(self.listbox.selectedItems()) > 0:
            if self.listbox.currentRow() < len(self._data):
                self.entertextbutton.setEnabled(self.directorytextbox.text() != self._data[self.listbox.currentRow()])
            else:
                row = self.listbox.currentRow() # noqa: F841
                size = len(self._data) # noqa: F841
                logger.error("listbox.currentRow >= len(self._data)!!  Currentrow: {row} size of _data (pathlist): {size}")
        else:
            logger.warning("{EditPathListWidget._editdirectory.__qualname__}: called with nothing selected in the list!!  WHY?!?!?!")

    @pyqtSlot()
    def _add_paths(self):
        add_to_list(self._data, self._directory_dialog(self.listname))
        self._applyfields()
    
    @pyqtSlot()
    def _remove_selected_path(self) -> None:
        if len(self.listbox.selectedItems()) > 0:
            index = self.listbox.currentRow()
            if len(self._data) > 0 and (index < len(self._data)):
                self._data.pop(index)
                logger.debug("Removed item at position " + str(index))
            else:
                #printing relevant errors... this should not happen, but just in case
                #we will want to know what happened.
                if len(self._data) <= 0:
                    logger.error("Failed to remove item: pathlist is empty!")
                elif index >= len(self._data):
                    logger.error("Failed to remove item: index " + str(index) + 
                        " is greater than the size of the pathlist (" + str(len(self._data)) + ")")
            #now that the element was removed, we update the ui to
            #reflect the changes.
            self._applyfields()

    @pyqtSlot()
    def _set_enabled_buttons(self):
        itemselected = (len(self.listbox.selectedItems()) > 0)
        self.del_button.setEnabled(itemselected)
        self.directorytextbox.setEnabled(itemselected)
        self.entertextbutton.setEnabled(False)
        self.directorytextbox.setText(self._data[self.listbox.currentRow()] if itemselected else "")


class ManageBackupsWidget(QWidget):
    '''
    CentralWidget:
        Manages backups
        The first thing the user sees when they start up the program.
    '''
    def __init__(self, parent):
        global PDATA

        super(ManageBackupsWidget, self).__init__(parent)
        self.parent().statusBar().showMessage("Loading Program Data...")
        self.parent().statusBar().showMessage("Program Data Loaded.", 5000)
        self._profiles = PDATA.profiles

        self._init_layout()
        self._connect_handlers()
        self._set_enabled_buttons()
    
    def _init_layout(self):
        self.parent().setWindowTitle("Backup")
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

        mainlayout.addStretch()

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
    
    @pyqtSlot()
    def _new_backup(self):
        self.parent().setCentralWidget(EditBackupProfileWidget(self.parent(), -1))
    
    @pyqtSlot()
    def _execute_backup(self):
        i = self.backup_combobox.currentIndex()
        if i < 0:
            return
        if i < len(self._profiles):
            self.parent().setCentralWidget(ExecuteBackupWidget(self.parent(), self._profiles[i]))

    @pyqtSlot()
    def _edit_selected_backup(self):
        i = self.backup_combobox.currentIndex()
        if i < 0:
            return
        if i < len(self._profiles):
            self.parent().setCentralWidget(EditBackupProfileWidget(self.parent(), self._profiles[i].ID))


class ExecuteBackupWidget(QWidget):
    def __init__(self, parent, backup: BackupProfile):
        super(ExecuteBackupWidget, self).__init__(parent)
        self.parent().statusBar().showMessage("Execute: " + backup.name, 3000)
        self.backup = backup
        self.backupmapping = backup.find_mapping(CONFIG)
        self.executions = []
        
        self.threadmanager = ThreadManager(int(CONFIG["BackupBehavior"]["threadcount"]))
        self.threadmanager.throttle = 20
        self.threadmanager.start()

        self._init_layout()
        self._connect_handlers()
        
        for e in self.executions:
            e.startExecution()
    
    def __del__(self) -> None:
        if self.executions is not None:
            for e in self.executions: e.stopExecution()
        self.threadmanager.halt_thread()

    def _init_layout(self):
        self.mainlayout = QVBoxLayout()

        #add execution widgets
        self.mainlayout.addWidget(self._execution_widgets(self.backup))
        
        #errors textbox
        gbox = QGroupBox("Errors:")
        gbox_layout = QVBoxLayout()
        self.errors_textedit = QPlainTextEdit()
        gbox_layout.addWidget(self.errors_textedit)
        gbox.setLayout(gbox_layout)
        self.mainlayout.addWidget(gbox)

        #Cancel button
        self.cancel_button = QPushButton("Cancel")
        self.mainlayout.addWidget(self.cancel_button)

        #some settings:
        self.errors_textedit.setReadOnly(True)
        
        self.setLayout(self.mainlayout)

        if not self._can_backup(self.backup):
            self.cancel_button.setText("Return")
    
    def _connect_handlers(self):
        for e in self.executions:
            e.backupthread.qcom.show_error.connect(self._show_execution_error)
            e.removeself.connect(self._remove_completed)
        self.cancel_button.clicked.connect(self._cancel_backups)
        if hasattr(self, "prunewidget"):
            self.prunewidget.pruneCompleted.connect(self._onPruneComplete)
    
    def _invalid_paths(self, backup_profile) -> (typing.List[str], typing.List[str]):
        '''
        makes sure that all the paths in the passed profile are ok.  This function
        should return true if and only if the souces and destiations of the backup
        are valid.

        returns [invalid_sources], [invalid_destinations]
        '''
        invalid_src = [entry for entry in backup_profile.sources if not os.path.isdir(entry)]
        invalid_dest = [entry for entry in backup_profile.destinations if not os.path.isdir(entry)]
        return invalid_src, invalid_dest

    def _can_backup(self, backup) -> bool:
        valid_sources = [s for s in backup.sources if os.path.isdir(s)]
        valid_destinations = [d for d in backup.destinations if os.path.isdir(d)]
        return (len(valid_sources) > 0) and (len(valid_destinations) > 0) and (len(self.executions) > 0)

    def _execution_widgets(self, backup: BackupProfile) -> QScrollArea:
        #executions qwidgets
        scrollingview = QScrollArea()
        scrollingview.setWidgetResizable(True)
        gb = QGroupBox()
        gb.setFlat(True)
        gblayout = QVBoxLayout()

        #first, though, we need to be sure that everything is good:
        invalid_sources, invalid_destinations = self._invalid_paths(backup)

        valid_sources = [source for source in backup.sources if os.path.isdir(source)]
        valid_destinations = [dest for dest in backup.destinations if os.path.isdir(dest)]
        
        if len(invalid_destinations) > 0:
            message = "Can not backup to certain destinations: "
            for entry in invalid_destinations:
                message += (os.linesep + entry)
            logger.warning(message)
            QMessageBox.warning(self, "Invalid Destination Directories", message)
        if len(invalid_sources) > 0:
            message = "Can not backup certain sources: "
            for entry in invalid_sources:
                message += (os.linesep + entry)
            logger.warning(message)
            QMessageBox.warning(self, "Invalid Source Directories", message)

        if (len(valid_sources) > 0) and (len(valid_destinations) > 0):
            gblayout.addWidget(self._label_list("Destinations: ", valid_destinations))
            for entry in valid_sources:
                self.executions.append(QBackupExecution(self, 
                    {"source": entry, "destinations": valid_destinations, "newdest": self.backupmapping[entry]}, 
                    self.threadmanager))
                
                gblayout.addWidget(self.executions[(len(self.executions) - 1)])
            self.prunewidget = QPruneBackupExecution(self, self.backup, self.backupmapping)
            gblayout.addWidget(self.prunewidget)
            self.prunewidget.hide()
        else:
            if len(valid_sources) == 0:
                logger.error("No valid sources to backup from")
            if len(valid_destinations) == 0:
                logger.error("No valid destinations to backup to.")
            QMessageBox.critical(self.parent(), "Error!", "Unable to perform the backup.")
            messagelabel = QLabel("Nothing to backup!")
            messagelabel.setAlignment(Qt.AlignCenter)
            gblayout.addWidget(messagelabel)
        
        gb.setLayout(gblayout)
        scrollingview.setWidget(gb)
        return scrollingview
    
    def _label_list(self, name: str="No name set", paths: list=[]) -> QGroupBox:
        gb = QGroupBox(name)
        glayout = QVBoxLayout()

        for p in paths:
            glayout.addWidget(QLabel(p))
        gb.setLayout(glayout)
        return gb

    @pyqtSlot(recursivecopy.UnexpectedError)
    def _show_execution_error(self, error):
        self.errors_textedit.appendPlainText(str(error))

    @pyqtSlot()
    def _cancel_backups(self):
        if self.cancel_button.text() == "Cancel":
            logger.warning("Cancel button clicked!")
        self.parent().setCentralWidget(ManageBackupsWidget(self.parent()))

    @pyqtSlot()
    def _onPruneComplete(self)->None:
        self.cancel_button.setText("Back")
        QMessageBox.information(self, "Complete!", "Backup Finished.")

    @pyqtSlot()
    def _remove_completed(self):
        for x in range(0, len(self.executions)):
            if self.executions[x].complete:
                self.executions[x].hide()
        tempexecs = [e for e in self.executions if not e.isHidden()]
        if len(tempexecs) == 0:
            self.prunewidget.start_process()


class QBackupExecution(QWidget):
    removeself = pyqtSignal()

    def __init__(self, parent, backup: dict = None, manager: ThreadManager = None):
        super(QBackupExecution, self).__init__(parent)
        if backup is None:
            backup = {"source": "", "destinations": [], "newdest": None}

        logger.info("instantiating new QBackupExecution: " + str(backup))
        self.complete = False
        self.threadmanager = manager
        self.backupthread = BackupThread(backup)

        self._init_layout()
        self._connect_handlers()
    
    def _init_layout(self):
        mainlayout = QVBoxLayout()
        
        self.progressbar = QProgressBar()
        self.currentop_label = QLabel()
        self.groupbox = QGroupBox(self.backupthread.backup["source"])
        t = QVBoxLayout()
        t.addWidget(self.progressbar)
        t.addWidget(self.currentop_label)
        self.groupbox.setLayout(t)
        
        mainlayout.addWidget(self.groupbox)
        
        self.setLayout(mainlayout)
    
    def _connect_handlers(self):
        if not hasattr(self.backupthread, "qcom"):
            self.backupthread.qcom = BackupThread.QtComObject()
        self.backupthread.qcom.progress_update.connect(self._update_progress)
        self.backupthread.qcom.exec_finished.connect(self._backup_finished)

    def startExecution(self):
        self.threadmanager.addThread(self.backupthread)

    def stopExecution(self):
        if self.backupthread.isAlive(): logger.warning("Aborting backup in progress: " + str(self.backupthread.backup))
        self.backupthread.cancelExec()
        #the thread should pass-through its run() method and die, then be picked
        #up by the thread manager.

    @pyqtSlot(ProcessStatus)
    def _update_progress(self, status):
        self.progressbar.setValue(status.percent)
        self.currentop_label.setText(status.message)
    
    @pyqtSlot()
    def _backup_finished(self):
        self.complete = True
        self.removeself.emit()


class QPruneBackupExecution(QWidget):
    pruneCompleted = pyqtSignal()

    def __init__(self, parent, backup: BackupProfile = None, mapping: BackupMapping = None):
        super(QPruneBackupExecution, self).__init__(parent)
        self.prunethread = PruneBackupThread(backup, mapping)

        self._layout()
        self._connect_handlers()
    
    def __del__(self):
        if self.prunethread is not None:
            if self.prunethread.isAlive():
                self.prunethread.join()
            self.prunethread = None

    def _layout(self) -> None:
        groupbox = QGroupBox(f"Pruning \"{self.prunethread.backup.name}\"")
        gblayout = QVBoxLayout()

        self.statuslabel = QLabel("Preparing...")
        self.progressbar = QProgressBar()

        gblayout.addWidget(self.progressbar)
        gblayout.addWidget(self.statuslabel)
        groupbox.setLayout(gblayout)

        mainlayout = QVBoxLayout()
        mainlayout.addWidget(groupbox)
        self.setLayout(mainlayout)
    
    def _connect_handlers(self) -> None:
        self.prunethread.statusUpdated.connect(self.update_progress)
        self.prunethread.finished.connect(self.complete_operation)

    def start_process(self) -> None:
        if self.isHidden():
            self.setVisible(True)
        self.prunethread.start()

    @pyqtSlot(ProcessStatus)
    def update_progress(self, status: ProcessStatus = None) -> None:
        logger.debug(f"{QPruneBackupExecution.update_progress.__qualname__}: signal caught.  Updating progressbar.")
        self.progressbar.setValue(status.percent)
        self.statuslabel.setText(status.message)

    @pyqtSlot()
    def complete_operation(self) -> None:
        logger.debug(f"{QPruneBackupExecution.complete_operation.__qualname__}: called -> raisining the pruneCompleted signal!")
        self.pruneCompleted.emit()
    
