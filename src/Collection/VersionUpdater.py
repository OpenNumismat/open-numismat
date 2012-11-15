from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import Qt
from PyQt4.QtGui import QApplication
from PyQt4.QtSql import QSqlQuery

class Updater(QtCore.QObject):
    def __init__(self, collection):
        self.collection = collection
        self.currentVersion = int(self.collection.settings.Settings['Version'])
    
    def check(self):
        return self.currentVersion != self.collection.settings.DefaultSettings['Version']
    
    def update(self):
        if self.check():
            if self.__begin():
                if self.currentVersion < 2:
                    updater = UpdaterTo2(self.collection)
                    updater.update()
                
                self.__finalize()
    
    def __begin(self):
        return self.collection.backup()
    
    def __finalize(self):
        # TODO: Move vacuum here
        pass

class _Updater(QtCore.QObject):
    def __init__(self, collection):
        self.collection = collection
        self.db = collection.db
        
        self.totalCount = self.getTotalCount()
        
        self.progressDlg = QtGui.QProgressDialog(QApplication.translate('_Updater', "Updating records"),
                                            None, 0, self.totalCount,
                                            collection.parent(), Qt.WindowTitleHint)
        self.progressDlg.setWindowModality(Qt.WindowModal)
        self.progressDlg.setMinimumDuration(250)
        self.progress = 0
    
    def getTotalCount(self):
        raise NotImplementedError
    
    def update(self):
        pass
    
    def _begin(self):
        pass
    
    def _updateRecord(self):
        self.progressDlg.setValue(self.progress)
        self.progress = self.progress + 1
    
    def _finish(self):
        self.progressDlg.setValue(self.totalCount)

class UpdaterTo2(_Updater):
    def __init__(self, collection):
        super(UpdaterTo2, self).__init__(collection)
    
    def getTotalCount(self):
        sql = "SELECT count(*) FROM coins"
        query = QSqlQuery(sql, self.db)
        query.first()
        return query.record().value(0) + 2 # Add 2 for updating progress label
    
    def update(self):
        self._begin()
    
        self.db.transaction()
        
        fields = ['quantity', 'url', 'barcode']
        for field in fields:
            fieldDesc = getattr(self.collection.fields, field)
            fieldDesc.enabled = True
            query = QSqlQuery(self.db)
            query.prepare("""INSERT INTO fields (id, title, enabled)
                VALUES (?, ?, ?)""")
            query.addBindValue(fieldDesc.id)
            query.addBindValue(fieldDesc.title)
            query.addBindValue(int(fieldDesc.enabled))
            query.exec_()
            
            self.collection.fields.userFields.append(fieldDesc)
        
        sql = """ALTER TABLE coins RENAME TO tmp_coins"""
        QSqlQuery(sql, self.db)
        
        self.collection.createCoinsTable()
    
        query = QSqlQuery("SELECT * FROM tmp_coins", self.db)
        while query.next():
            self._updateRecord()
            
            record = query.record()
            
            imgIds = {}
            fields = ['obverseimg', 'reverseimg', 'edgeimg', 'photo1', 'photo2', 'photo3', 'photo4']
            for field in fields:
                if not record.isNull(field):
                    image_query = QSqlQuery(self.db)
                    image_query.prepare("""INSERT INTO images (title, image)
                            VALUES (?, ?)""")
                    fieldDesc = getattr(self.collection.fields, field)
                    image_query.addBindValue(fieldDesc.title)
                    image_query.addBindValue(record.value(field))
                    image_query.exec_()
                    imgIds[field] = image_query.lastInsertId()
                else:
                    imgIds[field] = None
    
            coin_query = QSqlQuery(self.db)
            coin_query.prepare("""INSERT INTO coins (title, value, unit, country, year, period, mint, mintmark, issuedate, type, series, subjectshort, status, material, fineness, shape, diameter, thickness, weight, grade, edge, edgelabel, obvrev, quality, mintage, dateemis, catalognum1, catalognum2, catalognum3, catalognum4, rarity, price1, price2, price3, price4, variety, obversevar, reversevar, edgevar, paydate, payprice, totalpayprice, saller, payplace, payinfo, saledate, saleprice, totalsaleprice, buyer, saleplace, saleinfo, note, image, obverseimg, obversedesign, obversedesigner, reverseimg, reversedesign, reversedesigner, edgeimg, subject, photo1, photo2, photo3, photo4, defect, storage, features, createdat, updatedat)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""")
            coin_query.addBindValue(record.value('title'))
            coin_query.addBindValue(record.value('value'))
            coin_query.addBindValue(record.value('unit'))
            coin_query.addBindValue(record.value('country'))
            coin_query.addBindValue(record.value('year'))
            coin_query.addBindValue(record.value('period'))
            coin_query.addBindValue(record.value('mint'))
            coin_query.addBindValue(record.value('mintmark'))
            coin_query.addBindValue(record.value('issuedate'))
            coin_query.addBindValue(record.value('type'))
            coin_query.addBindValue(record.value('series'))
            coin_query.addBindValue(record.value('subjectshort'))
            coin_query.addBindValue(record.value('status'))
            coin_query.addBindValue(record.value('metal'))
            coin_query.addBindValue(record.value('fineness'))
            coin_query.addBindValue(record.value('form'))
            coin_query.addBindValue(record.value('diameter'))
            coin_query.addBindValue(record.value('thick'))
            coin_query.addBindValue(record.value('mass'))
            coin_query.addBindValue(record.value('grade'))
            coin_query.addBindValue(record.value('edge'))
            coin_query.addBindValue(record.value('edgelabel'))
            coin_query.addBindValue(record.value('obvrev'))
            coin_query.addBindValue(record.value('quality'))
            coin_query.addBindValue(record.value('mintage'))
            coin_query.addBindValue(record.value('dateemis'))
            coin_query.addBindValue(record.value('catalognum1'))
            coin_query.addBindValue(record.value('catalognum2'))
            coin_query.addBindValue(record.value('catalognum3'))
            coin_query.addBindValue(record.value('catalognum4'))
            coin_query.addBindValue(record.value('rarity'))
            coin_query.addBindValue(record.value('price1'))
            coin_query.addBindValue(record.value('price2'))
            coin_query.addBindValue(record.value('price3'))
            coin_query.addBindValue(record.value('price4'))
            coin_query.addBindValue(record.value('variety'))
            coin_query.addBindValue(record.value('obversevar'))
            coin_query.addBindValue(record.value('reversevar'))
            coin_query.addBindValue(record.value('edgevar'))
            coin_query.addBindValue(record.value('paydate'))
            coin_query.addBindValue(record.value('payprice'))
            coin_query.addBindValue(record.value('totalpayprice'))
            coin_query.addBindValue(record.value('saller'))
            coin_query.addBindValue(record.value('payplace'))
            coin_query.addBindValue(record.value('payinfo'))
            coin_query.addBindValue(record.value('saledate'))
            coin_query.addBindValue(record.value('saleprice'))
            coin_query.addBindValue(record.value('totalsaleprice'))
            coin_query.addBindValue(record.value('buyer'))
            coin_query.addBindValue(record.value('saleplace'))
            coin_query.addBindValue(record.value('saleinfo'))
            coin_query.addBindValue(record.value('note'))
            coin_query.addBindValue(record.value('image'))
            coin_query.addBindValue(imgIds['obverseimg'])
            coin_query.addBindValue(record.value('obversedesign'))
            coin_query.addBindValue(record.value('obversedesigner'))
            coin_query.addBindValue(imgIds['reverseimg'])
            coin_query.addBindValue(record.value('reversedesign'))
            coin_query.addBindValue(record.value('reversedesigner'))
            coin_query.addBindValue(imgIds['edgeimg'])
            coin_query.addBindValue(record.value('subject'))
            coin_query.addBindValue(imgIds['photo1'])
            coin_query.addBindValue(imgIds['photo2'])
            coin_query.addBindValue(imgIds['photo3'])
            coin_query.addBindValue(imgIds['photo4'])
            coin_query.addBindValue(record.value('defect'))
            coin_query.addBindValue(record.value('storage'))
            coin_query.addBindValue(record.value('features'))
            coin_query.addBindValue(record.value('createdat'))
            coin_query.addBindValue(record.value('updatedat'))
            if not coin_query.exec_():
                print(coin_query.lastError().text())
        
        self.progressDlg.setLabelText(QApplication.translate('UpdaterTo2', "Saving..."))
        self._updateRecord()
        
        sql = """DROP TABLE tmp_coins"""
        QSqlQuery(sql, self.db)
        
        self.collection.settings.Settings['Version'] = 2
        self.collection.settings.save()
        
        self.db.commit()

        self.progressDlg.setLabelText(QApplication.translate('UpdaterTo2', "Vacuum..."))
        self._updateRecord()

        self.collection.vacuum()
    
        self._finish()

def updateCollection(collection):
    updater = Updater(collection)
    if updater.check():
        updater.update()
