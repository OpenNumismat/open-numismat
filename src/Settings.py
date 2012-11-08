# -*- coding: utf-8 -*-

from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import Qt

from EditCoinDialog.FormItems import NumberEdit
import version

class Settings(QtCore.QObject):
    BackupFolder = version.AppDir + "/backup/"
    Reference = version.AppDir + "/reference.ref"
    
    def __init__(self, parent=None):
        super(Settings, self).__init__(parent)
        self.settings = QtCore.QSettings()
        self.language = self.__language()
        self.backupFolder = self.__backupFolder()
        self.reference = self.__reference()
        self.sendError = self.__sendError()
        self.fractionType = self.__fractionType()
    
    def save(self):
        self.settings.setValue('mainwindow/locale', self.language)
        self.settings.setValue('mainwindow/backup', self.backupFolder)
        self.settings.setValue('mainwindow/reference', self.reference)
        self.settings.setValue('mainwindow/error', self.sendError)
        self.settings.setValue('mainwindow/fraction', self.fractionType)
    
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
    
    def __fractionType(self):
        fraction = self.settings.value('mainwindow/fraction')
        if not fraction:
            return 0
        
        return int(fraction)

class MainSettingsPage(QtGui.QWidget):
    Languages = [("English", 'en'), ("Русский", 'ru'), ("Español", 'es')]
    
    def __init__(self, collection, parent=None):
        super(MainSettingsPage, self).__init__(parent)

        settings = Settings()
        self.collectionSettings = collection.settings
        
        layout = QtGui.QFormLayout()
        layout.setRowWrapPolicy(QtGui.QFormLayout.WrapLongRows)
        
        current = 0
        self.languageSelector = QtGui.QComboBox(self)
        for i, lang in enumerate(self.Languages):
            self.languageSelector.addItem(lang[0], lang[1])
            if settings.language == lang[1]:
                current = i
        self.languageSelector.setCurrentIndex(current)
        
        layout.addRow(self.tr("Language"), self.languageSelector)
        
        self.backupFolder = QtGui.QLineEdit(self)
        self.backupFolder.setMinimumWidth(120)
        self.backupFolder.setText(settings.backupFolder)
        style = QtGui.QApplication.style()
        icon = style.standardIcon(QtGui.QStyle.SP_DirOpenIcon)
        self.backupFolderButton = QtGui.QPushButton(icon, '', self)
        self.backupFolderButton.clicked.connect(self.backupButtonClicked)
        
        hLayout = QtGui.QHBoxLayout()
        hLayout.addWidget(self.backupFolder)
        hLayout.addWidget(self.backupFolderButton)
        hLayout.setContentsMargins(QtCore.QMargins())
        
        layout.addRow(self.tr("Backup folder"), hLayout)
        
        self.reference = QtGui.QLineEdit(self)
        self.reference.setMinimumWidth(120)
        self.reference.setText(settings.reference)
        icon = style.standardIcon(QtGui.QStyle.SP_DialogOpenButton)
        self.referenceButton = QtGui.QPushButton(icon, '', self)
        self.referenceButton.clicked.connect(self.referenceButtonClicked)
        
        hLayout = QtGui.QHBoxLayout()
        hLayout.addWidget(self.reference)
        hLayout.addWidget(self.referenceButton)
        hLayout.setContentsMargins(QtCore.QMargins())

        layout.addRow(self.tr("Reference"), hLayout)
        
        self.errorSending = QtGui.QCheckBox(self.tr("Send error info to author"), self)
        self.errorSending.setChecked(settings.sendError)
        layout.addRow(self.errorSending)
        
        self.imageSideLen = NumberEdit(self)
        self.imageSideLen.setMaximumWidth(60)
        layout.addRow(self.tr("Max image side len"), self.imageSideLen)
        if not collection.isOpen():
            self.imageSideLen.setDisabled(True)
        else:
            self.imageSideLen.setText(self.collectionSettings.Settings['ImageSideLen'])
        
        self.setLayout(layout)

    def backupButtonClicked(self):
        folder = QtGui.QFileDialog.getExistingDirectory(self, self.tr("Backup folder"), self.backupFolder.text())
        if folder:
            self.backupFolder.setText(folder)

    def referenceButtonClicked(self):
        file = QtGui.QFileDialog.getOpenFileName(self, self.tr("Select reference"), self.reference.text(), "*.ref")
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
        
        self.collectionSettings.Settings['ImageSideLen'] = self.imageSideLen.text()
        self.collectionSettings.save()

class FieldsSettingsPage(QtGui.QWidget):
    DataRole = Qt.UserRole

    def __init__(self, collection, parent=None):
        super(FieldsSettingsPage, self).__init__(parent)

        self.listWidget = QtGui.QListWidget(self)
        self.listWidget.setWrapping(True)

        self.fields = collection.fields
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

    def resizeEvent(self, event):
        self.listWidget.setWrapping(True)

    def save(self):
        for i in range(self.listWidget.count()):
            item = self.listWidget.item(i)
            field = item.data(self.DataRole)
            field.enabled = (item.checkState() == Qt.Checked)
            field.title = item.text()
        
        self.fields.save()

class ViewSettingsPage(QtGui.QWidget):
    def __init__(self, collection, parent=None):
        super(ViewSettingsPage, self).__init__(parent)

        self.radios = []
        self.radios.append(QtGui.QRadioButton(self.tr("2.5")))
        self.radios.append(QtGui.QRadioButton(self.tr("2 1/2")))
        self.radios.append(QtGui.QRadioButton(self.tr("2 ½")))

        vbox = QtGui.QVBoxLayout(self)
        for r in self.radios:
            vbox.addWidget(r)
        vbox.addStretch(1)
        
        groupBox = QtGui.QGroupBox(self.tr("Show coin value fraction as"))
        groupBox.setLayout(vbox)
        
        layout = QtGui.QVBoxLayout(self)
        layout.addWidget(groupBox)

        self.setLayout(layout)

        settings = Settings()
        self.radios[settings.fractionType].setChecked(True)

    def save(self):
        settings = Settings()

        for i, r in enumerate(self.radios):
            if r.isChecked():
                settings.fractionType = i
                break

        settings.save()

class SettingsDialog(QtGui.QDialog):
    def __init__(self, collection, parent=None):
        super(SettingsDialog, self).__init__(parent, Qt.WindowSystemMenuHint)
        
        mainPage = MainSettingsPage(collection, self)
        fieldsPage = FieldsSettingsPage(collection, self)
        viewPage = ViewSettingsPage(collection, self)

        self.setWindowTitle(self.tr("Settings"))
        
        self.tab = QtGui.QTabWidget(self)
        self.tab.addTab(mainPage, self.tr("Main"))
        index = self.tab.addTab(fieldsPage, self.tr("Fields"))
        if not collection.isOpen():
            self.tab.setTabEnabled(index, False)
        self.tab.addTab(viewPage, self.tr("View"))
        
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
