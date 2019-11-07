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

import sys, atexit, os
from UI.MainWindow import display_gui
from globaldata import *
from data import BackupProfile
import logging

def setup_logging():
    root = logging.getLogger()
    f = logging.Formatter("%(asctime)s [%(name)s] [%(levelname)s] -> %(message)s")
    sh = logging.StreamHandler(sys.stdout)
    fh = logging.FileHandler(LOGFILE)

    sh.setFormatter(f)
    fh.setFormatter(f)

    root.addHandler(sh)
    root.addHandler(fh)
    root.setLevel(LOG_LEVEL)
    print("log level: " + str(LOG_LEVEL))

def onexit():
    global CONFIG
    global PDATA
    CONFIG.save()
    PDATA.save()

if __name__ == "__main__":
    setup_logging()
    logging.getLogger("main").info("logger initialized")
    atexit.register(onexit)
    
    returnvalue = -1
    try:
        returnvalue = display_gui(sys.argv)
    except:
        logging.getLogger().exception("CRITICAL EXCEPTION")
    sys.exit(returnvalue)