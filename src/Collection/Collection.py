from PyQt4 import QtGui, QtCore
from PyQt4.QtSql import QSqlTableModel, QSqlDatabase, QSqlQuery

from .CollectionFields import FieldTypes as Type
from .CollectionFields import CollectionFields
from .CollectionPages import CollectionPages

class CollectionModel(QSqlTableModel):
    def __init__(self, parent=None, db=QSqlDatabase(), fields=CollectionFields()):
        super(CollectionModel, self).__init__(parent, db)
        
        self.fields = fields
    
    def data(self, index, role=QtCore.Qt.DisplayRole):
        ret = super(CollectionModel, self).data(index, role)
        
        fieldType = self.fields.fields[index.column()].type
        if fieldType == Type.Date:
            if role == QtCore.Qt.DisplayRole:
                date = QtCore.QDate.fromString(ret)
                return date.toString(QtCore.Qt.SystemLocaleShortDate)

        return ret
    
    def columnType(self, column):
        if isinstance(column, QtCore.QModelIndex):
            column = column.column()

        return self.fields.fields[column].type

class Collection(QtCore.QObject):
    def __init__(self, parent=None):
        super(Collection, self).__init__(parent)

        self.db = QSqlDatabase.addDatabase('QSQLITE')
        self._pages = None
        
        self.fields = CollectionFields()
    
    def open(self, fileName):
        file = QtCore.QFileInfo(fileName)
        if file.isFile():
            self.db.setDatabaseName(fileName)
            if not self.db.open():
                print(self.db.lastError().text())
                QtGui.QMessageBox.critical(self.parent(), self.tr("Open collection"), self.tr("Can't open collection"))
                return False
        else:
            QtGui.QMessageBox.critical(self.parent(), self.tr("Open collection"), self.tr("Collection not exists"))
            return False
            
        self.fileName = fileName
        self._pages = CollectionPages(self.db)
        
        return True
    
    def create(self, fileName):
        if QtCore.QFileInfo(fileName).exists():
            QtGui.QMessageBox.critical(self.parent(), self.tr("Create collection"), self.tr("Specified file already exists"))
            return False
        
        self.db.setDatabaseName(fileName)
        if not self.db.open():
            print(self.db.lastError().text())
            QtGui.QMessageBox.critical(self.parent(), self.tr("Create collection"), self.tr("Can't open collection"))
            return False
        
        self.fileName = fileName

        sqlFields = []
        for field in self.fields:
            if field.name == 'id':
                sqlFields.append('id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT')
            else:
                sqlFields.append(self.__fieldToSql(field))
        
        sql = "CREATE TABLE IF NOT EXISTS coins (" + ", ".join(sqlFields) + ")"
        QSqlQuery(sql, self.db)
        
        self._pages = CollectionPages(self.db)
        
        return True

    def __fieldToSql(self, field):
        if field.type == Type.String:
            type_ = 'CHAR'
        elif field.type == Type.ShortString:
            type_ = 'CHAR(10)'
        elif field.type == Type.Number:
            type_ = 'NUMERIC(4)'
        elif field.type == Type.Text:
            type_ = 'TEXT'
        elif field.type == Type.Money:
            type_ = 'NUMERIC(10,2)'
        elif field.type == Type.Date:
            type_ = 'CHAR'
        elif field.type == Type.BigInt:
            type_ = 'INTEGER'
        elif field.type == Type.Image:
            type_ = 'BLOB'
        elif field.type == Type.Value:
            type_ = 'NUMERIC(10,3)'
        elif field.type == Type.State:
            type_ = 'CHAR'
        else:
            raise
        
        return field.name + ' ' + type_

    def getFileName(self):
        return self.fileName
    
    def getCollectionName(self):
        return Collection.fileNameToCollectionName(self.fileName)
    
    def model(self):
        return self.createModel()
    
    def pages(self):
        return self._pages
    
    def createModel(self):
        model = CollectionModel(None, self.db, self.fields)
        model.setEditStrategy(QSqlTableModel.OnManualSubmit)
        model.setTable('coins')
        model.select()
        for field in self.fields:
            model.setHeaderData(field.id, QtCore.Qt.Horizontal, field.title)
        return model
    
    @staticmethod
    def fileNameToCollectionName(fileName):
        file = QtCore.QFileInfo(fileName)
        return file.baseName()
