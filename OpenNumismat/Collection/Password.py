import hashlib

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QMessageBox,
    QVBoxLayout,
)


def cryptPassword(password=''):
    return hashlib.md5(password.encode('utf-8')).hexdigest()


def checkPassword(crypted_password, password):
    if crypted_password != cryptPassword(password):
        return False

    return True


class PasswordDialog(QDialog):

    def __init__(self, crypted_password, collection_name='', parent=None):
        super().__init__(parent,
                         Qt.WindowCloseButtonHint | Qt.WindowSystemMenuHint)
        self.crypted_password = crypted_password

        self.setWindowTitle(collection_name)

        mainLayout = QFormLayout()

        self.passwordWidget = QLineEdit(self)
        self.passwordWidget.setEchoMode(QLineEdit.Password)
        mainLayout.addRow(self.tr("Password"), self.passwordWidget)

        buttonBox = QDialogButtonBox(Qt.Horizontal)
        buttonBox.addButton(QDialogButtonBox.Ok)
        buttonBox.addButton(QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.apply)
        buttonBox.rejected.connect(self.reject)

        layout = QVBoxLayout()
        layout.addLayout(mainLayout)
        layout.addWidget(buttonBox)

        self.setLayout(layout)

    def apply(self):
        text = self.passwordWidget.text()
        if checkPassword(self.crypted_password, text):
            self.accept()
        else:
            QMessageBox.critical(self, self.tr("Open collection"),
                                       self.tr("Incorrect password"))
            self.reject()


class PasswordSetDialog(QDialog):
    def __init__(self, settings, parent=None):
        super().__init__(parent,
                         Qt.WindowCloseButtonHint | Qt.WindowSystemMenuHint)
        self.settings = settings

        self.setWindowTitle(self.tr("Set password"))

        mainLayout = QFormLayout()

        self.passwordWidget = QLineEdit(self)
        self.passwordWidget.setEchoMode(QLineEdit.Password)
        if checkPassword(self.settings['Password'], ''):
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

        layout = QVBoxLayout()
        layout.addLayout(mainLayout)
        layout.addWidget(buttonBox)

        self.setLayout(layout)

    def save(self):
        text = self.passwordWidget.text()
        if checkPassword(self.settings['Password'], text):
            text = self.newPasswordWidget.text()
            newPassword = cryptPassword(text)
            text = self.confirmPasswordWidget.text()
            confirmPassword = cryptPassword(text)
            if newPassword != confirmPassword:
                QMessageBox.warning(self, self.tr("Change password"),
                            self.tr("The new password and confirmation "
                                    "password must match"))
                return

            self.settings['Password'] = newPassword
            self.settings.save()
            self.accept()
        else:
            QMessageBox.critical(self, self.tr("Change password"),
                                       self.tr("Incorrect password"))
            self.reject()
