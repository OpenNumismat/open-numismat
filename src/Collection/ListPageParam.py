from PyQt4 import QtCore
from PyQt4.QtSql import QSqlQuery, QSqlRecord

from .CollectionFields import CollectionFields

class ColumnListParam:
    def __init__(self, arg1, arg2=None, arg3=None):
        if isinstance(arg1, QSqlRecord):
            record = arg1
            for name in ['fieldid', 'enabled', 'width']:
                setattr(self, name, record.value(name))
        else:
            fieldId, enabled, width = arg1, arg2, arg3
            self.fieldid = fieldId
            self.enabled = enabled
            self.width = width

class ListPageParam(QtCore.QObject):
    def __init__(self, pageId, db, parent=None):
        super(ListPageParam, self).__init__(parent)
        
        self.pageId = pageId
        self.db = db
        sql = "CREATE TABLE IF NOT EXISTS lists (\
            id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,\
            pageid INTEGER,\
            fieldid INTEGER,\
            position INTEGER,\
            enabled INTEGER,\
            width INTEGER)"
        QSqlQuery(sql, self.db)

        query = QSqlQuery(self.db)
        query.prepare("SELECT * FROM lists WHERE pageid=? ORDER BY position")
        query.addBindValue(pageId)
        query.exec_()
        self.columns = []
        while query.next():
            param = ColumnListParam(query.record())
            self.columns.append(param)
        
        # Create default parameters
        if not self.columns:
            for field in CollectionFields().fields:
                if field.name == 'id':  # skip ID field
                    continue

                enabled = False
                # TODO: Customize default fields
                if field.name in ['title', 'value', 'unit', 'country', 'year']:
                    enabled = True
                param = ColumnListParam(field.id, enabled)
                self.columns.append(param)

    def save(self):
        self.db.transaction()
        
        # Remove old values
        query = QSqlQuery(self.db)
        query.prepare("DELETE FROM lists WHERE pageid=?")
        query.addBindValue(self.pageId)
        query.exec_()
        
        # Save new all
        for position, param in enumerate(self.columns):
            query = QSqlQuery(self.db)
            query.prepare("INSERT INTO lists (pageid, fieldid, position, enabled, width) "
                          "VALUES (?, ?, ?, ?, ?)")
            query.addBindValue(self.pageId)
            query.addBindValue(param.fieldid)
            query.addBindValue(position)
            query.addBindValue(int(param.enabled))
            query.addBindValue(param.width)
            query.exec_()
        
        self.db.commit()

    def remove(self):
        query = QSqlQuery(self.db)
        query.prepare("DELETE FROM lists WHERE pageid=?")
        query.addBindValue(self.pageId)
        query.exec_()
