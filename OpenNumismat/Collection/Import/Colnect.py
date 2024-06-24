import csv
import io
import json
import re
import urllib3

from PySide6.QtCore import Qt, QObject
from PySide6.QtGui import QImage, QPixmap, QIcon
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from OpenNumismat import version
from OpenNumismat.Collection.Import.Cache import Cache
from OpenNumismat.Collection.Import import _Import2
from OpenNumismat.Settings import Settings
from OpenNumismat.Tools.CursorDecorators import waitCursorDecorator
from OpenNumismat.Tools.DialogDecorators import storeDlgSizeDecorator
from OpenNumismat.Tools.Gui import ProgressDialog

colnectAvailable = True

try:
    from OpenNumismat.private_keys import COLNECT_PROXY, COLNECT_KEY
except ImportError:
    print('Importing from Colnect not available')
    colnectAvailable = False

CONNECTION_TIMEOUT = 10
MAX_ITEMS = 150


class ColnectConnector(QObject):

    def __init__(self, parent):
        super().__init__(parent)

        urllib3.disable_warnings()
        timeout = urllib3.Timeout(connect=CONNECTION_TIMEOUT / 2,
                                  read=CONNECTION_TIMEOUT)
        self.http = urllib3.PoolManager(num_pools=2,
                                        headers={'User-Agent': version.AppName},
                                        timeout=timeout,
                                        cert_reqs="CERT_NONE")
        self.cache = Cache()
        self.skip_currency = Settings()['colnect_skip_currency']
        self.lang = Settings()['colnect_locale']
        self.uuid = Settings()['UUID']

    def makeItem(self, category, data, record):
        fields = self.getFields(category)

        # construct Record object from data json
        columns = {'coins': (('title', 'Name'), ('country', 'Country'), ('series', 'Series'), ('year', 'Issued on'),
                             ('mintage', 'Known mintage'), ('unit', 'Currency'), ('value', 'FaceValue'), ('material', 'Composition'),
                             ('diameter', 'Diameter'), ('weight', 'Weight'), ('subject', 'Description'), ('type', 'Distribution'),
                             ('issuedate', 'Issued on'), ('edge', 'EdgeVariety'), ('shape', 'Shape'), ('obvrev', 'Orientation'),
                             ('catalognum1', 'Catalog Codes'), ('thickness', 'Thickness'), ('fineness', 'Composition Details'),
                            ),
                   'banknotes': (('title', 'Name'), ('country', 'Country'), ('series', 'Series'), ('year', 'Issued on'),
                                 ('mintage', 'Mintage'), ('unit', 'Currency'), ('value', 'FaceValue'), ('material', 'Composition'),
                                 ('width', 'Width'), ('height', 'Height'), ('subject', 'Description'), ('mint', 'Printer'),
                                 ('issuedate', 'Issued on'), ('catalognum1', 'Catalog Codes'), ('type', 'Distribution'),
                                ),
                   'stamps': (('title', 'Name'), ('country', 'Country'), ('series', 'Series'), ('year', 'Issued on'),
                              ('mintage', 'Print run'), ('unit', 'Currency'), ('value', 'FaceValue'), ('material', 'Paper'),
                              ('width', 'Width'), ('height', 'Height'), ('subject', 'Description'), ('type', 'Emission'),
                              ('quality', 'Printing'), ('obvrev', 'Gum'), ('edgelabel', 'Watermark'),
                              ('issuedate', 'Issued on'), ('edge', 'Perforation'), ('obversecolor', 'Colors'),
                              ('format', 'Format'), ('catalognum1', 'Catalog Codes'),
                             ),
                   'philatelic_products': (('title', 'Name'), ('country', 'Country'), ('subjectshort', 'Series'), ('year', 'Issued on'),
                              ('mintage', 'Print run'), ('unit', 'Currency'), ('value', 'FaceValue'),
                              ('subject', 'Description'), ('mint', 'Issuer'),
                              ('issuedate', 'Issued on'), ('type', 'Subformat'),
                              ('series', 'Format'), ('catalognum1', 'Catalog Codes'),
                            )}

        for column in columns[category]:
            pos = fields.index(column[1])
            value = data[pos]
            if column[0] == 'year' and isinstance(value, str):
                value = value[:4]
            elif column[0] == 'year' and isinstance(value, int):
                if value > 5000:
                    value -= 10000
            elif column[0] == 'unit' and self.skip_currency:
                value = value.split(' - ', 1)[-1].strip()
            elif column[0] == 'subject':
                value = value.replace('[b]', '').replace('[/b]', '').replace('  ', '\n')
            elif column[0] == 'catalognum1':
                codes = value.split(',', 3)
                for i, code in enumerate(codes):
                    field = 'catalognum%d' % (i + 1)
                    record.setValue(field, code.strip())
                continue
            elif column[0] == 'obversecolor':
                if type(value) is str:
                    color = int(value.split(',', 1)[0])
                else:
                    color = value
                value = ''
                colors = self.getColors(category)
                for color_set in colors:
                    if color_set[0] == color:
                        value = color_set[1]
                        break
            elif column[0] == 'fineness':
                if type(value) is float:
                    value = int(value*1000)
                elif type(value) is str:
                    result = ''
                    if '/1000' in value:
                        pos = value.find('/1000') - 1
                        while pos >= 0 and value[pos] in '0123456789.,':
                            result = value[pos] + result
                            pos -= 1
                        if result:
                            result = float(result.replace(',', '.'))
                    elif '0.' in value:
                        pos = value.find('0.') + 2
                        while pos < len(value) and value[pos].isdigit():
                            result += value[pos]
                            pos += 1
                    elif '0,' in value:
                        pos = value.find('0,') + 2
                        while pos < len(value) and value[pos].isdigit():
                            result += value[pos]
                            pos += 1
                    elif '%' in value:
                        pos = value.find('%') - 1
                        while pos >= 0 and value[pos] in '0123456789.,':
                            result = value[pos] + result
                            pos -= 1
                        if result:
                            result = float(result.replace(',', '.'))
                            result *= 10
                    elif '.' in value:
                        pos = value.find('.') + 1
                        while pos < len(value) and value[pos].isdigit():
                            result += value[pos]
                            pos += 1
                    try:
                        value = int(result)
                    except:
                        value = ''
                
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
        url = f"{COLNECT_PROXY}/{self.uuid}/en/api/{COLNECT_KEY}/fields/cat/{category}"

        raw_data = self.cache.get(url)
        if raw_data:
            data = json.loads(raw_data)
            return data

        try:
            resp = self.http.request("GET", url)
            raw_data = resp.data.decode()
        except urllib3.exceptions.MaxRetryError:
            QMessageBox.warning(self.parent(), "Colnect",
                                self.tr("Colnect proxy-server not response"))
            return []
        except:
            return []

        data = json.loads(raw_data)
        self.cache.set(url, raw_data)

        return data

    @waitCursorDecorator
    def getImage(self, image_id, name, full):
        data = None

        if not image_id:
            return data

        url = self._imageUrl(image_id, name, full)

        if not full:
            # full images was not cached - store previous behaviour
            data = self.cache.get(url)
            if data:
                return data

        try:
            resp = self.http.request("GET", url, timeout=CONNECTION_TIMEOUT * 3)
            data = resp.data
        except:
            return None

        if not full:
            self.cache.set(url, data)

        return data

    def _imageUrl(self, image_id, name, full):
        name = self._urlize(name)
        url = "https://i.colnect.net/%s/%d/%03d/%s.jpg" % (
            ('b' if full else 't'), image_id // 1000, image_id % 1000, name)
            # ('f' if full else 't'), image_id // 1000, image_id % 1000, name)
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

    def _baseUrl(self, lang=None):
        if lang is None:
            lang = self.lang
        url = f"{COLNECT_PROXY}/{self.uuid}/{lang}/api/{COLNECT_KEY}/"
        return url

    def _makeQuery(self, category, country=None, series=None,
                 distribution=None, year=None, value=None, currency=None):
        params = "/cat/%s" % category
        if country:
            params += "/producer/%d" % country
        if series:
            params += "/series/%s" % series
        if distribution:
            if category == 'coins':
                params += "/distribution/%s" % distribution
            elif category == 'stamps':
                params += "/emission/%s" % distribution
        if year:
            params += "/year/%s" % year
        if value:
            params += "/face_value/%s" % value
        if currency:
            params += "/currency/%s" % currency
        
        return params

    def getCount(self, category, country, series=None,
                 distribution=None, year=None, value=None, currency=None):
        action = "list_id" + self._makeQuery(category, country, series,
                 distribution, year, value, currency)
        item_ids = self.getData(action, 'en')
        return len(item_ids)
    
    @waitCursorDecorator
    def getData(self, action, lang=None):
        url = self._baseUrl(lang) + action
        raw_data = self.cache.get(url)
        if raw_data:
            data = json.loads(raw_data)
            return data

        try:
            resp = self.http.request("GET", url)
            raw_data = resp.data.decode()
        except urllib3.exceptions.MaxRetryError:
            QMessageBox.warning(self.parent(), "Colnect",
                                self.tr("Colnect proxy-server not response"))
            return []
        except:
            return []

        if raw_data.startswith('Invalid key'):
            QMessageBox.warning(self.parent(), "Colnect",
                                self.tr("Colnect service not available"))
            return []
        elif raw_data.startswith('Limits exceeded daily'):
            QMessageBox.warning(self.parent(), "Colnect",
                                self.tr("Daily request limit reached"))
            return []
        elif raw_data.startswith('Limits exceeded weekly'):
            QMessageBox.warning(self.parent(), "Colnect",
                                self.tr("Weekly request limit reached"))
            return []
        elif raw_data.startswith('Limits exceeded monthly'):
            QMessageBox.warning(self.parent(), "Colnect",
                                self.tr("Monthly request limit reached"))
            return []
        elif raw_data.startswith('Limits exceeded'):
            QMessageBox.warning(self.parent(), "Colnect",
                                self.tr("Number of requests exceeded"))
            return []
        elif raw_data.startswith('Visit colnect.com'):
            QMessageBox.warning(self.parent(), "Colnect",
                                self.tr("Colnect data not recognised"))
            return []
        elif raw_data.startswith('<!DOCTYPE html>'):
            self.cache.set(url, '[]')
            return []

        data = json.loads(raw_data)  # resp.json()
        self.cache.set(url, raw_data)  # self.cache.set(url, json.dumps(data, ensure_ascii=False))

        return data

    def getIds(self, category, country, series=None,
                 distribution=None, year=None, value=None, currency=None):
        action = "list_id" + self._makeQuery(category, country, series,
                 distribution, year, value, currency)
        item_ids = self.getData(action, 'en')
        return item_ids
    
    def getCountries(self, category):
        action = "countries/cat/%s" % category
        return self.getData(action)

    def getYears(self, category, country, series=None, distribution=None,
                  value=None, currency=None):
        action = "years" + self._makeQuery(category, country, series,
                 distribution, None, value, currency)
        return self.getData(action)

    def getSeries(self, category, country, distribution=None, year=None,
                  value=None, currency=None):
        action = "series" + self._makeQuery(category, country, None,
                 distribution, year, value, currency)
        return self.getData(action)

    def getColors(self, category):
        action = "colors/cat/%s/producer/252" % category    # TODO: Remove producer filter
        return self.getData(action)

    def getDistributions(self, category, country, series=None, year=None,
                         value=None, currency=None):
        if category == 'coins':
            action = "distributions" + self._makeQuery(category, country, series,
                     None, year, value, currency)
        elif category == 'stamps':
            action = "emissions" + self._makeQuery(category, country, series,
                     None, year, value, currency)
        else:
            return []

        return self.getData(action)

    def getValues(self, category, country, series=None, distribution=None,
                  year=None, currency=None):
        action = "face_values" + self._makeQuery(category, country, series,
                 distribution, year, None, currency)
        return self.getData(action)

    def getCurrencies(self, category, country, series=None, distribution=None,
                      year=None, value=None):
        action = "currencies" + self._makeQuery(category, country, series,
                 distribution, year, value, None)
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
        self.model = model
        self.items = []

        settings = Settings()
        self.lang = settings['colnect_locale']
        self.enable_bc = self.model.settings['enable_bc']

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
                      ('stamps', self.tr("Stamps")),
                      ('philatelic_products', self.tr("Philatelic products")))

        self.categorySelector = QComboBox()
        self.categorySelector.setSizePolicy(QSizePolicy.Fixed,
                                            QSizePolicy.Fixed)
        for category in categories:
            self.categorySelector.addItem(category[1], category[0])
        default_category = self.model.settings['colnect_category']
        index = self.categorySelector.findData(default_category)
        self.categorySelector.setCurrentIndex(index)
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

        self.colnect = ColnectConnector(self)

        self.categoryChanged()

        default_country = self.model.settings['colnect_country']
        index = self.countrySelector.findData(default_country)
        if index >= 0:
            self.countrySelector.setCurrentIndex(index)
        self.countryChanged()

    def sectionDoubleClicked(self, index):
        self.table.resizeColumnToContents(index)

    def _partsEnable(self, enabled):
        for part in self.parts:
            part.setEnabled(enabled)

    def tableClicked(self, index):
        if index and index.row() < len(self.items):
            record = self.makeCoin(index)
            self.model.addCoin(record, self)

    def makeCoin(self, index):
        data = self.items[index.row()]
        category = self.categorySelector.currentData()
        record = self.model.record()
        self.colnect.makeItem(category, data, record)
        return record
    
    def _isDistributionEnabled(self, category):
        return category in ('coins', 'stamps')

    def _clearTable(self):
        self.addButton.setEnabled(False)
        self.addCloseButton.setEnabled(False)

        self.table.hide()
        self.label.show()
        self.label_empty.hide()
        self.previewButton.setEnabled(False)
        self.table.setRowCount(0)
        self.items = []

    def _updatePart(self, selector, all_values, cur_value=None):
        selector.currentIndexChanged.disconnect(self.partChanged)
        selector.clear()
        selector.addItem(self.tr("(All)"), None)
        for val in all_values:
            if selector == self.yearSelector:
                year = str(val[0])
                if '&nbsp;BC' in year:
                    if self.enable_bc:
                        year_str = year.replace('&nbsp;', ' ')
                    else:
                        year_str = str(-int(year.replace('&nbsp;BC', '')))
                    year_key = year.replace('&nbsp;', '')
                else:
                    year_str = year
                    year_key = year
                selector.addItem(year_str, year_key)
            else:
                selector.addItem(str(val[1]), val[0])
        index = selector.findData(cur_value)
        if index >= 0:
            selector.setCurrentIndex(index)
        selector.currentIndexChanged.connect(self.partChanged)

    def categoryChanged(self):
        self._clearTable()

        if self.categorySelector.currentIndex() >= 0:
            category = self.categorySelector.currentData()
            self.distributionSelector.setVisible(self._isDistributionEnabled(category))

            countries = self.colnect.getCountries(category)
            self.countrySelector.clear()
            for country in countries:
                if len(country) == 3 and country[2]:  # Country contain coins
                    self.countrySelector.addItem(country[1], country[0])
        else:
            self._partsEnable(False)

    def countryChanged(self):
        self._clearTable()

        if self.countrySelector.currentIndex() >= 0:
            self._partsEnable(True)
    
            category = self.categorySelector.currentData()
            country = self.countrySelector.currentData()
            if not country:
                return
    
            series = self.colnect.getSeries(category, country)
            self._updatePart(self.seriesSelector, series)

            if self._isDistributionEnabled(category):
                distributions = self.colnect.getDistributions(category, country)
                self._updatePart(self.distributionSelector, distributions)
    
            years = self.colnect.getYears(category, country)
            self._updatePart(self.yearSelector, years)
    
            values = self.colnect.getValues(category, country)
            self._updatePart(self.valueSelector, values)
    
            currencies = self.colnect.getCurrencies(category, country)
            self._updatePart(self.currencySelector, currencies)
        else:
            self._partsEnable(False)
    
    def partChanged(self, _index):
        self._clearTable()

        category = self.categorySelector.currentData()
        country = self.countrySelector.currentData()
        series = self.seriesSelector.currentData()
        year = self.yearSelector.currentData()
        value = self.valueSelector.currentData()
        currency = self.currencySelector.currentData()
        if self._isDistributionEnabled(category):
            distribution = self.distributionSelector.currentData()
        else:
            distribution = None

        all_series = self.colnect.getSeries(category, country,
            distribution=distribution, year=year, value=value,
            currency=currency)
        self._updatePart(self.seriesSelector, all_series, series)

        if self._isDistributionEnabled(category):
            distributions = self.colnect.getDistributions(category, country,
                series=series, year=year, value=value, currency=currency)
            self._updatePart(self.distributionSelector, distributions, distribution)

        years = self.colnect.getYears(category, country, series=series,
            distribution=distribution, value=value, currency=currency)
        self._updatePart(self.yearSelector, years, year)

        values = self.colnect.getValues(category, country, series=series,
            distribution=distribution, year=year, currency=currency)
        self._updatePart(self.valueSelector, values, value)

        currencies = self.colnect.getCurrencies(category, country, series=series,
            distribution=distribution, year=year, value=value)
        self._updatePart(self.currencySelector, currencies, currency)

        if series or distribution or year or value or currency:
            count = self.colnect.getCount(category=category, country=country,
                series=series, distribution=distribution, year=year,
                value=value, currency=currency)

            if count == 0:
                self.label_empty.show()
                self.label.hide()
            elif ((series or distribution) and year and value and currency) or (count < MAX_ITEMS):
                self.previewButton.setEnabled(True)
                self.label.hide()

    def preview(self):
        self.table.show()

        category = self.categorySelector.currentData()
        country = self.countrySelector.currentData()
        series = self.seriesSelector.currentData()
        year = self.yearSelector.currentData()
        value = self.valueSelector.currentData()
        currency = self.currencySelector.currentData()
        if self._isDistributionEnabled(category):
            distribution = self.distributionSelector.currentData()
        else:
            distribution = None

        item_ids = self.colnect.getIds(category, country, series=series,
            distribution=distribution, year=year, value=value,
            currency=currency)

        if item_ids:
            progressDlg = ProgressDialog(self.tr("Downloading"), self.tr("Cancel"),
                                         len(item_ids), self)

            fields = self.colnect.getFields(category)

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
                if isinstance(value, int):
                    if value > 5000:
                        value -= 10000
                    if self.enable_bc and value < 0:
                        value = "%d BC" % -value
                item = QTableWidgetItem(str(value))
                self.table.setItem(i, 4, item)
                if category == 'philatelic_products':
                    value = self._getFieldData(data, fields, 'Subformat')
                elif category == 'stamps':
                    value = self._getFieldData(data, fields, 'Emission')
                elif category == 'coins':
                    value = self._getFieldData(data, fields, 'Distribution')
                else:
                    value = ''
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
            if image.height() > self.HEIGHT:
                image = image.scaled(self.HEIGHT, self.HEIGHT,
                                     Qt.KeepAspectRatio, Qt.SmoothTransformation)
        return image

    def _itemUrl(self, category, item_id):
        url = "https://colnect.com/%s/%s/%s/%d" % (self.lang, category,
                                                   category[:-1], item_id)
        return url

    def addCoins(self, indexes):
        progressDlg = None

        for progress, index in enumerate(indexes):
            if index.row() >= len(self.items):
                break

            if progressDlg:
                progressDlg.setValue(progress)
                if progressDlg.wasCanceled():
                    break

            record = self.makeCoin(index)

            if progressDlg:
                if not record.value('status'):
                    record.setValue('status', self.model.settings['default_status'])
                self.model.appendRecord(record)
            else:
                btn = self.model.addCoins(record, len(indexes) - progress)
                if btn == QDialogButtonBox.Abort:
                    break
                if btn == QDialogButtonBox.SaveAll:
                    progressDlg = ProgressDialog(
                        self.tr("Inserting records"),
                        self.tr("Cancel"),
                        len(indexes), self)

        if progressDlg:
            progressDlg.reset()

    def clicked(self, button):
        if button == self.addButton:
            indexes = self.table.selectionModel().selectedRows()
            self.addCoins(indexes)
        elif button == self.addCloseButton:
            indexes = self.table.selectionModel().selectedRows()
            self.addCoins(indexes)

            self.accept()
        else:
            self.accept()

    def done(self, r):
        if self.countrySelector.currentIndex() >= 0:
            self.model.settings['colnect_country'] = self.countrySelector.currentData()
        if self.categorySelector.currentIndex() >= 0:
            self.model.settings['colnect_category'] = self.categorySelector.currentData()
        self.model.settings.save()

        self.colnect.close()
        super().done(r)


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
