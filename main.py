import sys, atexit, os
from UI.MainWindow import display_gui
from globaldata import *
from data import BackupProfile

def onexit():
    print("Cleaning up globals...")
    global CONFIG
    global PDATA
    CONFIG.save()
    PDATA.save()

if __name__ == "__main__":
    atexit.register(onexit)
    sys.exit(display_gui(sys.argv))