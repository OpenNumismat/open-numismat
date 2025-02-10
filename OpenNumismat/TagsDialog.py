from PySide6.QtCore import Qt, QFileInfo, QIODevice, QBuffer
from PySide6.QtGui import QIcon, QImage, QKeySequence, QPainter, QPixmap
from PySide6.QtSql import QSqlQuery
from PySide6.QtWidgets import (
    QAbstractItemDelegate,
    QApplication,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QHBoxLayout,
    QMenu,
    QMessageBox,
    QPushButton,
    QStyle,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
)

import OpenNumismat
from OpenNumismat.Settings import Settings
from OpenNumismat.Tools.DialogDecorators import storeDlgSizeDecorator
from OpenNumismat.Tools.misc import readImageFilters


class TagsTreeWidget(QTreeWidget):

    def __init__(self, db, readonly, parent=None):
        super().__init__(parent)

        self.readonly = readonly
        self.db = db
        self.record = None
        self.tristate = False

        self.setHeaderHidden(True)

        self.update()

    def update(self):
        self.clear()

        sql = "SELECT id, tag, position, parent_id, icon FROM tags ORDER BY position"
        query = QSqlQuery(self.db)
        query.exec(sql)

        items = {}
        while query.next():
            record = query.record()

            tag_id = record.value(0)
            position = record.value(2)
            tag = record.value(1)
            parent_id = record.value(3)
            icon_data = record.value(4)
            
            item = QTreeWidgetItem((tag,))
            item.setData(0, Qt.UserRole, tag_id)
            item.setData(0, Qt.UserRole + 1, position)
            item.setData(0, Qt.UserRole + 2, parent_id)
            if icon_data:
                pixmap = QPixmap()
                if pixmap.loadFromData(icon_data):
                    item.setData(0, Qt.DecorationRole, pixmap)

            if self.readonly:
                item.setFlags(Qt.ItemIsEnabled)
            else:
                item.setFlags(item.flags() | Qt.ItemIsSelectable)

            item.setCheckState(0, Qt.Unchecked)

            items[tag_id] = item

        for tag_id, item in items.items():
            parent_id = item.data(0, Qt.UserRole + 2)

            if parent_id:
                parent_item = items[parent_id]
                parent_item.addChild(item)
            else:
                self.addTopLevelItem(item)

        self.expandAll()

        self.fill(self.record)

    def fill(self, record):
        if record:
            if isinstance(record.value('tags'), dict):
                self.tristate = True
            self.record = record
            self.tag_ids = record.value('tags')
            self.execForAll(self.markItem)

    def markItem(self, item):
        if self.tristate:
            item.setFlags(item.flags() | Qt.ItemIsUserTristate)

        tag_id = item.data(0, Qt.UserRole)
        if tag_id in self.tag_ids:
            if self.tristate:
                item.setCheckState(0, self.tag_ids[tag_id])
            else:
                item.setCheckState(0, Qt.Checked)
        else:
            item.setCheckState(0, Qt.Unchecked)

    def getTags(self):
        if self.tristate:
            self.tag_ids = {}
        else:
            self.tag_ids = []
        self.execForAll(self.storeTagId)
        return self.tag_ids

    def storeTagId(self, item):
        if self.tristate:
            tag_id = item.data(0, Qt.UserRole)
            self.tag_ids[tag_id] = item.checkState(0)
        else:
            if item.checkState(0) == Qt.Checked:
                tag_id = item.data(0, Qt.UserRole)
                self.tag_ids.append(tag_id)

    def execForAll(self, func):
        for i in range(self.topLevelItemCount()):
            item = self.topLevelItem(i)
            self.execForItem(func, item)

    def execForItem(self, func, item):
        func(item)

        for i in range(item.childCount()):
            child = item.child(i)
            self.execForItem(func, child)


class EditTagsTreeWidget(QTreeWidget):
    latestDir = OpenNumismat.IMAGE_PATH

    def __init__(self, db, parent=None):
        super().__init__(parent)

        self.db = db

        self.setHeaderHidden(True)

        sql = "SELECT id, tag, position, parent_id, icon FROM tags ORDER BY position"
        query = QSqlQuery(self.db)
        query.exec(sql)

        items = {}
        while query.next():
            record = query.record()

            tag_id = record.value(0)
            position = record.value(2)
            tag = record.value(1)
            parent_id = record.value(3)
            icon_data = record.value(4)

            item = QTreeWidgetItem((tag,))
            item.setData(0, Qt.UserRole, tag_id)
            item.setData(0, Qt.UserRole + 1, position)
            item.setData(0, Qt.UserRole + 2, parent_id)
            if icon_data:
                pixmap = QPixmap()
                if pixmap.loadFromData(icon_data):
                    item.setData(0, Qt.DecorationRole, pixmap)
            item.setFlags(item.flags() | Qt.ItemIsEditable)

            items[tag_id] = item

        for tag_id, item in items.items():
            parent_id = item.data(0, Qt.UserRole + 2)
            # position = item.data(0, Qt.UserRole + 1)

            if parent_id:
                parent_item = items[parent_id]
                parent_item.addChild(item)
            else:
                # self.insertTopLevelItem(position, item)
                self.addTopLevelItem(item)

        self.expandAll()

    def contextMenuEvent(self, event):
        indexes = self.selectedIndexes()
        if indexes:
            index = indexes[-1]
        else:
            index = None

        menu = QMenu(self)

        menu.addAction(QIcon(':/add.png'), self.tr("New tag"), Qt.Key_Insert, self.addItem)

        act = menu.addAction(self.tr("New subtag"), self.addSubItem)
        if not index:
            act.setDisabled(True)

        menu.addSeparator()

        if index and index.data(Qt.DecorationRole):
            act = menu.addAction(self.tr("Change icon..."), self.addIcon)
        else:
            act = menu.addAction(self.tr("Add icon..."), self.addIcon)
        if not index:
            act.setDisabled(True)

        act = menu.addAction(self.tr("Paste icon"), self.pasteIcon)
        if not index:
            act.setDisabled(True)

        act = menu.addAction(self.tr("Clear icon"), self.clearIcon)
        if not index or not index.data(Qt.DecorationRole):
            act.setDisabled(True)

        menu.addSeparator()

        act = menu.addAction(QIcon(':/pencil.png'), self.tr("Rename"), self.renameItem)
        if not index:
            act.setDisabled(True)

        style = QApplication.style()
        icon = style.standardIcon(QStyle.SP_TrashIcon)
        act = menu.addAction(icon, self.tr("Delete"), QKeySequence.Delete, self.deleteItem)
        if not index:
            act.setDisabled(True)

        menu.exec(self.mapToGlobal(event.pos()))

    def addItem(self):
        parent_item = self.currentItem()
        if parent_item:
            parent_item = parent_item.parent()
        if not parent_item:
            parent_item = self
        item = QTreeWidgetItem(parent_item, (self.defaultValue(),))
        position = self._getNewPosition()
        item.setData(0, Qt.UserRole + 1, position)
        item.setFlags(item.flags() | Qt.ItemIsEditable)
        self.setCurrentItem(item)
        self.editItem(item)

    def addSubItem(self):
        parent_item = self.currentItem()
        item = QTreeWidgetItem(parent_item, (self.defaultValue(),))
        position = self._getNewPosition()
        item.setData(0, Qt.UserRole + 1, position)
        item.setFlags(item.flags() | Qt.ItemIsEditable)
        parent_item.setExpanded(True)
        self.setCurrentItem(item)
        self.editItem(item)

    def _getNewPosition(self):
        sql = "SELECT MAX(id) FROM tags"
        query = QSqlQuery(sql, self.db)
        query.exec()
        query.first()
        max_id = query.record().value(0)

        if max_id:
            position = max_id + 1
        else:
            position = 0

        return position

    def renameItem(self):
        item = self.currentItem()
        self.editItem(item)

    def deleteItem(self):
        item = self.currentItem()
        if item:
            if item.parent():
                item.parent().removeChild(item)
            else:
                index = self.currentIndex()
                self.takeTopLevelItem(index.row())

            self.execForItem(self.remove, item)

    def addIcon(self):
        fileName, _selectedFilter = QFileDialog.getOpenFileName(self,
                self.tr("Open File"), self.latestDir,
                ';;'.join(readImageFilters()))
        if fileName:
            file_info = QFileInfo(fileName)
            self.latestDir = file_info.absolutePath()

            self.loadFromFile(fileName)

    def pasteIcon(self):
        mime = QApplication.clipboard().mimeData()
        if mime.hasImage():
            image = mime.imageData()
            if image.hasAlphaChannel() and not Settings()['transparent_store']:
                # Fill transparent color if present
                color = Settings()['transparent_color']
                fixedImage = QImage(image.size(), QImage.Format_RGB32)
                fixedImage.fill(color)
                painter = QPainter(fixedImage)
                painter.drawImage(0, 0, image)
                painter.end()
            else:
                fixedImage = image

            self._setNewImage(fixedImage)
        elif mime.hasUrls():
            url = mime.urls()[0]
            self.loadFromFile(url.toLocalFile())

    def clearIcon(self):
        item = self.currentItem()
        if item:
            tag_id = item.data(0, Qt.UserRole)

            sql = "UPDATE tags SET icon=NULL WHERE id=?"
            query = QSqlQuery(self.db)
            query.prepare(sql)
            query.addBindValue(tag_id)
            query.exec()

            item.setData(0, Qt.DecorationRole, None)

    def loadFromFile(self, fileName):
        image = QImage()
        if image.load(fileName):
            self._setNewImage(image)

    def _setNewImage(self, image):
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

        item = self.currentItem()
        if item:
            tag_id = item.data(0, Qt.UserRole)

            sql = "UPDATE tags SET icon=? WHERE id=?"
            query = QSqlQuery(self.db)
            query.prepare(sql)
            query.addBindValue(buffer.data())
            query.addBindValue(tag_id)
            query.exec()

            pixmap = QPixmap()
            if pixmap.loadFromData(buffer.data()):
                item.setData(0, Qt.DecorationRole, pixmap)

    def remove(self, item):
        tag_id = item.data(0, Qt.UserRole)

        sql = "DELETE FROM tags WHERE id=?"
        query = QSqlQuery(self.db)
        query.prepare(sql)
        query.addBindValue(tag_id)
        query.exec()

        sql = "DELETE FROM coins_tags WHERE tag_id=?"
        query = QSqlQuery(self.db)
        query.prepare(sql)
        query.addBindValue(tag_id)
        query.exec()

    def commitData(self, editor):
        text = editor.text().strip()
        if len(text) > 0:
            super().commitData(editor)

    def closeEditor(self, editor, hint):
        super().closeEditor(editor, hint)

        valid = True
        text = editor.text().strip()
        if len(text) == 0:
            valid = False
        elif text == self.defaultValue():
            if hint == QAbstractItemDelegate.RevertModelCache:
                valid = False

        item = self.currentItem()
        tag_id = item.data(0, Qt.UserRole)
        position = item.data(0, Qt.UserRole + 1) or 1
        parent_item = item.parent()

        if not valid and not tag_id:
            if item.parent():
                item.parent().removeChild(item)
            else:
                index = self.currentIndex()
                self.takeTopLevelItem(index.row())
            return

        sql = "INSERT OR REPLACE INTO tags (id, tag, position, parent_id) VALUES (?, ?, ?, ?)"
        query = QSqlQuery(self.db)
        query.prepare(sql)
        query.addBindValue(tag_id)
        query.addBindValue(item.text(0))
        query.addBindValue(position)
        if parent_item:
            query.addBindValue(parent_item.data(0, Qt.UserRole))
        else:
            query.addBindValue(None)

        query.exec()

        tag_id = query.lastInsertId()
        item.setData(0, Qt.UserRole, tag_id)

    def defaultValue(self):
        return self.tr("Enter value")

    def execForAll(self, func):
        for i in range(self.topLevelItemCount()):
            item = self.topLevelItem(i)
            self.execForItem(func, item)

    def execForItem(self, func, item):
        func(item)

        for i in range(item.childCount()):
            child = item.child(i)
            self.execForItem(func, child)


@storeDlgSizeDecorator
class TagsDialog(QDialog):

    def __init__(self, db, parent=None):
        super().__init__(parent,
                         Qt.WindowCloseButtonHint | Qt.WindowSystemMenuHint)

        self.db = db
        self.db.transaction()

        self.setWindowTitle(self.tr("Tags"))

        self.tagsTree = EditTagsTreeWidget(self.db)

        add_button = QPushButton(QIcon(':/add.png'), '')
        add_button.setToolTip(self.tr("New tag"))
        add_button.setShortcut(Qt.Key_Insert)
        add_button.clicked.connect(self.tagsTree.addItem)

        rename_button = QPushButton(QIcon(':/pencil.png'), '')
        rename_button.setToolTip(self.tr("Rename"))
        rename_button.clicked.connect(self.tagsTree.renameItem)

        style = QApplication.style()
        icon = style.standardIcon(QStyle.SP_TrashIcon)
        del_button = QPushButton(icon, '')
        del_button.setToolTip(self.tr("Delete"))
        del_button.setShortcut(QKeySequence.Delete)
        del_button.clicked.connect(self.tagsTree.deleteItem)

        buttons = QVBoxLayout()
        buttons.addWidget(add_button)
        buttons.addWidget(rename_button)
        buttons.addWidget(del_button)
        buttons.addStretch()

        tree_layout = QHBoxLayout()
        tree_layout.addWidget(self.tagsTree)
        tree_layout.addLayout(buttons)

        buttonBox = QDialogButtonBox(Qt.Horizontal)
        buttonBox.addButton(QDialogButtonBox.Ok)
        buttonBox.addButton(QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        layout = QVBoxLayout()
        layout.addLayout(tree_layout)
        layout.addWidget(buttonBox)

        self.setLayout(layout)

    def accept(self):
        if not self.db.commit():
            QMessageBox.critical(self.parent(),
                            self.tr("Save tags"),
                            self.tr("Something went wrong when saving. Please restart"))
            self.db.rollback()

        super().accept()

    def reject(self):
        if not self.db.rollback():
            QMessageBox.critical(self.parent(),
                            self.tr("Save tags"),
                            self.tr("Something went wrong when canceling. Please restart"))

        super().reject()
