# -*- coding: utf-8 -*-

from PySide6.QtCore import Qt, QSortFilterProxyModel, QObject, QFile, QFileInfo, QDateTime
from PySide6.QtCore import Signal as pyqtSignal
from PySide6.QtGui import QPixmap, QIcon
from PySide6.QtSql import QSqlDatabase, QSqlQuery, QSqlTableModel, QSqlRelationalTableModel, QSqlRelation
from PySide6.QtWidgets import QDialog, QMessageBox, QPushButton

from OpenNumismat.Reference.ReferenceDialog import ReferenceDialog, CrossReferenceDialog


class SqlTableModel(QSqlTableModel):

    def __init__(self, parent, db):
        super().__init__(parent, db)

        self._proxyModel = QSortFilterProxyModel(self)
        self._proxyModel.setSortLocaleAware(True)
        self._proxyModel.setSourceModel(self)

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
        if sort:
            self._proxyModel.sort(self.fieldIndex('value'))
        else:
            self._proxyModel.sort(-1)


class SqlRelationalTableModel(QSqlRelationalTableModel):
    def __init__(self, model, parent, db):
        super().__init__(parent, db)

        self.model = model
        self._proxyModel = QSortFilterProxyModel(self)
        self._proxyModel.setSortLocaleAware(True)
        self._proxyModel.setSourceModel(self)

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
        if sort:
            self._proxyModel.sort(self.fieldIndex('value'))
        else:
            self._proxyModel.sort(-1)


class BaseReferenceSection(QObject):
    changed = pyqtSignal(object)

    def __init__(self, name, title, letter, sort=False, parent=None):
        super().__init__(parent)

        self.name = name
        self.table_name = "ref_%s" % name
        self.title = title
        self.letter = letter
        self.sort = sort
        self.parent_name = None

    def reload(self):
        self.getSort()
        self.setSort()
        self.model.select()

    def button(self, parent=None):
        self.parent = parent
        button = QPushButton(self.letter, parent)
        button.setFixedWidth(25)
        button.clicked.connect(self.clickedButton)
        return button

    def clickedButton(self):
        old_text = self.parent.text()

        dialog = self._getDialog()
        result = dialog.exec()
        if result == QDialog.Accepted:
            self.reload()

            index = dialog.selectedIndex()
            if index:
                self.changed.emit(index.data())
            else:
                self.changed.emit(old_text)
        dialog.deleteLater()

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
            sql = "CREATE TABLE %s (\
                id INTEGER PRIMARY KEY,\
                parentid INTEGER,\
                value TEXT, icon BLOB)" % self.table_name
        else:
            sql = "CREATE TABLE %s (\
                id INTEGER PRIMARY KEY,\
                value TEXT, icon BLOB)" % self.table_name
        QSqlQuery(sql, db)

        query = QSqlQuery(db)
        if self.name in cross_ref:
            sql = "INSERT INTO sections (name, letter, parent, sort)\
                VALUES (?, ?, ?, ?)"
        else:
            sql = "INSERT INTO sections (name, letter, sort)\
                VALUES (?, ?, ?)"
        query.prepare(sql)
        query.addBindValue(self.name)
        query.addBindValue(self.letter)
        if self.name in cross_ref:
            if self.name == 'country':
                query.addBindValue('region')
            else:
                query.addBindValue('country')
        query.addBindValue(int(self.sort))
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

    def _getDialog(self):
        copy = ReferenceSection(self.name, self.title,
                                self.letter, self.sort, self.parent)
        copy.load(self.db)

        return ReferenceDialog(copy, self.parent.text(), self.parent)

    def addItem(self, value, icon=None):
        record = self.model.record()
        record.setValue('value', value)
        if icon:
            record.setValue('icon', icon)
        self.model.insertRecord(-1, record)

    def fillFromQuery(self, query):
        while query.next():
            value = query.record().value(0)
            fillQuery = QSqlQuery(self.db)
            fillQuery.prepare("INSERT INTO %s (value) "
                        "SELECT ? "
                        "WHERE NOT EXISTS (SELECT 1 FROM %s WHERE value=?)" %
                                            (self.table_name, self.table_name))
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

    def _getDialog(self):
        copy = CrossReferenceSection(self.name, self.parentRef, self.title,
                                     self.letter, self.sort, self.parent)
        copy.load(self.db)

        return CrossReferenceDialog(copy, self.parentIndex,
                                    self.parent.text(), self.parent)

    def fillFromQuery(self, parentId, query):
        while query.next():
            value = query.record().value(0)
            fillQuery = QSqlQuery(self.db)
            fillQuery.prepare("INSERT INTO %s (value, parentid) "
                        "SELECT ?, ? "
                        "WHERE NOT EXISTS "
                        "(SELECT 1 FROM %s WHERE value=? AND parentid=?)" %
                                            (self.table_name, self.table_name))
            fillQuery.addBindValue(value)
            fillQuery.addBindValue(parentId)
            fillQuery.addBindValue(value)
            fillQuery.addBindValue(parentId)
            fillQuery.exec()


class Reference(QObject):
    VERSION = 1

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
        sql = "CREATE TABLE IF NOT EXISTS sections (\
            id INTEGER PRIMARY KEY,\
            name TEXT,\
            icon BLOB,\
            letter TEXT,\
            parent TEXT,\
            sort INTEGER)"
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
            sql = "SELECT 1 FROM %s WHERE icon IS NOT NULL LIMIT 1" % name
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

        table_name = "ref_%s" % section
        if table_name in self.sections_with_icons:
            sql = "SELECT icon FROM %s WHERE value=?" % table_name
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
