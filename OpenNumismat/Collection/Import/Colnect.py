import csv
import io
import json
import re
import os
import tempfile
import urllib.request

from PyQt5 import QtCore
from PyQt5.QtCore import Qt, QObject, QDate
from PyQt5.QtGui import QImage, QPixmap, QIcon
from PyQt5.QtSql import QSqlDatabase, QSqlQuery
from PyQt5.QtWidgets import *

from OpenNumismat import version
from OpenNumismat.Collection.Import import _Import2
from OpenNumismat.Settings import Settings
from OpenNumismat.Tools.CursorDecorators import waitCursorDecorator
from OpenNumismat.Tools.DialogDecorators import storeDlgSizeDecorator
from OpenNumismat.Tools.Gui import ProgressDialog

colnectAvailable = True

try:
    from OpenNumismat.private_keys import COLNECT_PROXY
except ImportError:
    print('Importing from Colnect not available')
    colnectAvailable = False


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
            QMessageBox.warning(self, "Colnect", self.tr("Can't open Colnect cache"))
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


class ColnectConnector(QObject):

    def __init__(self, parent):
        super().__init__(parent)

        self.cache = ColnectCache()
        self.skip_currency = Settings()['colnect_skip_currency']
        self.lang = Settings()['colnect_locale']

    def makeItem(self, category, data, record):
        fields = self.getFields(category)

        # construct Record object from data json
        columns = {'coins': (('title', 'Name'), ('country', 'Country'), ('series', 'Series'), ('year', 'Issued on'),
                             ('mintage', 'Known mintage'), ('unit', 'Currency'), ('value', 'FaceValue'), ('material', 'Composition'),
                             ('diameter', 'Diameter'), ('weight', 'Weight'), ('subject', 'Description'), ('type', 'Distribution'),
                             ('issuedate', 'Issued on'), ('edge', 'EdgeVariety'), ('shape', 'Shape'), ('obvrev', 'Orientation'),
                             ('catalognum1', 'Catalog Codes'),
                            ),
                   'banknotes': (('title', 'Name'), ('country', 'Country'), ('series', 'Series'), ('year', 'Issued on'),
                                 ('mintage', 'Mintage'), ('unit', 'Currency'), ('value', 'FaceValue'), ('material', 'Composition'),
                                 ('diameter', 'Width'), ('thickness', 'Height'), ('subject', 'Description'), ('mint', 'Printer'),
                                 ('issuedate', 'Issued on'), ('catalognum1', 'Catalog Codes'),
                                ),
                   'stamps': (('title', 'Name'), ('country', 'Country'), ('series', 'Series'), ('year', 'Issued on'),
                              ('mintage', 'Print run'), ('unit', 'Currency'), ('value', 'FaceValue'), ('material', 'Paper'),
                              ('diameter', 'Width'), ('thickness', 'Height'), ('subject', 'Description'), ('type', 'Emission'),
                              ('quality', 'Printing'), ('obvrev', 'Gum'), ('edgelabel', 'Watermark'),
                              ('issuedate', 'Issued on'), ('edge', 'Perforation'), ('obversecolor', 'Colors'),
                              ('format', 'Format'), ('catalognum1', 'Catalog Codes'),
                             )}

        for column in columns[category]:
            pos = fields.index(column[1])
            value = data[pos]
            if column[0] == 'year' and isinstance(value, str):
                value = value[:4]
            elif column[0] == 'unit' and self.skip_currency:
                value = value.split('-', 1)[-1].strip()
            elif column[0] == 'catalognum1':
                codes = value.split(',', 3)
                for i, code in enumerate(codes):
                    field = 'catalognum%d' % (i + 1)
                    record.setValue(field, code.strip())
                continue
            record.setValue(column[0], value)
        # Add URL
        record.setValue('url', data[-1])

        img_pos = fields.index('FrontPicture')
        image = self.getImage(int(data[img_pos]), data[0], True)
        record.setValue('obverseimg', image)
        img_pos = fields.index('BackPicture')
        image = self.getImage(int(data[img_pos]), data[0], True)
        record.setValue('reverseimg', image)
        if 'ExtPicture' in fields:
            img_pos = fields.index('ExtPicture')
            if data[img_pos]:
                image = self.getImage(int(data[img_pos]), data[0], True)
                record.setValue('photo1', image)

    @waitCursorDecorator
    def getFields(self, category):
        url = "https://%s/en/api/COLNECT_KEY/fields/cat/%s" % (COLNECT_PROXY, category)

        raw_data = self.cache.get(ColnectCache.Image, url)
        if raw_data:
            data = json.loads(raw_data)
            return data

        try:
            req = urllib.request.Request(url,
                                    headers={'User-Agent': version.AppName})
            raw_data = urllib.request.urlopen(req).read().decode()
        except:
            return []

        data = json.loads(raw_data)
        self.cache.set(ColnectCache.Image, url, raw_data)

        return data

    @waitCursorDecorator
    def getImage(self, image_id, name, full):
        data = None

        if not image_id:
            return data

        url = self._imageUrl(image_id, name, full)

        if not full:
            # full images was not cached - store previous behaviour
            data = self.cache.get(ColnectCache.Image, url)
            if data:
                return data

        try:
            req = urllib.request.Request(url,
                                    headers={'User-Agent': version.AppName})
            data = urllib.request.urlopen(req).read()
        except:
            return None

        if not full:
            self.cache.set(ColnectCache.Image, url, data)

        return data

    def _imageUrl(self, image_id, name, full):
        name = self._urlize(name)
        url = "https://i.colnect.net/%s/%d/%03d/%s.jpg" % (
            ('b' if full else 't'), image_id / 1000, image_id % 1000, name)
            # ('f' if full else 't'), image_id / 1000, image_id % 1000, name)
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

    def _baseUrl(self):
        url = "https://%s/%s/api/COLNECT_KEY/" % (COLNECT_PROXY, self.lang)
        return url

    @waitCursorDecorator
    def getData(self, action):
        url = self._baseUrl() + action
        raw_data = self.cache.get(ColnectCache.Action, url)
        if raw_data:
            data = json.loads(raw_data)
            return data

        try:
            req = urllib.request.Request(url,
                                    headers={'User-Agent': version.AppName})
            raw_data = urllib.request.urlopen(req).read().decode()
        except:
            return []

        if raw_data.startswith('Invalid key'):
            QMessageBox.warning(self.parent(), "Colnect",
                                self.tr("Colnect service not available"))
            return []
        elif raw_data.startswith('Visit colnect.com'):
            QMessageBox.warning(self.parent(), "Colnect",
                                self.tr("Colnect data not recognised"))
            return []

        data = json.loads(raw_data)
        self.cache.set(ColnectCache.Action, url, raw_data)

        return data

    def getCountries(self, category):
        action = "countries/cat/%s" % category
        return self.getData(action)

    def getYears(self, category, country):
        action = "years/cat/%s/producer/%d" % (category, country)
        return self.getData(action)

    def getSeries(self, category, country):
        action = "series/cat/%s/producer/%d" % (category, country)
        return self.getData(action)

    def getDistributions(self, category, country):
        if category == 'coins':
            action = "distributions/cat/%s/producer/%d" % (category, country)
        elif category == 'stamps':
            action = "emissions/cat/%s/producer/%d" % (category, country)
        else:
            return []

        return self.getData(action)

    def getValues(self, category, country):
        action = "face_values/cat/%s/producer/%d" % (category, country)
        return self.getData(action)

    def getCurrencies(self, category, country):
        action = "currencies/cat/%s/producer/%d" % (category, country)
        return self.getData(action)

    def close(self):
        self.cache.close()


@storeDlgSizeDecorator
class ColnectDialog(QDialog):
    HEIGHT = 62

    def __init__(self, model, parent=None):
        super().__init__(parent,
                         Qt.WindowCloseButtonHint | Qt.WindowSystemMenuHint)
        self.setWindowIcon(QIcon(':/colnect.png'))
        self.setWindowTitle("Colnect")

        fields = model.fields

        settings = Settings()
        self.lang = settings['colnect_locale']
        self.autoclose = settings['colnect_autoclose']

        layout = QFormLayout()
        layout.setRowWrapPolicy(QFormLayout.WrapLongRows)

        self.colnectLabel = QLabel(self.tr(
            "Catalog information courtesy of"
            " <a href=\"https://colnect.com/\">Colnect</a>,"
            " an online collectors community."))
        self.colnectLabel.setTextFormat(Qt.RichText)
        self.colnectLabel.setTextInteractionFlags(Qt.TextBrowserInteraction)
        self.colnectLabel.setOpenExternalLinks(True)
        font = self.colnectLabel.font()
        font.setPointSize(11)
        self.colnectLabel.setFont(font)
        layout.addRow(self.colnectLabel)
        layout.addRow(QWidget())

        categories = (('coins', self.tr("Coins")),
                      ('banknotes', self.tr("Banknotes")),
                      ('stamps', self.tr("Stamps")))

        self.categorySelector = QComboBox()
        self.categorySelector.setSizePolicy(QSizePolicy.Fixed,
                                            QSizePolicy.Fixed)
        for category in categories:
            self.categorySelector.addItem(category[1], category[0])
        layout.addRow(self.tr("Category"), self.categorySelector)
        self.categorySelector.currentIndexChanged.connect(self.categoryChanged)

        self.countrySelector = QComboBox()
        self.countrySelector.setSizePolicy(QSizePolicy.Fixed,
                                           QSizePolicy.Fixed)
        self.countrySelector.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.countrySelector.currentIndexChanged.connect(self.countryChanged)
        layout.addRow(fields.getCustomTitle('country'), self.countrySelector)

        self.distributionSelector = QComboBox()
        self.distributionSelector.setSizePolicy(QSizePolicy.Fixed,
                                                QSizePolicy.Fixed)
        self.distributionSelector.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.distributionSelector.currentIndexChanged.connect(self.partChanged)
        layout.addRow(fields.getCustomTitle('type'), self.distributionSelector)

        self.seriesSelector = QComboBox()
        self.seriesSelector.setSizePolicy(QSizePolicy.Fixed,
                                          QSizePolicy.Fixed)
        self.seriesSelector.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.seriesSelector.currentIndexChanged.connect(self.partChanged)
        layout.addRow(fields.getCustomTitle('series'), self.seriesSelector)

        self.yearSelector = QComboBox()
        self.yearSelector.setSizePolicy(QSizePolicy.Fixed,
                                        QSizePolicy.Fixed)
        self.yearSelector.currentIndexChanged.connect(self.partChanged)
        self.yearSelector.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        layout.addRow(fields.getCustomTitle('year'), self.yearSelector)

        self.valueSelector = QComboBox()
        self.valueSelector.setSizePolicy(QSizePolicy.Fixed,
                                         QSizePolicy.Fixed)
        self.valueSelector.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.valueSelector.currentIndexChanged.connect(self.partChanged)
        layout.addRow(fields.getCustomTitle('value'), self.valueSelector)

        self.currencySelector = QComboBox()
        self.currencySelector.setSizePolicy(QSizePolicy.Fixed,
                                            QSizePolicy.Fixed)
        self.currencySelector.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.currencySelector.currentIndexChanged.connect(self.partChanged)
        layout.addRow(fields.getCustomTitle('unit'), self.currencySelector)

        self.parts = (self.seriesSelector, self.distributionSelector,
                      self.yearSelector,
                      self.valueSelector, self.currencySelector)

        self.table = QTableWidget(self)
        self.table.doubleClicked.connect(self.tableClicked)
        self.table.setColumnCount(9)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.horizontalHeader().sectionDoubleClicked.connect(self.sectionDoubleClicked)
        font = self.table.horizontalHeader().font()
        font.setBold(True)
        self.table.horizontalHeader().setFont(font)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(self.HEIGHT + 2)
        self.table.setColumnWidth(0, self.HEIGHT + 6)
        self.table.setColumnWidth(1, self.HEIGHT + 6)

        field_names = ('obverseimg', 'reverseimg', 'title', 'series',
                       'year', 'type', 'material', 'value', 'unit')
        field_titles = []
        for field_name in field_names:
            title = fields.getCustomTitle(field_name)
            field_titles.append(title)
        self.table.setHorizontalHeaderLabels(field_titles)

        self.addButton = QPushButton(self.tr("Add"))
        self.addButton.setEnabled(False)
        self.addCloseButton = QPushButton(self.tr("Add and close"))
        self.addCloseButton.setEnabled(False)
        if self.autoclose:
            self.addCloseButton.setDefault(True)
        else:
            self.addButton.setDefault(True)

        self.previewButton = QPushButton(self.tr("Preview"))
        self.previewButton.setEnabled(False)
        self.previewButton.clicked.connect(self.preview)
        self.label = QLabel(self.tr("Specify more parameters"), self)
        self.label_empty = QLabel(self.tr("Nothing found"), self)
        self.label_empty.hide()
        previewBox = QHBoxLayout()
        previewBox.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        previewBox.addWidget(self.previewButton)
        previewBox.addWidget(self.label)
        previewBox.addWidget(self.label_empty)

        buttonBox = QDialogButtonBox(Qt.Horizontal, self)
        buttonBox.addButton(self.addButton, QDialogButtonBox.ActionRole)
        buttonBox.addButton(self.addCloseButton, QDialogButtonBox.ActionRole)
        buttonBox.addButton(QDialogButtonBox.Close)
        buttonBox.clicked.connect(self.clicked)

        self.table.hide()

        vlayout = QVBoxLayout()
        vlayout.addLayout(layout)
        vlayout.addLayout(previewBox)
        vlayout.addWidget(self.table)
        vlayout.addWidget(buttonBox)

        self.setLayout(vlayout)

        self._partsEnable(False)

        self.model = model
        self.settings = model.settings
        self.items = []

        default_category = self.settings['colnect_category']
        default_country = self.settings['colnect_country']

        self.colnect = ColnectConnector(self)

        index = self.categorySelector.findData(default_category)
        self.categorySelector.setCurrentIndex(index)
        self.categoryChanged(0)

        index = self.countrySelector.findData(default_country)
        if index >= 0:
            self.countrySelector.setCurrentIndex(index)
        self.countryChanged(0)

    def sectionDoubleClicked(self, index):
        self.table.resizeColumnToContents(index)

    def _partsEnable(self, enabled):
        for part in self.parts:
            part.setEnabled(enabled)

    def tableClicked(self, index):
        if not index:
            return

        self.addCoin(index, self.autoclose)

    def addCoin(self, index, close):
        category = self.categorySelector.currentData()
        data = self.items[index.row()]
        newRecord = self.model.record()
        self.colnect.makeItem(category, data, newRecord)
        if close:
            self.accept()
        self.model.addCoin(newRecord, self)

    def _clearTable(self):
        self.addButton.setEnabled(False)
        self.addCloseButton.setEnabled(False)

        self.table.hide()
        self.label.show()
        self.label_empty.hide()
        self.previewButton.setEnabled(False)
        self.table.setRowCount(0)
        self.items = []

    def categoryChanged(self, _index):
        self._clearTable()
        self.countrySelector.clear()

        category = self.categorySelector.currentData()
        countries = self.colnect.getCountries(category)
        for country in countries:
            self.countrySelector.addItem(country[1], country[0])

        self.settings['colnect_category'] = category

    def countryChanged(self, _index):
        self._clearTable()

        self._partsEnable(True)

        category = self.categorySelector.currentData()
        country = self.countrySelector.currentData()
        if not country:
            return

        series = self.colnect.getSeries(category, country)
        self.seriesSelector.clear()
        self.seriesSelector.addItem(self.tr("(All)"), None)
        for ser in series:
            self.seriesSelector.addItem(str(ser[1]), ser[0])

        distributions = self.colnect.getDistributions(category, country)
        self.distributionSelector.clear()
        self.distributionSelector.addItem(self.tr("(All)"), None)
        for distr in distributions:
            self.distributionSelector.addItem(str(distr[1]), distr[0])

        years = self.colnect.getYears(category, country)
        self.yearSelector.clear()
        self.yearSelector.addItem(self.tr("(All)"), None)
        for year in years:
            self.yearSelector.addItem(str(year[0]), year[0])

        values = self.colnect.getValues(category, country)
        self.valueSelector.clear()
        self.valueSelector.addItem(self.tr("(All)"), None)
        for value in values:
            self.valueSelector.addItem(str(value[1]), value[0])

        currencies = self.colnect.getCurrencies(category, country)
        self.currencySelector.clear()
        self.currencySelector.addItem(self.tr("(All)"), None)
        for currency in currencies:
            self.currencySelector.addItem(str(currency[1]), currency[0])

        self.settings['colnect_country'] = country

    def partChanged(self, _index):
        self._clearTable()

        category = self.categorySelector.currentData()
        if category in ('coins', 'stamps'):
            self.distributionSelector.setVisible(True)
        else:
            self.distributionSelector.setVisible(False)

        series = self.seriesSelector.currentData()
        year = self.yearSelector.currentData()
        value = self.valueSelector.currentData()
        currency = self.currencySelector.currentData()
        if self.distributionSelector.isVisible():
            distribution = self.distributionSelector.currentData()
        else:
            distribution = None

        if series or distribution or year or value or currency:
            country = self.countrySelector.currentData()
            action = "list_id/cat/%s/producer/%d" % (category, country)
            if series:
                action += "/series/%s" % series
            if distribution:
                if category == 'coins':
                    action += "/distribution/%s" % distribution
                elif category == 'stamps':
                    action += "/emission/%s" % distribution
            if year:
                action += "/year/%s" % year
            if value:
                action += "/face_value/%s" % value
            if currency:
                action += "/currency/%s" % currency
            item_ids = self.colnect.getData(action)

            if len(item_ids) == 0:
                self.label_empty.show()
                self.label.hide()
            elif ((series or distribution) and year and value and currency) or (len(item_ids) < 100):
                self.previewButton.setEnabled(True)
                self.label.hide()

    def preview(self):
        self.table.show()

        category = self.categorySelector.currentData()
        if category in ('coins', 'stamps'):
            self.distributionSelector.setVisible(True)
        else:
            self.distributionSelector.setVisible(False)

        series = self.seriesSelector.currentData()
        year = self.yearSelector.currentData()
        value = self.valueSelector.currentData()
        currency = self.currencySelector.currentData()
        if self.distributionSelector.isVisible():
            distribution = self.distributionSelector.currentData()
        else:
            distribution = None

        country = self.countrySelector.currentData()
        action = "list_id/cat/%s/producer/%d" % (category, country)
        if series:
            action += "/series/%s" % series
        if distribution:
            if category == 'coins':
                action += "/distribution/%s" % distribution
            elif category == 'stamps':
                action += "/emission/%s" % distribution
        if year:
            action += "/year/%s" % year
        if value:
            action += "/face_value/%s" % value
        if currency:
            action += "/currency/%s" % currency
        item_ids = self.colnect.getData(action)

        if item_ids:
            progressDlg = ProgressDialog(self.tr("Downloading"), self.tr("Cancel"),
                                         len(item_ids), self)

            action = "fields/cat/%s" % category
            fields = self.colnect.getFields(action)

            self.table.setRowCount(len(item_ids))
            for i, item_id in enumerate(item_ids):
                progressDlg.step()
                if progressDlg.wasCanceled():
                    break

                action = "item/cat/%s/id/%d" % (category, item_id)
                data = self.colnect.getData(action)
                data.append(self._itemUrl(category, item_id))
                self.items.append(data)

                name_val = self._getFieldData(data, fields, 'Name')
                img_pos = fields.index('FrontPicture')
                image = self._getImage(int(data[img_pos]), name_val)
                pixmap = QPixmap.fromImage(image)
                item = QTableWidgetItem()
                item.setData(Qt.DecorationRole, pixmap)
                self.table.setItem(i, 0, item)

                img_pos = fields.index('BackPicture')
                image = self._getImage(int(data[img_pos]), name_val)
                pixmap = QPixmap.fromImage(image)
                item = QTableWidgetItem()
                item.setData(Qt.DecorationRole, pixmap)
                self.table.setItem(i, 1, item)

                value = self._getFieldData(data, fields, 'Name')
                item = QTableWidgetItem(value)
                self.table.setItem(i, 2, item)
                value = self._getFieldData(data, fields, 'Series')
                item = QTableWidgetItem(value)
                self.table.setItem(i, 3, item)
                value = self._getFieldData(data, fields, 'Issued on')
                item = QTableWidgetItem(str(value))
                self.table.setItem(i, 4, item)
                value = self._getFieldData(data, fields, 'Distribution')
                item = QTableWidgetItem(value)
                self.table.setItem(i, 5, item)
                value = self._getFieldData(data, fields, 'Composition')
                item = QTableWidgetItem(value)
                self.table.setItem(i, 6, item)
                value = self._getFieldData(data, fields, 'FaceValue')
                item = QTableWidgetItem(str(value))
                self.table.setItem(i, 7, item)
                value = self._getFieldData(data, fields, 'Currency')
                item = QTableWidgetItem(value)
                self.table.setItem(i, 8, item)

            progressDlg.reset()

            self.addButton.setEnabled(True)
            self.addCloseButton.setEnabled(True)

    def _getFieldData(self, data, fields, field_name):
        try:
            pos = fields.index(field_name)
            return data[pos]
        except ValueError:
            return None

    def _getImage(self, image_id, name):
        image = QImage()

        if not image_id:
            return image

        result = image.loadFromData(self.colnect.getImage(image_id, name, False))
        if result:
            ba = QtCore.QByteArray()
            buffer = QtCore.QBuffer(ba)
            buffer.open(QtCore.QIODevice.WriteOnly)

            if image.height() > self.HEIGHT:
                image = image.scaled(self.HEIGHT, self.HEIGHT,
                                     Qt.KeepAspectRatio, Qt.SmoothTransformation)
            image.save(buffer, 'png')
        return image

    def _itemUrl(self, category, item_id):
        url = "https://colnect.com/%s/%s/%s/%d" % (self.lang, category,
                                                   category[:-1], item_id)
        return url

    def clicked(self, button):
        if button == self.addButton:
            for index in self.table.selectedIndexes():
                if index.column() == 0:
                    self.addCoin(index, False)
        elif button == self.addCloseButton:
            for index in self.table.selectedIndexes():
                if index.column() == 0:
                    self.addCoin(index, True)

            self.accept()
        else:
            self.accept()

    def accept(self):
        self.settings.save()
        self.colnect.close()
        super().accept()


class ImportColnect(_Import2):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.colnect = ColnectConnector(parent)
        self.urls = []

    @staticmethod
    def isAvailable():
        return True

    def _connect(self, src):
        csvFile = io.open(src, "r", encoding='utf-8-sig')
        cur_line = 0
        for row in csv.reader(csvFile):
            cur_line += 1
            if cur_line <= 7:  # skip 7 header lines
                continue
            for field in row:
                # Can't rely on hardcoded column number because different export files have url in
                # diferent columns depending on type of collection (i.e. stamps/coins/etc).
                # Can't rely on hardcoded column name because of possible inconsistences
                # with translations.
                if field.startswith('https://colnect.com/'):
                    self.urls.append(field)
        csvFile.close()
        return True

    def _getRowsCount(self, connection):
        return len(self.urls)

    def _setRecord(self, record, row):
        url = self.urls[row]
        url_parts = url.rsplit('/', maxsplit=3)
        category = url_parts[1]
        item_id = url_parts[3]
        action = "item/cat/%s/id/%s" % (category, item_id)
        data = self.colnect.getData(action)
        data.append(url)
        self.colnect.makeItem(category, data, record)
