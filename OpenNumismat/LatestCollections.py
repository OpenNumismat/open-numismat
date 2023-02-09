from PyQt6.QtCore import QObject, QSettings
from PyQt6.QtGui import QAction

import OpenNumismat
from OpenNumismat.Collection.Collection import Collection


class LatestCollections(QObject):
    DefaultCollectionName = OpenNumismat.HOME_PATH + "/demo.db"
    SettingsKey = 'collection/latest'
    LatestCount = 7

    def __init__(self, parent=None):
        super().__init__(parent)

        self.settings = QSettings()

    # Create menu actions
    def actions(self):
        actions = []
        for i in range(LatestCollections.LatestCount):
            key = self.__key(i)
            fileName = self.settings.value(key)
            if fileName:
                title = Collection.fileNameToCollectionName(fileName)
                act = QAction(title, self)
                act.setData(fileName)
                actions.append(act)

        return actions

    # Return latest opened collection file name
    def latest(self):
        fileName = self.settings.value(self.SettingsKey)
        if not fileName:
            fileName = LatestCollections.DefaultCollectionName

        return fileName

    def add(self, fileName):
        # Get stored latest collections
        values = []
        for i in range(LatestCollections.LatestCount):
            val = self.settings.value(self.__key(i))
            if val:
                values.append(val)

        values.insert(0, fileName)
        # Uniqify collections name (order preserving)
        checked = []
        for e in values:
            if e not in checked:
                checked.append(e)
        values = checked

        # Store updated latest collections
        for i, value in enumerate(values):
            self.settings.setValue(self.__key(i), value)

        # Remove unused settings entries
        for i in range(len(values), LatestCollections.LatestCount):
            self.settings.remove(self.__key(i))

        # Store latest collection for auto opening
        self.settings.setValue(self.SettingsKey, fileName)

    def delete(self, fileName):
        for i in range(LatestCollections.LatestCount):
            value = self.settings.value(self.__key(i))
            if value == fileName:
                self.settings.remove(self.__key(i))

    def __key(self, i):
        return self.SettingsKey + str(i + 1)
