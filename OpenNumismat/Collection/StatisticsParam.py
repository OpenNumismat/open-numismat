from PyQt5.QtSql import QSqlDatabase, QSqlQuery

from OpenNumismat.Settings import BaseSettings


class StatisticsParam(BaseSettings):
    Default = {
            'showed': False,
            'chart': None,
            'fieldid': None,
            'subfieldid': None,
            'items': None,
            'period': None,
    }

    def __init__(self, page):
        super().__init__(autoSave=True)

        self.pageId = page.id
        self.db = page.db
        if 'statistics' not in self.db.tables():
            self.create(self.db)

        self._load()

    def keys(self):
        return self.Default.keys()

    def _getValue(self, key):
        return self.Default[key]

    def _saveValue(self, _key, _val):
        self.save()

    def _load(self):
        query = QSqlQuery(self.db)
        query.prepare("SELECT * FROM statistics WHERE pageid=?")
        query.addBindValue(self.pageId)
        query.exec_()
        if query.first():
            record = query.record()
            self.__setitem__('showed', bool(record.value('showed')))
            self.__setitem__('chart', record.value('chart'))
            self.__setitem__('fieldid', record.value('fieldid'))
            self.__setitem__('subfieldid', record.value('subfieldid'))
            self.__setitem__('items', record.value('items'))
            self.__setitem__('period', record.value('period'))

    def save(self):
        self.db.transaction()

        self.remove()

        query = QSqlQuery(self.db)
        query.prepare("INSERT INTO statistics (pageid, showed, chart, fieldid, subfieldid, items, period)"
                      " VALUES (?, ?, ?, ?, ?, ?, ?)")
        query.addBindValue(self.pageId)
        query.addBindValue(int(self.__getitem__('showed')))
        query.addBindValue(self.__getitem__('chart'))
        query.addBindValue(self.__getitem__('fieldid'))
        query.addBindValue(self.__getitem__('subfieldid'))
        query.addBindValue(self.__getitem__('items'))
        query.addBindValue(self.__getitem__('period'))
        query.exec_()

        self.db.commit()

    def remove(self):
        query = QSqlQuery(self.db)
        query.prepare("DELETE FROM statistics WHERE pageid=?")
        query.addBindValue(self.pageId)
        query.exec_()

    @staticmethod
    def create(db=QSqlDatabase()):
        sql = """CREATE TABLE statistics (
            id INTEGER NOT NULL PRIMARY KEY,
            pageid INTEGER,
            showed INTEGER,
            chart TEXT,
            fieldid INTEGER,
            subfieldid INTEGER,
            items TEXT,
            period TEXT)"""
        QSqlQuery(sql, db)
