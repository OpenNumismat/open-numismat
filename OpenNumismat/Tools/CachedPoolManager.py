import os
import time
from urllib.parse import urlparse

from PySide6.QtCore import QObject, QByteArray, QEventLoop, QStandardPaths, Qt
from PySide6.QtGui import QCursor
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest
from PySide6.QtSql import QSqlDatabase, QSqlQuery
from PySide6.QtWidgets import QApplication, QMessageBox, QProgressDialog

import OpenNumismat
from OpenNumismat import version
from OpenNumismat.Settings import Settings

TIMEOUT = 10
SITES_CATALOG = {
    # "theratesapi.com": "The Rates API",
    # "api.db.nomics.world": "DBnomics",
    "opennumismat.duckdns.org": "OpenNumismat proxy",
    "i.colnect.net": "Colnect",
    "numismatics.org": "American Numismatic Society",
    "nomisma.org": "Nomisma.org",
    "api.numista.com": "Numista",
    "en.numista.com": "Numista",
    "nominatim.openstreetmap.org": "OpenStreetMap Nominatim",
    "static.coinidentifierai.com": "CoinSnap",
}


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

        sql_create_table = "CREATE TABLE cache (\
                id INTEGER PRIMARY KEY,\
                url TEXT, data BLOB,\
                expires_at INTEGER DEFAULT (strftime('%s', 'now') + 864000))"
        if 'cache' not in db.tables():
            QSqlQuery(sql_create_table, db)
            sql = "CREATE INDEX index_cache_url ON cache(url)"
            QSqlQuery(sql, db)
        else:
            sql = "SELECT count(*) FROM pragma_table_info('cache') WHERE name='expires_at'"
            query = QSqlQuery(sql, db)
            if query.first():
                data = query.record().value(0)
                query.finish()
                if data == 0:
                    QSqlQuery("DROP TABLE IF EXISTS cache", db)
                    QSqlQuery(sql_create_table, db)
                    sql = "CREATE INDEX index_cache_url ON cache(url)"
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

    def set(self, url, data, cache_expiry_days=None):
        if not self.db:
            return

        if not data:
            return

        query = QSqlQuery(self.db)
        if cache_expiry_days is not None:
            query.prepare("INSERT INTO cache (url, data, expires_at)"
                          " VALUES (?, ?, (strftime('%s', 'now') + ?))")
        else:
            query.prepare("INSERT INTO cache (url, data)"
                          " VALUES (?, ?)")
        query.addBindValue(url)
        if isinstance(data, bytes):
            data = QByteArray(data)
        query.addBindValue(data)
        if cache_expiry_days is not None:
            query.addBindValue(int(cache_expiry_days * 60 * 60 * 24))
        query.exec()

    def _compact(self):
        if self.db:
            sql = "DELETE FROM cache WHERE expires_at < strftime('%s', 'now')"
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

        self._cache = None
        self._available = True
        self._last_request_time = 0
        self._network_manager = None

    def get(self, url, timeout=None, retries=None, headers=None, cache=None, delay=None, quiet=False):
        if cache != False:
            if not self._cache:
                self._cache = Cache(self.parent())

            cached_data = self._cache.get(url)
            if cached_data:
                return cached_data

        if not self._available:
            return None

        self._createHttp()

        if delay:
            if self._last_request_time:
                elapsed_time = time.time() - self._last_request_time
                wait_time = delay - elapsed_time
                if wait_time > 0:
                    time.sleep(wait_time)
            self._last_request_time = time.time()

        loop = QEventLoop()

        request = QNetworkRequest(url)
        if timeout is not None:
            request.setTransferTimeout(timeout * 1000)
        else:
            request.setTransferTimeout(TIMEOUT * 1000)
        request.setRawHeader(b"User-Agent", version.UserAgent.encode('utf-8'))
        if headers:
            for key, val in headers.items():
                request.setRawHeader(key.encode('utf-8'), val.encode('utf-8'))
        reply = self._network_manager.get(request)

        reply.finished.connect(loop.quit)

        loop.exec()

        reply.deleteLater()
        http_code = reply.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute)
        if reply.error() == reply.NetworkError.NoError and http_code == 200:
            response_data = reply.readAll().data()
            if cache != False:
                self._cache.set(url, response_data, cache)

            return response_data
        elif reply.error() == reply.NetworkError.TimeoutError:
            if not quiet:
                result = self._showServerNotResponseMessage(url)
                if result == QMessageBox.Retry:
                    return self.get(url, timeout, retries, headers, cache)
        elif http_code == 429:
            if not quiet:
                result = self._showTooManyRequestsMessage()
                if result == QMessageBox.Retry:
                    return self.get(url, timeout, retries, headers, cache)
        else:
            if not quiet:
                if http_code:
                    message = http_code
                else:
                    message = reply.errorString()
                result = self._showErrorResponseMessage(url, message)
                if result == QMessageBox.Retry:
                    return self.get(url, timeout, retries, headers, cache)

        self._available = False
        return None

    def isAvailable(self):
        return self._available

    def _createHttp(self):
        self._network_manager = QNetworkAccessManager(self)

        if not Settings()['verify_ssl']:
            self._network_manager.sslErrors.connect(self._handle_ssl_errors)

    def _handle_ssl_errors(self, reply, _errors):
        reply.ignoreSslErrors()

    def close(self):
        if self._cache:
            self._cache.close()
            self._cache = None
        if self._network_manager:
            self._network_manager.deleteLater()

    def _showServerNotResponseMessage(self, url):
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        if domain in SITES_CATALOG:
            site = SITES_CATALOG[domain]
        else:
            site = self.tr("Server")

        error_str = self.tr("not response")
        message = f"{site} {error_str}"

        return self._showErrorMessage(message)

    def _showErrorResponseMessage(self, url, status):
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        if domain in SITES_CATALOG:
            site = SITES_CATALOG[domain]
        else:
            site = self.tr("Server")

        error_str = self.tr("response with error or empty data")
        message = f"{site} {error_str} ({status})"

        return self._showErrorMessage(message)

    def _showTooManyRequestsMessage(self):
        return self._showErrorMessage(self.tr("Too many requests. Try later"))

    def _showErrorMessage(self, message):
        QApplication.setOverrideCursor(QCursor(Qt.ArrowCursor))

        parent = self.parent()
        if parent:
            progress_dlg = self.parent().findChild(QProgressDialog)
            if progress_dlg:
                parent = progress_dlg
        msgBox = QMessageBox(QMessageBox.Warning,
                             self.tr("Downloading"), message,
                             QMessageBox.Retry | QMessageBox.Cancel,
                             parent)
        result = msgBox.exec()

        QApplication.restoreOverrideCursor()

        return result


def singleHttpRequest(url, parent=None, timeout=None, retries=None, quiet=False):
    http = CachedPoolManager(parent)
    response_data = http.get(url, cache=False, timeout=timeout, retries=retries, quiet=quiet)
    http.close()
    return response_data
