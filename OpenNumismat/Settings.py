# -*- coding: utf-8 -*-

from PyQt5.QtCore import Qt, QLocale, QSettings, QMargins
from PyQt5.QtWidgets import *

import OpenNumismat
from OpenNumismat.EditCoinDialog.FormItems import NumberEdit
from OpenNumismat.Collection.CollectionFields import CollectionFieldsBase
from OpenNumismat.Reports import Report
from OpenNumismat.Tools.DialogDecorators import storeDlgSizeDecorator


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
               'reference': OpenNumismat.HOME_PATH + "/reference.ref",
               'error': False, 'updates': False,
               'free_numeric': False,
               'store_sorting': False,
               'sort_filter': True,
               'sort_tree': True,
               'template': 'cbr',
               'ImageSideLen': 1024}

    def __init__(self, autoSave=False):
        super(Settings, self).__init__(autoSave)

        self.settings = QSettings()

    def keys(self):
        return self.Default.keys()

    def _getValue(self, key):
        value = self.settings.value('mainwindow/' + key)
        if value:
            if key in ('error', 'updates', 'free_numeric', 'store_sorting',
                       'sort_filter', 'sort_tree'):
                # Convert boolean value
                value = (value == 'true')
        else:
            value = self.Default[key]

        return value

    def _saveValue(self, key, val):
        self.settings.setValue('mainwindow/' + key, val)


class MainSettingsPage(QWidget):
    Languages = [("Català", 'ca'), ("Čeština", 'cs'), ("English", 'en'),
                 ("Ελληνικά", 'el'), ("Español", 'es'), ("Deutsch", 'de'),
                 ("Français", 'fr'), ("Italiano", 'it'), ("Magyar", 'hu'),
                 ("Nederlands", 'nl'), ("Polski", 'pl'), ("Português", 'pt'),
                 ("Русский", 'ru'), ("Український", 'uk'),
                 ]

    def __init__(self, collection, parent=None):
        super(MainSettingsPage, self).__init__(parent)

        settings = Settings()

        layout = QFormLayout()
        layout.setRowWrapPolicy(QFormLayout.WrapLongRows)

        current = 0
        self.languageSelector = QComboBox(self)
        for i, lang in enumerate(self.Languages):
            self.languageSelector.addItem(lang[0], lang[1])
            if settings['locale'] == lang[1]:
                current = i
        self.languageSelector.setCurrentIndex(current)
        self.languageSelector.setSizePolicy(QSizePolicy.Fixed,
                                            QSizePolicy.Fixed)

        layout.addRow(self.tr("Language"), self.languageSelector)

        self.backupFolder = QLineEdit(self)
        self.backupFolder.setMinimumWidth(120)
        self.backupFolder.setText(settings['backup'])
        style = QApplication.style()
        icon = style.standardIcon(QStyle.SP_DirOpenIcon)
        self.backupFolderButton = QPushButton(icon, '', self)
        self.backupFolderButton.clicked.connect(self.backupButtonClicked)

        hLayout = QHBoxLayout()
        hLayout.addWidget(self.backupFolder)
        hLayout.addWidget(self.backupFolderButton)
        hLayout.setContentsMargins(QMargins())

        layout.addRow(self.tr("Backup folder"), hLayout)

        self.reference = QLineEdit(self)
        self.reference.setMinimumWidth(120)
        self.reference.setText(settings['reference'])
        icon = style.standardIcon(QStyle.SP_DialogOpenButton)
        self.referenceButton = QPushButton(icon, '', self)
        self.referenceButton.clicked.connect(self.referenceButtonClicked)

        hLayout = QHBoxLayout()
        hLayout.addWidget(self.reference)
        hLayout.addWidget(self.referenceButton)
        hLayout.setContentsMargins(QMargins())

        layout.addRow(self.tr("Reference"), hLayout)

        self.errorSending = QCheckBox(
                            self.tr("Send error info to author"), self)
        self.errorSending.setChecked(settings['error'])
        layout.addRow(self.errorSending)

        self.checkUpdates = QCheckBox(
                            self.tr("Automatically check for updates"), self)
        self.checkUpdates.setChecked(settings['updates'])
        layout.addRow(self.checkUpdates)

        self.imageSideLen = NumberEdit(self)
        self.imageSideLen.setMaximumWidth(60)
        layout.addRow(self.tr("Max image side len"), self.imageSideLen)
        self.imageSideLen.setText(str(settings['ImageSideLen']))

        self.freeNumeric = QCheckBox(
                            self.tr("Free format numeric fields"), self)
        self.freeNumeric.setChecked(settings['free_numeric'])
        layout.addRow(self.freeNumeric)

        self.storeSorting = QCheckBox(
                            self.tr("Store column sorting"), self)
        self.storeSorting.setChecked(settings['store_sorting'])
        layout.addRow(self.storeSorting)

        self.sortFilter = QCheckBox(
                            self.tr("Sort items in filters (slow)"), self)
        self.sortFilter.setChecked(settings['sort_filter'])
        layout.addRow(self.sortFilter)

        self.sortTree = QCheckBox(
                            self.tr("Sort items in tree (slow)"), self)
        self.sortTree.setChecked(settings['sort_tree'])
        layout.addRow(self.sortTree)

        current = 0
        self.templateSelector = QComboBox(self)
        for i, template in enumerate(Report.scanTemplates()):
            self.templateSelector.addItem(template)
            if settings['template'] == template:
                current = i
        self.templateSelector.setCurrentIndex(current)
        self.templateSelector.setSizePolicy(QSizePolicy.Fixed,
                                            QSizePolicy.Fixed)

        layout.addRow(self.tr("Default template"), self.templateSelector)

        self.setLayout(layout)

    def backupButtonClicked(self):
        folder = QFileDialog.getExistingDirectory(self,
                                                self.tr("Backup folder"),
                                                self.backupFolder.text())
        if folder:
            self.backupFolder.setText(folder)

    def referenceButtonClicked(self):
        file, _selectedFilter = QFileDialog.getOpenFileName(self,
                                                self.tr("Select reference"),
                                                self.reference.text(),
                                                "*.ref")
        if file:
            self.reference.setText(file)

    def save(self):
        settings = Settings()

        current = self.languageSelector.currentIndex()
        settings['locale'] = self.languageSelector.itemData(current)
        settings['backup'] = self.backupFolder.text()
        settings['reference'] = self.reference.text()
        settings['error'] = self.errorSending.isChecked()
        settings['updates'] = self.checkUpdates.isChecked()
        settings['free_numeric'] = self.freeNumeric.isChecked()
        settings['store_sorting'] = self.storeSorting.isChecked()
        settings['sort_filter'] = self.sortFilter.isChecked()
        settings['sort_tree'] = self.sortTree.isChecked()
        settings['template'] = self.templateSelector.currentText()
        settings['ImageSideLen'] = int(self.imageSideLen.text())

        settings.save()


class FieldsSettingsPage(QWidget):
    DataRole = Qt.UserRole

    def __init__(self, collection, parent=None):
        super(FieldsSettingsPage, self).__init__(parent)

        self.listWidget = QListWidget(self)
        self.listWidget.setWrapping(True)
        self.listWidget.setMinimumWidth(330)
        self.listWidget.setMinimumHeight(180)
        self.listWidget.itemSelectionChanged.connect(self.itemSelectionChanged)

        self.fields = collection.fields
        for field in self.fields:
            item = QListWidgetItem(field.title, self.listWidget)
            item.setData(self.DataRole, field)
            item.setFlags(Qt.ItemIsEditable | Qt.ItemIsUserCheckable |
                          Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            checked = Qt.Unchecked
            if field.enabled:
                checked = Qt.Checked
            item.setCheckState(checked)
            self.listWidget.addItem(item)

        self.renameButton = QPushButton(self.tr("Rename"), self)
        self.renameButton.clicked.connect(self.renameButtonClicked)
        self.renameButton.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.renameButton.setEnabled(False)

        self.defaultFieldsButton = QPushButton(
                                            self.tr("Revert to default"), self)
        self.defaultFieldsButton.clicked.connect(
                                            self.defaultFieldsButtonClicked)
        self.defaultFieldsButton.setSizePolicy(QSizePolicy.Fixed,
                                               QSizePolicy.Fixed)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(self.tr("Global enabled fields:"), self))
        layout.addWidget(self.listWidget)

        hLayout = QHBoxLayout()
        hLayout.addWidget(self.renameButton, alignment=Qt.AlignLeft)
        hLayout.addWidget(self.defaultFieldsButton, alignment=Qt.AlignRight)
        layout.addLayout(hLayout)

        self.setLayout(layout)

    def itemSelectionChanged(self):
        self.renameButton.setEnabled(len(self.listWidget.selectedItems()) > 0)

    def resizeEvent(self, event):
        self.listWidget.setWrapping(True)

    def defaultFieldsButtonClicked(self):
        defaultFields = CollectionFieldsBase()
        for i in range(self.listWidget.count()):
            item = self.listWidget.item(i)
            field = item.data(self.DataRole)
            defaultField = defaultFields.field(field.id)
            item.setText(defaultField.title)

    def renameButtonClicked(self):
        items = self.listWidget.selectedItems()
        if len(items) > 0:
            self.listWidget.editItem(items[0])

    def save(self):
        for i in range(self.listWidget.count()):
            item = self.listWidget.item(i)
            field = item.data(self.DataRole)
            field.enabled = (item.checkState() == Qt.Checked)
            field.title = item.text()

        self.fields.save()


@storeDlgSizeDecorator
class SettingsDialog(QDialog):
    def __init__(self, collection, parent=None):
        super().__init__(parent,
                         Qt.WindowCloseButtonHint | Qt.WindowSystemMenuHint)

        mainPage = MainSettingsPage(collection, self)
        fieldsPage = FieldsSettingsPage(collection, self)

        self.setWindowTitle(self.tr("Settings"))

        self.tab = QTabWidget(self)
        self.tab.addTab(mainPage, self.tr("Main"))
        index = self.tab.addTab(fieldsPage, self.tr("Fields"))
        if not collection.isOpen():
            self.tab.setTabEnabled(index, False)

        buttonBox = QDialogButtonBox(Qt.Horizontal)
        buttonBox.addButton(QDialogButtonBox.Ok)
        buttonBox.addButton(QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.save)
        buttonBox.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(self.tab)
        layout.addWidget(buttonBox)

        self.setLayout(layout)

    def save(self):
        for i in range(self.tab.count()):
            page = self.tab.widget(i)
            page.save()

        self.accept()
