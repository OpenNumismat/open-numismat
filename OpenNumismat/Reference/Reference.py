from PyQt5 import QtCore, QtSql
from PyQt5.QtSql import QSqlDatabase, QSqlQuery
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import *

from OpenNumismat.Reference.ReferenceDialog import ReferenceDialog, CrossReferenceDialog


class SqlTableModel(QtSql.QSqlTableModel):
    def __init__(self, parent, db):
        super().__init__(parent, db)

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

    def relationModel(self, column):
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


class ReferenceSection(QtCore.QObject):
    changed = pyqtSignal(object)

    def __init__(self, name, title, letter='', sort=False, parent=None):
        super(ReferenceSection, self).__init__(parent)

        self.name = name
        self.parentName = None
        self.title = title
        self.letter = letter
        self.sort = sort

    def load(self, db):
        self.db = db
        if self.name not in self.db.tables():
            self.create(self.db)

        self.model = SqlTableModel(None, db)
        self.model.setEditStrategy(QtSql.QSqlTableModel.OnFieldChange)
        self.model.setTable(self.name)

        self.reload()

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
        copy = ReferenceSection(self.name, self.title, self.letter, self.sort, self.parent)
        copy.load(self.db)
        dialog = ReferenceDialog(copy, self.parent.text(), self.parent)
        result = dialog.exec_()
        if result == QDialog.Accepted:
            self.reload()

            index = dialog.selectedIndex()
            if index:
                self.changed.emit(index.data())
            else:
                self.changed.emit(old_text)

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
                                                        (self.name, self.name))
            fillQuery.addBindValue(value)
            fillQuery.addBindValue(value)
            fillQuery.exec_()

    def create(self, db=QSqlDatabase()):
        db.transaction()

        sql = "CREATE TABLE %s (\
            id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,\
            value TEXT, icon BLOB)" % self.name
        QSqlQuery(sql, db)

        query = QSqlQuery(db)
        query.prepare("INSERT INTO sections (name, letter)\
            VALUES (?, ?)")
        query.addBindValue(self.name)
        query.addBindValue(self.letter)
        query.exec_()

        db.commit()

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


class CrossReferenceSection(QtCore.QObject):
    changed = pyqtSignal(object)

    def __init__(self, name, parentRef, title, letter='', sort=False, parent=None):
        super(CrossReferenceSection, self).__init__(parent)

        self.parentIndex = None

        self.name = name
        self.parentRef = parentRef
        self.parentName = parentRef.name
        self.title = title
        self.letter = letter
        self.sort = sort

    def load(self, db):
        self.db = db
        if self.name not in self.db.tables():
            self.create(self.db)

        self.model = SqlRelationalTableModel(self.parentRef.model, None, db)
        self.model.setEditStrategy(QtSql.QSqlTableModel.OnFieldChange)
        self.model.setTable(self.name)
        parentIndex = self.model.fieldIndex('parentid')
        self.model.parentidIndex = parentIndex
        self.model.setRelation(parentIndex,
                           QtSql.QSqlRelation(self.parentName, 'id', 'value'))

        self.reload()

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
        copy = CrossReferenceSection(self.name, self.parentRef, self.title,
                                     self.letter, self.sort, self.parent)
        copy.load(self.db)
        dialog = CrossReferenceDialog(copy, self.parentIndex,
                                      self.parent.text(), self.parent)
        result = dialog.exec_()
        if result == QDialog.Accepted:
            self.reload()

            index = dialog.selectedIndex()
            if index:
                self.changed.emit(index.data())
            else:
                self.changed.emit(old_text)

    def fillFromQuery(self, parentId, query):
        while query.next():
            value = query.record().value(0)
            fillQuery = QSqlQuery(self.db)
            fillQuery.prepare("INSERT INTO %s (value, parentid) "
                          "SELECT ?, ? "
                          "WHERE NOT EXISTS "
                          "(SELECT 1 FROM %s WHERE value=? AND parentid=?)" %
                                                        (self.name, self.name))
            fillQuery.addBindValue(value)
            fillQuery.addBindValue(parentId)
            fillQuery.addBindValue(value)
            fillQuery.addBindValue(parentId)
            fillQuery.exec_()

    def create(self, db=QSqlDatabase()):
        db.transaction()

        sql = "CREATE TABLE %s (\
            id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,\
            parentid INTEGER NOT NULL,\
            value TEXT, icon BLOB)" % self.name
        QSqlQuery(sql, db)

        query = QSqlQuery(db)
        query.prepare("INSERT INTO sections (name, letter, parent)\
            VALUES (?, ?, ?)")
        query.addBindValue(self.name)
        query.addBindValue(self.letter)
        query.addBindValue(self.parentName)
        query.exec_()

        db.commit()

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


class Reference(QtCore.QObject):
    def __init__(self, parent=None):
        super(Reference, self).__init__(parent)

        self.db = QSqlDatabase.addDatabase('QSQLITE', "reference")

        ref_region = ReferenceSection('region', self.tr("Region"))
        ref_country = CrossReferenceSection('country', ref_region, self.tr("Country"), self.tr("C"))
        ref_type = ReferenceSection('type', self.tr("Type"), self.tr("T"))
        ref_grade = ReferenceSection('grade', self.tr("Grade"), self.tr("G"))
        ref_place = ReferenceSection('place', self.tr("Place"))
        ref_material = ReferenceSection('material', self.tr("Material"), self.tr("M"))
        ref_shape = ReferenceSection('shape', self.tr("Shape"), self.tr("F"))
        ref_obvrev = ReferenceSection('obvrev', self.tr("ObvRev"))
        ref_edge = ReferenceSection('edge', self.tr("Edge"), self.tr("E"))
        ref_unit = CrossReferenceSection('unit', ref_country, self.tr("Unit"), self.tr("U"))
        ref_mint = CrossReferenceSection('mint', ref_country, self.tr("Mint"))
        ref_period = CrossReferenceSection('period', ref_country, self.tr("Period"), self.tr("P"))
        ref_series = CrossReferenceSection('series', ref_country, self.tr("Series"), self.tr("S"))
        ref_quality = ReferenceSection('quality', self.tr("Quality"), self.tr("Q"))
        ref_defect = ReferenceSection('defect', self.tr("Defect"), self.tr("D"))
        ref_rarity = ReferenceSection('rarity', self.tr("Rarity"), self.tr("R"))
        ref_ruler = CrossReferenceSection('ruler', ref_country, self.tr("Ruler"))

        self.sections = [
            ref_region,
            ref_country,
            ref_period,
            ref_ruler,
            ref_unit,
            ref_mint,
            ref_series,
            ref_grade,
            ref_material,
            ref_shape,
            ref_quality,
            ref_edge,
            ref_rarity,
            ref_obvrev,
            ref_type,
            ref_defect,
            ref_place,
        ]

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

    def open(self, fileName):
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
                    for table in ['period', 'unit', 'mint', 'series']:
                        sql = "ALTER TABLE %s ADD COLUMN icon BLOB" % table
                        QSqlQuery(sql, self.db)
                # Update reference DB for version 1.5
                if self.db.record('country').indexOf('parentid') < 0:
                    sql = "ALTER TABLE country ADD COLUMN parentid INTEGER"
                    QSqlQuery(sql, self.db)
        else:
            QMessageBox.warning(self.parent(),
                            self.tr("Open reference"),
                            self.tr("Can't open reference:\n%s\nCreated new one" % fileName))
            self.db.setDatabaseName(fileName)
            self.db.open()
            self.create()

        self.fileName = fileName

        for section in self.sections:
            section.load(self.db)

        return True

    def section(self, name):
        # NOTE: payplace and saleplace fields has one reference section =>
        # editing one of it should change another
        if name in ['payplace', 'saleplace']:
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
