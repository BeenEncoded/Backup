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

import json, os, configparser, dataclasses, logging
from pathlib import Path

logger = logging.getLogger("data")


class Configuration:
    '''
    This helps to centralize all code relating to saving, storing, getting, and 
    initializing global program configuration.
    '''
    home_directory: str = str(Path.home())
    program_home: str = (home_directory + os.sep + ".backup")
    filename: str = (program_home + os.sep + "backup.conf")

    def __init__(self):
        logger.debug("Configuration instantiated.")

        # set up the configuration, initializing it with some sane defaults
        self.config = self._default_config()

        # here we make sure that we search for a config file, and
        # if none is loaded we write it.
        if len(self.config.read([Configuration.filename])) == 0:
            logger.warning("Configuration file not found, saving to " +
                           Configuration.filename)
            self.save()

    # This function returns a default configuration.
    def _default_config(self):
        '''
        Returns the a default configuration for the entire program.
        '''
        c = configparser.ConfigParser()

        c['DEFAULT'] = {
            "profilepath": os.path.join(Configuration.program_home, "backup_profiles.json"),
            "loglevel": "warning",
            "ignorederrors": "" #a space-separated list of error types.  ex. "PathTooLongError PathNotWorkingError"
        }

        c['ui'] = {
            "font_size": 12,
            "font": "monospaced"
        }

        c['BackupBehavior'] = {
            "threadcount": 3
        }

        return c

    def save(self) -> None:
        logger.info("Saving configuration")
        Path(Configuration.program_home).mkdir(parents=True, exist_ok=True)
        if not os.path.isdir(Configuration.program_home):
            raise NotADirectoryError(f"\"{Configuration.program_home}\" does not exist!")
        with open(Configuration.filename, 'w') as config_file:
            self.config.write(config_file)

    def __repr__(self):
        some_stuff = []
        for key in self.config:
            some_stuff.append(f"SECTION[{key}]")
            some_stuff += [f"{x}: {self.config[key][x]}" for x in self.config[key]]
        return os.linesep.join(some_stuff)

    def __getitem__(self, key):
        return self.config[key]

    def __setitem__(self, key, value):
        self.config[key] = value

@dataclasses.dataclass
class ProgramData:
    '''
    Stores and manages all global program data aside from configuration.
    It requires the program configuration to save and load.
    It does not load anything on construction.  This is to allow wiping the program
    data without deleting any files by simple assignment.

    This object is not responsible for configuration manegement, loading, or saving.  It simply
    requires it for use in determining locations of files and such.
    '''

    _config: Configuration = Configuration()
    profiles: list = dataclasses.field(default_factory=list)

    def load(self):
        logger.info("loading program data...")
        self._load_profiles()

        # print("Loaded")
        # print(str([str(b) for b in self.profiles]))
        logger.info("program data loaded.")

    def save(self):
        logger.info("program data being saved to the disk...")
        self._save_profiles()

        # print("Saved")
        # print(str([str(b) for b in self.profiles]))
        logger.info("program data saved.")

    def _load_profiles(self):
        logger.debug("loading backup profiles...")
        self.profiles.clear()
        self.profiles = BackupProfile.readjson(
            self._config['DEFAULT']['profilepath'])
        # now we re-assign the ids because the json could have been edited by the luser...
        BackupProfile.reassignAllIds(self.profiles)
        logger.debug("backup profiles loaded")

    def _save_profiles(self):
        logger.debug("saving backup profiles")
        BackupProfile.writejson(
            self.profiles, self._config['DEFAULT']['profilepath'])
        logger.debug("backup profiles saved")


@dataclasses.dataclass
class BackupProfile:
    name: str = ""
    sources: list = dataclasses.field(default_factory=list)
    destinations: list = dataclasses.field(default_factory=list)
    ID: int = 0

    def __str__(self):
        return "Name: " + self.name + \
            "      Sources: " + str(self.sources) + \
            "      Destinations: " + str(self.destinations)

    def assignID(self, profiles):
        logger.debug("Assigning a new id to backup profile: " + self.name)
        ids = [e.ID for e in profiles]
        self.ID = 0
        while self.ID in ids:
            self.ID += 1
        logger.debug("New id for \"" + self.name + "\" is " + str(self.ID))

    @staticmethod
    def getById(profiles, id):
        '''
        Returns the profile with the matching ID, or None if no profile
        or multiple profiles with the same ID was found.
        '''
        logger.debug("Finding backup profile with id: " + str(id))
        matches = [p for p in profiles if p.ID == id]
        if len(matches) == 0:
            return None
        elif len(matches) == 1:
            return matches[0]
        return None

    @staticmethod
    def reassignAllIds(profiles):
        logger.debug("Reassigning all backup profile ids.")
        for p in profiles: p.ID = -1
        for p in profiles: p.assignID(profiles)

    @staticmethod
    def writejson(profiles, filename):
        '''
        tojson(list[BackupProfile] profiles, string file)
        Writes a list of BackupProfile to a filename
        '''
        with open(filename, 'w') as file:
            return json.dump(
                [{"name": p.name, "sources": p.sources,
                    "destinations": p.destinations, "id": p.ID} for p in profiles],
                fp=file, indent=4, sort_keys=True)

    @staticmethod
    def readjson(filename):
        '''
        fromjson(string rawjson)
        returns a list[BackupProfile]        
        '''
        if os.path.isfile(filename):
            with open(filename, 'r') as file:
                x = json.load(file)
                return [_profile_from_dict(entry) for entry in x]
        return []


def _profile_from_dict(profile: dict = {"name": "", "sources": [], "destinations": [], "id": 0}) -> BackupProfile:
    return BackupProfile(profile["name"], profile["sources"], profile["destinations"], profile["id"])
