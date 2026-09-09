from PySide6.QtSql import QSqlQuery

from OpenNumismat.Settings import BaseSettings
from OpenNumismat.Tools.db_utils import DBTransaction, execute_query


class StatisticsParam(BaseSettings):
    Default = {
            'showed': False,
            'chart': None,
            'fieldid': None,
            'subfieldid': None,
            'items': None,
            'period': None,
            'color': False
    }

    def __init__(self, page):
        super().__init__()

        self.pageId = page.id
        self.db = page.db
        if 'statistics' not in self.db.tables():
            self.create()

        self._load()

    def keys(self):
        return self.Default.keys()

    def _getValue(self, key):
        return self.Default[key]

    def _saveValue(self, _key, _val):
        self.save()

    def _load(self):
        query = QSqlQuery(self.db)
        params = (self.pageId,)
        execute_query(query, "SELECT * FROM statistics WHERE pageid=?", params)
        if query.first():
            record = query.record()
            self.__setitem__('showed', bool(record.value('showed')))
            self.__setitem__('chart', record.value('chart'))
            self.__setitem__('fieldid', record.value('fieldid'))
            self.__setitem__('subfieldid', record.value('subfieldid'))
            self.__setitem__('items', record.value('items'))
            self.__setitem__('period', record.value('period'))
            self.__setitem__('color', bool(record.value('color')))

        self.autoSave = True

    def save(self):
        with DBTransaction(self.db):
            self.remove()

            query = QSqlQuery(self.db)
            sql = ("INSERT INTO statistics (pageid, showed, chart, fieldid, subfieldid, items, period, color)"
                   " VALUES (?, ?, ?, ?, ?, ?, ?, ?)")
            params = (
                self.pageId,
                int(self.__getitem__('showed')),
                self.__getitem__('chart'),
                self.__getitem__('fieldid'),
                self.__getitem__('subfieldid'),
                self.__getitem__('items'),
                self.__getitem__('period'),
                int(self.__getitem__('color'))
            )
            execute_query(query, sql, params)

    def remove(self):
        query = QSqlQuery(self.db)
        params = (self.pageId,)
        execute_query(query, "DELETE FROM statistics WHERE pageid=?", params)

    def create(self):
        query = QSqlQuery(self.db)
        sql = """CREATE TABLE statistics (
            id INTEGER NOT NULL PRIMARY KEY,
            pageid INTEGER,
            showed INTEGER,
            chart TEXT,
            fieldid INTEGER,
            subfieldid INTEGER,
            items TEXT,
            period TEXT,
            color INTEGER)"""
        execute_query(query, sql)
