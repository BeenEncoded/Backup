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
        self._config = self._default_config()

        #here we make sure that we search for a config file, and 
        #if none is loaded we write it.
        if len(self._config.read(["backup.conf"])) == 0:
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

    def getConfig(self):
        return self._config
    
    def save(self):
        with open("backup.conf", 'w') as config_file:
            self._config.write(config_file)

class BackupProfile():
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
            self._name = ""
            self._sources = []
            self._destinations = []
            self._ID = 0
        else:
            self._name = dictionary["name"]
            self._sources = dictionary["sources"]
            self._destinations = dictionary["destinations"]
            self._ID = dictionary["id"]

    def __eq__(self, other):
        if not isinstance(other, BackupProfile):
            return False
        return ((self._sources == other._sources) and (self._destinations == other._destinations) and \
        (self._name == other._name) and (self._ID == other._ID))
    
    def __str__(self):
        return """
        Name: """ + self._name + """\n
        Sources: """ + str(self._sources) + """\n
        Destinations: """ + str(self._destinations) + "\n"

    def setName(self, name):
        if not isinstance(name, str):
            raise WrongArgumentTypeError("BackupProfile.setName(string name): wrong argument type passed as \'name\'!")
        self._name = name
    
    def getName(self):
        return self._name

    def getSources(self):
        return self._sources
    
    def setSources(self, value):
        self._sources = value
    
    def getDestinations(self):
        return self._destinations
    
    def setDestinations(self, value):
        self._destinations = value
    
    def getID(self):
        return self._ID
    
    def setID(self, newid):
        self._ID = newid

    def assignID(self, profiles):
        ids = [e.getID() for e in profiles]
        self._ID = 0
        while self._ID in ids:
            self._ID += 1
    
    @staticmethod
    def writejson(profiles, file):
        '''
        tojson(list[BackupProfile] profiles, TextIOBase file)
        returns the json string nicely formatted.
        '''
        return json.dump(\
        [{"name": p.getName(), "sources": p.getSources(), "destinations": p.getDestinations(), "id": p.getID()} for p in profiles], \
            fp=file, indent=4, sort_keys=True)
    
    @staticmethod
    def readjson(file):
        '''
        fromjson(string rawjson)
        returns a list[BackupProfile]        
        '''        
        x = json.load(file)        
        return [BackupProfile(entry) for entry in x]