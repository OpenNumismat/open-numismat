# -*- coding: utf-8 -*-

from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import Qt

from Collection.CollectionFields import CollectionFields
import version

class Settings(QtCore.QObject):
    BackupFolder = version.AppDir + "/backup/"
    Reference = version.AppDir + "/reference.db"
    
    def __init__(self, parent=None):
        super(Settings, self).__init__(parent)
        self.settings = QtCore.QSettings()
        self.language = self.__language()
        self.backupFolder = self.__backupFolder()
        self.reference = self.__reference()
        self.sendError = self.__sendError()
    
    def save(self):
        self.settings.setValue('mainwindow/locale', self.language)
        self.settings.setValue('mainwindow/backup', self.backupFolder)
        self.settings.setValue('mainwindow/reference', self.reference)
        self.settings.setValue('mainwindow/error', self.sendError)
    
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

    def __reference(self):
        file = self.settings.value('mainwindow/reference')
        if not file:
            file = QtCore.QDir(self.Reference).absolutePath()
        
        return file

    def __sendError(self):
        error = self.settings.value('mainwindow/error')
        if not error:
            return False
        
        return error == 'true'

class MainSettingsPage(QtGui.QWidget):
    Languages = [("English", 'en_GB'), ("Русский", 'ru_RU')]
    
    def __init__(self, parent=None):
        super(MainSettingsPage, self).__init__(parent)

        settings = Settings()
        
        layout = QtGui.QGridLayout()
        
        current = 0
        self.languageSelector = QtGui.QComboBox(self)
        for i, lang in enumerate(self.Languages):
            self.languageSelector.addItem(lang[0], lang[1])
            if settings.language == lang[1]:
                current = i
        self.languageSelector.setCurrentIndex(current)
        
        layout.addWidget(QtGui.QLabel(self.tr("Language")), 0, 0)
        layout.addWidget(self.languageSelector, 0, 1, 1, 2)
        
        self.backupFolder = QtGui.QLineEdit(self)
        self.backupFolder.setText(settings.backupFolder)
        style = QtGui.QApplication.style()
        icon = style.standardIcon(QtGui.QStyle.SP_DirOpenIcon)
        self.backupFolderButton = QtGui.QPushButton(icon, '', self)
        self.backupFolderButton.clicked.connect(self.backupButtonClicked)
        
        layout.addWidget(QtGui.QLabel(self.tr("Backup folder")), 1, 0)
        layout.addWidget(self.backupFolder, 1, 1)
        layout.addWidget(self.backupFolderButton, 1, 2)
        
        self.reference = QtGui.QLineEdit(self)
        self.reference.setText(settings.reference)
        icon = style.standardIcon(QtGui.QStyle.SP_DialogOpenButton)
        self.referenceButton = QtGui.QPushButton(icon, '', self)
        self.referenceButton.clicked.connect(self.referenceButtonClicked)
        
        layout.addWidget(QtGui.QLabel(self.tr("Reference")), 2, 0)
        layout.addWidget(self.reference, 2, 1)
        layout.addWidget(self.referenceButton, 2, 2)
        
        self.errorSending = QtGui.QCheckBox(self.tr("Send error info to author"), self)
        self.errorSending.setChecked(settings.sendError)
        layout.addWidget(self.errorSending, 3, 0, 1, 2)
        
        self.setLayout(layout)

    def backupButtonClicked(self):
        folder = QtGui.QFileDialog.getExistingDirectory(self, self.tr("Backup folder"), self.backupFolder.text())
        if folder:
            self.backupFolder.setText(folder)

    def referenceButtonClicked(self):
        file = QtGui.QFileDialog.getOpenFileName(self, self.tr("Select reference"), self.reference.text(), "*.db")
        if file:
            self.reference.setText(file)

    def save(self):
        settings = Settings()

        current = self.languageSelector.currentIndex()
        settings.language = self.languageSelector.itemData(current)
        settings.backupFolder = self.backupFolder.text()
        settings.reference = self.reference.text()
        settings.sendError = self.errorSending.isChecked()

        settings.save()

class FieldsSettingsPage(QtGui.QWidget):
    DataRole = Qt.UserRole

    def __init__(self, db, parent=None):
        super(FieldsSettingsPage, self).__init__(parent)

        self.listWidget = QtGui.QListWidget(self)
        self.listWidget.setWrapping(True)

        self.fields = CollectionFields(db)
        for field in self.fields:
            item = QtGui.QListWidgetItem(field.title, self.listWidget)
            item.setData(self.DataRole, field)
            item.setFlags(Qt.ItemIsEditable | Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            checked = Qt.Unchecked
            if field.enabled:
                checked = Qt.Checked
            item.setCheckState(checked)
            self.listWidget.addItem(item)

        layout = QtGui.QVBoxLayout(self)
        layout.addWidget(QtGui.QLabel(self.tr("Global enabled fields:"), self))
        layout.addWidget(self.listWidget)

        self.setLayout(layout)

    def save(self):
        for i in range(self.listWidget.count()):
            item = self.listWidget.item(i)
            field = item.data(self.DataRole)
            field.enabled = (item.checkState() == Qt.Checked)
            field.title = item.text()
        
        self.fields.save()

class SettingsDialog(QtGui.QDialog):
    def __init__(self, db, parent=None):
        super(SettingsDialog, self).__init__(parent)
        
        mainPage = MainSettingsPage(self)
        fieldsPage = FieldsSettingsPage(db, self)

        self.tab = QtGui.QTabWidget(self)
        self.tab.addTab(mainPage, self.tr("Main"))
        self.tab.addTab(fieldsPage, self.tr("Fields"))
        
        buttonBox = QtGui.QDialogButtonBox(Qt.Horizontal)
        buttonBox.addButton(QtGui.QDialogButtonBox.Ok)
        buttonBox.addButton(QtGui.QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.save)
        buttonBox.rejected.connect(self.reject)

        layout = QtGui.QVBoxLayout(self)
        layout.addWidget(self.tab)
        layout.addWidget(buttonBox)

        self.setLayout(layout)
        
    def save(self):
        for i in range(self.tab.count()):
            page = self.tab.widget(i)
            page.save()

        self.accept()
