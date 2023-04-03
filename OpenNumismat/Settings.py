import os.path

from PySide6.QtCore import QLocale, QSettings

import OpenNumismat


class BaseSettings(dict):
    def __init__(self, autoSave=False):
        super().__init__()

        self.autoSave = autoSave

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
        if key in self.__dict__:
            return self.__dict__[key]

        if key in self.keys():
            value = self._getValue(key)
            self.__dict__[key] = value

            return value
        else:
            raise KeyError(key)

    def __setitem__(self, key, val):
        if key in self.keys():
            self.__dict__[key] = val
            if self.autoSave:
                self._saveValue(key, val)
        else:
            raise KeyError(key)

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
    default_template = os.path.join(OpenNumismat.PRJ_PATH, 'templates', 'full')
    Default = {
        'locale': _getLocale(),
        'backup': OpenNumismat.HOME_PATH + "/backup/",
        'autobackup': True,
        'autobackup_depth': 25,
        'reference': OpenNumismat.HOME_PATH + "/reference.ref",
        'error': True,
        'speedup': 1,
        'updates': False,
        'template': default_template,
        'images_by_default': 2,
        'colnect_locale': _getLocale(),
        'colnect_skip_currency': True,
        'ans_split_denomination': True,
        'ans_locale_en': False,
        'ans_trim_title': True,
        'numista_split_denomination': True,
        'numista_currency': 'EUR',
        'map_type': 0,
        'built_in_viewer': True,
        'font_size': 0,
        'use_blaf_palette': True,
        'style': '',
    }

    def __init__(self, autoSave=False):
        super().__init__(autoSave)

        self.settings = QSettings()

    def keys(self):
        return self.Default.keys()

    def _getValue(self, key):
        if key in (
            'error',
            'updates',
            'autobackup',
            'colnect_skip_currency',
            'ans_split_denomination',
            'ans_locale_en',
            'ans_trim_title',
            'built_in_viewer',
            'numista_split_denomination',
            'use_blaf_palette',
        ):
            value = self.settings.value('mainwindow/' + key, self.Default[key],
                                        type=bool)
        elif key in (
            'images_by_default',
            'autobackup_depth',
            'speedup',
            'map_type',
            'font_size',
        ):
            value = self.settings.value('mainwindow/' + key, self.Default[key],
                                        type=int)
        else:
            value = self.settings.value('mainwindow/' + key, self.Default[key])

            if key == 'template':
                if not os.path.isdir(value):
                    value = self.default_template

        return value

    def _saveValue(self, key, val):
        self.settings.setValue('mainwindow/' + key, val)
