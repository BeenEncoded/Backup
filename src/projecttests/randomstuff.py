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