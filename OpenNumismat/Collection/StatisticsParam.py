from PyQt5 import QtCore
from PyQt5.QtSql import QSqlDatabase, QSqlQuery


class StatisticsParam(QtCore.QObject):
    def __init__(self, page):
        QtCore.QObject.__init__(self, page)

        self.pageId = page.id
        self.db = page.db
        if 'statistics' not in self.db.tables():
            self.create(self.db)

        self._params = {}
        self._load()

    def params(self):
        return self._params

    def clear(self):
        # self._params.clear()
        self._params['showed'] = False
        self._params['chart'] = None
        self._params['fieldid'] = None
        self._params['subfieldid'] = None
        self._params['items'] = None
        self._params['period'] = None

    def _load(self):
        self.clear()

        query = QSqlQuery(self.db)
        query.prepare("SELECT * FROM statistics WHERE pageid=?")
        query.addBindValue(self.pageId)
        query.exec_()
        if query.first():
            self._params['showed'] = bool(query.record().value('showed'))
            self._params['chart'] = query.record().value('chart')
            self._params['fieldid'] = query.record().value('fieldid')
            self._params['subfieldid'] = query.record().value('subfieldid')
            self._params['items'] = query.record().value('items')
            self._params['period'] = query.record().value('period')

    def save(self):
        self.db.transaction()

        self.remove()

        query = QSqlQuery(self.db)
        query.prepare("INSERT INTO statistics (pageid, showed, chart, fieldid, subfieldid, items, period)"
                      " VALUES (?, ?, ?, ?, ?, ?, ?)")
        query.addBindValue(self.pageId)
        query.addBindValue(int(self._params['showed']))
        query.addBindValue(self._params['chart'])
        query.addBindValue(self._params['fieldid'])
        query.addBindValue(self._params['subfieldid'])
        query.addBindValue(self._params['items'])
        query.addBindValue(self._params['period'])
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
