from PyQt4 import QtGui, QtCore, QtSql
from PyQt4.QtSql import QSqlDatabase, QSqlQuery
from PyQt4.QtCore import Qt, pyqtSignal

from Reference.ReferenceDialog import ReferenceDialog, CrossReferenceDialog


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


class ReferenceSection(QtCore.QObject):
    changed = pyqtSignal(object)

    def __init__(self, name, title, letter='', parent=None):
        super(ReferenceSection, self).__init__(parent)

        self.name = name
        self.title = title
        self.letter = letter
        self.parentName = None

    def load(self, db):
        self.db = db
        if self.name not in self.db.tables():
            self.create(self.db)

        self.model = SqlTableModel(None, db)
        self.model.setEditStrategy(QtSql.QSqlTableModel.OnManualSubmit)
        self.model.setTable(self.name)
        self.model.select()

    def button(self, parent=None):
        self.parent = parent
        button = QtGui.QPushButton(self.letter, parent)
        button.setFixedWidth(25)
        button.clicked.connect(self.clickedButton)
        return button

    def clickedButton(self):
        dialog = ReferenceDialog(self.model, self.parent.text(), self.parent)
        dialog.setWindowTitle(self.title)
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


class CrossReferenceSection(QtCore.QObject):
    changed = pyqtSignal(object)

    def __init__(self, name, parentName, title, letter='', parent=None):
        super(CrossReferenceSection, self).__init__(parent)

        self.parentIndex = None

        self.name = name
        self.parentName = parentName
        self.title = title
        self.letter = letter

    def load(self, db):
        self.db = db
        if self.name not in self.db.tables():
            self.create(self.db)

        self.model = QtSql.QSqlRelationalTableModel(None, db)
        self.model.setEditStrategy(QtSql.QSqlTableModel.OnManualSubmit)
        self.model.setTable(self.name)
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
        dialog = CrossReferenceDialog(self.model, self.parentIndex,
                                      self.parent.text(), self.parent)
        dialog.setWindowTitle(self.title)
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
            parent TEXT)"
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
            QtGui.QMessageBox.critical(self.parent(),
                                       self.tr("Open reference"),
                                       self.tr("Can't open reference"))
            self.db.setDatabaseName(fileName)
            self.db.open()
            self.create()
            return False

        self.fileName = fileName

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
