import os

from PySide6.QtCore import QObject, QByteArray, QStandardPaths
from PySide6.QtSql import QSqlDatabase, QSqlQuery
from PySide6.QtWidgets import QMessageBox

import OpenNumismat
from OpenNumismat import version


class Cache(QObject):
    FILE_NAME = "opennumismat-cache.sqlite3"

    def __init__(self, parent=None):
        super().__init__(parent)

        self.db = self.open()
        self._compact()

    def open(self):
        os.makedirs(os.path.dirname(self._file_name()), exist_ok=True)

        db = QSqlDatabase.addDatabase('QSQLITE', 'cache')
        db.setDatabaseName(self._file_name())
        if not db.open():
            QMessageBox.warning(self.parent(), self.tr("Import"), self.tr("Can't open cache"))
            return None

        QSqlQuery("PRAGMA synchronous=OFF", db)
        QSqlQuery("PRAGMA journal_mode=OFF", db)

        if 'cache' not in db.tables():
            sql = "CREATE TABLE cache (\
                id INTEGER PRIMARY KEY,\
                url TEXT, data BLOB,\
                createdat TEXT DEFAULT CURRENT_DATE)"
            QSqlQuery(sql, db)
            sql = "CREATE INDEX index_cache_url ON cache (url)"
            QSqlQuery(sql, db)

        return db

    def close(self):
        if self.db:
            self.db.close()
            self.db = None
        QSqlDatabase.removeDatabase('cache')

    def get(self, url):
        if not self.db:
            return None

        query = QSqlQuery(self.db)
        query.prepare("SELECT data FROM cache WHERE url=?")
        query.addBindValue(url)
        query.exec_()
        if query.first():
            record = query.record()
            return record.value('data')

        return None

    def set(self, url, data):
        if not self.db:
            return

        if not data:
            return

        query = QSqlQuery(self.db)
        query.prepare("INSERT INTO cache (url, data)"
                      " VALUES (?, ?)")
        query.addBindValue(url)
        if isinstance(data, bytes):
            data = QByteArray(data)
        query.addBindValue(data)
        query.exec_()

    def _compact(self):
        if self.db:
            sql = "DELETE FROM cache WHERE createdat < date('now', '-30 day')"
            QSqlQuery(sql, self.db)

    @staticmethod
    def _file_name():
        if version.Portable:
            path = OpenNumismat.HOME_PATH
        else:
            path = QStandardPaths.standardLocations(QStandardPaths.AppLocalDataLocation)[0]
        return os.path.join(path, Cache.FILE_NAME)

    @staticmethod
    def clear():
        file_name = Cache._file_name()
        if os.path.exists(file_name):
            os.remove(file_name)
