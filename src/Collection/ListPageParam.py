from PyQt4 import QtCore
from PyQt4.QtSql import QSqlQuery, QSqlRecord

from .CollectionFields import CollectionFields
from .HeaderFilterMenu import Filter

class ColumnListParam:
    def __init__(self, arg1, arg2=None, arg3=None):
        if isinstance(arg1, QSqlRecord):
            record = arg1
            for name in ['fieldid', 'enabled', 'width']:
                if record.isNull(name):
                    value = None
                else:
                    value = record.value(name)
                setattr(self, name, value)
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
        
        sql = "CREATE TABLE IF NOT EXISTS filters (\
            id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,\
            pageid INTEGER,\
            fieldid INTEGER,\
            value INTEGER,\
            blank INTEGER,\
            data INTEGER)"
        QSqlQuery(sql, self.db)
        
        query = QSqlQuery(self.db)
        query.prepare("SELECT * FROM filters WHERE pageid=?")
        query.addBindValue(pageId)
        query.exec_()
        self.filters = {}
        while query.next():
            fieldId = query.record().value('fieldid')
            if query.record().isNull('value'):
                value = None
            else:
                value = str(query.record().value('value'))
            if query.record().isNull('data'):
                data = None
            else:
                data = query.record().value('data')
            if query.record().isNull('blank'):
                blank = None
            else:
                blank = query.record().value('blank')
            filter = Filter(CollectionFields().fields[fieldId].name, value, data, blank)
            if fieldId in self.filters.keys():
                self.filters[fieldId].append(filter)
            else:
                self.filters[fieldId] = [filter,]

    def save(self):
        self.db.transaction()
        
        # Remove old values
        self.remove()
        
        # Save new all
        for position, param in enumerate(self.columns):
            query = QSqlQuery(self.db)
            query.prepare("INSERT INTO lists (pageid, fieldid, position, enabled, width) "
                          "VALUES (?, ?, ?, ?, ?)")
            query.addBindValue(self.pageId)
            query.addBindValue(param.fieldid)
            query.addBindValue(position)
            query.addBindValue(int(param.enabled))
            if not param.enabled:
                param.width = None
            query.addBindValue(param.width)
            query.exec_()

        for fieldId, columnFilters in self.filters.items():
            for filter in columnFilters:
                query = QSqlQuery(self.db)
                query.prepare("INSERT INTO filters (pageid, fieldid, value, blank, data) "
                              "VALUES (?, ?, ?, ?, ?)")
                query.addBindValue(self.pageId)
                query.addBindValue(fieldId)
                query.addBindValue(filter.value)
                if filter.blank:
                    blank = int(True)
                else:
                    blank = None
                query.addBindValue(blank)
                if filter.data:
                    data = int(True)
                else:
                    data = None
                query.addBindValue(data)
                query.exec_()
        
        self.db.commit()

    def remove(self):
        query = QSqlQuery(self.db)
        query.prepare("DELETE FROM lists WHERE pageid=?")
        query.addBindValue(self.pageId)
        query.exec_()

        query = QSqlQuery(self.db)
        query.prepare("DELETE FROM filters WHERE pageid=?")
        query.addBindValue(self.pageId)
        query.exec_()
