import json, os, configparser

from errors import *

#TODO: fix this... thing
config = configparser.ConfigParser()
config['DEFAULT'] = {
    "profilepath": os.path.abspath("./")
}
config['BackupBehavior'] = {}

#here we make sure that we search for a config file, and 
#if none is loaded we write it.
if len(config.read(["backup.conf"])) == 0:
    with open("backup.conf", "w") as config_file:
        print("Writing default configuration, none was found!")
        config.write(config_file)
else:
    print("Successfully loaded configuration!")

class BackupProfile():
    '''
    ## Backup profile:
        string name
        list[string] sources
        list[string] destinations
    
    ## Serialization:
        A static methods are provided to convert the object from and to a json.
    '''
    def __init__(self, dictionary=None):
        '''
        Passing a dictionary initializes a BackupProfile using a dictionary {"names": ..., "sources": ..., "destinations":...}
        This is primarily useful for loading from the json serialization.
        '''
        super(BackupProfile, self).__init__()

        if dictionary is None:
            self._name = ""
            self._sources = []
            self._destinations = []
        else:
            self._name = dictionary["name"]
            self._sources = dictionary["sources"]
            self._destinations = dictionary["destinations"]

    def __eq__(self, other):
        if not isinstance(other, BackupProfile):
            return False
        return ((self._sources == other._sources) and (self._destinations == other._destinations))
    
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
    
    @staticmethod
    def writejson(profiles, file):
        '''
        tojson(list[BackupProfile] profiles, TextIOBase file)
        returns the json string nicely formatted.
        '''
        return json.dump([{"name": p.getName(), "sources": p.getSources(), "destinations": p.getDestinations()} for p in profiles], \
            fp=file, indent=4, sort_keys=True)
    
    @staticmethod
    def readjson(file):
        '''
        fromjson(string rawjson)
        returns a list[BackupProfile]
        '''
        x = json.load(file)
        return [BackupProfile(entry) for entry in x]