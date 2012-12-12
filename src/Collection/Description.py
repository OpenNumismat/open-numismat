from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import Qt
from PyQt4.QtSql import QSqlQuery


class CollectionDescription(QtCore.QObject):
    def __init__(self, collection):
        super(CollectionDescription, self).__init__(collection)
        self.db = collection.db

        if 'description' not in self.db.tables():
            self.create(collection)

        query = QSqlQuery("SELECT * FROM description", self.db)
        query.first()
        record = query.record()

        self.title = record.value('title')
        self.description = record.value('description')
        self.author = record.value('author')

    def save(self):
        self.db.transaction()

        query = QSqlQuery(self.db)
        query.prepare("UPDATE description SET title=?, description=?,"
                      " author=? WHERE id=1")
        query.addBindValue(self.title)
        query.addBindValue(self.description)
        query.addBindValue(self.author)
        query.exec_()

        self.db.commit()

    def create(self, collection):
        self.db.transaction()

        sql = """CREATE TABLE description (
            id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
            title CHAR,
            description TEXT,
            author CHAR)"""
        QSqlQuery(sql, self.db)

        query = QSqlQuery(self.db)
        query.prepare("""INSERT INTO description (title, description, author)
                VALUES (?, ?, ?)""")
        query.addBindValue(collection.getCollectionName())
        query.addBindValue('')
        query.addBindValue('')
        query.exec_()

        self.db.commit()


class DescriptionDialog(QtGui.QDialog):
    def __init__(self, description, parent=None):
        super(DescriptionDialog, self).__init__(parent,
                                                Qt.WindowSystemMenuHint)

        self.description = description

        self.setWindowTitle(self.tr("Description"))

        mainLayout = QtGui.QFormLayout()

        self.titleWidget = QtGui.QLineEdit(self.description.title, self)
        mainLayout.addRow(self.tr("Title"), self.titleWidget)
        self.descriptionWidget = QtGui.QTextEdit(self)
        self.descriptionWidget.setText(self.description.description)
        self.descriptionWidget.setAcceptRichText(False)
        self.descriptionWidget.setTabChangesFocus(True)
        mainLayout.addRow(self.tr("Description"), self.descriptionWidget)
        self.authorWidget = QtGui.QLineEdit(self.description.author, self)
        mainLayout.addRow(self.tr("Author"), self.authorWidget)

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
        self.description.title = self.titleWidget.text()
        self.description.description = self.descriptionWidget.toPlainText()
        self.description.author = self.authorWidget.text()
        self.description.save()

        self.accept()
