from PyQt5 import QtCore, QtSql
from PyQt5.QtSql import QSqlDatabase, QSqlQuery
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtWidgets import *

from OpenNumismat.Reference.ReferenceDialog import ReferenceDialog, CrossReferenceDialog


class SqlTableModel(QtSql.QSqlTableModel):
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


class SqlRelationalTableModel(QtSql.QSqlRelationalTableModel):
    def __init__(self, model, parent, db):
        super().__init__(parent, db)

        self.model = model

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


class BaseReferenceSection(QtCore.QObject):
    changed = pyqtSignal(object)

    def __init__(self, name, title, letter='', sort=False, parent=None):
        super().__init__(parent)

        self.name = name
        self.table_name = "ref_%s" % name
        self.title = title
        self.letter = letter
        self.sort = sort

        self.parentName = None

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
        result = dialog.exec_()
        if result == QDialog.Accepted:
            self.reload()

            index = dialog.selectedIndex()
            if index:
                self.changed.emit(index.data())
            else:
                self.changed.emit(old_text)

    def setSort(self):
        if self.sort:
            self.model.setSort(self.model.fieldIndex('value'), Qt.AscendingOrder)
        else:
            self.model.setSort(0, Qt.AscendingOrder)

    def getSort(self):
        query = QSqlQuery(self.db)
        query.prepare("SELECT sort FROM sections WHERE name=?")
        query.addBindValue(self.name)
        query.exec_()
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
            query.exec_()

        self.setSort()

    def create(self, db=QSqlDatabase()):
        in_transaction = db.transaction()

        cross_ref = ('country', 'period', 'ruler', 'unit', 'mint', 'series')

        if self.name in cross_ref:
            sql = "CREATE TABLE %s (\
                id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,\
                parentid INTEGER NOT NULL,\
                value TEXT, icon BLOB)" % self.table_name
        else:
            sql = "CREATE TABLE %s (\
                id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,\
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
        query.exec_()

        if in_transaction:
            db.commit()


class ReferenceSection(BaseReferenceSection):
    def __init__(self, name, title, letter='', sort=False, parent=None):
        super().__init__(name, title, letter, sort, parent)

    def load(self, db):
        self.db = db
        if self.table_name not in self.db.tables():
            self.create(self.db)

        self.model = SqlTableModel(None, db)
        self.model.setEditStrategy(QtSql.QSqlTableModel.OnFieldChange)
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
            fillQuery.exec_()


class CrossReferenceSection(BaseReferenceSection):
    def __init__(self, name, parentRef, title, letter='', sort=False, parent=None):
        super().__init__(name, title, letter, sort, parent)

        self.parentIndex = None
        self.parentRef = parentRef
        self.parentName = parentRef.table_name

    def load(self, db):
        self.db = db
        if self.table_name not in self.db.tables():
            self.create(self.db)

        self.model = SqlRelationalTableModel(self.parentRef.model, None, db)
        self.model.setJoinMode(QtSql.QSqlRelationalTableModel.LeftJoin)
        self.model.setEditStrategy(QtSql.QSqlTableModel.OnFieldChange)
        self.model.setTable(self.table_name)
        parentidIndex = self.model.fieldIndex('parentid')
        self.model.parentidIndex = parentidIndex
        self.model.setRelation(
            parentidIndex, QtSql.QSqlRelation(self.parentName, 'id', 'value'))

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
            fillQuery.exec_()


class Reference(QtCore.QObject):
    def __init__(self, fields, parent=None, db=None):
        super().__init__(parent)

        if db:
            self.db = db
        else:
            self.db = QSqlDatabase.addDatabase('QSQLITE', "reference")

        self.userFields = [field.name for field in fields.userFields]
        self.sections = []

        ref_region = self.__createReferenceSection(None, 'region',
                                                   self.tr("Region"))
        ref_country = self.__createReferenceSection(ref_region, 'country',
                                                    self.tr("Country"), self.tr("C"), True)
        self.__createReferenceSection(ref_country, 'period',
                                      self.tr("Period"), self.tr("P"), True)
        self.__createReferenceSection(ref_country, 'ruler',
                                      self.tr("Ruler"))
        self.__createReferenceSection(ref_country, 'unit',
                                      self.tr("Unit"), self.tr("U"))
        self.__createReferenceSection(ref_country, 'mint',
                                      self.tr("Mint"))
        self.__createReferenceSection(ref_country, 'series',
                                      self.tr("Series"), self.tr("S"), True)
        self.__createReferenceSection(None, 'grade',
                                      self.tr("Grade"), self.tr("G"))
        self.__createReferenceSection(None, 'material',
                                      self.tr("Material"), self.tr("M"))
        self.__createReferenceSection(None, 'shape',
                                      self.tr("Shape"), self.tr("F"))
        self.__createReferenceSection(None, 'quality',
                                      self.tr("Quality"), self.tr("Q"))
        self.__createReferenceSection(None, 'edge',
                                      self.tr("Edge"), self.tr("E"))
        self.__createReferenceSection(None, 'rarity',
                                      self.tr("Rarity"), self.tr("R"))
        self.__createReferenceSection(None, 'obvrev',
                                      self.tr("ObvRev"))
        self.__createReferenceSection(None, 'type',
                                      self.tr("Type"), self.tr("T"))
        self.__createReferenceSection(None, 'defect',
                                      self.tr("Defect"), self.tr("D"))

        if 'payplace' in self.userFields or 'saleplace' in self.userFields:
            ref_place = ReferenceSection('place', self.tr("Place"))
            self.sections.append(ref_place)

    def __createReferenceSection(self, parentRef, name, title,
                                 letter='', sort=False):
        if name in self.userFields:
            if parentRef:
                ref = CrossReferenceSection(name, parentRef, title,
                                            letter, sort)
            else:
                ref = ReferenceSection(name, title, letter, sort)
            self.sections.append(ref)

            return ref
        return None

    def create(self):
        sql = "CREATE TABLE IF NOT EXISTS sections (\
            id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,\
            name TEXT,\
            icon BLOB,\
            letter TEXT,\
            parent TEXT,\
            sort INTEGER)"
        QSqlQuery(sql, self.db)

        for section in self.sections:
            section.create(self.db)

    def open(self, fileName, interactive=True):
        file = QtCore.QFileInfo(fileName)
        if file.isFile():
            self.db.setDatabaseName(fileName)
            if not self.db.open():
                print(self.db.lastError().text())
                QMessageBox.critical(self.parent(),
                            self.tr("Open reference"),
                            self.tr("Can't open reference:\n%s" % fileName))
                return False
            else:
                # Update reference DB for version 1.4.3
                if self.db.record('sections').indexOf('sort') < 0:
                    sql = "ALTER TABLE sections ADD COLUMN sort INTEGER"
                    QSqlQuery(sql, self.db)
                    sql = "UPDATE sections SET name = 'material' WHERE name = 'metal'"
                    QSqlQuery(sql, self.db)
                # Update reference DB for version 1.4.9
                if self.db.record('period').indexOf('icon') < 0:
                    for table in ('period', 'unit', 'mint', 'series'):
                        sql = "ALTER TABLE %s ADD COLUMN icon BLOB" % table
                        QSqlQuery(sql, self.db)
                # Update reference DB for version 1.5
                if self.db.record('country').indexOf('parentid') < 0:
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
                            self.tr("Can't open reference:\n%s\nCreated new one" % fileName))

            self.db.setDatabaseName(fileName)
            if not self.db.open():
                print(self.db.lastError().text())
                QMessageBox.critical(self.parent(),
                            self.tr("Create reference"),
                            self.tr("Can't create reference:\n%s" % fileName))
                return False
            self.create()

        self.fileName = fileName

        self.load()

        return True

    def load(self):
        for section in self.sections:
            section.load(self.db)

        self.sections_with_icons = []
        for section in self.sections:
            name = section.table_name
            sql = "SELECT 1 FROM %s WHERE icon IS NOT NULL LIMIT 1" % name
            query = QtSql.QSqlQuery(sql, self.db)
            query.exec_()
            if query.first():
                self.sections_with_icons.append(name)

    def section(self, name):
        # NOTE: payplace and saleplace fields has one reference section =>
        # editing one of it should change another
        if name in ('payplace', 'saleplace'):
            name = 'place'

        for section in self.sections:
            if section.name == name:
                return section

        return None

    def allSections(self):
        sectionNames = []
        for section in self.sections:
            if section.name == 'place':
                sectionNames.extend(['payplace', 'saleplace'])
            else:
                sectionNames.append(section.name)

        return sectionNames

    def getIcon(self, section, value):
        if section in ('payplace', 'saleplace'):
            section = 'place'

        table_name = "ref_%s" % section
        if table_name in self.sections_with_icons:
            sql = "SELECT icon FROM %s WHERE value=?" % table_name
            query = QtSql.QSqlQuery(sql, self.db)
            query.addBindValue(value)
            query.exec_()
            if query.first():
                data = query.record().value(0)
                if data:
                    pixmap = QPixmap()
                    if pixmap.loadFromData(data):
                        icon = QIcon(pixmap)
                        return icon
        return None
