# -*- coding: utf-8 -*-

from PyQt5.QtCore import QLocale, QSettings

import OpenNumismat


class BaseSettings(dict):
    def __init__(self, autoSave=False):
        self.__autoSave = autoSave
        self.__items = {}

    def keys(self):
        raise NotImplementedError

    def items(self):
        result = []
        for key in self.keys():
            result.append((key, self.__getitem__(key)))
        return result

    def values(self):
        result = []
        for key in self.keys():
            result.append(self.__getitem__(key))
        return result

    def __getitem__(self, key):
        if key in self.__items:
            return self.__items[key]

        if key in self.keys():
            value = self._getValue(key)
            self.__items[key] = value

            return value
        else:
            raise KeyError(key)

    def __setitem__(self, key, val):
        if key in self.keys():
            self.__items[key] = val
            if self.__autoSave:
                self._saveValue(key, val)
        else:
            raise KeyError(key)

    def setAutoSave(self, autoSave):
        self.__autoSave = autoSave

    def autoSave(self):
        return self.__autoSave

    def save(self):
        for key in self.keys():
            self._saveValue(key, self.__getitem__(key))

    def _getValue(self, key):
        raise NotImplementedError

    def _saveValue(self, key, val):
        raise NotImplementedError


def _getLocale():
    locale = QLocale.system().name()
    if '_' in locale:
        return locale.split('_')[0]
    else:
        return locale


class Settings(BaseSettings):
    Default = {'locale': _getLocale(),
               'backup': OpenNumismat.HOME_PATH + "/backup/",
               'autobackup': True,
               'autobackup_depth': 25,
               'reference': OpenNumismat.HOME_PATH + "/reference.ref",
               'error': True,
               'speedup': 0,
               'updates': False,
               'template': 'full',
               'check_coin_title': True,
               'check_coin_duplicate': True,
               'images_by_default': 2}

    def __init__(self, autoSave=False):
        super().__init__(autoSave)

        self.settings = QSettings()

    def keys(self):
        return self.Default.keys()

    def _getValue(self, key):
        if key in ('error', 'updates', 'autobackup',
                   'check_coin_title', 'check_coin_duplicate'):
            value = self.settings.value('mainwindow/' + key, self.Default[key],
                                        type=bool)
        elif key in ('images_by_default', 'autobackup_depth'):
            value = self.settings.value('mainwindow/' + key, self.Default[key],
                                        type=int)
        else:
            value = self.settings.value('mainwindow/' + key, self.Default[key])

        return value

    def _saveValue(self, key, val):
        self.settings.setValue('mainwindow/' + key, val)
