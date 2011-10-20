from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import Qt

class SettingsDialog(QtGui.QDialog):
    Languages = [("English", 'en_UK'), ("Русский", 'ru_RU')]
    
    def __init__(self, parent=None):
        super(SettingsDialog, self).__init__(parent)
        
        mainLayout = QtGui.QGridLayout()
        
        settings = QtCore.QSettings()
        locale = settings.value('mainwindow/locale')
        if not locale:
            locale = QtCore.QLocale.system().name()

        current = 0
        self.languageSelector = QtGui.QComboBox(self)
        for i, lang in enumerate(self.Languages):
            self.languageSelector.addItem(lang[0], lang[1])
            if locale == lang[1]:
                current = i
        self.languageSelector.setCurrentIndex(current)
        
        mainLayout.addWidget(QtGui.QLabel(self.tr("Language")), 0, 0)
        mainLayout.addWidget(self.languageSelector, 0, 1)
        
        buttonBox = QtGui.QDialogButtonBox(Qt.Horizontal)
        buttonBox.addButton(QtGui.QDialogButtonBox.Ok)
        buttonBox.addButton(QtGui.QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.save)
        buttonBox.rejected.connect(self.reject)

        layout = QtGui.QVBoxLayout(self)
        layout.addLayout(mainLayout)
        layout.addWidget(buttonBox)

        self.setLayout(layout)

    def save(self):
        current = self.languageSelector.currentIndex()
        locale = self.languageSelector.itemData(current)

        settings = QtCore.QSettings()
        settings.setValue('mainwindow/locale', locale)

        self.accept()
