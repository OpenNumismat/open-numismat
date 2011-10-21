# -*- coding: utf-8 -*-

from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import Qt

class Settings(QtCore.QObject):
    # TODO: Change backup location
    BackupFolder = '../db/backup/'
    
    def __init__(self, parent=None):
        super(Settings, self).__init__(parent)
        self.settings = QtCore.QSettings()
        self.language = self.__language()
        self.backupFolder = self.__backupFolder()
    
    def save(self):
        self.settings.setValue('mainwindow/locale', self.language)
        self.settings.setValue('mainwindow/backup', self.backupFolder)
    
    def __language(self):
        locale = self.settings.value('mainwindow/locale')
        if not locale:
            locale = QtCore.QLocale.system().name()
        
        return locale
    
    def __backupFolder(self):
        folder = self.settings.value('mainwindow/backup')
        if not folder:
            folder = QtCore.QDir(self.BackupFolder).absolutePath()
        
        return folder

class SettingsDialog(QtGui.QDialog):
    Languages = [("English", 'en_UK'), ("Русский", 'ru_RU')]
    
    def __init__(self, parent=None):
        super(SettingsDialog, self).__init__(parent)
        
        settings = Settings()
        
        mainLayout = QtGui.QGridLayout()
        
        current = 0
        self.languageSelector = QtGui.QComboBox(self)
        for i, lang in enumerate(self.Languages):
            self.languageSelector.addItem(lang[0], lang[1])
            if settings.language == lang[1]:
                current = i
        self.languageSelector.setCurrentIndex(current)
        
        mainLayout.addWidget(QtGui.QLabel(self.tr("Language")), 0, 0)
        mainLayout.addWidget(self.languageSelector, 0, 1, 1, 2)
        
        self.backupFolder = QtGui.QLineEdit(self)
        self.backupFolder.setText(settings.backupFolder)
        style = QtGui.QApplication.style()
        icon = style.standardIcon(QtGui.QStyle.SP_DirOpenIcon)
        self.backupFolderButton = QtGui.QPushButton(icon, '', self)
        self.backupFolderButton.clicked.connect(self.backupButtonClicked)
        
        mainLayout.addWidget(QtGui.QLabel(self.tr("Backup folder")), 1, 0)
        mainLayout.addWidget(self.backupFolder, 1, 1)
        mainLayout.addWidget(self.backupFolderButton, 1, 2)
        
        buttonBox = QtGui.QDialogButtonBox(Qt.Horizontal)
        buttonBox.addButton(QtGui.QDialogButtonBox.Ok)
        buttonBox.addButton(QtGui.QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.save)
        buttonBox.rejected.connect(self.reject)

        layout = QtGui.QVBoxLayout(self)
        layout.addLayout(mainLayout)
        layout.addWidget(buttonBox)

        self.setLayout(layout)
    
    def backupButtonClicked(self):
        folder = QtGui.QFileDialog.getExistingDirectory(self, self.tr("Backup folder"), self.backupFolder.text())
        if folder:
            self.backupFolder.setText(folder)

    def save(self):
        settings = Settings()

        current = self.languageSelector.currentIndex()
        settings.language = self.languageSelector.itemData(current)

        settings.backupFolder = self.backupFolder.text()

        settings.save()

        self.accept()
