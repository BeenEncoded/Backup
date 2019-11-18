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

import sys
import atexit
import os
from UI.MainWindow import display_gui
from logging.handlers import RotatingFileHandler
from globaldata import PDATA, LOGS_FOLDER, CONFIG, LOG_LEVEL, LOGFILE
import logging


def setup_logging():
    if not os.path.exists(LOGS_FOLDER):
        os.makedirs(LOGS_FOLDER)

    root = logging.getLogger()
    f = logging.Formatter(
        "%(asctime)s [%(name)s] [%(levelname)s] -> %(message)s")
    sh = logging.StreamHandler(sys.stdout)
    #fh = logging.FileHandler(LOGFILE)
    fh = RotatingFileHandler(
        LOGFILE,
        mode='a',
        maxBytes=((2**20) * 2.5),
        backupCount=2,
        encoding=None,
        delay=False)

    sh.setFormatter(f)
    fh.setFormatter(f)

    root.addHandler(sh)
    root.addHandler(fh)
    root.setLevel(LOG_LEVEL)
    root.info("log level: " + str(LOG_LEVEL))


def onexit():
    global CONFIG
    global PDATA
    CONFIG.save()
    PDATA.save()
    logging.getLogger().info("[PROGRAM END]")


if __name__ == "__main__":
    PDATA.load()
    setup_logging()
    logging.getLogger("main").info("[PROGRAM START]")
    logging.getLogger("main").debug(
        "Configuration: " + str(CONFIG.config._sections))
    logging.getLogger("main").debug("ProgramData: " + str(PDATA))

    atexit.register(onexit)

    returnvalue = -1
    try:
        returnvalue = display_gui(sys.argv)
    except:  # noqa E722
        logging.getLogger().exception("CRITICAL EXCEPTION")
    sys.exit(returnvalue)
