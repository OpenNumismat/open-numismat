from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import Qt, pyqtSignal
from PyQt4.QtSql import QSqlTableModel, QSqlDatabase, QSqlQuery

from .CollectionFields import FieldTypes as Type
from .CollectionFields import CollectionFields
from .CollectionPages import CollectionPages
from Reference.Reference import CrossReferenceSection
from EditCoinDialog.EditCoinDialog import EditCoinDialog

class CollectionModel(QSqlTableModel):
    rowInserted = pyqtSignal(object)

    def __init__(self, reference, parent=None, db=QSqlDatabase(), fields=CollectionFields()):
        super(CollectionModel, self).__init__(parent, db)
        
        self.intFilter = ''
        self.extFilter = ''
        
        self.reference = reference
        self.fields = fields
        self.proxy = None

        self.rowsInserted.connect(self.rowsInsertedEvent)
    
    def rowsInsertedEvent(self, parent, start, end):
        self.insertedRowIndex = self.index(end, 0)

    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            data = super(CollectionModel, self).data(index, role)
            fieldType = self.fields.fields[index.column()].type
            if fieldType == Type.Date:
                date = QtCore.QDate.fromString(data, Qt.ISODate)
                return date.toString(Qt.SystemLocaleShortDate)
            elif fieldType == Type.DateTime:
                date = QtCore.QDateTime.fromString(data, Qt.ISODate)
                return date.toString(Qt.SystemLocaleShortDate)
        elif role == Qt.UserRole:
            return super(CollectionModel, self).data(index, Qt.DisplayRole)

        return super(CollectionModel, self).data(index, role)
    
    def addCoin(self, record, parent=None):
        dialog = EditCoinDialog(self.reference, record, parent)
        result = dialog.exec_()
        if result == QtGui.QDialog.Accepted:
            rowCount = self.rowCount()
            
            self.insertRecord(-1, record)
            self.submitAll()

            if rowCount < self.rowCount():  # inserted row visible in current model
                if self.insertedRowIndex.isValid():
                    self.rowInserted.emit(self.insertedRowIndex)
    
    def insertRecord(self, row, record):
        if self.proxy:
            self.proxy.setDynamicSortFilter(False)
        
        record.setNull('id')  # remove ID value from record
        currentTime = QtCore.QDateTime.currentDateTime()
        record.setValue('createdat', currentTime.toString(Qt.ISODate))
        record.setValue('updatedat', currentTime.toString(Qt.ISODate))
        super(CollectionModel, self).insertRecord(row, record)
    
    def setRecord(self, row, record):
        if self.proxy:
            self.proxy.setDynamicSortFilter(False)
        
        currentTime = QtCore.QDateTime.currentDateTime()
        record.setValue('updatedat', currentTime.toString(Qt.ISODate))
        super(CollectionModel, self).setRecord(row, record)
    
    def submitAll(self):
        super(CollectionModel, self).submitAll()
        
        if self.proxy:
            self.proxy.setDynamicSortFilter(True)
    
    def columnType(self, column):
        if isinstance(column, QtCore.QModelIndex):
            column = column.column()

        return self.fields.fields[column].type
    
    def setFilter(self, filter_):
        self.intFilter = filter_
        self.__applyFilter()

    def setAdditionalFilter(self, filter_):
        self.extFilter = filter_
        self.__applyFilter()
    
    def __applyFilter(self):
        if self.intFilter and self.extFilter:
            combinedFilter = self.intFilter + " AND " + self.extFilter
        else:
            combinedFilter = self.intFilter + self.extFilter
        super(CollectionModel, self).setFilter(combinedFilter)

class Collection(QtCore.QObject):
    def __init__(self, reference, parent=None):
        super(Collection, self).__init__(parent)

        self.reference = reference
        self.db = QSqlDatabase.addDatabase('QSQLITE')
        self._pages = None
        self.fileName = None
        
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
        elif field.type == Type.Status:
            type_ = 'CHAR'
        elif field.type == Type.DateTime:
            type_ = 'CHAR'
        elif field.type == Type.EdgeImage:
            type_ = 'BLOB'
        else:
            raise
        
        return field.name + ' ' + type_

    def getFileName(self):
        return QtCore.QDir(self.fileName).absolutePath()
    
    def getCollectionName(self):
        return Collection.fileNameToCollectionName(self.fileName)
    
    def model(self):
        return self.createModel()
    
    def pages(self):
        return self._pages
    
    def createModel(self):
        model = CollectionModel(self.reference, None, self.db, self.fields)
        model.title = self.getCollectionName()
        model.setEditStrategy(QSqlTableModel.OnManualSubmit)
        model.setTable('coins')
        model.select()
        for field in self.fields:
            model.setHeaderData(field.id, QtCore.Qt.Horizontal, field.title)
        
        return model
    
    def createReference(self):
        sections = self.reference.allSections()
        progressDlg = QtGui.QProgressDialog(self.tr("Updating reference"), self.tr("Cancel"), 0, len(sections), self.parent())
        progressDlg.setWindowModality(QtCore.Qt.WindowModal)
        progressDlg.setMinimumDuration(250)

        for progress, columnName in enumerate(sections):
            progressDlg.setValue(progress)
            if progressDlg.wasCanceled():
                break

            refSection = self.reference.section(columnName)
            if isinstance(refSection, CrossReferenceSection):
                rel = refSection.model.relationModel(1)
                for i in range(rel.rowCount()):
                    data = rel.data(rel.index(i, rel.fieldIndex('value')))
                    parentId = rel.data(rel.index(i, rel.fieldIndex('id')))
                    query = QSqlQuery(self.db)
                    sql = "SELECT DISTINCT %s FROM coins WHERE %s<>'' AND %s IS NOT NULL AND %s=?" % (columnName, columnName, columnName, refSection.parentName)
                    query.prepare(sql)
                    query.addBindValue(data)
                    query.exec_()
                    refSection.fillFromQuery(parentId, query)
            else:
                sql = "SELECT DISTINCT %s FROM coins WHERE %s<>'' AND %s IS NOT NULL" % (columnName, columnName, columnName)
                query = QSqlQuery(sql, self.db)
                refSection.fillFromQuery(query)
    
        progressDlg.setValue(len(sections))

    def referenceMenu(self, parent=None):
        createReferenceAct = QtGui.QAction(self.tr("Fill from collection"), parent)
        createReferenceAct.triggered.connect(self.createReference)
        
        return createReferenceAct
    
    @staticmethod
    def fileNameToCollectionName(fileName):
        file = QtCore.QFileInfo(fileName)
        return file.baseName()
