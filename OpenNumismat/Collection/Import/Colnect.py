import json
import re
import os
import tempfile
import urllib.request

from PyQt5 import QtCore
from PyQt5.QtCore import Qt, QObject, QDate
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtSql import QSqlDatabase, QSqlQuery
from PyQt5.QtWidgets import *

from OpenNumismat import version
from OpenNumismat.Settings import Settings
from OpenNumismat.Tools.CursorDecorators import waitCursorDecorator
from OpenNumismat.Tools.DialogDecorators import storeDlgSizeDecorator
from OpenNumismat.Tools.Gui import createIcon

from OpenNumismat.private_keys import COLNECT_KEY


class ColnectCache(QObject):
    FILE_NAME = "opennumismat-colnect"

    Action = 1
    Item = 2
    Image = 3

    def __init__(self, parent=None):
        super().__init__(parent)

        self.db = self.open()
        self._compact()

    def open(self):
        db = QSqlDatabase.addDatabase('QSQLITE', 'cache')
        db.setDatabaseName(self._file_name())
        if not db.open():
            QMessageBox.warning(self,
                                "Colnect",
                                self.tr("Can't open Colnect cache"))
            return None

        QSqlQuery("PRAGMA synchronous=OFF", db)
        QSqlQuery("PRAGMA journal_mode=MEMORY", db)

        if 'cache' not in db.tables():
            sql = "CREATE TABLE cache (\
                id INTEGER PRIMARY KEY,\
                type INTEGER, url TEXT, data BLOB,\
                createdat TEXT)"
            QSqlQuery(sql, db)

        return db

    def close(self):
        if self.db:
            self.db.close()
            self.db = None
        QSqlDatabase.removeDatabase('cache')

    def get(self, type_, url):
        if not self.db:
            return None

        query = QSqlQuery(self.db)
        query.prepare("SELECT data FROM cache WHERE type=? AND url=?")
        query.addBindValue(type_)
        query.addBindValue(url)
        query.exec_()
        if query.next():
            record = query.record()
            print('get', url, record.value('data'))
            return record.value('data')

        return None

    def set(self, type_, url, data):
        if not self.db:
            return

        if not data:
            return

        query = QSqlQuery(self.db)
        query.prepare("INSERT INTO cache (type, url, data, createdat)"
                      " VALUES (?, ?, ?, ?)")
        query.addBindValue(type_)
        query.addBindValue(url)
        query.addBindValue(data)
        currentDate = QDate.currentDate()
        days = QDate(2000, 1, 1).daysTo(currentDate)
        query.addBindValue(days)
        query.exec_()
        print('set', days, url)

    def _compact(self):
        if self.db:
            query = QSqlQuery(self.db)
            query.prepare("DELETE FROM cache WHERE"
                          " (createdat < ? AND type = 1) OR"
                          " (createdat < ? AND type = 2) OR"
                          " (createdat < ? AND type = 3)")
            currentDate = QDate.currentDate()
            days = QDate(2000, 1, 1).daysTo(currentDate)
            query.addBindValue(days - 30)  # actions older month
            query.addBindValue(days - 14)  # items older 2 weeks
            query.addBindValue(days - 7)  # images older week
            query.exec_()

    @staticmethod
    def _file_name():
        return os.path.join(tempfile.gettempdir(), ColnectCache.FILE_NAME)

    @staticmethod
    def clear():
        file_name = ColnectCache._file_name()
        if os.path.exists(file_name):
            os.remove(file_name)


@storeDlgSizeDecorator
class ColnectDialog(QDialog):
    HEIGHT = 62

    def __init__(self, parent=None):
        super().__init__(parent,
                         Qt.WindowCloseButtonHint | Qt.WindowSystemMenuHint)
        self.setWindowIcon(createIcon('colnect.ico'))
        self.setWindowTitle("Colnect")

        settings = Settings()
        self.lang = settings['locale']

        self.cache = ColnectCache()

        layout = QFormLayout()
        layout.setRowWrapPolicy(QFormLayout.WrapLongRows)

        self.countrySelector = QComboBox(self)
        self.countrySelector.setSizePolicy(QSizePolicy.Fixed,
                                           QSizePolicy.Fixed)
        countries = self.getCountries()
        for country in countries:
            self.countrySelector.addItem(country[1], country[0])
        self.countrySelector.currentIndexChanged.connect(self.countyChanged)
        layout.addRow(self.tr("Country"), self.countrySelector)

        self.seriesSelector = QComboBox(self)
        self.seriesSelector.setSizePolicy(QSizePolicy.Preferred,
                                          QSizePolicy.Fixed)
        self.seriesSelector.currentIndexChanged.connect(self.partChanged)
        layout.addRow(self.tr("Series"), self.seriesSelector)

        self.yearSelector = QComboBox(self)
        self.yearSelector.setSizePolicy(QSizePolicy.Fixed,
                                        QSizePolicy.Fixed)
        self.yearSelector.currentIndexChanged.connect(self.partChanged)
        layout.addRow(self.tr("Year"), self.yearSelector)

        self.valueSelector = QComboBox(self)
        self.valueSelector.setSizePolicy(QSizePolicy.Fixed,
                                         QSizePolicy.Fixed)
        self.valueSelector.currentIndexChanged.connect(self.partChanged)
        layout.addRow(self.tr("Value"), self.valueSelector)

        self.currencySelector = QComboBox(self)
        self.currencySelector.setSizePolicy(QSizePolicy.Preferred,
                                            QSizePolicy.Fixed)
        self.currencySelector.currentIndexChanged.connect(self.partChanged)
        layout.addRow(self.tr("Unit"), self.currencySelector)

        self.parts = (self.seriesSelector, self.yearSelector,
                      self.valueSelector, self.currencySelector)

        self.table = QTableWidget(self)
        self.table.setColumnCount(9)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.horizontalHeader().sectionDoubleClicked.connect(
                                                self.sectionDoubleClicked)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(self.HEIGHT)
        self.table.setColumnWidth(0, self.HEIGHT + 6)
        self.table.setColumnWidth(1, self.HEIGHT + 6)

        buttonBox = QDialogButtonBox(Qt.Horizontal)
        buttonBox.addButton(QDialogButtonBox.Ok)
        buttonBox.addButton(QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        vlayout = QVBoxLayout()
        vlayout.addLayout(layout)
        vlayout.addWidget(self.table)
        vlayout.addWidget(buttonBox)

        self.setLayout(vlayout)

        self._partsEnable(False)

    def sectionDoubleClicked(self, index):
        self.table.resizeColumnToContents(index)

    def _partsEnable(self, enabled):
        for part in self.parts:
            part.setEnabled(enabled)

    def countyChanged(self, _index):
        self.table.clear()
        self.table.setRowCount(0)

        country = self.countrySelector.currentData()

        self._partsEnable(True)

        series = self.getSeries(country)
        self.seriesSelector.clear()
        self.seriesSelector.addItem(self.tr("(All)"), None)
        for ser in series:
            self.seriesSelector.addItem(str(ser[1]), ser[0])

        years = self.getYears(country)
        self.yearSelector.clear()
        self.yearSelector.addItem(self.tr("(All)"), None)
        for year in years:
            self.yearSelector.addItem(str(year[0]), year[0])

        values = self.getValues(country)
        self.valueSelector.clear()
        self.valueSelector.addItem(self.tr("(All)"), None)
        for value in values:
            self.valueSelector.addItem(str(value[1]), value[0])

        currencies = self.getCurrencies(country)
        self.currencySelector.clear()
        self.currencySelector.addItem(self.tr("(All)"), None)
        for currency in currencies:
            self.currencySelector.addItem(str(currency[1]), currency[0])

    def partChanged(self, _index):
        self.table.clear()
        self.table.setRowCount(0)

        series = self.seriesSelector.currentData()
        year = self.yearSelector.currentData()
        value = self.valueSelector.currentData()
        currency = self.currencySelector.currentData()

        if series or year or value or currency:
            country = self.countrySelector.currentData()
            action = "list_id/cat/coins/producer/%d" % country
            if series:
                action += "/series/%s" % series
            if year:
                action += "/year/%s" % year
            if value:
                action += "/face_value/%s" % value
            if currency:
                action += "/currency/%s" % currency
            item_ids = self._getData(action)
            print(len(item_ids))

            if (series and year and value and currency) or (len(item_ids) < 50):
                self.table.setRowCount(len(item_ids))
                for i, item_id in enumerate(item_ids):
                    action = "item/cat/coins/producer/%d/id/%d" % (country, item_id)
                    data = self._getData(action)

                    image = self._getImage(int(data[8]), data[0])
                    pixmap = QPixmap.fromImage(image)
                    item = QTableWidgetItem()
                    item.setData(Qt.DecorationRole, pixmap)
                    self.table.setItem(i, 0, item)

                    image = self._getImage(int(data[9]), data[0])
                    pixmap = QPixmap.fromImage(image)
                    item = QTableWidgetItem()
                    item.setData(Qt.DecorationRole, pixmap)
                    self.table.setItem(i, 1, item)

                    item = QTableWidgetItem(data[0])
                    self.table.setItem(i, 2, item)
                    item = QTableWidgetItem(data[2])
                    self.table.setItem(i, 3, item)
                    item = QTableWidgetItem(str(data[4]))
                    self.table.setItem(i, 4, item)
                    item = QTableWidgetItem(data[14])
                    self.table.setItem(i, 5, item)
                    item = QTableWidgetItem(data[19])
                    self.table.setItem(i, 6, item)
                    item = QTableWidgetItem(str(data[13]))
                    self.table.setItem(i, 7, item)
                    item = QTableWidgetItem(str(data[12]))
                    self.table.setItem(i, 8, item)

    def getCountries(self):
        action = "countries/cat/coins"
        return self._getData(action)

    def getYears(self, country):
        action = "years/cat/coins/producer/%d" % country
        return self._getData(action)

    def getSeries(self, country):
        action = "series/cat/coins/producer/%d" % country
        return self._getData(action)

    def getValues(self, country):
        action = "face_values/cat/coins/producer/%d" % country
        return self._getData(action)

    def getCurrencies(self, country):
        action = "currencies/cat/coins/producer/%d" % country
        return self._getData(action)

    def _baseUrl(self):
        url = "https://api.colnect.net/%s/api/%s/" % (self.lang, COLNECT_KEY)
        return url

    @waitCursorDecorator
    def _getData(self, action):
        data = []

        url = self._baseUrl() + action
        raw_data = self.cache.get(ColnectCache.Action, url)
        if raw_data:
            data = json.loads(raw_data)
            return data

        try:
            req = urllib.request.Request(url,
                                    headers={'User-Agent': version.AppName})
            raw_data = urllib.request.urlopen(req).read().decode()
            self.cache.set(ColnectCache.Action, url, raw_data)
            data = json.loads(raw_data)
            print(data)
        except:
            pass

        return data

    @waitCursorDecorator
    def _getImage(self, image_id, name):
        image = QImage()

        if not image_id:
            return image

        url = self._imageUrl(image_id, name)
        raw_data = self.cache.get(ColnectCache.Image, url)
        if raw_data:
            result = image.loadFromData(raw_data)
            if result:
                return image

        try:
            req = urllib.request.Request(url,
                                    headers={'User-Agent': version.AppName})
            raw_data = urllib.request.urlopen(req).read()
            result = image.loadFromData(raw_data)
            if result:
                ba = QtCore.QByteArray()
                buffer = QtCore.QBuffer(ba)
                buffer.open(QtCore.QIODevice.WriteOnly)

                if image.height() > self.HEIGHT:
                    image = image.scaled(self.HEIGHT, self.HEIGHT,
                            Qt.KeepAspectRatio, Qt.SmoothTransformation)
                image.save(buffer, 'png')

                self.cache.set(ColnectCache.Image, url, ba)
        except:
            pass

        return image

    def _imageUrl(self, image_id, name):
        name = self._urlize(name)
        url = "https://i.colnect.net/t/%d/%d/%s.jpg" % (image_id / 1000, image_id % 1000, name)
        print(url)
        return url

    def _urlize(self, name):
        # change HTML elements to underscore
        name = re.sub(r"&[^;]+;", '_', name)

        name = re.sub(r"[.\"><\\:/?#\[\]@!$&'()\*\+,;=]", '', name)
        name = re.sub(r"[^\x00-\x7F]", '', name)

        # any space sequence becomes a single underscore
        name = re.sub(r"[\s_]+", '_', name)

        name = name.strip('_')

        return name

    def accept(self):
        self.cache.close()
        super().accept()

    def reject(self):
        self.cache.close()
        super().reject()
