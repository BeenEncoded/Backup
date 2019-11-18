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


class CopyPathError(Exception):
    def __init__(self, message, errors=[]):
        super(CopyPathError, self).__init__(message)
        self.errors = errors

    def __str__(self):
        return "CopyPathError(\"" + self.message + "\"  errors: " + str(self.errors) + ")"


class IncompleteCopyError(Exception):
    def __init__(self, message, errors):
        super(IncompleteCopyError, self).__init__(message)
        self.errors = errors

    def __str__(self):
        return "IncompleteCopyError(\"" + self.message + "\"  errors: " + str(self.errors) + ")"


class CopyFolderError(Exception):
    def __init__(self, message, errors):
        super(CopyFolderError, self).__init__(message)
        self.errors = errors

    def __str__(self):
        return "CopyFolderError(\"" + self.message + "\"  errors: " + str(self.errors) + ")"


class WrongArgumentTypeError(Exception):
    def __init__(self, message, errors):
        super(CopyFolderError, self).__init__(message)
        self.errors = errors


class BackupProfileNotFoundError(Exception):
    def __init__(self, message, errors):
        super(CopyFolderError, self).__init__(message)
        self.errors = errors

    def __str__(self):
        return "BackupProfileNotFoundError: " + self.message