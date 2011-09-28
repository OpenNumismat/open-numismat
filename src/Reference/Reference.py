from PyQt4 import QtGui, QtCore
from PyQt4.QtSql import QSqlDatabase, QSqlQuery, QSqlRecord

class ReferenceSection:
    def __init__(self, name, letter=''):
        if isinstance(name, QSqlRecord):
            record = name
            self.id = record.value('id')
            self.name = record.value('name')
            self.letter = record.value('letter')
        else:
            self.name = name
            self.letter = letter
    
    def load(self, db):
        sql = "CREATE TABLE IF NOT EXISTS %s (\
            id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,\
            value CHAR)" % self.name
        QSqlQuery(sql, db)

        sql = "SELECT * FROM %s" % self.name
        query = QSqlQuery(sql, db)

        self.values = []
        while query.next():
            val = query.record().value('value')
            self.values.append(val)

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
                ReferenceSection('grade', self.tr("G"))
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
    
    def getTypes(self):
        return ['a', 'b']
