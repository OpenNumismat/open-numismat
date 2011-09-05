from PyQt4 import QtGui, QtCore
from PyQt4.QtSql import *

class Collection(QtCore.QObject):
    def __init__(self, parent=None):
        super(Collection, self).__init__(parent)

        self.db = QSqlDatabase.addDatabase('QSQLITE')
        
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
        return True
    
    def create(self, fileName):
        self.db.setDatabaseName(fileName)
        if not self.db.open():
            print(self.db.lastError().text())
            QtGui.QMessageBox.critical(self.parent(), self.tr("Create collection"), self.tr("Can't open collection"))
            return False
        
        self.fileName = fileName

        QSqlQuery("CREATE TABLE IF NOT EXISTS coins \
            (id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,\
             title CHAR NOT NULL, \
             value NUMERIC(10,2), \
             unit CHAR, \
             country CHAR, \
             year NUMERIC(4), \
             period CHAR, \
             mint CHAR, \
             mintmark CHAR(10), \
             issuedate CHAR, \
             type CHAR, \
             series CHAR, \
             metal CHAR, \
             fineness NUMERIC(3), \
             form CHAR, \
             diameter NUMERIC(10,3), \
             thick NUMERIC(10,3), \
             mass NUMERIC(10,3), \
             grade CHAR, \
             edge CHAR, \
             edgelabel CHAR, \
             obvrev CHAR, \
             state CHAR,\
             mintage INTEGER, \
             dateemis CHAR, \
             catalognum1 CHAR,\
             catalognum2 CHAR,\
             catalognum3 CHAR,\
             rarity CHAR(10), \
             price1 NUMERIC(10,2), \
             price2 NUMERIC(10,2), \
             price3 NUMERIC(10,2), \
             price4 NUMERIC(10,2), \
             price5 NUMERIC(10,2), \
             price6 NUMERIC(10,2), \
             obversevar TEXT, \
             reversevar TEXT, \
             edgevar TEXT, \
             paydate CHAR, \
             payprice NUMERIC(10,2), \
             saller CHAR, \
             payplace CHAR, \
             payinfo TEXT, \
             saledate CHAR, \
             saleprice NUMERIC(10,2), \
             buyer CHAR, \
             saleplace CHAR, \
             saleinfo TEXT, \
             note TEXT, \
             obverseimg BLOB, \
             obversedesign TEXT, \
             obversedesigner CHAR, \
             reverseimg BLOB, \
             reversedesign TEXT, \
             reversedesigner CHAR, \
             edgeimg BLOB, \
             subject TEXT, \
             photo1 BLOB, \
             photo2 BLOB, \
             photo3 BLOB, \
             photo4 BLOB \
            )", self.db)
        
        return True

    def getFileName(self):
        return self.fileName
    
    def getCollectionName(self):
        return Collection.fileNameToCollectionName(self.fileName)
    
    def model(self):
        model = QSqlTableModel(None, self.db)
        model.setEditStrategy(QSqlTableModel.OnManualSubmit)
        return model
    
    @staticmethod
    def fileNameToCollectionName(fileName):
        file = QtCore.QFileInfo(fileName)
        return file.baseName()
