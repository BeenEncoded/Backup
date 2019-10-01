import json, os, configparser

from errors import *

class Configuration:
    '''
    This helps to centralize all code relating to saving, storing, getting, and 
    initializing global program configuration.
    '''
    def __init__(self):
        super(Configuration, self).__init__()

        #set up the configuration, initializing it with some sane defaults
        self.config = self._default_config()

        #here we make sure that we search for a config file, and 
        #if none is loaded we write it.
        if len(self.config.read(["backup.conf"])) == 0:
            self.save()
    
    #This function returns a default configuration.
    def _default_config(self):
        '''
        Returns the a default configuration for the entire program.
        '''
        c = configparser.ConfigParser()

        c['DEFAULT'] = {
            "profilepath": os.path.abspath("./backup_profiles.json")
        }

        c['ui'] = {
            "font_size": 12,
            "font": "monospaced"
        }

        c['BackupBehavior'] = {}

        return c

    def save(self):
        with open("backup.conf", 'w') as config_file:
            self.config.write(config_file)

class ProgramData:
    '''
    Stores and manages all global program data aside from configuration.
    It requires the program configuration to save and load.
    It does not load anything on construction.  This is to allow wiping the program
    data without deleting any files by simple assignment.
    '''
    def __init__(self, configuration):
        self.profiles = []
        self._config = configuration
    
    def load(self):
        self._load_profiles()

        # print("Loaded")
        # print(str([str(b) for b in self.profiles]))

    def save(self):
        self._save_profiles()

        # print("Saved")
        # print(str([str(b) for b in self.profiles]))

    def _load_profiles(self):
        self.profiles.clear()
        self.profiles = BackupProfile.readjson(self._config['DEFAULT']['profilepath'])
        #now we re-assign the ids because the json could have been edited by the luser...
        BackupProfile.reassignAllIds(self.profiles)
    
    def _save_profiles(self):
        BackupProfile.writejson(self.profiles, self._config['DEFAULT']['profilepath'])

class BackupProfile:
    '''
    ## Backup profile:
        string name
        list[string] sources
        list[string] destinations
        int ID
    
    ## Serialization:
        A static methods are provided to convert the object from and to a json.
    '''
    def __init__(self, dictionary=None):
        '''
        Passing a dictionary initializes a BackupProfile using a dictionary 
        {"names": ..., "sources": ..., "destinations":...,"ID": ...}
        This is primarily useful for loading from the json serialization.
        '''
        super(BackupProfile, self).__init__()

        if dictionary is None:
            self.name = ""
            self.sources = []
            self.destinations = []
            self.ID = 0
        else:
            self.name = dictionary["name"]
            self.sources = dictionary["sources"]
            self.destinations = dictionary["destinations"]
            self.ID = dictionary["id"]
    
    def __eq__(self, other):
        if not isinstance(other, BackupProfile):
            return False
        return ((self.sources == other.sources) and (self.destinations == other.destinations) and \
        (self.name == other.name) and (self.ID == other.ID))
    
    def __str__(self):
        return "Name: " + self.name + \
        "      Sources: " + str(self.sources) + \
        "      Destinations: " + str(self.destinations)

    def assignID(self, profiles):
        ids = [e.ID for e in profiles]
        self.ID = 0
        while self.ID in ids:
            self.ID += 1
    
    @staticmethod
    def getById(profiles, id):
        '''
        Returns the profile with the matching ID, or None if no profile
        or multiple profiles with the same ID was found.
        '''
        matches = [p for p in profiles if p.ID == id]
        if len(matches) == 0:
            return None
        elif len(matches) == 1:
            return matches[0]
        return None

    @staticmethod
    def reassignAllIds(profiles):
        for p in profiles:
            p.ID = -1
        for p in profiles:
            p.assignID(profiles)

    @staticmethod
    def writejson(profiles, filename):
        '''
        tojson(list[BackupProfile] profiles, string file)
        Writes a list of BackupProfile to a filename
        '''
        with open(filename, 'w') as file:
            return json.dump(\
            [{"name": p.name, "sources": p.sources, "destinations": p.destinations, "id": p.ID} for p in profiles], \
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
                return [BackupProfile(entry) for entry in x]
        return []
