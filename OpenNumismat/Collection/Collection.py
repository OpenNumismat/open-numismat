# -*- coding: utf-8 -*-

import codecs
import json
import math
import os
import shutil

from PySide6 import QtCore
from PySide6.QtWidgets import *
from PySide6.QtGui import QImage, QPainter, QAction
from PySide6.QtCore import Qt, QCryptographicHash, QLocale
from PySide6.QtCore import QT_TRANSLATE_NOOP
from PySide6.QtCore import Signal as pyqtSignal
from PySide6.QtSql import QSqlTableModel, QSqlDatabase, QSqlQuery, QSqlField

from OpenNumismat.Collection.CollectionFields import CollectionFieldsBase
from OpenNumismat.Collection.CollectionFields import FieldTypes as Type
from OpenNumismat.Collection.CollectionFields import CollectionFields
from OpenNumismat.Collection.CollectionFields import ImageFields
from OpenNumismat.Collection.CollectionPages import CollectionPages
from OpenNumismat.Collection.Password import cryptPassword, PasswordDialog
from OpenNumismat.Collection.Description import CollectionDescription
from OpenNumismat.Reference.Reference import Reference
from OpenNumismat.Reference.Reference import CrossReferenceSection
from OpenNumismat.Reference.ReferenceDialog import AllReferenceDialog
from OpenNumismat.EditCoinDialog.EditCoinDialog import EditCoinDialog
from OpenNumismat.Collection.CollectionFields import Statuses
from OpenNumismat.Collection.VersionUpdater import updateCollection
from OpenNumismat.Tools.CursorDecorators import waitCursorDecorator
from OpenNumismat.Tools import Gui
from OpenNumismat.Tools.Gui import infoMessageBox
from OpenNumismat.Settings import Settings, BaseSettings
from OpenNumismat import version
from OpenNumismat.Collection.Export import ExportDialog
from OpenNumismat.Tools.Converters import numberWithFraction, htmlToPlainText


class CollectionModel(QSqlTableModel):
    rowInserted = pyqtSignal(object)
    modelChanged = pyqtSignal()
    tagsChanged = pyqtSignal()
    IMAGE_FORMAT = 'jpg'
    SQLITE_READONLY = '8'

    def __init__(self, collection, parent=None):
        super().__init__(parent, collection.db)

        self.intFilter = ''
        self.extFilter = ''
        self.searchFilter = ''

        self.reference = collection.reference
        self.fields = collection.fields
        self.description = collection.description
        self.settings = collection.settings
        self.proxy = None

        self.rowsInserted.connect(self.rowsInsertedEvent)

    def supportedDropActions(self):
        return Qt.MoveAction

    def rowsInsertedEvent(self, parent, start, end):
        self.insertedRowIndex = self.index(end, 0)

    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            # Localize values
            data = super().data(index, role)
            field = self.fields.fields[index.column()]
            try:
                if field.name == 'status':
                    text = Statuses[data]
                elif field.name == 'year':
                    year = str(data)
                    if year and year[0] == '-':
                        text = "%s BC" % year[1:]
                    else:
                        text = year
                elif field.name == 'axis':
                    if self.settings['axis_in_hours']:
                        value = int(data)
                        value += 360 / 12 / 2
                        value /= 360 / 12
                        value = int(value)
                        if value == 0:
                            value = 12
                        text = str(value) + self.tr("h")
                    else:
                        return data
                elif field.name == 'rating':
                    maxStarCount = self.settings['stars_count']
                    star_count = math.ceil(data.count('*') / (10 / maxStarCount))
                    # text = '★' * star_count  # black star
                    text = '⭐' * star_count  # white medium star
                elif field.type == Type.BigInt:
                    text = QLocale.system().toString(int(data))
                elif field.type == Type.Text:
                    text = htmlToPlainText(data)
                elif field.type == Type.Money:
                    text = QLocale.system().toString(float(data), 'f', precision=2)
                    dp = QLocale.system().decimalPoint()
                    text = text.rstrip('0').rstrip(dp)
                elif field.type == Type.Denomination:
                    text, converted = numberWithFraction(data, self.settings['convert_fraction'])
                    if not converted:
                        text = QLocale.system().toString(float(data), 'f', precision=2)
                        dp = QLocale.system().decimalPoint()
                        text = text.rstrip('0').rstrip(dp)
                elif field.type == Type.Value:
                    text = QLocale.system().toString(float(data), 'f', precision=3)
                    dp = QLocale.system().decimalPoint()
                    text = text.rstrip('0').rstrip(dp)
                elif field.type == Type.PreviewImage:
                    if data:
                        return self.getPreviewImage(data)
                    else:
                        return None
                elif field.type == Type.Image:
                    if data:
                        return self.getImage(data)
                    else:
                        return None
                elif field.type == Type.Date:
                    date = QtCore.QDate.fromString(data, Qt.ISODate)
                    text = QLocale.system().toString(date, QLocale.ShortFormat)
                elif field.type == Type.DateTime:
                    date = QtCore.QDateTime.fromString(data, Qt.ISODate)
                    # Timestamp in DB stored in UTC
                    date.setTimeSpec(Qt.UTC)
                    date = date.toLocalTime()
                    text = QLocale.system().toString(date, QLocale.ShortFormat)
                else:
                    return data
            except (ValueError, TypeError):
                return data
            return text
        elif role == Qt.UserRole:
            field = self.fields.fields[index.column()]
            if field.type == Type.Denomination:
                data = super().data(index, Qt.DisplayRole)
                data, _ = numberWithFraction(data, self.settings['convert_fraction'])
                return data
            return super().data(index, Qt.DisplayRole)
        elif role == Qt.DecorationRole:
            field = self.fields.fields[index.column()]
            data = super().data(index, Qt.DisplayRole)
            if data:
                if field.name == 'status':
                    icon = Gui.statusIcon(data)
                else:
                    icon = self.reference.getIcon(field.name, data)

                return icon
        elif role == Qt.TextAlignmentRole:
            field = self.fields.fields[index.column()]
            if field.type == Type.BigInt:
                return Qt.AlignRight | Qt.AlignVCenter

        return super().data(index, role)

    def dataDisplayRole(self, index):
        return super().data(index, Qt.DisplayRole)

    def addCoin(self, record, parent=None):
        record.setNull('id')  # remove ID value from record
        if not record.value('status'):
            record.setValue('status', self.settings['default_status'])

        dialog = EditCoinDialog(self, record, parent)
        result = dialog.exec_()
        if result == QDialog.Accepted:
            self.appendRecord(record)

    def appendRecord(self, record):
        rowCount = self.rowCount()

        tag_ids = record.value('tags')
        record.remove(record.indexOf('tags'))

        # pas
        record.remove(record.indexOf('uid'))

        self.insertRecord(-1, record)
        self.submitAll()

        # query = self.query()
        # print(query.lastInsertId())
        query = QSqlQuery(self.database())
        query.exec_('SELECT last_insert_rowid()')
        if query.first():
            coin_id = query.value(0)
            for tag_id in tag_ids:
                query = QSqlQuery(self.database())
                query.prepare("INSERT INTO coins_tags(coin_id, tag_id) VALUES(?, ?)")
                query.addBindValue(coin_id)
                query.addBindValue(tag_id)
                query.exec_()

        if rowCount < self.rowCount():  # inserted row visible in current model
            if self.insertedRowIndex.isValid():
                self.rowInserted.emit(self.insertedRowIndex)

    def insertRecord(self, row, record):
        self._updateRecord(record)
        record.setNull('id')  # remove ID value from record
        record.setValue('createdat', record.value('updatedat'))

        query = QSqlQuery("SELECT MAX(sort_id) FROM coins", self.database())
        query.first()
        sort_id = query.record().value(0)
        if not sort_id:
            sort_id = 0
        record.setValue('sort_id', sort_id + 1)

        self.database().transaction()
        for field in ImageFields:
            value = record.value(field)
            if value:
                query = QSqlQuery(self.database())
                query.prepare("INSERT INTO photos (title, image) VALUES (?, ?)")
                query.addBindValue(record.value(field + '_title'))
                query.addBindValue(value)
                query.exec_()

                img_id = query.lastInsertId()
            else:
                img_id = None

            record.setValue(field, img_id)
            record.remove(record.indexOf(field + '_id'))
            record.remove(record.indexOf(field + '_title'))

        value = record.value('image')
        if value:
            query = QSqlQuery(self.database())
            query.prepare("INSERT INTO images (image) VALUES (?)")
            query.addBindValue(value)
            query.exec_()

            img_id = query.lastInsertId()
        else:
            img_id = None
        self.database().commit()

        record.setValue('image', img_id)
        record.remove(record.indexOf('image_id'))

        return super().insertRecord(row, record)

    def setRecord(self, row, record):
        self._updateRecord(record)

        self.database().transaction()
        # TODO : check that images was realy changed
        for field in ImageFields:
            img_id = record.value(field + '_id')
            value = record.value(field)
            if not value:
                if img_id:
                    query = QSqlQuery(self.database())
                    query.prepare("DELETE FROM photos WHERE id=?")
                    query.addBindValue(img_id)
                    query.exec_()

                    img_id = None
            else:
                if img_id:
                    query = QSqlQuery(self.database())
                    query.prepare("UPDATE photos SET title=?, image=? WHERE id=?")
                    query.addBindValue(record.value(field + '_title'))
                    query.addBindValue(record.value(field))
                    query.addBindValue(img_id)
                    query.exec_()
                else:
                    query = QSqlQuery(self.database())
                    query.prepare("INSERT INTO photos (title, image) VALUES (?, ?)")
                    query.addBindValue(record.value(field + '_title'))
                    query.addBindValue(record.value(field))
                    query.exec_()

                    img_id = query.lastInsertId()

            if img_id:
                record.setValue(field, img_id)
            else:
                record.setNull(field)
            record.remove(record.indexOf(field + '_id'))
            record.remove(record.indexOf(field + '_title'))

        img_id = record.value('image_id')
        value = record.value('image')
        if not value:
            if img_id:
                query = QSqlQuery(self.database())
                query.prepare("DELETE FROM images WHERE id=?")
                query.addBindValue(img_id)
                query.exec_()

                img_id = None
        else:
            if img_id:
                query = QSqlQuery(self.database())
                query.prepare("UPDATE images SET image=? WHERE id=?")
                query.addBindValue(record.value('image'))
                query.addBindValue(img_id)
                query.exec_()
            else:
                query = QSqlQuery(self.database())
                query.prepare("INSERT INTO images (image) VALUES (?)")
                query.addBindValue(record.value('image'))
                query.exec_()

                img_id = query.lastInsertId()

        coin_id = record.value('id')

        query = QSqlQuery(self.database())
        query.prepare("DELETE FROM coins_tags WHERE coin_id=?")
        query.addBindValue(coin_id)
        query.exec_()

        for tag_id in record.value('tags'):
            query = QSqlQuery(self.database())
            query.prepare("INSERT INTO coins_tags(coin_id, tag_id) VALUES(?, ?)")
            query.addBindValue(coin_id)
            query.addBindValue(tag_id)
            query.exec_()

        record.remove(record.indexOf('tags'))

        # pas
        record.remove(record.indexOf('uid'))
        
        self.database().commit()

        if img_id:
            record.setValue('image', img_id)
        else:
            record.setNull('image')
        record.remove(record.indexOf('image_id'))

        return super().setRecord(row, record)

    def record(self, row=-1):
        if row >= 0:
            record = super().record(row)
        else:
            record = super().record()

        for field in ImageFields:
            record.append(QSqlField(field + '_title'))
            record.append(QSqlField(field + '_id'))

            img_id = record.value(field)
            if img_id:
                data = self.getImage(img_id)
                record.setValue(field, data)
                record.setValue(field + '_title', self.getImageTitle(img_id))
                record.setValue(field + '_id', img_id)
            else:
                record.setValue(field, None)

        record.append(QSqlField('image_id'))
        img_id = record.value('image')
        if img_id:
            data = self.getPreviewImage(img_id)
            record.setValue('image', data)
            record.setValue('image_id', img_id)
        else:
            record.setValue('image', None)

        tag_ids = []
        coin_id = record.value('id')
        if coin_id:
            query = QSqlQuery(self.database())
            query.prepare("SELECT tag_id FROM coins_tags WHERE coin_id=?")
            query.addBindValue(coin_id)
            query.exec_()

            while query.next():
                tag_id = query.record().value(0)
                tag_ids.append(tag_id)

        record.append(QSqlField('tags'))
        record.setValue('tags', tag_ids)

        # pas
        record.append(QSqlField('uid'))
        record.setValue('uid', coin_id)

        return record

    def removeRow(self, row):
        record = super().record(row)

        ids = []
        for field in ImageFields:
            value = record.value(field)
            if value:
                ids.append(value)

        if ids:
            ids_sql = '(' + ','.join('?' * len(ids)) + ')'

            query = QSqlQuery(self.database())
            query.prepare("DELETE FROM photos WHERE id IN " + ids_sql)
            for id_ in ids:
                query.addBindValue(id_)
            query.exec_()

        value = record.value('image')
        if value:
            query = QSqlQuery(self.database())
            query.prepare("DELETE FROM images WHERE id=?")
            query.addBindValue(value)
            query.exec_()

        coin_id = record.value('id')
        if coin_id:
            query = QSqlQuery(self.database())
            query.prepare("DELETE FROM coins_tags WHERE coin_id=?")
            query.addBindValue(coin_id)
            query.exec_()

        return super().removeRow(row)

    def _updateRecord(self, record):
        if self.proxy:
            self.proxy.setDynamicSortFilter(False)

        for field in self.fields.userFields:
            if field.type == Type.Image:
                # Convert image to DB format
                image = record.value(field.name)
                if isinstance(image, str):
                    # Copying record as text (from Excel) store missed images
                    # as string
                    record.setNull(field.name)
                elif isinstance(image, QImage):
                    ba = QtCore.QByteArray()
                    buffer = QtCore.QBuffer(ba)
                    buffer.open(QtCore.QIODevice.WriteOnly)

                    # Resize big images for storing in DB
                    sideLen = self.settings['ImageSideLen']
                    if sideLen > 0:
                        maxWidth = sideLen
                        maxHeight = sideLen
                        if image.width() > maxWidth or image.height() > maxHeight:
                            image = image.scaled(maxWidth, maxHeight,
                                    Qt.KeepAspectRatio, Qt.SmoothTransformation)

                    image.save(buffer, self.IMAGE_FORMAT)
                    record.setValue(field.name, ba)
                elif isinstance(image, bytes):
                    ba = QtCore.QByteArray(image)
                    record.setValue(field.name, ba)

        # Creating preview image for list
        self._recalculateImage(record)

        currentTime = QtCore.QDateTime.currentDateTimeUtc()
        # currentTime.setTimeSpec(Qt.LocalTime)
        record.setValue('updatedat', currentTime.toString(Qt.ISODateWithMs))

    def _recalculateImage(self, record):
        # Creating preview image for list
        if record.isNull('obverseimg') and record.isNull('reverseimg'):
            record.setNull('image')
        else:
            # Get height of list view for resizing images
            tmp = QTableView()
            height_multiplex = self.settings['image_height']
            height = int(tmp.verticalHeader().defaultSectionSize() * height_multiplex - 1)

            obverseImage = QImage()
            reverseImage = QImage()

            if not record.isNull('obverseimg'):
                obverseImage.loadFromData(record.value('obverseimg'))
                obverseImage = obverseImage.scaledToHeight(height,
                                                    Qt.SmoothTransformation)
            if not record.isNull('reverseimg') and reverseImage.isNull():
                reverseImage.loadFromData(record.value('reverseimg'))
                reverseImage = reverseImage.scaledToHeight(height,
                                                    Qt.SmoothTransformation)

            image = QImage(obverseImage.width() + reverseImage.width(),
                                 height, QImage.Format_RGB32)
            image.fill(Qt.white)

            paint = QPainter(image)
            if not record.isNull('obverseimg'):
                paint.drawImage(QtCore.QRectF(0, 0, obverseImage.width(), height), obverseImage,
                                QtCore.QRectF(0, 0, obverseImage.width(), height))
            if not record.isNull('reverseimg'):
                paint.drawImage(QtCore.QRectF(obverseImage.width(), 0, reverseImage.width(), height), reverseImage,
                                QtCore.QRectF(0, 0, reverseImage.width(), height))
            paint.end()

            ba = QtCore.QByteArray()
            buffer = QtCore.QBuffer(ba)
            buffer.open(QtCore.QIODevice.WriteOnly)

            # Store as PNG for better view
            image.save(buffer, 'png')
            record.setValue('image', ba)

    def moveRows(self, row1, row2):
        if self.proxy:
            self.proxy.setDynamicSortFilter(False)

            sort_column_id = self.fields.sort_id.id
            self.sort(sort_column_id, Qt.AscendingOrder)

        row_rang = []
        if row2 == -1:
            row_rang = range(row1 + 1, self.rowCount())
        elif row1 > row2:
            row_rang = range(row1 - 1, row2 - 1, -1)
        elif row1 < row2:
            row_rang = range(row1 + 1, row2 + 1)

        if row_rang:
            record = super().record(row1)
            old_sort_id = record.value('sort_id')
            for row in row_rang:
                record1 = super().record(row)
                sort_id = record1.value('sort_id')
                record1.setValue('sort_id', old_sort_id)
                super().setRecord(row, record1)
                old_sort_id = sort_id
            record.setValue('sort_id', old_sort_id)
            super().setRecord(row1, record)

        self.submitAll()

        if self.proxy:
            self.sort(-1, Qt.AscendingOrder)

    @waitCursorDecorator
    def setRowsPos(self, indexes):
        sorted_ids = sorted([index.data(Qt.UserRole) for index in indexes])
        for index, sort_id in zip(indexes, sorted_ids):
            record = super().record(index.row())
            record.setValue('sort_id', sort_id)
            super().setRecord(index.row(), record)

        self.submitAll()

    def recalculateAllImages(self, parent=None):
        while self.canFetchMore():
            self.fetchMore()
        rowCount = self.rowCount()

        if not parent:
            parent = self.parent()

        progressDlg = Gui.ProgressDialog(self.tr("Updating records"),
                                         self.tr("Cancel"), rowCount, parent)

        self.database().transaction()

        for row in range(rowCount):
            progressDlg.step()
            if progressDlg.wasCanceled():
                break

            record = self.record(row)
            self._recalculateImage(record)
            img_id = record.value('image_id')
            value = record.value('image')
            if value and img_id:
                query = QSqlQuery(self.database())
                query.prepare("UPDATE images SET image=? WHERE id=?")
                query.addBindValue(record.value('image'))
                query.addBindValue(img_id)
                query.exec_()

        progressDlg.setLabelText(self.tr("Saving..."))

        self.database().commit()

        progressDlg.reset()

    def submitAll(self):
        ret = super().submitAll()
        if not ret:
            if self.lastError().nativeErrorCode() == self.SQLITE_READONLY:
                message = self.tr("file is readonly")
            else:
                message = self.lastError().databaseText()
            QMessageBox.critical(
                self.parent(), self.tr("Saving"),
                self.tr("Can't save data: %s") % message)

        if self.proxy:
            self.proxy.setDynamicSortFilter(True)

        return ret

    def select(self):
        ret = super().select()

        self.modelChanged.emit()

        return ret

    def columnType(self, column):
        if isinstance(column, QtCore.QModelIndex):
            column = column.column()

        return self.fields.fields[column].type

    def columnName(self, column):
        if isinstance(column, QtCore.QModelIndex):
            column = column.column()

        return self.fields.fields[column].name

    def getImage(self, img_id):
        query = QSqlQuery(self.database())
        query.prepare("SELECT image FROM photos WHERE id=?")
        query.addBindValue(img_id)
        query.exec_()
        if query.first():
            return query.record().value(0)

    def getPreviewImage(self, img_id):
        query = QSqlQuery(self.database())
        query.prepare("SELECT image FROM images WHERE id=?")
        query.addBindValue(img_id)
        query.exec_()
        if query.first():
            return query.record().value(0)

    def getImageTitle(self, img_id):
        query = QSqlQuery(self.database())
        query.prepare("SELECT title FROM photos WHERE id=?")
        query.addBindValue(img_id)
        query.exec_()
        if query.first():
            return query.record().value(0)

    def clearFilters(self):
        self.intFilter = ''
        self.searchFilter = ''
        self.__applyFilter()

    def setFilter(self, filter_):
        self.intFilter = filter_
        self.__applyFilter()

    def setAdditionalFilter(self, filter_):
        self.extFilter = filter_
        self.__applyFilter()

    def setSearchFilter(self, filter_):
        self.searchFilter = filter_
        self.__applyFilter()

    def __applyFilter(self):
        filters = []
        if self.intFilter:
            filters.append(self.intFilter)
        if self.extFilter:
            filters.append(self.extFilter)
        if self.searchFilter:
            filters.append(self.searchFilter)
        combinedFilter = ' AND '.join(filters)

        # Checking for SQLITE_MAX_SQL_LENGTH (default value - 1 000 000)
        if len(combinedFilter) > 900000:
            QMessageBox.warning(self.parent(),
                            self.tr("Filtering"),
                            self.tr("Filter is too complex. Will be ignored"))
            return

        super().setFilter(combinedFilter)

    def isExist(self, record):
        fields = ('title', 'value', 'unit', 'country', 'period', 'ruler',
                  'year', 'mint', 'mintmark', 'type', 'series', 'subjectshort',
                  'status', 'material', 'quality', 'paydate', 'payprice',
                  'saller', 'payplace', 'saledate', 'saleprice', 'buyer',
                  'saleplace', 'variety', 'obversevar', 'reversevar',
                  'edgevar')
        filterParts = [field + '=?' for field in fields]
        sqlFilter = ' AND '.join(filterParts)

        db = self.database()
        query = QSqlQuery(db)
        query.prepare("SELECT 1 FROM coins WHERE id<>? AND " + sqlFilter + " LIMIT 1")
        query.addBindValue(record.value('id'))
        for field in fields:
            query.addBindValue(record.value(field))
        query.exec_()
        if query.first():
            return True

        return False


class CollectionSettings(BaseSettings):
    Default = {
            'Version': 9,
            'Type': version.AppName,
            'Password': cryptPassword(),
            'ImageSideLen': 1024,
            'image_height': 1.5,
            'free_numeric': False,
            'convert_fraction': False,
            'images_at_bottom': False,
            'demo_status_used': True,
            'pass_status_used': True,
            'owned_status_used': True,
            'ordered_status_used': True,
            'sold_status_used': True,
            'sale_status_used': True,
            'wish_status_used': True,
            'missing_status_used': True,
            'bidding_status_used': True,
            'duplicate_status_used': True,
            'replacement_status_used': True,
            'demo_status_title': '',
            'pass_status_title': '',
            'owned_status_title': '',
            'ordered_status_title': '',
            'sold_status_title': '',
            'sale_status_title': '',
            'wish_status_title': '',
            'missing_status_title': '',
            'bidding_status_title': '',
            'duplicate_status_title': '',
            'replacement_status_title': '',
            'enable_bc': True,
            'rich_text': False,
            'default_status': 'demo',
            'colnect_category': '',
            'colnect_country': 0,
            'ans_department': '',
            'ans_has_image': False,
            'title_template': '<value> <unit> <year> <subjectshort> <mintmark> <variety>',
            'coin_group_title': QT_TRANSLATE_NOOP("CollectionSettings", "Overall"),
            'coin_main_group_title': QT_TRANSLATE_NOOP("CollectionSettings", "Main details"),
            'coin_state_group_title': QT_TRANSLATE_NOOP("CollectionSettings", "State"),
            'market_group_title': QT_TRANSLATE_NOOP("CollectionSettings", "Market"),
            'market_buy_group_title': QT_TRANSLATE_NOOP("CollectionSettings", "Buy"),
            'market_sale_group_title': QT_TRANSLATE_NOOP("CollectionSettings", "Sale"),
            'map_group_title': QT_TRANSLATE_NOOP("CollectionSettings", "Map"),
            'parameters_group_title': QT_TRANSLATE_NOOP("CollectionSettings", "Technical data"),
            'parameters_parameters_group_title': QT_TRANSLATE_NOOP("CollectionSettings", "Parameters"),
            'parameters_specificity_group_title': QT_TRANSLATE_NOOP("CollectionSettings", "Specificity"),
            'parameters_minting_group_title': QT_TRANSLATE_NOOP("CollectionSettings", "Minting"),
            'design_group_title': QT_TRANSLATE_NOOP("CollectionSettings", "Design"),
            'design_obverse_group_title': QT_TRANSLATE_NOOP("CollectionSettings", "Obverse"),
            'design_reverse_group_title': QT_TRANSLATE_NOOP("CollectionSettings", "Reverse"),
            'design_edge_group_title': QT_TRANSLATE_NOOP("CollectionSettings", "Edge"),
            'classification_group_title': QT_TRANSLATE_NOOP("CollectionSettings", "Classification"),
            'classification_catalogue_group_title': QT_TRANSLATE_NOOP("CollectionSettings", "Catalogue"),
            'classification_price_group_title': QT_TRANSLATE_NOOP("CollectionSettings", "Price"),
            'classification_variation_group_title': QT_TRANSLATE_NOOP("CollectionSettings", "Variation"),
            'images_group_title': QT_TRANSLATE_NOOP("CollectionSettings", "Images"),
            'tags_group_title': QT_TRANSLATE_NOOP("CollectionSettings", "Tags"),
            'relative_url': False,
            'axis_in_hours': False,
            'stars_count': 10,
            'tags_used': True,
            'market_paysale_group_title': QT_TRANSLATE_NOOP("CollectionSettings", "Pay And Sale"),
    }

    def __init__(self, db):
        super().__init__()
        self.db = db

        if 'settings' not in self.db.tables():
            self.create(self.db)

        query = QSqlQuery("SELECT * FROM settings", self.db)
        while query.next():
            record = query.record()
            title = record.value('title')
            if title in self.keys():
                if title in ('Version', 'ImageSideLen', 'colnect_country',
                             'stars_count'):
                    value = int(record.value('value'))
                elif title in ('image_height',):
                    value = float(record.value('value'))
                elif title in ('free_numeric', 'convert_fraction',
                               'images_at_bottom', 'enable_bc', 'rich_text',
                               'relative_url', 'axis_in_hours', 'tags_used'):
                    value = record.value('value').lower() in ('true', '1')
                elif '_status_used' in title:
                    value = record.value('value').lower() in ('true', '1')
                else:
                    value = record.value('value')
                self.__setitem__(title, value)

        for status, title in Statuses.items():
            # Fill default status titles
            self.Default[status + '_status_title'] = QApplication.translate("Status", title)
        # Fill global statuses from settings
        Statuses.init(self)

        for key in self.keys():
            if '_group_title' in key:
                self.Default[key] = QApplication.translate(
                    "CollectionSettings", self.Default[key]
                )

    def keys(self):
        return self.Default.keys()

    def _getValue(self, key):
        return self.Default[key]

    def save(self):
        self.db.transaction()

        for key, value in self.items():
            query = QSqlQuery(self.db)
            query.prepare("INSERT OR REPLACE INTO settings (title, value)"
                          " VALUES (?, ?)")
            query.addBindValue(key)
            query.addBindValue(str(value))
            query.exec_()

        self.db.commit()

    @staticmethod
    def create(db=QSqlDatabase()):
        db.transaction()

        sql = """CREATE TABLE settings (
            title CHAR NOT NULL UNIQUE,
            value CHAR)"""
        QSqlQuery(sql, db)

        for key, value in CollectionSettings.Default.items():
            query = QSqlQuery(db)
            query.prepare("INSERT INTO settings (title, value)"
                          " VALUES (?, ?)")
            query.addBindValue(key)
            query.addBindValue(str(value))
            query.exec_()

        db.commit()


class Collection(QtCore.QObject):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.db = QSqlDatabase.addDatabase('QSQLITE')
        self._pages = None
        self.fileName = None

    def isOpen(self):
        return self.db.isValid() and self.fileName

    def open(self, fileName):
        self.fileName = None

        file = QtCore.QFileInfo(fileName)
        if file.isFile():
            self.db.setDatabaseName(fileName)
            if not self.db.open() or not self.db.tables():
                print(self.db.lastError().text())
                QMessageBox.critical(self.parent(),
                                self.tr("Open collection"),
                                self.tr("Can't open collection %s") % fileName)
                return False
        else:
            QMessageBox.critical(self.parent(),
                                self.tr("Open collection"),
                                self.tr("Collection %s not exists") % fileName)
            return False

        if ('coins' not in self.db.tables()) or ('settings' not in self.db.tables()):
            QMessageBox.critical(self.parent(),
                    self.tr("Open collection"),
                    self.tr("Collection %s in wrong format") % fileName)
            return False

        self.settings = CollectionSettings(self.db)
        if self.settings['Type'] != version.AppName:
            QMessageBox.critical(self.parent(),
                    self.tr("Open collection"),
                    self.tr("Collection %s in wrong format") % fileName)
            return False
        if int(self.settings['Version']) > self.settings.Default['Version']:
            QMessageBox.critical(self.parent(),
                    self.tr("Open collection"),
                    self.tr("Collection %s a newer version.\n"
                            "Please update OpenNumismat") % fileName)
            return False

        if self.settings['Password'] != cryptPassword():
            dialog = PasswordDialog(
                self.settings['Password'], self.fileNameToCollectionName(fileName),
                self.parent())
            result = dialog.exec_()
            if result == QDialog.Rejected:
                return False

        self.fields = CollectionFields(self.db)

        self.fileName = fileName

        if not updateCollection(self):
            self.fileName = None
            return False

        self._pages = CollectionPages(self.db)

        self.description = CollectionDescription(self)

        self.__speedup()

        return True

    def create(self, fileName):
        self.fileName = None

        if QtCore.QFileInfo(fileName).exists():
            QMessageBox.critical(self.parent(),
                                    self.tr("Create collection"),
                                    self.tr("Specified file already exists"))
            return False

        self.db.setDatabaseName(fileName)
        if not self.db.open():
            print(self.db.lastError().text())
            QMessageBox.critical(self.parent(),
                                       self.tr("Create collection"),
                                       self.tr("Can't open collection"))
            return False

        self.settings = CollectionSettings(self.db)

        self.fields = CollectionFields(self.db)

        self.createCoinsTable()
        self.createTagsTable()
        self.createPaySalesTable()

        self.fileName = fileName

        self._pages = CollectionPages(self.db)

        self.description = CollectionDescription(self)

        self.__speedup()

        return True

    def __speedup(self):
        settings = Settings()
        if settings['speedup'] == 1:
            sql = "PRAGMA synchronous=NORMAL"
            QSqlQuery(sql, self.db)
            sql = "PRAGMA journal_mode=MEMORY"
            QSqlQuery(sql, self.db)
        elif settings['speedup'] == 2:
            sql = "PRAGMA synchronous=OFF"
            QSqlQuery(sql, self.db)
            sql = "PRAGMA journal_mode=MEMORY"
            QSqlQuery(sql, self.db)

    def createCoinsTable(self):
        sqlFields = []
        for field in self.fields:
            if field.name == 'id':
                sqlFields.append('id INTEGER PRIMARY KEY')
            else:
                sqlFields.append("%s %s" % (field.name, Type.toSql(field.type)))

        sql = "CREATE TABLE coins (" + ", ".join(sqlFields) + ")"
        QSqlQuery(sql, self.db)

        sql = "CREATE TABLE photos (id INTEGER PRIMARY KEY, title TEXT, image BLOB)"
        QSqlQuery(sql, self.db)

        sql = "CREATE TABLE images (id INTEGER PRIMARY KEY, image BLOB)"
        QSqlQuery(sql, self.db)

    def createTagsTable(self):
        sql = """CREATE TABLE tags (
                    id INTEGER NOT NULL PRIMARY KEY,
                    tag TEXT,
                    parent_id INTEGER,
                    position INTEGER)"""
        QSqlQuery(sql, self.db)

        sql = """CREATE TABLE coins_tags (
                    coin_id INTEGER,
                    tag_id INTEGER)"""
        QSqlQuery(sql, self.db)

    # pas
    def createPaySalesTable(self):
        sql = """CREATE TABLE coins_paysales (
                    id         INTEGER         PRIMARY KEY AUTOINCREMENT,
                    coin_id    INTEGER         REFERENCES coins (id) ON DELETE CASCADE
                                                                     ON UPDATE CASCADE,
                    oper_date  DATE,
                    oper_name  TEXT,
                    cost       NUMERIC (10, 2),
                    quantity   INTEGER,
                    place      TEXT,
                    oper_actor TEXT
                )"""
        QSqlQuery(sql, self.db)

    def isReferenceAttached(self):
        return ('sections' in self.db.tables())

    def loadReference(self, fileName):
        if self.isReferenceAttached():
            self.reference = Reference(self.fields, self.parent(), db=self.db)
        else:
            self.reference = Reference(self.fields, self.parent())
            self.reference.open(fileName)
        self.reference.load()

    def getFileName(self):
        return QtCore.QDir(self.fileName).absolutePath()

    def getCollectionName(self):
        return Collection.fileNameToCollectionName(self.fileName)

    def getDescription(self):
        return self.description

    def model(self):
        return self.createModel()

    def pages(self):
        return self._pages

    def createModel(self):
        model = CollectionModel(self)
        model.title = self.getCollectionName()
        model.setEditStrategy(QSqlTableModel.OnManualSubmit)
        model.setTable('coins')
        model.select()
        for field in self.fields:
            model.setHeaderData(field.id, QtCore.Qt.Horizontal, field.title)

        return model

    def fillReference(self):
        sections = self.reference.allSections()
        progressDlg = Gui.ProgressDialog(self.tr("Updating reference"),
                            self.tr("Cancel"), len(sections), self.parent())

        for columnName in sections:
            progressDlg.step()
            if progressDlg.wasCanceled():
                break

            refSection = self.reference.section(columnName)
            if isinstance(refSection, CrossReferenceSection):
                rel = refSection.model.relationModel(1)
                for i in range(rel.rowCount()):
                    data = rel.data(rel.index(i, rel.fieldIndex('value')))
                    parentId = rel.data(rel.index(i, rel.fieldIndex('id')))
                    query = QSqlQuery(self.db)
                    sql = "SELECT DISTINCT %s FROM coins WHERE %s<>'' AND %s IS NOT NULL AND %s=?" % (columnName, columnName, columnName, refSection.parent_name)
                    query.prepare(sql)
                    query.addBindValue(data)
                    query.exec_()
                    refSection.fillFromQuery(parentId, query)
                    refSection.reload()
            else:
                sql = "SELECT DISTINCT %s FROM coins WHERE %s<>'' AND %s IS NOT NULL" % (columnName, columnName, columnName)
                query = QSqlQuery(sql, self.db)
                refSection.fillFromQuery(query)
                refSection.reload()

        progressDlg.reset()

    def editReference(self):
        dialog = AllReferenceDialog(self.reference, self.parent())
        dialog.exec_()

    def attachReference(self):
        result = QMessageBox.information(
            self.parent(), self.tr("Attach"),
            self.tr("Attach current reference to a collection file?"),
            QMessageBox.Yes | QMessageBox.Cancel,
            QMessageBox.Cancel)
        if result == QMessageBox.Yes:
            progressDlg = Gui.ProgressDialog(
                self.tr("Attaching reference"), None,
                len(self.reference.sections), self.parent())

            query = QSqlQuery(self.db)
            query.prepare("ATTACH ? AS ref")
            query.addBindValue(self.reference.fileName)
            res = query.exec_()
            if not res:
                progressDlg.reset()
                QMessageBox.critical(self.parent(),
                            self.tr("Attaching reference"),
                            self.tr("Can't attach reference:\n%s" %
                                    query.lastError().text()))
                return

            reference = Reference(self.fields, self.parent(), db=self.db)
            reference.db.transaction()
            reference.create()

            for section in self.reference.sections:
                progressDlg.step()

                if res:
                    query = QSqlQuery(self.db)
                    query.prepare("INSERT INTO %s SELECT * FROM ref.%s" %
                                  (section.table_name, section.table_name))
                    res = query.exec_()

            if res:
                reference.db.commit()
                self.reference = reference
            else:
                reference.db.rollback()
                progressDlg.reset()
                QMessageBox.critical(self.parent(),
                            self.tr("Attaching reference"),
                            self.tr("Can't attach reference:\n%s") %
                                    query.lastError().text())

            QSqlQuery("DETACH ref", reference.db)

            self.reference.load()

            progressDlg.reset()

            self.__updateAttachAction()

    def detachReference(self):
        fileName, _selectedFilter = QFileDialog.getSaveFileName(
            self.parent(), self.tr("Save reference as"),
            filter=self.tr("Reference (*.ref)"))
        if fileName:
            if os.path.isfile(fileName):
                os.remove(fileName)

            progressDlg = Gui.ProgressDialog(
                self.tr("Detaching reference"), None,
                len(self.reference.sections), self.parent())

            reference = Reference(self.fields, self.parent())
            if not reference.open(fileName, interactive=False):
                return

            query = QSqlQuery(reference.db)
            query.prepare("ATTACH ? AS ref")
            query.addBindValue(self.fileName)
            res = query.exec_()
            if not res:
                progressDlg.reset()
                QMessageBox.critical(self.parent(),
                            self.tr("Detach reference"),
                            self.tr("Can't detach reference:\n%s") %
                                    query.lastError().text())
                return

            reference.db.transaction()

            for section in self.reference.sections:
                progressDlg.step()

                if res:
                    query = QSqlQuery(reference.db)
                    query.prepare("INSERT INTO %s SELECT * FROM ref.%s" % (section.table_name, section.table_name))
                    res = query.exec_()

            if res:
                reference.db.commit()
            else:
                reference.db.rollback()
                progressDlg.reset()
                QMessageBox.critical(self.parent(),
                            self.tr("Create reference"),
                            self.tr("Can't create reference:\n%s") % fileName)
                return

            for section in self.reference.sections:
                section.model.clear()

            self.db.transaction()

            for table_name in self.db.tables():
                if 'ref_' in table_name:
                    if res:
                        query = QSqlQuery(self.db)
                        query.prepare("DROP TABLE %s" % table_name)
                        res = query.exec_()

            if res:
                query = QSqlQuery(self.db)
                query.prepare("DROP TABLE sections")
                res = query.exec_()

            if res:
                query = QSqlQuery(self.db)
                query.prepare("DROP TABLE ref")
                res = query.exec_()

            if res:
                self.db.commit()
                self.reference = reference
            else:
                self.db.rollback()
                QMessageBox.critical(self.parent(),
                            self.tr("Create reference"),
                            self.tr("Can't clear attached reference:\n%s") %
                                    query.lastError().text())

            QSqlQuery("DETACH ref", reference.db)

            self.reference.load()

            progressDlg.reset()

            self.__updateAttachAction()

    def __updateAttachAction(self):
        try:
            self.attachReferenceAct.triggered.disconnect()
        except RuntimeError:
            pass  # nothing is connected yet

        if self.isReferenceAttached():
            self.attachReferenceAct.setText(self.tr("Detach current reference"))
            self.attachReferenceAct.triggered.connect(self.detachReference)
        else:
            self.attachReferenceAct.setText(self.tr("Attach current reference"))
            self.attachReferenceAct.triggered.connect(self.attachReference)

    def referenceMenu(self, parent=None):
        fillReferenceAct = QAction(self.tr("Fill from collection"), parent)
        fillReferenceAct.triggered.connect(self.fillReference)

        editReferenceAct = QAction(self.tr("Edit..."), parent)
        editReferenceAct.triggered.connect(self.editReference)

        separator = QAction(parent)
        separator.setSeparator(True)

        self.attachReferenceAct = QAction(parent)
        self.__updateAttachAction()

        acts = (fillReferenceAct, editReferenceAct,
                separator, self.attachReferenceAct)

        return acts

    @waitCursorDecorator
    def __make_backup(self, backupFileName):
        srcFile = QtCore.QFile(self.fileName)
        return srcFile.copy(backupFileName)

    def backup(self):
        backupDir = QtCore.QDir(Settings()['backup'])
        if not backupDir.exists():
            backupDir.mkpath(backupDir.absolutePath())

        backupFileName = backupDir.filePath("%s_%s.db" % (self.getCollectionName(), QtCore.QDateTime.currentDateTime().toString('yyMMddhhmmss')))
        if not self.__make_backup(backupFileName):
            QMessageBox.critical(self.parent(),
                            self.tr("Backup collection"),
                            self.tr("Can't make a collection backup at %s") %
                                                                backupFileName)
            return False

        infoMessageBox("backup", self.tr("Backup"),
                       self.tr("Backup saved as %s") % backupFileName,
                       parent=self.parent())

        return True

    def isNeedBackup(self):
        settings = Settings()
        autobackup_depth = settings['autobackup_depth']
        filter_ = ('%s_????????????.db' % self.getCollectionName(),)
        files = QtCore.QDirIterator(settings['backup'], filter_, QtCore.QDir.Files)
        while files.hasNext():
            file_info = files.nextFileInfo()

            file_title = file_info.baseName()
            file_date = file_title[-12:]

            date_time = QtCore.QDateTime.fromString(file_date, 'yyMMddhhmmss')
            if date_time.isValid():
                if date_time.date().year() < 2000:
                    date_time = date_time.addYears(100)
                date_time = date_time.toUTC()

                query = QSqlQuery(self.db)
                query.prepare("SELECT count(*) FROM coins WHERE updatedat > ?")
                query.addBindValue(date_time.toString(Qt.ISODate))
                query.exec_()
                query.first()
                if query.record().value(0) < autobackup_depth:
                    return False

        return True

    @waitCursorDecorator
    def vacuum(self):
        QSqlQuery("VACUUM", self.db)

    @staticmethod
    def fileNameToCollectionName(fileName):
        file = QtCore.QFileInfo(fileName)
        return file.baseName()

    def exportToMobile(self, params):
        IMAGE_FORMAT = 'jpg'
        SKIPPED_FIELDS = ('signatureimg', 'varietyimg', 'edgeimg', 'photo1', 'photo2', 'photo3', 'photo4', 'photo5', 'photo6',
            'obversedesigner', 'reversedesigner', 'catalognum2', 'catalognum3', 'catalognum4',
            'saledate', 'saleprice', 'totalsaleprice', 'buyer', 'saleplace', 'saleinfo',
            'paydate', 'payprice', 'totalpayprice', 'saller', 'payplace', 'payinfo',
            'url', 'obversedesigner', 'reversedesigner')

        if os.path.isfile(params['file']):
            os.remove(params['file'])

        db = QSqlDatabase.addDatabase('QSQLITE', 'mobile')
        db.setDatabaseName(params['file'])
        if not db.open():
            print(db.lastError().text())
            QMessageBox.critical(self.parent(),
                                       self.tr("Create mobile collection"),
                                       self.tr("Can't open collection"))
            return

        mobile_settings = {'Version': 5, 'Type': 'Mobile', 'Filter': params['filter']}

        QSqlQuery("PRAGMA synchronous=OFF", db)
        QSqlQuery("PRAGMA journal_mode=MEMORY", db)

        sql = """CREATE TABLE settings (
            title CHAR NOT NULL UNIQUE,
            value CHAR)"""
        QSqlQuery(sql, db)
        for key, value in mobile_settings.items():
            query = QSqlQuery(db)
            query.prepare("""INSERT INTO settings (title, value)
                    VALUES (?, ?)""")
            query.addBindValue(key)
            query.addBindValue(str(value))
            query.exec_()

        sql = """CREATE TABLE updates (
            title CHAR NOT NULL UNIQUE,
            value CHAR)"""
        QSqlQuery(sql, db)

        sql = """CREATE TABLE photos (
            id INTEGER PRIMARY KEY,
            image BLOB)"""
        QSqlQuery(sql, db)

        sqlFields = []
        fields = CollectionFieldsBase()
        for field in fields:
            if field.name == 'id':
                sqlFields.append('id INTEGER PRIMARY KEY')
            elif field.name == 'image':
                sqlFields.append('image INTEGER')
            elif field.name in SKIPPED_FIELDS:
                continue
            else:
                sqlFields.append("%s %s" % (field.name, Type.toSql(field.type)))

        sql = "CREATE TABLE coins (" + ", ".join(sqlFields) + ")"
        QSqlQuery(sql, db)

        model = self.model()
        while model.canFetchMore():
            model.fetchMore()

        dest_model = QSqlTableModel(self.parent(), db)
        dest_model.setEditStrategy(QSqlTableModel.OnManualSubmit)
        dest_model.setTable('coins')
        dest_model.select()

        height = 64
        if params['density'] == 'HDPI':
            height = int(height * 1.5)
        elif params['density'] == 'XHDPI':
            height *= 2
        elif params['density'] == 'XXHDPI':
            height *= 3
        elif params['density'] == 'XXXHDPI':
            height *= 4
        maxHeight = height * 4

        is_obverse_enabled = params['image'] in (ExportDialog.IMAGE_OBVERSE, ExportDialog.IMAGE_BOTH)
        is_reverse_enabled = params['image'] in (ExportDialog.IMAGE_REVERSE, ExportDialog.IMAGE_BOTH)

        fields = CollectionFieldsBase()
        count = model.rowCount()
        progressDlg = Gui.ProgressDialog(self.tr("Exporting records"),
                                        self.tr("Cancel"), count, self.parent())

        for i in range(count):
            progressDlg.step()
            if progressDlg.wasCanceled():
                break

            coin = model.record(i)
            if coin.value('status') in ('pass', 'sold'):
                continue

            dest_record = dest_model.record()

            for field in fields:
                if field.name in ('id', 'image', 'obverseimg', 'reverseimg'):
                    continue
                if field.name in SKIPPED_FIELDS:
                    continue

                val = coin.value(field.name)
                if val is None or val == '':
                    continue

                dest_record.setValue(field.name, val)

            # Process images
            is_obverse_present = not coin.isNull('obverseimg')
            is_reverse_present = not coin.isNull('reverseimg')
            if is_obverse_present or is_reverse_present:
                obverseImage = QImage()
                reverseImage = QImage()

                if is_obverse_present:
                    ba = QtCore.QByteArray()
                    buffer = QtCore.QBuffer(ba)
                    buffer.open(QtCore.QIODevice.WriteOnly)

                    obverseImage.loadFromData(coin.value('obverseimg'))
                    if not obverseImage.isNull() and not params['fullimage'] and obverseImage.height() > maxHeight:
                        scaledImage = obverseImage.scaled(maxHeight, maxHeight,
                                Qt.KeepAspectRatio, Qt.SmoothTransformation)
                        scaledImage.save(buffer, IMAGE_FORMAT, 50)
                        save_data = ba
                    else:
                        if not obverseImage.isNull():
                            obverseImage.save(buffer, IMAGE_FORMAT, 50)
                            save_data = ba
                        else:
                            save_data = coin.value('obverseimg')

                    query = QSqlQuery(db)
                    query.prepare("""INSERT INTO photos (image)
                            VALUES (?)""")
                    query.addBindValue(save_data)
                    query.exec_()
                    img_id = query.lastInsertId()
                    dest_record.setValue('obverseimg', img_id)
                if not obverseImage.isNull():
                    obverseImage = obverseImage.scaledToHeight(height,
                                                            Qt.SmoothTransformation)

                if is_reverse_present:
                    ba = QtCore.QByteArray()
                    buffer = QtCore.QBuffer(ba)
                    buffer.open(QtCore.QIODevice.WriteOnly)

                    reverseImage.loadFromData(coin.value('reverseimg'))
                    if not reverseImage.isNull() and not params['fullimage'] and reverseImage.height() > maxHeight:
                        scaledImage = reverseImage.scaled(maxHeight, maxHeight,
                                Qt.KeepAspectRatio, Qt.SmoothTransformation)
                        scaledImage.save(buffer, IMAGE_FORMAT, 50)
                        save_data = ba
                    else:
                        if not reverseImage.isNull():
                            reverseImage.save(buffer, IMAGE_FORMAT, 50)
                            save_data = ba
                        else:
                            save_data = coin.value('reverseimg')

                    query = QSqlQuery(db)
                    query.prepare("""INSERT INTO photos (image)
                            VALUES (?)""")
                    query.addBindValue(save_data)
                    query.exec_()
                    img_id = query.lastInsertId()
                    dest_record.setValue('reverseimg', img_id)
                if not reverseImage.isNull():
                    reverseImage = reverseImage.scaledToHeight(height,
                                                        Qt.SmoothTransformation)

                if not is_obverse_enabled:
                    obverseImage = QImage()
                if not is_reverse_enabled:
                    reverseImage = QImage()

                image = QImage(obverseImage.width() + reverseImage.width(),
                                     height, QImage.Format_RGB32)
                image.fill(Qt.white)

                paint = QPainter(image)
                if is_obverse_present and is_obverse_enabled:
                    paint.drawImage(QtCore.QRectF(0, 0, obverseImage.width(), height), obverseImage,
                                    QtCore.QRectF(0, 0, obverseImage.width(), height))
                if is_reverse_present and is_reverse_enabled:
                    paint.drawImage(QtCore.QRectF(obverseImage.width(), 0, reverseImage.width(), height), reverseImage,
                                    QtCore.QRectF(0, 0, reverseImage.width(), height))
                paint.end()

                ba = QtCore.QByteArray()
                buffer = QtCore.QBuffer(ba)
                buffer.open(QtCore.QIODevice.WriteOnly)

                # Store as PNG for better view
                image.save(buffer, 'png')
                dest_record.setValue('image', ba)

            dest_model.insertRecord(-1, dest_record)

        progressDlg.setLabelText(self.tr("Saving..."))
        dest_model.submitAll()

        progressDlg.setLabelText(self.tr("Compact..."))
        QSqlQuery("""UPDATE coins
            SET
              reverseimg = (select t2.id from coins t3 join (select id, image from photos group by image having count(*) > 1) t2 on t1.image = t2.image join photos t1 on t3.reverseimg = t1.id where t1.id <> t2.id and t3.id = coins.id)
            WHERE coins.id in (select t3.id from coins t3 join (select id, image from photos group by image having count(*) > 1) t2 on t1.image = t2.image join photos t1 on t3.reverseimg = t1.id where t1.id <> t2.id)
            """, db)
        QSqlQuery("""UPDATE coins
            SET
              obverseimg = (select t2.id from coins t3 join (select id, image from photos group by image having count(*) > 1) t2 on t1.image = t2.image join photos t1 on t3.obverseimg = t1.id where t1.id <> t2.id and t3.id = coins.id)
            WHERE coins.id in (select t3.id from coins t3 join (select id, image from photos group by image having count(*) > 1) t2 on t1.image = t2.image join photos t1 on t3.obverseimg = t1.id where t1.id <> t2.id)
            """, db)

        QSqlQuery("""DELETE FROM photos
            WHERE id NOT IN (SELECT id FROM photos GROUP BY image)""", db)

        db.close()
        QSqlDatabase.removeDatabase('mobile')

        progressDlg.setLabelText(self.tr("Vacuum..."))
        db = QSqlDatabase.addDatabase('QSQLITE', 'mobile')
        db.setDatabaseName(params['file'])
        db.open()
        QSqlQuery("PRAGMA synchronous=OFF", db)
        QSqlQuery("PRAGMA journal_mode=MEMORY", db)
        QSqlQuery("VACUUM", db)
        db.close()
        QSqlDatabase.removeDatabase('mobile')

        progressDlg.reset()
        
    def exportToJson(self):
        file = self.getFileName()
        json_file_name = '.json'.join(file.rsplit('.db', 1))
        json_file_name, _selectedFilter = QFileDialog.getSaveFileName(
            self.parent(), self.tr("Save as"), json_file_name, "*.json")
        if json_file_name:
            json_file = codecs.open(json_file_name, "w", "utf-8")

            filename, _extension = os.path.splitext(json_file_name)
            image_path = filename + '_images'
            shutil.rmtree(image_path, ignore_errors=True)
            os.makedirs(image_path)
        
            model = self.model()
    
            sort_column_id = model.fields.sort_id.id
            model.sort(sort_column_id, Qt.AscendingOrder)
        
            while model.canFetchMore():
                model.fetchMore()
            count = model.rowCount()

            desc = self.getDescription()
            data = {'title': desc.title, 'description': desc.description,
                    'author': desc.author, 'type': "OpenNumismat",
                    'count': count, 'db_version': self.settings['Version']}
            json_file.write('{"description": ')
            json.dump(data, json_file, indent=2, sort_keys=True, ensure_ascii=False)
            json_file.write(',\n"coins": [\n')
            
            img_file_dict = {}
            
            progressDlg = Gui.ProgressDialog(self.tr("Exporting records"),
                                            self.tr("Cancel"), count, self.parent())

            fields = CollectionFieldsBase()
            for i in range(count):
                progressDlg.step()
                if progressDlg.wasCanceled():
                    break
                
                data = {}
                coin = model.record(i)
                for field in fields:
                    val = coin.value(field.name)
                    if val is None or val == '':
                        continue
        
                    if field.name in ('id', 'createdat', 'updatedat', 'sort_id') or field.type == Type.PreviewImage:
                        continue
                    if field.type == Type.Date and val == '2000-01-01':
                        continue
        
                    if field.type == Type.Image:
                        hash_ = QCryptographicHash.hash(val, QCryptographicHash.Sha1)
                        if hash_ in img_file_dict:
                            img_file_title = img_file_dict[hash_]
                        else:
                            img_file_title = "%d_%s.jpg" % (i + 1, field.name)
                            img_file_name = os.path.join(image_path, img_file_title)
                            img_file = open(img_file_name, 'wb')
                            img_file.write(val.data())
                            img_file.close()
                            
                            img_file_dict[hash_] = img_file_title

                        data[field.name] = img_file_title
                    else:
                        data[field.name] = val
        
                json.dump(data, json_file, indent=2, sort_keys=True, ensure_ascii=False)
                if i < count - 1:
                    json_file.write(',\n')
            
            json_file.write(']\n}')
            json_file.close()

            progressDlg.reset()

    def merge(self, fileName):
        query = QSqlQuery(self.db)
        query.prepare("ATTACH ? AS src")
        query.addBindValue(fileName)
        res = query.exec_()
        if not res:
            QMessageBox.critical(self.parent(),
                                 self.tr("Synchronizing"),
                                 self.tr("Can't open collection:\n%s") %
                                 query.lastError().text())
            return

        sql = "SELECT value FROM src.settings WHERE title='Type'"
        query = QSqlQuery(sql, self.db)
        query.first()
        type_ = query.record().value(0)
        if type_ != version.AppName:
            QMessageBox.critical(self.parent(),
                    self.tr("Synchronizing"),
                    self.tr("Collection %s in wrong format") % fileName)
            return

        sql = "SELECT value FROM src.settings WHERE title='Version'"
        query = QSqlQuery(sql, self.db)
        query.first()
        ver = query.record().value(0)
        if int(ver) != CollectionSettings.Default['Version']:
            QMessageBox.critical(self.parent(),
                    self.tr("Synchronizing"),
                    self.tr("Collection %s in old format.\n(Try to open it before merging.)") % fileName)
            return

        sql = "SELECT value FROM src.settings WHERE title='Password'"
        query = QSqlQuery(sql, self.db)
        query.first()
        pas = query.record().value(0)
        if pas != cryptPassword():
            dialog = PasswordDialog(
                pas, self.fileNameToCollectionName(fileName), self.parent())
            result = dialog.exec_()
            if result == QDialog.Rejected:
                return

        query = QSqlQuery("SELECT COUNT(*) FROM src.coins", self.db)
        query.first()
        count = query.record().value(0)

        progressDlg = Gui.ProgressDialog(
            self.tr("Synchronizing"), self.tr("Cancel"), count, self.parent())

        fields_query = QSqlQuery("PRAGMA table_info(coins)", self.db)
        fields_query.exec_()
        fields = []
        while fields_query.next():
            fields.append(fields_query.record().value(1))
        fields.remove('id')
        sql_fields = ','.join(fields)

        inserted_count = 0
        updated_count = 0
        query = QSqlQuery("SELECT DISTINCT createdat FROM src.coins", self.db)
        while query.next():
            progressDlg.step()
            if progressDlg.wasCanceled():
                break

            self.db.transaction()

            sql = "SELECT 1 FROM coins WHERE createdat=? LIMIT 1"
            select_query = QSqlQuery(sql, self.db)
            select_query.addBindValue(query.record().value(0))
            select_query.exec_()
            if select_query.first():
                dst_fields = ImageFields + \
                             ('id', 'image', 'sort_id')
                sql_dst_fields = ','.join(['coins.%s AS coins_%s' % (f, f) for f in dst_fields])
                sql_src_fields = ','.join(['src_coins.%s' % f for f in fields])
                sql = "SELECT %s, %s FROM coins\
                    INNER JOIN src.coins src_coins ON coins.id=src_coins.id\
                    WHERE src_coins.createdat=? AND\
                          src_coins.createdat=coins.createdat AND\
                          src_coins.updatedat>coins.updatedat" % (sql_src_fields, sql_dst_fields)
                sel_query = QSqlQuery(sql, self.db)
                sel_query.addBindValue(query.record().value(0))
                sel_query.exec_()
                if sel_query.first():
                    sql = "UPDATE coins SET %s WHERE id=?" % ','.join(['%s=?' % f for f in fields])
                    up_query = QSqlQuery(sql, self.db)
                    for field in fields:
                        if field == 'image':
                            img_id = sel_query.record().value(field)
                            old_img_id = sel_query.record().value('coins_image')
                            if img_id and old_img_id:
                                sql = "UPDATE images SET image=(SELECT image FROM src.images WHERE id=?) WHERE id=?"
                                img_query = QSqlQuery(sql, self.db)
                                img_query.addBindValue(img_id)
                                img_query.addBindValue(old_img_id)
                                img_query.exec_()
                            elif img_id:
                                sql = "INSERT INTO images (image) SELECT image FROM src.images WHERE id=?"
                                img_query = QSqlQuery(sql, self.db)
                                img_query.addBindValue(img_id)
                                img_query.exec_()
                                img_id = img_query.lastInsertId()
                            elif old_img_id:
                                sql = "DELETE FROM images WHERE id=?"
                                img_query = QSqlQuery(sql, self.db)
                                img_query.addBindValue(old_img_id)
                                img_query.exec_()
                                img_id = None

                            up_query.addBindValue(img_id)
                        elif field in ImageFields:
                            img_id = sel_query.record().value(field)
                            old_img_id = sel_query.record().value('coins_%s' % field)
                            if img_id and old_img_id:
                                sql = "UPDATE photos SET title=(SELECT title FROM src.photos WHERE id=?), image=(SELECT image FROM src.photos WHERE id=?) WHERE id=?"
                                img_query = QSqlQuery(sql, self.db)
                                img_query.addBindValue(img_id)
                                img_query.addBindValue(img_id)
                                img_query.addBindValue(old_img_id)
                                img_query.exec_()
                                img_id = old_img_id
                            elif img_id:
                                sql = "INSERT INTO photos (title, image) SELECT title, image FROM src.photos WHERE id=?"
                                img_query = QSqlQuery(sql, self.db)
                                img_query.addBindValue(img_id)
                                img_query.exec_()
                                img_id = img_query.lastInsertId()
                            elif old_img_id:
                                sql = "DELETE FROM photos WHERE id=?"
                                img_query = QSqlQuery(sql, self.db)
                                img_query.addBindValue(old_img_id)
                                img_query.exec_()
                                img_id = None

                            up_query.addBindValue(img_id)
                        elif field == 'sort_id':
                            up_query.addBindValue(sel_query.record().value('coins_sort_id'))
                        else:
                            up_query.addBindValue(sel_query.record().value(field))
                    up_query.addBindValue(sel_query.record().value('coins_id'))

                    up_query.exec_()
                    updated_count += 1
            else:
                sql = "SELECT %s FROM src.coins WHERE createdat=?" % sql_fields
                sel_query = QSqlQuery(sql, self.db)
                sel_query.addBindValue(query.record().value(0))
                sel_query.exec_()
                while sel_query.next():
                    sql = "INSERT INTO coins (%s) VALUES (%s)" % (sql_fields, ','.join(['?'] * len(fields)))
                    ins_query = QSqlQuery(sql, self.db)
                    for field in fields:
                        if field == 'image':
                            old_img_id = sel_query.record().value(field)
                            if old_img_id:
                                sql = "INSERT INTO images (image) SELECT image FROM src.images WHERE id=?"
                                img_query = QSqlQuery(sql, self.db)
                                img_query.addBindValue(old_img_id)
                                img_query.exec_()

                                img_id = img_query.lastInsertId()
                            else:
                                img_id = None
                            ins_query.addBindValue(img_id)
                        elif field in ImageFields:
                            old_img_id = sel_query.record().value(field)
                            if old_img_id:
                                sql = "INSERT INTO photos (title, image) SELECT title, image FROM src.photos WHERE id=?"
                                img_query = QSqlQuery(sql, self.db)
                                img_query.addBindValue(old_img_id)
                                img_query.exec_()

                                img_id = img_query.lastInsertId()
                            else:
                                img_id = None
                            ins_query.addBindValue(img_id)
                        elif field == 'sort_id':
                            sort_query = QSqlQuery("SELECT MAX(sort_id) FROM coins", self.db)
                            sort_query.first()
                            sort_id = sort_query.record().value(0)
                            if not sort_id:
                                sort_id = 0
                            ins_query.addBindValue(sort_id + 1)
                        else:
                            ins_query.addBindValue(sel_query.record().value(field))

                    ins_query.exec_()
                    inserted_count += 1

            self.db.commit()

        query = QSqlQuery("DETACH src", self.db)
        query.exec_()

        progressDlg.reset()

        if inserted_count or updated_count:
            text = self.tr("Inserted %d coins, updated %d coins.\nThe application will need to restart now.") % (inserted_count, updated_count)
            QMessageBox.information(self.parent(), self.tr("Synchronizing"),
                                    text)
            # TODO: refresh
            self.parent().restart()
        else:
            text = self.tr("Collections looks like identical")
            QMessageBox.information(self.parent(), self.tr("Synchronizing"),
                                    text)
