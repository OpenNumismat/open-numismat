# -*- coding: utf-8 -*-

import sys

from PySide6.QtCore import Qt, QSortFilterProxyModel, QObject, QFile, QFileInfo, QDateTime, QDataStream
from PySide6.QtCore import Signal as pyqtSignal
from PySide6.QtGui import QPixmap, QIcon
from PySide6.QtSql import QSqlDatabase, QSqlQuery, QSqlTableModel, QSqlRelationalTableModel, QSqlRelation
from PySide6.QtWidgets import QDialog, QMessageBox, QPushButton

from OpenNumismat.Reference.ReferenceDialog import ReferenceDialog, CrossReferenceDialog


class SqlTableModel(QSqlTableModel):

    MimeType = "application/x-qabstractitemmodeldatalist"

    def __init__(self, parent, db):
        super().__init__(parent, db)

        self.is_sorted = False

        self._proxyModel = QSortFilterProxyModel(self)
        self._proxyModel.setSortLocaleAware(True)
        self._proxyModel.setSourceModel(self)

    def supportedDropActions(self):
        return Qt.MoveAction

    def flags(self, index):
        defaultFlags = super().flags(index)

        if self.is_sorted:
            return defaultFlags

        if index.isValid():
            return Qt.ItemIsDragEnabled | defaultFlags
        else:
            return Qt.ItemIsDropEnabled | defaultFlags

    def dropMimeData(self, data, action, row, column, parent):
        if action == Qt.IgnoreAction:
            return True

        encodedData = data.data(self.MimeType)
        stream = QDataStream(encodedData)
        row1 = stream.readInt32()
        proxyIndex = self.index(row1, 0)
        index = self._proxyModel.mapFromSource(proxyIndex)
        row1 = index.row()

        proxyIndex = self.index(row, 0)
        index = self._proxyModel.mapFromSource(proxyIndex)
        row2 = index.row()

        if row1 > row2:
            self.moveRows(row1, row2)
        else:
            self.moveRows(row1, row2 - 1)

        return True

    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.DecorationRole:
            if index.row() < 0:
                return None
            iconIndex = self.index(index.row(), self.fieldIndex('icon'))
            if not self.data(iconIndex) or self.data(iconIndex).isNull():
                return None
            icon = QPixmap()
            icon.loadFromData(self.data(iconIndex))
            return icon

        return super().data(index, role)

    def proxyModel(self):
        return self._proxyModel

    def sort(self, sort=True):
        self.is_sorted = sort

        if sort:
            self._proxyModel.sort(self.fieldIndex('value'))
        else:
            self._proxyModel.sort(self.fieldIndex('position'))

    def moveRows(self, row1, row2):
        row_rang = []
        if row2 == -1:
            row_rang = range(row1 + 1, self.rowCount())
        elif row1 > row2:
            row_rang = range(row1 - 1, row2 - 1, -1)
        elif row1 < row2:
            row_rang = range(row1 + 1, row2 + 1)

        sort_column_id = self.fieldIndex('position')
        super().sort(sort_column_id, Qt.AscendingOrder)

        if row_rang:
            record = self.record(row1)
            old_sort_id = record.value('position')
            for row in row_rang:
                record1 = self.record(row)
                sort_id = record1.value('position')
                record1.setValue('position', old_sort_id)
                self.setRecord(row, record1)
                old_sort_id = sort_id
            record.setValue('position', old_sort_id)
            self.setRecord(row1, record)

        super().sort(-1, Qt.AscendingOrder)

    def nextPosition(self):
        new_position = 0
        query = QSqlQuery(self.database())
        query.prepare(f"SELECT MAX(position) FROM {self.tableName()}")
        query.exec()
        if query.first():
            max_position = query.record().value(0)
            if isinstance(max_position, int):
                new_position = query.record().value(0) + 1

        return new_position


class SqlRelationalTableModel(QSqlRelationalTableModel):

    MimeType = "application/x-qabstractitemmodeldatalist"

    def __init__(self, model, parent, db):
        super().__init__(parent, db)

        self.is_sorted = False

        self.model = model
        self._proxyModel = QSortFilterProxyModel(self)
        self._proxyModel.setSortLocaleAware(True)
        self._proxyModel.setSourceModel(self)

    def supportedDropActions(self):
        return Qt.MoveAction

    def flags(self, index):
        defaultFlags = super().flags(index)

        if self.is_sorted:
            return defaultFlags

        if index.isValid():
            return Qt.ItemIsDragEnabled | defaultFlags
        else:
            return Qt.ItemIsDropEnabled | defaultFlags

    def dropMimeData(self, data, action, row, column, parent):
        if action == Qt.IgnoreAction:
            return True

        encodedData = data.data(self.MimeType)
        stream = QDataStream(encodedData)
        row1 = stream.readInt32()
        proxyIndex = self.index(row1, 0)
        index = self._proxyModel.mapFromSource(proxyIndex)
        row1 = index.row()

        proxyIndex = self.index(row, 0)
        index = self._proxyModel.mapFromSource(proxyIndex)
        row2 = index.row()

        if row1 > row2:
            self.moveRows(row1, row2)
        else:
            self.moveRows(row1, row2 - 1)

        return True

    def relationModel(self, _column):
        return self.model

    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.DecorationRole:
            if index.row() < 0:
                return None
            iconIndex = self.index(index.row(), self.fieldIndex('icon'))
            if not self.data(iconIndex) or self.data(iconIndex).isNull():
                return None
            icon = QPixmap()
            icon.loadFromData(self.data(iconIndex))
            return icon

        return super().data(index, role)

    def proxyModel(self):
        return self._proxyModel

    def sort(self, sort=True):
        self.is_sorted = sort

        if sort:
            self._proxyModel.sort(self.fieldIndex('value'))
        else:
            self._proxyModel.sort(self.fieldIndex('position'))

    def moveRows(self, row1, row2):
        row_rang = []
        if row2 == -1:
            row_rang = range(row1 + 1, self.rowCount())
        elif row1 > row2:
            row_rang = range(row1 - 1, row2 - 1, -1)
        elif row1 < row2:
            row_rang = range(row1 + 1, row2 + 1)

        sort_column_id = self.fieldIndex('position')
        super().sort(sort_column_id, Qt.AscendingOrder)

        if row_rang:
            record = self.record(row1)
            old_sort_id = record.value('position')
            for row in row_rang:
                record1 = self.record(row)
                sort_id = record1.value('position')
                record1.setValue('position', old_sort_id)
                self.setRecord(row, record1)
                old_sort_id = sort_id
            record.setValue('position', old_sort_id)
            self.setRecord(row1, record)

        super().sort(-1, Qt.AscendingOrder)

    def nextPosition(self):
        new_position = 0
        query = QSqlQuery(self.database())
        query.prepare(f"SELECT MAX(position) FROM {self.tableName()}")
        query.exec()
        if query.first():
            max_position = query.record().value(0)
            if isinstance(max_position, int):
                new_position = query.record().value(0) + 1

        return new_position


class BaseReferenceSection(QObject):
    beforeReload = pyqtSignal()
    afterReload = pyqtSignal()

    def __init__(self, name, title, letter, sort=False, parent=None):
        super().__init__(parent)

        self.name = name
        self.table_name = f"ref_{name}"
        self.title = title
        self.letter = letter
        self.sort = sort
        self.parent_name = None

    def reload(self):
        self.beforeReload.emit()
        self.getSort()
        self.setSort()
        self.model.select()
        self.afterReload.emit()

    def setSort(self):
        self.model.sort(self.sort)

    def getSort(self):
        query = QSqlQuery(self.db)
        query.prepare("SELECT sort FROM sections WHERE name=?")
        query.addBindValue(self.name)
        query.exec()
        if query.first():
            data = query.record().value(0)
            if data:
                self.sort = bool(data)
            else:
                self.sort = False
        query.clear()

        return self.sort

    def saveSort(self, sort):
        if self.sort != sort:
            self.sort = sort

            query = QSqlQuery(self.db)
            query.prepare("UPDATE sections SET sort=? WHERE name=?")
            query.addBindValue(int(sort))
            query.addBindValue(self.name)
            query.exec()

        self.setSort()

    def create(self, db=QSqlDatabase()):
        in_transaction = db.transaction()

        cross_ref = ('country', 'period', 'emitent', 'ruler',
                     'unit', 'mint', 'series')

        if self.name in cross_ref:
            sql = f"""CREATE TABLE {self.table_name} (
                id INTEGER PRIMARY KEY,
                parentid INTEGER,
                value TEXT, icon BLOB,
                position INTEGER, description TEXT, plural TEXT)"""
        else:
            sql = f"""CREATE TABLE {self.table_name} (
                id INTEGER PRIMARY KEY,
                value TEXT, icon BLOB,
                position INTEGER, description TEXT, plural TEXT)"""
        QSqlQuery(sql, db)

        query = QSqlQuery(db)
        if self.name in cross_ref:
            sql = """INSERT INTO sections (name, letter, parent, sort, plural)
                VALUES (?, ?, ?, ?, ?)"""
        else:
            sql = """INSERT INTO sections (name, letter, sort, plural)
                VALUES (?, ?, ?, ?)"""
        query.prepare(sql)
        query.addBindValue(self.name)
        query.addBindValue(self.letter)
        if self.name in cross_ref:
            if self.name == 'country':
                query.addBindValue('region')
            else:
                query.addBindValue('country')
        query.addBindValue(int(self.sort))
        if self.name == 'unit':
            query.addBindValue(1)
        else:
            query.addBindValue(0)

        query.exec()

        if in_transaction:
            db.commit()


class ReferenceSection(BaseReferenceSection):
    def __init__(self, name, title, letter='…', sort=False, parent=None):
        super().__init__(name, title, letter, sort, parent)

    def load(self, db):
        self.db = db
        if self.table_name not in self.db.tables():
            self.create(self.db)

        self.model = SqlTableModel(None, db)
        self.model.setEditStrategy(QSqlTableModel.OnFieldChange)
        self.model.setTable(self.table_name)

        self.reload()

    def _getDialog(self, parent):
        copy = ReferenceSection(self.name, self.title,
                                self.letter, self.sort, parent)
        copy.load(self.db)

        return ReferenceDialog(copy, parent.text(), parent)

    def addItem(self, value, icon=None):
        new_position = self.model.nextPosition()

        record = self.model.record()
        record.setValue('value', value)
        record.setValue('position', new_position)
        if icon:
            record.setValue('icon', icon)
        self.model.insertRecord(-1, record)

    def fillFromQuery(self, query):
        while query.next():
            value = query.record().value(0)
            fillQuery = QSqlQuery(self.db)
            fillQuery.prepare(f"INSERT INTO {self.table_name} (value, position) "
                    "SELECT ?, "
                    f"(SELECT ifnull(MAX(position)+1, 0) FROM {self.table_name}) "
                    "WHERE NOT EXISTS "
                    f"(SELECT 1 FROM {self.table_name} WHERE value=?)")
            fillQuery.addBindValue(value)
            fillQuery.addBindValue(value)
            fillQuery.exec()


class CrossReferenceSection(BaseReferenceSection):
    def __init__(self, name, parentRef, title, letter='…', sort=False, parent=None):
        super().__init__(name, title, letter, sort, parent)

        self.parentIndex = None
        self.parentRef = parentRef
        self.parent_name = parentRef.name
        self.parent_table_name = parentRef.table_name

    def load(self, db):
        self.db = db
        if self.table_name not in self.db.tables():
            self.create(self.db)

        self.model = SqlRelationalTableModel(self.parentRef.model, None, db)
        self.model.setJoinMode(QSqlRelationalTableModel.LeftJoin)
        self.model.setEditStrategy(QSqlTableModel.OnFieldChange)
        self.model.setTable(self.table_name)
        parentidIndex = self.model.fieldIndex('parentid')
        self.model.parentidIndex = parentidIndex
        self.model.setRelation(
            parentidIndex, QSqlRelation(self.parent_table_name, 'id', 'value'))

        self.reload()

    def _getDialog(self, parent):
        copy = CrossReferenceSection(self.name, self.parentRef, self.title,
                                     self.letter, self.sort, parent)
        copy.load(self.db)

        return CrossReferenceDialog(copy, self.parentIndex,
                                    parent.text(), parent)

    def fillFromQuery(self, parentId, query):
        while query.next():
            value = query.record().value(0)
            fillQuery = QSqlQuery(self.db)
            fillQuery.prepare(f"INSERT INTO {self.table_name} (value, parentid, position) "
                        "SELECT ?, ?, "
                        f"(SELECT ifnull(MAX(position)+1, 0) FROM {self.table_name}) "
                        "WHERE NOT EXISTS "
                        f"(SELECT 1 FROM {self.table_name} WHERE value=? AND parentid=?)")
            fillQuery.addBindValue(value)
            fillQuery.addBindValue(parentId)
            fillQuery.addBindValue(value)
            fillQuery.addBindValue(parentId)
            fillQuery.exec()


class Reference(QObject):
    VERSION = 2

    def __init__(self, fields, parent=None, db=None):
        super().__init__(parent)

        if db:
            self.db = db
        else:
            self.db = QSqlDatabase.addDatabase('QSQLITE', "reference")

        self.fileName = None
        self.userFields = [field.name for field in fields.userFields]
        self.sections = []

        self.__createReferenceSection(None, fields.category)
        ref_region = self.__createReferenceSection(None, fields.region)
        ref_country = self.__createReferenceSection(ref_region, fields.country,
                                                    self.tr("C"), True)
        self.__createReferenceSection(ref_country, fields.period,
                                      self.tr("P"), True)
        self.__createReferenceSection(ref_country, fields.emitent)
        self.__createReferenceSection(ref_country, fields.ruler)
        self.__createReferenceSection(ref_country, fields.unit, self.tr("U"))
        self.__createReferenceSection(ref_country, fields.mint)
        self.__createReferenceSection(ref_country, fields.series,
                                      self.tr("S"), True)
        self.__createReferenceSection(None, fields.grade, self.tr("G"))
        self.__createReferenceSection(None, fields.shape, self.tr("F"))
        self.__createReferenceSection(None, fields.quality, self.tr("Q"))
        self.__createReferenceSection(None, fields.rarity, self.tr("R"))
        self.__createReferenceSection(None, fields.obvrev)
        self.__createReferenceSection(None, fields.type, self.tr("T"))
        self.__createReferenceSection(None, fields.defect, self.tr("D"))
        self.__createReferenceSection(None, fields.format)
        self.__createReferenceSection(None, fields.condition)
        self.__createReferenceSection(None, fields.grader)
        self.__createReferenceSection(None, fields.storage)
        self.__createReferenceSection(None, fields.composition)
        self.__createReferenceSection(None, fields.technique)
        self.__createReferenceSection(None, fields.modification)

        if 'payplace' in self.userFields or 'saleplace' in self.userFields:
            ref_place = ReferenceSection('place', self.tr("Place"))
            self.sections.append(ref_place)
        if 'obversecolor' in self.userFields or 'reversecolor' in self.userFields:
            ref_color = ReferenceSection('color', self.tr("Color"))
            self.sections.append(ref_color)
        if 'edge' in self.userFields or 'signaturetype' in self.userFields:
            ref_edge = ReferenceSection('edge', self.tr("Edge"))
            self.sections.append(ref_edge)
        if 'material' in self.userFields or 'material2' in self.userFields:
            ref_material = ReferenceSection('material', self.tr("Material"), self.tr("M"))
            self.sections.append(ref_material)

    def __createReferenceSection(self, parentRef, field,
                                 letter='…', sort=False):
        if field.name in self.userFields:
            if parentRef:
                ref = CrossReferenceSection(field.name, parentRef, field.title,
                                            letter, sort)
            else:
                ref = ReferenceSection(field.name, field.title, letter, sort)
            self.sections.append(ref)

            return ref
        return None

    def create(self):
        sql = """CREATE TABLE IF NOT EXISTS sections (
            id INTEGER PRIMARY KEY,
            name TEXT,
            icon BLOB,
            letter TEXT,
            parent TEXT,
            sort INTEGER,
            plural INTEGER)"""
        QSqlQuery(sql, self.db)

        sql = """CREATE TABLE ref (
            title CHAR NOT NULL UNIQUE,
            value CHAR)"""
        QSqlQuery(sql, self.db)

        query = QSqlQuery(self.db)
        query.prepare("INSERT INTO ref (title, value) VALUES ('version', ?)")
        query.addBindValue(self.VERSION)
        query.exec()

        for section in self.sections:
            section.create(self.db)

    def open(self, fileName, interactive=True):
        file = QFileInfo(fileName)
        if file.isFile():
            self.db.setDatabaseName(fileName)
            if not self.db.open():
                print(self.db.lastError().text())
                QMessageBox.critical(self.parent(),
                            self.tr("Open reference"),
                            self.tr("Can't open reference:\n%s") % fileName)
                return False
            else:
                # Update reference DB for version 1.4.3
                if self.db.record('sections').indexOf('sort') < 0:
                    sql = "ALTER TABLE sections ADD COLUMN sort INTEGER"
                    QSqlQuery(sql, self.db)
                    sql = "UPDATE sections SET name = 'material' WHERE name = 'metal'"
                    QSqlQuery(sql, self.db)
                # Update reference DB for version 1.4.9
                if 'period' in self.db.tables() and \
                        self.db.record('period').indexOf('icon') < 0:
                    for table in ('period', 'unit', 'mint', 'series'):
                        sql = "ALTER TABLE %s ADD COLUMN icon BLOB" % table
                        QSqlQuery(sql, self.db)
                # Update reference DB for version 1.6
                if 'country' in self.db.tables() and \
                        self.db.record('country').indexOf('parentid') < 0:
                    sql = "ALTER TABLE country ADD COLUMN parentid INTEGER"
                    QSqlQuery(sql, self.db)
                    sql = "UPDATE sections SET parent = 'region' WHERE name = 'country'"
                    QSqlQuery(sql, self.db)

                    tables = ('region', 'country', 'period', 'ruler', 'unit',
                              'mint', 'series', 'grade', 'material', 'shape',
                              'quality', 'edge', 'rarity', 'obvrev', 'type',
                              'defect', 'place')
                    for table in tables:
                        sql = "ALTER TABLE %s RENAME TO ref_%s" % (table, table)
                        QSqlQuery(sql, self.db)
        else:
            if interactive:
                QMessageBox.warning(self.parent(),
                            self.tr("Open reference"),
                            self.tr("Can't open reference:\n%s\nCreated new one") % fileName)

            self.db.setDatabaseName(fileName)
            if not self.db.open():
                print(self.db.lastError().text())
                QMessageBox.critical(self.parent(),
                            self.tr("Create reference"),
                            self.tr("Can't create reference:\n%s") % fileName)
                return False
            self.create()

        self.fileName = fileName

        return True

    def load(self):
        # Update reference DB for version 1.6.2
        if 'ref' not in self.db.tables():
            self.__updateTo1()

        query = QSqlQuery("SELECT value FROM ref WHERE title='version'", self.db)
        query.exec()
        if query.first():
            current_version = int(query.record().value(0))
            if current_version == 1:
                # Update reference DB for version 1.10
                self.__updateTo2()
                current_version = 2

            if current_version > self.VERSION:
                QMessageBox.critical(self.parent(),
                        self.tr("Open reference"),
                        self.tr("Reference is a newer version.\n"
                                "Please update OpenNumismat"))
                return

        for section in self.sections:
            section.load(self.db)

        self.sections_with_icons = []
        for section in self.sections:
            name = section.table_name
            sql = f"SELECT 1 FROM {name} WHERE icon IS NOT NULL LIMIT 1"
            query = QSqlQuery(sql, self.db)
            query.exec()
            if query.first():
                self.sections_with_icons.append(name)

    def section(self, name):
        # NOTE: payplace and saleplace fields has one reference section =>
        # editing one of it should change another
        if name in ('payplace', 'saleplace'):
            name = 'place'
        elif name in ('obversecolor', 'reversecolor'):
            name = 'color'
        elif name in ('edge', 'signaturetype'):
            name = 'edge'
        elif name in ('material', 'material2'):
            name = 'material'

        for section in self.sections:
            if section.name == name:
                return section

        return None

    def allSections(self):
        sectionNames = []
        for section in self.sections:
            if section.name == 'place':
                sectionNames.extend(['payplace', 'saleplace'])
            elif section.name == 'color':
                sectionNames.extend(['obversecolor', 'reversecolor'])
            elif section.name == 'edge':
                sectionNames.extend(['edge', 'signaturetype'])
            elif section.name == 'material':
                sectionNames.extend(['material', 'material2'])
            else:
                sectionNames.append(section.name)

        return sectionNames

    def getIcon(self, section, value):
        if section in ('payplace', 'saleplace'):
            section = 'place'
        elif section in ('obversecolor', 'reversecolor'):
            section = 'color'
        elif section in ('edge', 'signaturetype'):
            section = 'edge'
        elif section in ('material', 'material2'):
            section = 'material'

        table_name = f"ref_{section}"
        if table_name in self.sections_with_icons:
            sql = f"SELECT icon FROM {table_name} WHERE value=?"
            query = QSqlQuery(sql, self.db)
            query.addBindValue(value)
            query.exec()
            if query.first():
                data = query.record().value(0)
                if data:
                    pixmap = QPixmap()
                    if pixmap.loadFromData(data):
                        icon = QIcon(pixmap)
                        return icon
        return None

    def getPosition(self, section, value):
        if section in ('payplace', 'saleplace'):
            section = 'place'
        elif section in ('obversecolor', 'reversecolor'):
            section = 'color'
        elif section in ('edge', 'signaturetype'):
            section = 'edge'
        elif section in ('material', 'material2'):
            section = 'material'

        sql = f"SELECT position FROM ref_{section} WHERE value=?"
        query = QSqlQuery(sql, self.db)
        query.addBindValue(value)
        query.exec()
        if query.first():
            data = query.record().value(0)
            if isinstance(data, int):
                return data

        return sys.maxsize

    def backup(self):
        if self.fileName:
            file = QFileInfo(self.fileName)
            backupDir = file.dir()
            backupFileName = backupDir.filePath("%s_%s.ref" % (file.baseName(),
                                                               QDateTime.currentDateTime().toString('yyMMddhhmmss')))
            srcFile = QFile(self.fileName)
            srcFile.copy(backupFileName)

    def __updateTo1(self):
        self.backup()

        self.db.transaction()

        for cross_ref in ('country', 'period', 'ruler',
                          'unit', 'mint', 'series'):
            sql = "ALTER TABLE ref_%s RENAME TO old_ref_%s" % (cross_ref, cross_ref)
            QSqlQuery(sql, self.db)

            sql = "CREATE TABLE ref_%s (\
                id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,\
                parentid INTEGER,\
                value TEXT, icon BLOB)" % cross_ref
            QSqlQuery(sql, self.db)

            sql = "INSERT INTO ref_%s\
                SELECT id, parentid, value, icon\
                FROM old_ref_%s" % (cross_ref, cross_ref)
            QSqlQuery(sql, self.db)

            sql = "DROP TABLE old_ref_%s" % cross_ref
            QSqlQuery(sql, self.db)

        sql = """CREATE TABLE ref (
            title CHAR NOT NULL UNIQUE,
            value CHAR)"""
        QSqlQuery(sql, self.db)

        sql = """INSERT INTO ref (title, value)
            VALUES ('version', 1)"""
        QSqlQuery(sql, self.db)

        self.db.commit()

    def __updateTo2(self):
        self.backup()

        self.db.transaction()

        tables = (
            'ref_category', 'ref_color', 'ref_composition', 'ref_condition',
            'ref_country', 'ref_defect', 'ref_edge', 'ref_emitent',
            'ref_format', 'ref_grade', 'ref_grader', 'ref_material',
            'ref_mint', 'ref_modification', 'ref_obvrev', 'ref_period',
            'ref_place', 'ref_quality', 'ref_rarity', 'ref_region',
            'ref_ruler', 'ref_series', 'ref_shape', 'ref_storage',
            'ref_technique', 'ref_type', 'ref_unit',
        )
        for table in tables:
            sql = f"ALTER TABLE {table} ADD COLUMN position INTEGER"
            QSqlQuery(sql, self.db)
            sql = f"ALTER TABLE {table} ADD COLUMN description TEXT"
            QSqlQuery(sql, self.db)
            sql = f"ALTER TABLE {table} ADD COLUMN plural TEXT"
            QSqlQuery(sql, self.db)

            sql = f"UPDATE {table} SET position=id"
            QSqlQuery(sql, self.db)

        sql = f"ALTER TABLE sections ADD COLUMN plural INTEGER"
        QSqlQuery(sql, self.db)
        sql = f"UPDATE sections SET plural=1 WHERE name='unit'"
        QSqlQuery(sql, self.db)

        sql = "UPDATE ref SET value=2 WHERE title='version'"
        QSqlQuery(sql, self.db)

        self.db.commit()
