from PySide6.QtCore import QObject
from PySide6.QtSql import QSqlQuery, QSqlRecord

from OpenNumismat.Collection.HeaderFilterMenu import ColumnFilters, ValueFilter, DataFilter, BlankFilter
from OpenNumismat.Tools.db_utils import DBTransaction, execute_query


class ColumnListParam:
    def __init__(self, arg1, arg2=None, arg3=None):
        if isinstance(arg1, QSqlRecord):
            record = arg1
            for name in ('fieldid', 'enabled', 'width'):
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


class ListPageParam(QObject):
    def __init__(self, page):
        super().__init__(page)

        self.__lists_changed = False
        self.page = page
        self.db = page.db
        self.fields = page.fields

        if 'lists' not in self.db.tables():
            sql = """CREATE TABLE lists (
                id INTEGER PRIMARY KEY,
                pageid INTEGER,
                fieldid INTEGER,
                position INTEGER,
                enabled INTEGER,
                width INTEGER,
                sortorder INTEGER)"""
            QSqlQuery(sql, self.db)

        query = QSqlQuery(self.db)
        query.prepare("SELECT * FROM lists WHERE pageid=? ORDER BY position")
        query.addBindValue(self.page.id)
        query.exec()
        self.columns = []
        while query.next():
            param = ColumnListParam(query.record())
            field = self.fields.field(param.fieldid)
            if not field.enabled:
                param.enabled = 0
            self.columns.append(param)

        # Create default parameters
        if not self.columns:
            for field in self.fields.userFields:
                enabled = False
                if field.name in ('image', 'title', 'value', 'unit',
                                  'country', 'year', 'status'):
                    enabled = True
                param = ColumnListParam(field.id, enabled)
                self.columns.append(param)

        if 'filters' not in self.db.tables():
            sql = """CREATE TABLE filters (
                id INTEGER PRIMARY KEY,
                pageid INTEGER,
                fieldid INTEGER,
                value INTEGER,
                blank INTEGER,
                data INTEGER,
                revert INTEGER)"""
            QSqlQuery(sql, self.db)

        query = QSqlQuery(self.db)
        query.prepare("SELECT * FROM filters WHERE pageid=?")
        query.addBindValue(self.page.id)
        query.exec()
        self.filters = {}
        while query.next():
            fieldId = query.record().value('fieldid')
            column_name = self.fields.field(fieldId).name
            if not query.record().isNull('value'):
                value = str(query.record().value('value'))
                filter_ = ValueFilter(column_name, value)
            if not query.record().isNull('data'):
                if query.record().value('data'):
                    filter_ = DataFilter(column_name)
            if not query.record().isNull('blank'):
                if query.record().value('blank'):
                    filter_ = BlankFilter(column_name)
            if not query.record().isNull('revert'):
                if query.record().value('revert'):
                    filter_.revert = True

            if fieldId not in self.filters.keys():
                self.filters[fieldId] = ColumnFilters(column_name)
            self.filters[fieldId].addFilter(filter_)

    def clone(self):
        newList = ListPageParam(self.parent())
        newList.columns = list(self.columns)
        newList.filters = self.filters.copy()
        newList.mark_lists_changed()
        return newList

    def mark_lists_changed(self):
        self.__lists_changed = True

    def save(self):
        self.save_lists()
        self.save_filters()

    def save_lists(self, only_if_changed=False):
        if not only_if_changed or self.__lists_changed:
            with DBTransaction(self.db):
                # Remove old values
                self.__remove_lists()

                query = QSqlQuery(self.db)
                for position, param in enumerate(self.columns):
                    sql = ("INSERT INTO lists (pageid, fieldid, position, enabled, width)"
                           " VALUES (?, ?, ?, ?, ?)")
                    if not param.enabled:
                        param.width = None
                    params = (self.page.id, param.fieldid, position,
                              int(param.enabled), param.width)
                    execute_query(query, sql, params)

            self.__lists_changed = False

    def save_filters(self):
        with DBTransaction(self.db):
            # Remove old values
            self.__remove_filters()

            query = QSqlQuery(self.db)
            for fieldId, columnFilters in self.filters.items():
                for filter_ in columnFilters.filters():
                    sql = ("INSERT INTO filters (pageid, fieldid, value, blank, data, revert)"
                           " VALUES (?, ?, ?, ?, ?, ?)")
                    if filter_.isBlank():
                        blank = int(True)
                    else:
                        blank = None
                    if filter_.isData():
                        data = int(True)
                    else:
                        data = None
                    if filter_.isRevert():
                        revert = int(True)
                    else:
                        revert = None
                    params = (self.page.id, fieldId, filter_.value, blank, data, revert)
                    execute_query(query, sql, params)

    def remove(self):
        self.__remove_lists()
        self.__remove_filters()

    def __remove_lists(self):
        query = QSqlQuery(self.db)
        sql = "DELETE FROM lists WHERE pageid=?"
        params = (self.page.id,)
        execute_query(query, sql, params)

    def __remove_filters(self):
        query = QSqlQuery(self.db)
        sql = "DELETE FROM filters WHERE pageid=?"
        params = (self.page.id,)
        execute_query(query, sql, params)
