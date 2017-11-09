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

    def _load(self):
        self.clear()

        query = QSqlQuery(self.db)
        query.prepare("SELECT showed, chart, fieldid, subfieldid FROM statistics WHERE pageid=?")
        query.addBindValue(self.pageId)
        query.exec_()
        if query.first():
            self._params['showed'] = bool(query.record().value(0))
            self._params['chart'] = query.record().value(1)
            self._params['fieldid'] = query.record().value(2)
            self._params['subfieldid'] = query.record().value(3)

    def save(self):
        self.db.transaction()

        self.remove()

        query = QSqlQuery(self.db)
        query.prepare("INSERT INTO statistics (pageid, showed, chart, fieldid, subfieldid)"
                      " VALUES (?, ?, ?, ?, ?)")
        query.addBindValue(self.pageId)
        query.addBindValue(int(self._params['showed']))
        query.addBindValue(self._params['chart'])
        query.addBindValue(self._params['fieldid'])
        query.addBindValue(self._params['subfieldid'])
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
            subfieldid INTEGER)"""
        QSqlQuery(sql, db)
