from PySide6.QtCore import QObject
from PySide6.QtSql import QSqlQuery

from OpenNumismat.Tools.db_utils import DBTransaction, execute_query


class TreeParam(QObject):

    def __init__(self, page):
        super().__init__(page)

        self.pageId = page.id
        self.db = page.db
        if 'treeparam' not in self.db.tables():
            self.create()

        self.fields = page.fields
        self._params = []
        self._load()
        if not self._params:
            allFields = self.fields
            self._params = [[allFields.type, ], [allFields.country, ],
                            [allFields.period, ],
                            [allFields.value, allFields.unit],
                            [allFields.series, ], [allFields.year, ]]

    def params(self):
        return self._params

    def clear(self):
        del self._params[:]  # clearing list

    def append(self, fields):
        if not isinstance(fields, list):
            fields = [fields, ]

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
        sql = ("SELECT COUNT(DISTINCT position)"
               " FROM treeparam WHERE pageid=?")
        params = (self.pageId,)
        execute_query(query, sql, params)
        if query.first():
            count = query.record().value(0)

        if count:
            for _ in range(count):
                self._params.append([])

            sql = "SELECT * FROM treeparam WHERE pageid=?"
            params = (self.pageId,)
            execute_query(query, sql, params)

            while query.next():
                record = query.record()
                position = record.value('position')
                fieldId = record.value('fieldid')
                self._params[position].append(self.fields.field(fieldId))

    def save(self):
        with DBTransaction(self.db):
            self.remove()

            query = QSqlQuery(self.db)
            for position, param in enumerate(self.params()):
                for field in param:
                    sql = ("INSERT INTO treeparam (pageid, fieldid, position)"
                           " VALUES (?, ?, ?)")
                    params = (self.pageId, field.id, position)
                    execute_query(query, sql, params)

    def remove(self):
        query = QSqlQuery(self.db)
        params = (self.pageId,)
        execute_query(query, "DELETE FROM treeparam WHERE pageid=?", params)

    def __iter__(self):
        self.index = 0
        return self

    def __next__(self):
        if self.index == len(self._params):
            raise StopIteration
        self.index = self.index + 1
        return self._params[self.index - 1]

    def create(self):
        query = QSqlQuery(self.db)
        sql = """CREATE TABLE treeparam (
            id INTEGER NOT NULL PRIMARY KEY,
            pageid INTEGER,
            fieldid INTEGER,
            position INTEGER)"""
        execute_query(query, sql)
