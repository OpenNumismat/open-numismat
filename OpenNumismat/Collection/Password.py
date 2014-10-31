import hashlib

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import *


def cryptPassword(password=''):
    return hashlib.md5(password.encode('utf-8')).hexdigest()


def checkPassword(collection, password):
    collectionPassword = collection.settings['Password']
    if collectionPassword != cryptPassword(password):
        return False

    return True


class PasswordDialog(QDialog):
    def __init__(self, collection, parent=None):
        super().__init__(parent,
                         Qt.WindowCloseButtonHint | Qt.WindowSystemMenuHint)
        self.collection = collection

        self.setWindowTitle(self.tr("Password"))

        mainLayout = QFormLayout()

        self.passwordWidget = QLineEdit(self)
        self.passwordWidget.setEchoMode(QLineEdit.Password)
        mainLayout.addRow(self.tr("Password"), self.passwordWidget)

        buttonBox = QDialogButtonBox(Qt.Horizontal)
        buttonBox.addButton(QDialogButtonBox.Ok)
        buttonBox.addButton(QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.apply)
        buttonBox.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(mainLayout)
        layout.addWidget(buttonBox)

        self.setLayout(layout)

    def apply(self):
        text = self.passwordWidget.text()
        if checkPassword(self.collection, text):
            self.accept()
        else:
            QMessageBox.critical(self, self.tr("Open collection"),
                                       self.tr("Incorrect password"))
            self.reject()


class PasswordSetDialog(QDialog):
    def __init__(self, collection, parent=None):
        super().__init__(parent,
                         Qt.WindowCloseButtonHint | Qt.WindowSystemMenuHint)
        self.collection = collection

        self.setWindowTitle(self.tr("Set password"))

        mainLayout = QFormLayout()

        self.passwordWidget = QLineEdit(self)
        self.passwordWidget.setEchoMode(QLineEdit.Password)
        if checkPassword(self.collection, ''):
            self.passwordWidget.setDisabled(True)
        mainLayout.addRow(self.tr("Current password"), self.passwordWidget)
        self.newPasswordWidget = QLineEdit(self)
        self.newPasswordWidget.setEchoMode(QLineEdit.Password)
        mainLayout.addRow(self.tr("New password"), self.newPasswordWidget)
        self.confirmPasswordWidget = QLineEdit(self)
        self.confirmPasswordWidget.setEchoMode(QLineEdit.Password)
        mainLayout.addRow(self.tr("Confirm password"),
                          self.confirmPasswordWidget)

        buttonBox = QDialogButtonBox(Qt.Horizontal)
        buttonBox.addButton(QDialogButtonBox.Ok)
        buttonBox.addButton(QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.save)
        buttonBox.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
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
                QMessageBox.warning(self, self.tr("Change password"),
                            self.tr("The new password and confirmation "
                                    "password must match"))
                return

            self.collection.settings['Password'] = newPassword
            self.collection.settings.save()
            self.accept()
        else:
            QMessageBox.critical(self, self.tr("Change password"),
                                       self.tr("Incorrect password"))
            self.reject()
