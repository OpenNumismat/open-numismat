import os
import tempfile

from PySide6.QtCore import QObject, QByteArray
from PySide6.QtSql import QSqlDatabase, QSqlQuery
from PySide6.QtWidgets import QMessageBox


class Cache(QObject):
    FILE_NAME = "opennumismat-cache.sqlite3"

    def __init__(self, parent=None):
        super().__init__(parent)

        self.db = self.open()
        self._compact()

    def open(self):
        db = QSqlDatabase.addDatabase('QSQLITE', 'cache')
        db.setDatabaseName(self._file_name())
        if not db.open():
            QMessageBox.warning(self, self.tr("Import"), self.tr("Can't open cache"))
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
        return os.path.join(tempfile.gettempdir(), Cache.FILE_NAME)

    @staticmethod
    def clear():
        file_name = Cache._file_name()
        if os.path.exists(file_name):
            os.remove(file_name)
