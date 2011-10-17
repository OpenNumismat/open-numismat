from PyQt4 import QtGui, QtCore, QtSql
from PyQt4.QtSql import QSqlDatabase, QSqlQuery, QSqlRecord
from PyQt4.QtCore import Qt, pyqtSignal

class ReferenceDialog(QtGui.QDialog):
    def __init__(self, model, text='', parent=None):
        super(ReferenceDialog, self).__init__(parent)
        
        self.model = model

        self.listWidget = QtGui.QListView(self)
        self.listWidget.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        self.listWidget.setModel(self.model)
        self.listWidget.setModelColumn(self.model.fieldIndex('value'))
        
        startIndex = self.model.index(0, self.model.fieldIndex('value'))
        indexes = self.model.match(startIndex, 0, text, flags=Qt.MatchFixedString)
        if indexes:
            self.listWidget.selectionModel().setCurrentIndex(indexes[0], QtGui.QItemSelectionModel.ClearAndSelect)

        # TODO: Customize edit buttons
        editButtonBox = QtGui.QDialogButtonBox(Qt.Horizontal)
        self.addButton = QtGui.QPushButton(self.tr("Add"))
        editButtonBox.addButton(self.addButton, QtGui.QDialogButtonBox.ActionRole)
        self.delButton = QtGui.QPushButton(self.tr("Del"))
        editButtonBox.addButton(self.delButton, QtGui.QDialogButtonBox.ActionRole)
        editButtonBox.clicked.connect(self.clicked)

        buttonBox = QtGui.QDialogButtonBox(Qt.Horizontal)
        buttonBox.addButton(QtGui.QDialogButtonBox.Ok)
        buttonBox.addButton(QtGui.QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        layout = QtGui.QVBoxLayout(self)
        layout.addWidget(self.listWidget)
        layout.addWidget(editButtonBox)
        layout.addWidget(buttonBox)

        self.setLayout(layout)
    
    def clicked(self, button):
        if button == self.addButton:
            row = self.model.rowCount()
            self.model.insertRow(row)
            index = self.model.index(row, self.model.fieldIndex('value'))
            self.model.setData(index, self.tr("Enter value"))
            self.listWidget.edit(index)
            self.listWidget.selectionModel().setCurrentIndex(index, QtGui.QItemSelectionModel.ClearAndSelect)
        elif button == self.delButton:
            index = self.listWidget.currentIndex()
            if index.isValid() and index in self.listWidget.selectedIndexes():
                self.model.removeRow(index.row())
                self.listWidget.setRowHidden(index.row(), True)

class CrossReferenceDialog(ReferenceDialog):
    def __init__(self, model, parentIndex, text='', parent=None):
        super(CrossReferenceDialog, self).__init__(model, text, parent)
        
        self.rel = self.model.relationModel(1)

        self.comboBox = QtGui.QComboBox(self)
        self.comboBox.setModel(self.rel)
        self.comboBox.setModelColumn(self.rel.fieldIndex('value'))
        if parentIndex:
            row = parentIndex.row()
        else:
            row = -1
        self.comboBox.setCurrentIndex(row)
        self.comboBox.setDisabled(True)
        self.comboBox.currentIndexChanged.connect(self.currentIndexChanged)

        layout = self.layout()
        layout.insertWidget(0, self.comboBox)
    
    def currentIndexChanged(self, index):
        idIndex = self.rel.fieldIndex('id')
        self.model.setFilter('parentid=%d' % self.rel.data(self.rel.index(index, idIndex)))
    
    def clicked(self, button):
        if button == self.addButton:
            idIndex = self.rel.fieldIndex('id')
            parentId = self.rel.data(self.rel.index(self.comboBox.currentIndex(), idIndex))

            row = self.model.rowCount()
            self.model.insertRow(row)
            index = self.model.index(row, 1)
            self.model.setData(index, parentId)
            index = self.model.index(row, self.model.fieldIndex('value'))
            self.model.setData(index, self.tr("Enter value"))
            self.listWidget.edit(index)
            self.listWidget.selectionModel().setCurrentIndex(index, QtGui.QItemSelectionModel.ClearAndSelect)
        elif button == self.delButton:
            super(CrossReferenceDialog, self).clicked(button)

class ReferenceSection(QtCore.QObject):
    changed = pyqtSignal(object)

    def __init__(self, name, letter='', parent=None):
        super(ReferenceSection, self).__init__(parent)

        if isinstance(name, QSqlRecord):
            record = name
            self.id = record.value('id')
            self.name = record.value('name')
            self.letter = record.value('letter')
        else:
            self.name = name
            self.letter = letter
        self.parentName = None
    
    def load(self, db):
        self.db = db
        sql = "CREATE TABLE IF NOT EXISTS %s (\
            id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,\
            value CHAR)" % self.name
        QSqlQuery(sql, db)

        self.model = QtSql.QSqlRelationalTableModel(None, db)
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
        result = dialog.exec_()
        if result == QtGui.QDialog.Accepted:
            index = dialog.listWidget.currentIndex()
            if index in dialog.listWidget.selectedIndexes():
                self.model.submitAll()
                self.changed.emit(index.data())
            else:
                self.model.submitAll()
        else:
            self.model.revertAll()
    
    def fillFromQuery(self, query):
        while query.next():
            value = query.record().value(0)
            fillQuery = QSqlQuery(self.db)
            fillQuery.prepare("INSERT INTO %s (value) "
                          "SELECT ? "
                          "WHERE NOT EXISTS (SELECT 1 FROM %s WHERE value=?)" % (self.name, self.name))
            fillQuery.addBindValue(value)
            fillQuery.addBindValue(value)
            fillQuery.exec_()

class CrossReferenceSection(QtCore.QObject):
    changed = pyqtSignal(object)

    def __init__(self, name, parentName=None, letter='', parent=None):
        super(CrossReferenceSection, self).__init__(parent)
        
        self.parentIndex = None

        if isinstance(name, QSqlRecord):
            record = name
            self.id = record.value('id')
            self.name = record.value('name')
            self.letter = record.value('letter')
            self.parentName = record.value('parent')
        else:
            self.name = name
            self.letter = letter
            self.parentName = parentName
    
    def load(self, db):
        self.db = db
        sql = "CREATE TABLE IF NOT EXISTS %s (\
            id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,\
            parentid INTEGER NOT NULL,\
            value CHAR)" % self.name
        QSqlQuery(sql, db)

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
        dialog = CrossReferenceDialog(self.model, self.parentIndex, self.parent.text(), self.parent)
        result = dialog.exec_()
        if result == QtGui.QDialog.Accepted:
            index = dialog.listWidget.currentIndex()
            if index in dialog.listWidget.selectedIndexes():
                self.model.submitAll()
                self.changed.emit(index.data())
            else:
                self.model.submitAll()
        else:
            self.model.revertAll()

    def fillFromQuery(self, parentId, query):
        while query.next():
            value = query.record().value(0)
            fillQuery = QSqlQuery(self.db)
            fillQuery.prepare("INSERT INTO %s (value, parentid) "
                          "SELECT ?, ? "
                          "WHERE NOT EXISTS (SELECT 1 FROM %s WHERE value=? AND parentid=?)" % (self.name, self.name))
            fillQuery.addBindValue(value)
            fillQuery.addBindValue(parentId)
            fillQuery.addBindValue(value)
            fillQuery.addBindValue(parentId)
            fillQuery.exec_()

class Reference(QtCore.QObject):
    def __init__(self, parent=None):
        super(Reference, self).__init__(parent)

        self.db = QSqlDatabase.addDatabase('QSQLITE', "reference")
    
    def create(self):
        sql = "CREATE TABLE IF NOT EXISTS sections (\
            id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,\
            name CHAR,\
            icon BLOB,\
            letter CHAR(1),\
            parent CHAR)"
        QSqlQuery(sql, self.db)

        sections = [
                ReferenceSection('country', self.tr("C")),
                ReferenceSection('type', self.tr("T")),
                ReferenceSection('grade', self.tr("G")),
                ReferenceSection('place'),
                ReferenceSection('metal', self.tr("M")),
                ReferenceSection('form', self.tr("F")),
                ReferenceSection('obvrev'),
                ReferenceSection('edge', self.tr("E")),
                CrossReferenceSection('unit', 'country', self.tr("U")),
                CrossReferenceSection('mint', 'country'),
                CrossReferenceSection('period', 'country', self.tr("P")),
                CrossReferenceSection('series', 'country', self.tr("S")),
                ReferenceSection('quality', self.tr("Q")),
                ReferenceSection('defect', self.tr("D")),
                ReferenceSection('rarity', self.tr("R"))
            ]
        for section in sections:
            query = QSqlQuery(self.db)
            if isinstance(section, CrossReferenceSection):
                query.prepare("INSERT INTO sections (name, letter, parent) "
                              "VALUES (?, ?, ?)")
                query.addBindValue(section.name)
                query.addBindValue(section.letter)
                query.addBindValue(section.parentName)
            else:
                query.prepare("INSERT INTO sections (name, letter) "
                              "VALUES (?, ?)")
                query.addBindValue(section.name)
                query.addBindValue(section.letter)
            query.exec_()
    
    def open(self, fileName):
        file = QtCore.QFileInfo(fileName)
        if file.isFile():
            self.db.setDatabaseName(fileName)
            if not self.db.open():
                print(self.db.lastError().text())
                QtGui.QMessageBox.critical(self.parent(), self.tr("Open reference"), self.tr("Can't open reference"))
                return False
        else:
            QtGui.QMessageBox.critical(self.parent(), self.tr("Open reference"), self.tr("Can't open reference"))
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
        
        query = QSqlQuery(self.db)
        query.prepare("SELECT * FROM sections WHERE name=?")
        query.addBindValue(name)
        query.exec_()
        
        if query.first():
            if query.record().isNull('parent'):
                section = ReferenceSection(query.record())
            else:
                section = CrossReferenceSection(query.record())
            section.load(self.db)
        
        return section
    
    def allSections(self):
        query = QSqlQuery(self.db)
        query.prepare("SELECT * FROM sections")
        query.exec_()
        
        sections = []
        while query.next():
            sections.append(query.record().value('name'))
        
        if 'place' in sections:
            sections.remove('place')
            sections.extend(['payplace', 'saleplace'])
        
        return sections
