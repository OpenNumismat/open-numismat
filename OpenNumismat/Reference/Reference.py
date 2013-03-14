from PyQt4 import QtGui, QtCore, QtSql
from PyQt4.QtSql import QSqlDatabase, QSqlQuery
from PyQt4.QtCore import Qt, pyqtSignal

from OpenNumismat.Reference.ReferenceDialog import ReferenceDialog, CrossReferenceDialog


class SqlTableModel(QtSql.QSqlTableModel):
    def __init__(self, parent, db):
        super(SqlTableModel, self).__init__(parent, db)

    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.DecorationRole:
            if index.row() < 0:
                return None
            iconIndex = self.index(index.row(), self.fieldIndex('icon'))
            if not self.data(iconIndex) or self.data(iconIndex).isNull():
                return None
            icon = QtGui.QPixmap()
            icon.loadFromData(self.data(iconIndex))
            return icon

        return super(SqlTableModel, self).data(index, role)


class SqlRelationalTableModel(QtSql.QSqlRelationalTableModel):
    def __init__(self, parent, db):
        super(SqlRelationalTableModel, self).__init__(parent, db)

        self.model = None

    def relationModel(self, column):
        if not self.model:
            self.model = SqlTableModel(self, self.database())
            self.model.setTable(self.relation(column).tableName())
            self.model.select()

        return self.model


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
        self.model.setEditStrategy(QtSql.QSqlTableModel.OnManualSubmit)
        self.model.setTable(self.name)
        if self.sort:
            self.model.setSort(self.model.fieldIndex('value'), Qt.AscendingOrder)
        self.model.select()

    def button(self, parent=None):
        self.parent = parent
        button = QtGui.QPushButton(self.letter, parent)
        button.setFixedWidth(25)
        button.clicked.connect(self.clickedButton)
        return button

    def clickedButton(self):
        dialog = ReferenceDialog(self, self.parent.text(), self.parent)
        result = dialog.exec_()
        if result == QtGui.QDialog.Accepted:
            self.model.submitAll()

            index = dialog.selectedIndex()
            if index:
                self.changed.emit(index.data())
        else:
            self.model.revertAll()

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

    def setSort(self, sort):
        if self.sort != sort:
            self.sort = sort

            query = QSqlQuery(self.db)
            query.prepare("UPDATE sections SET sort=? WHERE name=?")
            query.addBindValue(sort)
            query.addBindValue(self.name)
            query.exec_()


class CrossReferenceSection(QtCore.QObject):
    changed = pyqtSignal(object)

    def __init__(self, name, parentName, title, letter='', sort=False, parent=None):
        super(CrossReferenceSection, self).__init__(parent)

        self.parentIndex = None

        self.name = name
        self.parentName = parentName
        self.title = title
        self.letter = letter
        self.sort = sort

    def load(self, db):
        self.db = db
        if self.name not in self.db.tables():
            self.create(self.db)

        self.model = SqlRelationalTableModel(None, db)
        self.model.setEditStrategy(QtSql.QSqlTableModel.OnManualSubmit)
        self.model.setTable(self.name)
        if self.sort:
            self.model.setSort(self.model.fieldIndex('value'), Qt.AscendingOrder)
        parentIndex = self.model.fieldIndex('parentid')
        self.model.setRelation(parentIndex,
                           QtSql.QSqlRelation(self.parentName, 'id', 'value'))
        self.model.select()

    def button(self, parent=None):
        self.parent = parent
        button = QtGui.QPushButton(self.letter, parent)
        button.setFixedWidth(25)
        button.clicked.connect(self.clickedButton)
        return button

    def clickedButton(self):
        dialog = CrossReferenceDialog(self, self.parentIndex,
                                      self.parent.text(), self.parent)
        result = dialog.exec_()
        if result == QtGui.QDialog.Accepted:
            self.model.submitAll()

            index = dialog.selectedIndex()
            if index:
                self.changed.emit(index.data())
        else:
            self.model.revertAll()

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
            value TEXT)" % self.name
        QSqlQuery(sql, db)

        query = QSqlQuery(db)
        query.prepare("INSERT INTO sections (name, letter, parent)\
            VALUES (?, ?, ?)")
        query.addBindValue(self.name)
        query.addBindValue(self.letter)
        query.addBindValue(self.parentName)
        query.exec_()

        db.commit()

    def setSort(self, sort):
        if self.sort != sort:
            self.sort = sort

            query = QSqlQuery(self.db)
            query.prepare("UPDATE sections SET sort=? WHERE name=?")
            query.addBindValue(sort)
            query.addBindValue(self.name)
            query.exec_()


class Reference(QtCore.QObject):
    def __init__(self, parent=None):
        super(Reference, self).__init__(parent)

        self.db = QSqlDatabase.addDatabase('QSQLITE', "reference")

        self.sections = {
            'country': ReferenceSection('country', self.tr("Country"), self.tr("C")),
            'type': ReferenceSection('type', self.tr("Type"), self.tr("T")),
            'grade': ReferenceSection('grade', self.tr("Grade"), self.tr("G")),
            'place': ReferenceSection('place', self.tr("Place")),
            'material': ReferenceSection('material', self.tr("Material"), self.tr("M")),
            'shape': ReferenceSection('shape', self.tr("Shape"), self.tr("F")),
            'obvrev': ReferenceSection('obvrev', self.tr("ObvRev")),
            'edge': ReferenceSection('edge', self.tr("Edge"), self.tr("E")),
            'unit': CrossReferenceSection('unit', 'country', self.tr("Unit"), self.tr("U")),
            'mint': CrossReferenceSection('mint', 'country', self.tr("Mint")),
            'period': CrossReferenceSection('period', 'country', self.tr("Period"), self.tr("P")),
            'series': CrossReferenceSection('series', 'country', self.tr("Series"), self.tr("S")),
            'quality': ReferenceSection('quality', self.tr("Quality"), self.tr("Q")),
            'defect': ReferenceSection('defect', self.tr("Defect"), self.tr("D")),
            'rarity': ReferenceSection('rarity', self.tr("Rarity"), self.tr("R"))
        }

    def create(self):
        sql = "CREATE TABLE IF NOT EXISTS sections (\
            id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,\
            name TEXT,\
            icon BLOB,\
            letter TEXT,\
            parent TEXT,\
            sort INTEGER)"
        QSqlQuery(sql, self.db)

        for section in self.sections.values():
            section.create(self.db)

    def open(self, fileName):
        file = QtCore.QFileInfo(fileName)
        if file.isFile():
            self.db.setDatabaseName(fileName)
            if not self.db.open():
                print(self.db.lastError().text())
                QtGui.QMessageBox.critical(self.parent(),
                                           self.tr("Open reference"),
                                           self.tr("Can't open reference"))
                return False
            else:
                # Update reference DB for version 1.4.3
                if self.db.record('sections').indexOf('sort') < 0:
                    sql = "ALTER TABLE sections ADD COLUMN sort INTEGER"
                    QSqlQuery(sql, self.db)
                    sql = "UPDATE sections SET name = 'material' WHERE name = 'metal'"
                    QSqlQuery(sql, self.db)
        else:
            QtGui.QMessageBox.critical(self.parent(),
                                       self.tr("Open reference"),
                                       self.tr("Can't open reference"))
            self.db.setDatabaseName(fileName)
            self.db.open()
            self.create()
            return False

        self.fileName = fileName

        for section_name, section in self.sections.items():
            query = QSqlQuery(self.db)
            query.prepare("SELECT sort FROM sections WHERE name=?")
            query.addBindValue(section_name)
            query.exec_()
            if query.first():
                data = query.record().value(0)
                if not isinstance(data, QtCore.QPyNullVariant):
                    section.sort = bool(data)

        return True

    def section(self, name):
        section = None

        # NOTE: payplace and saleplace fields has one reference section =>
        # editing one of it should change another
        if name in ['payplace', 'saleplace']:
            name = 'place'

        if name in self.sections:
            section = self.sections[name]
            section.load(self.db)

        return section

    def allSections(self):
        sectionNames = list(self.sections.keys())
        # Move cross section to bottom for filling after parent reference
        for key in ['unit', 'mint', 'period', 'series']:
            sectionNames.remove(key)
            sectionNames.append(key)

        if 'place' in sectionNames:
            sectionNames.remove('place')
            sectionNames.extend(['payplace', 'saleplace'])

        return sectionNames
