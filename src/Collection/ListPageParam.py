from PyQt4 import QtCore
from PyQt4.QtSql import QSqlQuery

from .CollectionFields import CollectionFields

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
            record = query.record()
            fieldId = record.value('fieldid')
            enabled = record.value('enabled')
            self.columns.append((fieldId, enabled))
        
        # Create default parameters
        if not self.columns:
            for field in CollectionFields().fields:
                if field.name == 'id':  # skip ID field
                    continue

                enabled = False
                # TODO: Customize default fields
                if field.name in ['title', 'value', 'unit', 'country', 'year']:
                    enabled = True
                self.columns.append((field.id, enabled))

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
            query.prepare("INSERT INTO lists (pageid, fieldid, position, enabled) "
                          "VALUES (?, ?, ?, ?)")
            query.addBindValue(self.pageId)
            query.addBindValue(param[0])
            query.addBindValue(position)
            query.addBindValue(int(param[1]))
            query.exec_()
        
        self.db.commit()

    def remove(self):
        query = QSqlQuery(self.db)
        query.prepare("DELETE FROM lists WHERE pageid=?")
        query.addBindValue(self.pageId)
        query.exec_()
        