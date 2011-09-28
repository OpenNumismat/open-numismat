from PyQt4 import QtGui, QtCore
from PyQt4.QtSql import QSqlDatabase, QSqlQuery, QSqlRecord
from PyQt4.QtCore import Qt, pyqtSignal

class ReferenceDialog(QtGui.QDialog):
    def __init__(self, refSection, parent=None):
        super(ReferenceDialog, self).__init__(parent)
        
        self.refSection = refSection

        self.listWidget = QtGui.QListWidget(self)
        self.listWidget.setDragDropMode(QtGui.QAbstractItemView.InternalMove)
        self.listWidget.setDropIndicatorShown(True) 
        for val in self.refSection.values:
            item = QtGui.QListWidgetItem(val, self.listWidget)
            item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsEditable | Qt.ItemIsSelectable | Qt.ItemIsDragEnabled)
            self.listWidget.addItem(item)

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
        buttonBox.accepted.connect(self.save)
        buttonBox.rejected.connect(self.reject)

        layout = QtGui.QVBoxLayout(self)
        layout.addWidget(self.listWidget)
        layout.addWidget(editButtonBox)
        layout.addWidget(buttonBox)

        self.setLayout(layout)
    
    def clicked(self, button):
        if button == self.addButton:
            item = QtGui.QListWidgetItem(self.tr("Enter value"), self.listWidget)
            item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsEditable | Qt.ItemIsSelectable | Qt.ItemIsDragEnabled)
            row = self.listWidget.currentRow()
            self.listWidget.insertItem(row, item)
            self.listWidget.editItem(item)
        elif button == self.delButton:
            item = self.listWidget.currentItem()
            self.listWidget.removeItemWidget(item)
    
    def save(self):
        self.refSection.values = []
        for i in range(self.listWidget.count()):
            item = self.listWidget.item(i)
            val = item.text().strip()
            if val:
                self.refSection.values.append(val)

        self.accept()

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
    
    def load(self, db):
        self.db = db
        
        sql = "CREATE TABLE IF NOT EXISTS %s (\
            id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,\
            value CHAR)" % self.name
        QSqlQuery(sql, self.db)

        sql = "SELECT * FROM %s" % self.name
        query = QSqlQuery(sql, self.db)

        self.values = []
        while query.next():
            val = query.record().value('value')
            self.values.append(val)
    
    def save(self):
        self.db.transaction()

        query = QSqlQuery(self.db)
        query.prepare("DELETE FROM %s" % self.name)
        query.exec_()

        for val in self.values:
            query = QSqlQuery(self.db)
            query.prepare("INSERT INTO %s (value) "
                          "VALUES (?)" % self.name)
            query.addBindValue(val)
            query.exec_()

        self.db.commit()
    
    def button(self, parent=None):
        self.parent = parent
        button = QtGui.QPushButton(self.letter, parent)
        button.setFixedWidth(25)
        button.clicked.connect(self.clickedButton)
        return button
    
    def clickedButton(self):
        dialog = ReferenceDialog(self, self.parent)
        result = dialog.exec_()
        if result == QtGui.QDialog.Accepted:
            self.save()
            self.changed.emit(dialog.listWidget.currentItem().text())

class Reference(QtCore.QObject):
    def __init__(self, parent=None):
        super(Reference, self).__init__(parent)

        self.db = QSqlDatabase.addDatabase('QSQLITE', "reference")
    
    def create(self):
        sql = "CREATE TABLE IF NOT EXISTS sections (\
            id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,\
            name CHAR,\
            icon BLOB,\
            letter CHAR(1))"
        QSqlQuery(sql, self.db)

        sections = [
                ReferenceSection('country', self.tr("C")),
                ReferenceSection('type', self.tr("T")),
                ReferenceSection('grade', self.tr("G")),
                ReferenceSection('payplace'),
                ReferenceSection('saleplace'),
                ReferenceSection('metal', self.tr("M")),
                ReferenceSection('form', self.tr("F")),
                ReferenceSection('obvrev'),
                ReferenceSection('edge', self.tr("E"))
            ]
        for section in sections:
            query = QSqlQuery(self.db)
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
        
        query = QSqlQuery(self.db)
        query.prepare("SELECT * FROM sections WHERE name=?")
        query.addBindValue(name)
        query.exec_()
        
        if query.first():
            section = ReferenceSection(query.record())
            section.load(self.db)
        
        return section
