import os
import urllib3

from PySide6.QtCore import QObject, QByteArray, QStandardPaths, Qt
from PySide6.QtGui import QCursor
from PySide6.QtSql import QSqlDatabase, QSqlQuery
from PySide6.QtWidgets import QApplication, QMessageBox

import OpenNumismat
from OpenNumismat import version

TIMEOUT = 10


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
            QApplication.setOverrideCursor(QCursor(Qt.ArrowCursor))
            QMessageBox.warning(self.parent(), self.tr("Downloading"), self.tr("Can't open cache"))
            QApplication.restoreOverrideCursor()
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
        query.exec()
        if query.first():
            record = query.record()
            data = record.value('data')
            if isinstance(data, QByteArray):
                data = bytes(data)
            elif isinstance(data, str):
                data = data.encode('utf-8')
            return data

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
        query.exec()

    def _compact(self):
        if self.db:
            sql = "DELETE FROM cache WHERE createdat < date('now', '-10 day')"
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
            try:
                os.remove(file_name)
            except PermissionError:
                return False

        return True


class CachedPoolManager(QObject):

    def __init__(self, parent=None):
        super().__init__(parent)

        self._http = None
        self._cache = None
        self._available = True

    def get(self, url, timeout=None, retries=None, headers=None, cache=True):
        if cache:
            if not self._cache:
                self._cache = Cache(self.parent())

            cached_data = self._cache.get(url)
            if cached_data:
                return cached_data

        if not self._available:
            return None

        if not self._http:
            self._http = self._createHttp()

        try:
            request_kwargs = {}
            if timeout is not None:
                request_kwargs['timeout'] = timeout
            if retries is not None:
                request_kwargs['retries'] = retries
            if headers is not None:
                request_kwargs['headers'] = headers
            response = self._http.request("GET", url, **request_kwargs)
        except (urllib3.exceptions.MaxRetryError,
                urllib3.exceptions.ReadTimeoutError,
                urllib3.exceptions.ProtocolError):
            QApplication.setOverrideCursor(QCursor(Qt.ArrowCursor))
            QMessageBox.warning(self.parent(), self.tr("Downloading"), self.tr("Server not response"))
            QApplication.restoreOverrideCursor()

            self._available = False
            return None

        if response.status == 429:
            QApplication.setOverrideCursor(QCursor(Qt.ArrowCursor))
            QMessageBox.warning(self.parent(), self.tr("Downloading"),
                                self.tr("Too many requests. Try later"))
            QApplication.restoreOverrideCursor()

            self._available = False
            return None

        response_data = response.data
        if response.status == 200 and response_data:
            if cache:
                self._cache.set(url, response_data)

            return response_data
        else:
            QApplication.setOverrideCursor(QCursor(Qt.ArrowCursor))
            QMessageBox.warning(self.parent(), self.tr("Downloading"), self.tr("Server not response"))
            QApplication.restoreOverrideCursor()

            self._available = False
            return None

    def isAvailable(self):
        return self._available

    def _createHttp(self):
        urllib3.disable_warnings()
        retries = urllib3.Retry(1)
        timeout = urllib3.Timeout(connect=2.5, read=TIMEOUT)
        http = urllib3.PoolManager(num_pools=3,
                                   headers={'User-Agent': version.AppName},
                                   timeout=timeout,
                                   retries=retries,
                                   cert_reqs="CERT_NONE")
        return http

    def close(self):
        if self._http:
            self._http.clear()
            self._http = None
        if self._cache:
            self._cache.close()
            self._cache = None
