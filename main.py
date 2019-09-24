import sys, atexit, os
from UI.MainWindow import display_gui
from globaldata import *
from data import BackupProfile

def onexit():
    print("Cleaning up globals...")
    global CONFIG
    global BACKUPS
    CONFIG.save()

    with open(CONFIG.getConfig()['DEFAULT']['profilepath'], 'w') as bfile:
        BackupProfile.writejson(BACKUPS, bfile)

def load_globals():
    print("Loading globals...")
    global BACKUPS
    global CONFIG
    if os.path.exists(CONFIG.getConfig()['DEFAULT']['profilepath']):
        with open(CONFIG.getConfig()['DEFAULT']['profilepath'], 'r') as backupfile:
            BACKUPS = BackupProfile.readjson(backupfile)
        if len(BACKUPS) > 0:
            for b in BACKUPS:
                b.assignID(BACKUPS)

if __name__ == "__main__":
    atexit.register(onexit)
    load_globals()
    sys.exit(display_gui(sys.argv))