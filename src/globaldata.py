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
import semver
import os
import logging

from data import Configuration, ProgramData

# This file contains globals

# Global non-constant data
CONFIG = Configuration()
PDATA = ProgramData(_config=CONFIG.config)

#global constants
VERSION = semver.VersionInfo(1, 2, 0, "beta")
LOGS_FOLDER = os.path.abspath("./logs")
LOGFILE = (LOGS_FOLDER + os.path.sep + "backup_program.log")
LOG_LEVEL = {
    "critical": logging.CRITICAL,
    "error":    logging.ERROR,
    "warning":  logging.WARNING,
    "info":     logging.INFO,
    "debug":    logging.DEBUG,
    "notset":   logging.NOTSET}[CONFIG.config['DEFAULT']['loglevel']]
