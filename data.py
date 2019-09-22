import json

from errors import *

class BackupProfile:
    '''
    ## Backup profile:
        string name
        list[string] sources
        list[string] destinations
    
    ## Serialization:
        A static methods are provided to convert the object from and to a json.
    '''
    def __init__(self):
        self._name = ""
        self._sources = []
        self._destinations = []

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
    def json(profiles):
        '''
        json(list[BackupProfile] profiles)
        '''
        return json.dumps([{"name": p.getName(), "sources": p.getSources(), "destinations": p.getDestinations()} for p in profiles], \
            indent=4, sort_keys=True)