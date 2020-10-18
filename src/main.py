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

# First is logging:
import commandline
import logging
import os
import sys
import atexit
import argparse
from typing import List
from logging.handlers import RotatingFileHandler
from UI.MainWindow import display_gui

from globaldata import LOGFILE, LOGS_FOLDER, LOG_LEVEL, PDATA, CONFIG


def setup_logging():
    if not os.path.exists(LOGS_FOLDER):
        os.makedirs(LOGS_FOLDER)

    root = logging.getLogger()
    f = logging.Formatter("%(asctime)s [%(name)s] [%(levelname)s] -> %(message)s")
    sh = logging.StreamHandler(sys.stdout)
    # fh = logging.FileHandler(LOGFILE)
    fh = RotatingFileHandler(
        LOGFILE,
        mode='a',
        maxBytes=((2 ** 20) * 2.5),
        backupCount=2,
        encoding=None,
        delay=False)

    sh.setFormatter(f)
    fh.setFormatter(f)

    if len(sys.argv) <= 1: root.addHandler(sh)
    root.addHandler(fh)
    root.setLevel(LOG_LEVEL)
    root.info("log level: " + str(LOG_LEVEL))


setup_logging()
logger = logging.getLogger(__name__)


def validate_source(d: str = "") -> bool:
    if os.path.isdir(d):
        return True
    raise argparse.ArgumentTypeError(
        r"The source folder is not a directory.  Please pass a path that represents an existing folder.")


def validate_destination(d: str = "") -> bool:
    if os.path.isdir(d): return True
    raise argparse.ArgumentTypeError(
        r"The destination folder is not a directory.  Please pass a path that represents an existing folder.")


def setup_argparse() -> argparse.ArgumentParser:
    helptext = r"""This software backs up a user's computer using backup profiles."""

    arguments = argparse.ArgumentParser(description=helptext)
    mugroup = arguments.add_mutually_exclusive_group()

    mugroup.add_argument("--profile", "-p", help="A backup profile.  This is loaded " +
                                                 "from the configuration file.  You will have to create a backup " +
                                                 "profile before using this option.  It is recommended you do so through the UI.")

    mugroup.add_argument("-l", "--list", help="Lists the backup profiles available to use.",
                         action="store_true")

    mugroup.add_argument("--listerrortypes", "-e", help="List the types of errors that can be reported." +
                                                        "  Use this to ignore certain types of errors.",
                         action="store_true")

    arguments.add_argument("--loglevel", help="Set the log level for this run.  Levels are:" +
                                              "\ncritical\nerror\nwarning\ninfo\ndebug")
    return arguments


def onexit():
    CONFIG.save()
    PDATA.save()
    logger.info("[PROGRAM END]")


def cmd(args: List[str] = []) -> int:
    PDATA.load()
    logger.info("[PROGRAM START]")
    logger.debug("Configuration: " + repr(CONFIG))
    logger.debug("ProgramData: " + str(PDATA))
    arguments = setup_argparse().parse_args(
        args)  # for some reason parse args takes it upon itself to terminate the goddamn program...

    return commandline.run_commandline(arguments)


def gui(args: List[str] = []) -> int:
    PDATA.load()
    logger.info("[PROGRAM START]")
    logger.debug("Configuration: " + repr(CONFIG))
    logger.debug("ProgramData: " + str(PDATA))

    returnvalue = -1
    try:
        returnvalue = display_gui(sys.argv)
    except:  # noqa E722
        logging.getLogger().exception("CRITICAL EXCEPTION")
    return returnvalue


def command_cmd(args: argparse.ArgumentParser = None) -> bool:
    """
    Returns true if arguments were passed to the program.  This will
    mean the user wants a command line!  YAYAYAYAYAYAY
    """
    return len(args) > 1


if __name__ == "__main__":
    atexit.register(onexit)

    if command_cmd(sys.argv):
        sys.exit(cmd(sys.argv[1:]))
    logger.info("No arguments passed.  Starting graphical user interface.")
    sys.exit(gui(sys.argv))
