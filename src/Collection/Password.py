import hashlib

from PyQt4 import QtGui
from PyQt4.QtCore import Qt

def cryptPassword(password=''):
    return hashlib.md5(password.encode('utf-8')).hexdigest()

def checkPassword(collection, password):
    collectionPassword = collection.settings.Settings['Password']
    if collectionPassword != cryptPassword(password):
        return False
    
    return True

class PasswordDialog(QtGui.QDialog):
    def __init__(self, collection, parent=None):
        super(PasswordDialog, self).__init__(parent, Qt.WindowSystemMenuHint)
        self.collection = collection

        self.setWindowTitle(self.tr("Password"))
        
        mainLayout = QtGui.QFormLayout()
        
        self.passwordWidget = QtGui.QLineEdit(self)
        self.passwordWidget.setEchoMode(QtGui.QLineEdit.Password)
        mainLayout.addRow(self.tr("Password"), self.passwordWidget)
        
        buttonBox = QtGui.QDialogButtonBox(Qt.Horizontal)
        buttonBox.addButton(QtGui.QDialogButtonBox.Ok)
        buttonBox.addButton(QtGui.QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.apply)
        buttonBox.rejected.connect(self.reject)
        
        layout = QtGui.QVBoxLayout(self)
        layout.addLayout(mainLayout)
        layout.addWidget(buttonBox)
        
        self.setLayout(layout)
    
    def apply(self):
        text = self.passwordWidget.text()
        if checkPassword(self.collection, text):
            self.accept()
        else:
            QtGui.QMessageBox.critical(self, self.tr("Open collection"), self.tr("Incorrect password"))
            self.reject()

class PasswordSetDialog(QtGui.QDialog):
    def __init__(self, collection, parent=None):
        super(PasswordSetDialog, self).__init__(parent, Qt.WindowSystemMenuHint)
        self.collection = collection

        self.setWindowTitle(self.tr("Set password"))
        
        mainLayout = QtGui.QFormLayout()
        
        self.passwordWidget = QtGui.QLineEdit(self)
        self.passwordWidget.setEchoMode(QtGui.QLineEdit.Password)
        if checkPassword(self.collection, ''):
            self.passwordWidget.setDisabled(True)
        mainLayout.addRow(self.tr("Current password"), self.passwordWidget)
        self.newPasswordWidget = QtGui.QLineEdit(self)
        self.newPasswordWidget.setEchoMode(QtGui.QLineEdit.Password)
        mainLayout.addRow(self.tr("New password"), self.newPasswordWidget)
        self.confirmPasswordWidget = QtGui.QLineEdit(self)
        self.confirmPasswordWidget.setEchoMode(QtGui.QLineEdit.Password)
        mainLayout.addRow(self.tr("Confirm password"), self.confirmPasswordWidget)
        
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
        text = self.passwordWidget.text()
        if checkPassword(self.collection, text):
            text = self.newPasswordWidget.text()
            newPassword = cryptPassword(text)
            text = self.confirmPasswordWidget.text()
            confirmPassword = cryptPassword(text)
            if newPassword != confirmPassword:
                QtGui.QMessageBox.warning(self, self.tr("Change password"), self.tr("The new password and confirmation password must match"))
                return
            
            self.collection.settings.Settings['Password'] = newPassword
            self.collection.settings.save()
            self.accept()
        else:
            QtGui.QMessageBox.critical(self, self.tr("Change password"), self.tr("Incorrect password"))
            self.reject()
