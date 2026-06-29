from PySide6.QtCore import Qt, QBuffer, QIODevice, QObject
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtSql import QSqlQuery
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)

import OpenNumismat
from OpenNumismat.Tools.misc import readImageFilters


class CollectionDescription(QObject):
    def __init__(self, collection):
        super().__init__(collection)
        self.db = collection.db

        if 'description' not in self.db.tables():
            self.create(collection)

        query = QSqlQuery("SELECT * FROM description", self.db)
        query.first()
        record = query.record()

        self.title = record.value('title')
        self.description = record.value('description')
        self.author = record.value('author')
        self.icon = record.value('icon')

    def save(self):
        self.db.transaction()

        query = QSqlQuery(self.db)
        query.prepare("UPDATE description SET title=?, description=?,"
                      " author=?, icon=? WHERE id=1")
        query.addBindValue(self.title)
        query.addBindValue(self.description)
        query.addBindValue(self.author)
        query.addBindValue(self.icon)
        query.exec()

        self.db.commit()

    def create(self, collection):
        self.db.transaction()

        sql = """CREATE TABLE description (
            id INTEGER PRIMARY KEY,
            title TEXT,
            description TEXT,
            author TEXT,
            icon BLOB)"""
        QSqlQuery(sql, self.db)

        query = QSqlQuery(self.db)
        query.prepare("""INSERT INTO description (title, description, author)
                VALUES (?, ?, ?)""")
        query.addBindValue(collection.getCollectionName())
        query.addBindValue('')
        query.addBindValue('')
        query.exec()

        self.db.commit()


class DescriptionDialog(QDialog):
    def __init__(self, description, parent=None):
        super().__init__(parent,
                         Qt.WindowCloseButtonHint | Qt.WindowSystemMenuHint)

        self.description = description

        self.setWindowTitle(self.tr("Description"))

        mainLayout = QFormLayout()

        self.titleWidget = QLineEdit(self.description.title, self)
        mainLayout.addRow(self.tr("Title"), self.titleWidget)
        self.descriptionWidget = QTextEdit(self)
        self.descriptionWidget.setText(self.description.description)
        self.descriptionWidget.setAcceptRichText(False)
        self.descriptionWidget.setTabChangesFocus(True)
        mainLayout.addRow(self.tr("Description"), self.descriptionWidget)
        self.authorWidget = QLineEdit(self.description.author, self)
        mainLayout.addRow(self.tr("Author"), self.authorWidget)

        self.iconButton = QPushButton('…', self)
        if self.description.icon:
            self.iconButton.setProperty('new_icon', self.description.icon)
            pixmap = QPixmap()
            if pixmap.loadFromData(self.description.icon):
                self.iconButton.setIcon(pixmap)
                self.iconButton.setText('')
        self.iconButton.clicked.connect(self.iconButtonClicked)
        mainLayout.addRow(self.tr("Icon"), self.iconButton)

        buttonBox = QDialogButtonBox(Qt.Horizontal)
        buttonBox.addButton(QDialogButtonBox.Ok)
        buttonBox.addButton(QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.save)
        buttonBox.rejected.connect(self.reject)

        layout = QVBoxLayout()
        layout.addLayout(mainLayout)
        layout.addWidget(buttonBox)

        self.setLayout(layout)

    def iconButtonClicked(self):
        fileName, _selectedFilter = QFileDialog.getOpenFileName(self,
                self.tr("Open File"), OpenNumismat.IMAGE_PATH,
                ';;'.join(readImageFilters()))
        if fileName:
            image = QImage()
            if image.load(fileName):
                maxWidth = 16
                maxHeight = 16
                if image.width() > maxWidth or image.height() > maxHeight:
                    scaledImage = image.scaled(maxWidth, maxHeight,
                            Qt.KeepAspectRatio, Qt.SmoothTransformation)
                else:
                    scaledImage = image

                buffer = QBuffer()
                buffer.open(QIODevice.WriteOnly)
                scaledImage.save(buffer, 'webp', 100)

                self.iconButton.setProperty('new_icon', buffer.data())

                pixmap = QPixmap.fromImage(scaledImage)
                self.iconButton.setIcon(pixmap)
                self.iconButton.setText('')

    def save(self):
        self.description.title = self.titleWidget.text()
        self.description.description = self.descriptionWidget.toPlainText()
        self.description.author = self.authorWidget.text()
        self.description.icon = self.iconButton.property('new_icon')
        self.description.save()

        self.accept()
