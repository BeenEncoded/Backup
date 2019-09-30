import random

from data import BackupProfile

def randomstring(minl, maxl):
    '''
    Returns a random string with a length [minl, maxl]
    '''
    s = ""
    length = random.randint(minl, maxl)
    for x in range(0, length):
        s += chr(random.randint(0, 255))
    return s

def randomBackupProfile():
    '''
    returns a random BackupProfile for testing.
    '''
    profile = BackupProfile()
    for x in range(0, random.randint(2, 10)):
        profile.destinations.append(sanitize_string(randomstring(20, 50)))
    for x in range(0, random.randint(1, 5)):
        profile.sources.append(sanitize_string(randomstring(20,50)))
    profile.name = sanitize_string(randomstring(10, 20))
    return profile

def sanitize_string(s):
    '''
    escapes characters that will cause mayhem and destruction
    returns the sanitized string.
    '''
    chars = "\b\n\'\"{\t}[]\\"
    for x in range(0, len(chars)):
        s = s.replace(chars[x], "")
    return s