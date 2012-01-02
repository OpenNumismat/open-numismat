from PyQt4 import QtCore
from PyQt4.QtSql import QSqlDatabase, QSqlQuery

class TreeParam(QtCore.QObject):
    def __init__(self, page):
        QtCore.QObject.__init__(self, page)
        
        self.pageId = page.id
        self.db = page.db
        if 'treeparam' not in self.db.tables():
            self.create(self.db)
        
        self.fields = page.fields
        self._params = []
        self._load()
        if not self._params:
            allFields = self.fields
            self._params = [[allFields.type,], [allFields.country,], [allFields.period,],
                            [allFields.value, allFields.unit],
                            [allFields.series,], [allFields.year,]]
    
    def params(self):
        return self._params
    
    def clear(self):
        del self._params[:]   # clearing list
    
    def append(self, fields):
        if not isinstance(fields, list):
            fields = [fields,]
        
        self._params.append(fields)
    
    def usedFieldNames(self):
        names = []
        for param in self._params:
            names.extend([field.name for field in param])
        
        return names
    
    def fieldNames(self, index):
        if index >= len(self._params):
            return None
        
        names = [field.name for field in self._params[index]]
        return names
    
    def _load(self):
        self.clear()
        count = 0
        
        query = QSqlQuery(self.db)
        query.prepare("SELECT COUNT(DISTINCT position) FROM treeparam WHERE pageid=?")
        query.addBindValue(self.pageId)
        query.exec_()
        if query.first():
            count = query.record().value(0)
        
        if count:
            for _ in range(count):
                self._params.append([])
            
            query = QSqlQuery(self.db)
            query.prepare("SELECT * FROM treeparam WHERE pageid=?")
            query.addBindValue(self.pageId)
            query.exec_()
            
            while query.next():
                record = query.record()
                position = record.value('position')
                fieldId = record.value('fieldid')
                self._params[position].append(self.fields.field(fieldId))
    
    def save(self):
        self.db.transaction()
        
        self.remove()
        
        for position, param in enumerate(self.params()):
            for field in param:
                query = QSqlQuery(self.db)
                query.prepare("""INSERT INTO treeparam (pageid, fieldid, position)
                                 VALUES (?, ?, ?)""")
                query.addBindValue(self.pageId)
                query.addBindValue(field.id)
                query.addBindValue(position)
                query.exec_()
        
        self.db.commit()
    
    def remove(self):
        query = QSqlQuery(self.db)
        query.prepare("DELETE FROM treeparam WHERE pageid=?")
        query.addBindValue(self.pageId)
        query.exec_()
    
    def __iter__(self):
        self.index = 0
        return self
    
    def __next__(self):
        if self.index == len(self._params):
            raise StopIteration
        self.index = self.index + 1
        return self._params[self.index-1]
    
    @staticmethod
    def create(db=QSqlDatabase()):
        sql = """CREATE TABLE treeparam (
            id INTEGER NOT NULL PRIMARY KEY,
            pageid INTEGER,
            fieldid INTEGER,
            position INTEGER)"""
        QSqlQuery(sql, db)
