from PyQt5 import QtCore
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QAction

import OpenNumismat
from OpenNumismat.Collection.Collection import Collection


class LatestCollectionAction(QAction):
    latestTriggered = pyqtSignal(str)

    def __init__(self, key, parent=None):
        super(LatestCollectionAction, self).__init__(parent)

        settings = QtCore.QSettings()
        self.fileName = settings.value(key)
        self.setText(Collection.fileNameToCollectionName(self.fileName))
        self.triggered.connect(self.trigger)

    def trigger(self):
        self.latestTriggered.emit(self.fileName)


class LatestCollections(QtCore.QObject):
    DefaultCollectionName = OpenNumismat.HOME_PATH + "/demo.db"
    SettingsKey = 'collection/latest'
    LatestCount = 5

    def __init__(self, parent=None):
        super(LatestCollections, self).__init__(parent)

        self.settings = QtCore.QSettings()

    # Create menu actions
    def actions(self):
        actions = []
        for i in range(LatestCollections.LatestCount):
            key = self.__key(i)
            if self.settings.value(key):
                actions.append(LatestCollectionAction(key, self))

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
        for i in range(len(values)):
            self.settings.setValue(self.__key(i), values[i])

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
