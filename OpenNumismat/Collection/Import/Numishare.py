# http://numismatics.org/search/apis
# http://numismatics.org/crro/apis
# http://nomisma.org/apis, http://nomisma.org/datasets (https://oscar.nationalmuseum.ch/apis/search?q=reference_facet:%22NHMZ%201-288a%22, https://oscar.nationalmuseum.ch/results?q=*%3A*)
# http://nomisma.org/id/coins_ptolemaic_empire
# https://github.com/nomisma/data/blob/master/id/ar.rdf
# Find: https://numismatics.org/search/apis/search?q=denomination_facet%3A%22Victoriatus%22+AND+department_facet%3A%22Roman%22&lang=ru
# Coin: https://numismatics.org/search/id/1944.100.147.jsonld
# Details: http://numismatics.org/crro/id/rrc-71.1a.jsonld

import os
import tempfile
import urllib.request
from urllib.parse import quote_plus
from socket import timeout

numishareAvailable = True

try:
    import lxml.etree
    import lxml.html
except ImportError:
    print('lxml module missed. Importing from Numishare not available')
    numishareAvailable = False

from PyQt5.QtCore import Qt, QObject, QDate, QByteArray
from PyQt5.QtGui import QImage, QPixmap, QIcon
from PyQt5.QtSql import QSqlDatabase, QSqlQuery
from PyQt5.QtWidgets import *

from OpenNumismat import version
from OpenNumismat.Settings import Settings
from OpenNumismat.Tools.CursorDecorators import waitCursorDecorator
from OpenNumismat.Tools.DialogDecorators import storeDlgSizeDecorator
from OpenNumismat.Tools.Gui import ProgressDialog


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
        print(url)
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
        if isinstance(data, bytes):
            data = QByteArray(data)
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


class NumishareConnector(QObject):

    def __init__(self, parent):
        super().__init__(parent)

        self.cache = ColnectCache()
        self.skip_currency = Settings()['colnect_skip_currency']
        self.lang = Settings()['colnect_locale']

    @waitCursorDecorator
    def getImage(self, url, full):
        data = None

        if not url:
            return data

        if not full:
            # full images was not cached - store previous behaviour
            data = self.cache.get(ColnectCache.Image, url)
            if data:
                return data

        try:
            req = urllib.request.Request(url,
                                    headers={'User-Agent': version.AppName})
            data = urllib.request.urlopen(req, timeout=30).read()
        except:
            return None

        if not full:
            self.cache.set(ColnectCache.Image, url, data)

        return data

    def _baseUrl(self):
        url = "http://numismatics.org/search/"
        return url
    
    @waitCursorDecorator
    def _download(self, action):
        url = self._baseUrl() + action
        raw_data = self.cache.get(ColnectCache.Action, url)
        is_cashed = bool(raw_data)
        if not is_cashed:
            try:
                req = urllib.request.Request(url,
                                        headers={'User-Agent': version.AppName})
                raw_data = urllib.request.urlopen(req, timeout=10).read().decode()
            except timeout:
                QMessageBox.warning(self.parent(), "Numishare",
                                    self.tr("Numishare not response"))
                return ''
            except:
                return ''

        if not is_cashed:
            self.cache.set(ColnectCache.Action, url, raw_data)

        return raw_data

    def _makeQuery(self, images, department=None, country=None, year=None, dinasty=None,
                 ruler=None, denomination=None, material=None, type_=None):
        params = []
        if images:
            params.append('imagesavailable:true')
        if department:
            params.append('department_facet:"%s"' % department)
        if country:
            params.append('region_facet:"%s"' % country)
        if year:
            params.append('year_num:"%s"' % year)
        if dinasty:
            params.append('dynasty_facet:"%s"' % dinasty)
        if ruler:
            params.append('authority_facet:"%s"' % ruler)
        if denomination:
            params.append('denomination_facet:"%s"' % denomination)
        if material:
            params.append('material_facet:"%s"' % material)
        if type_:
            params.append('objectType_facet:"%s"' % type_)

        return quote_plus(" AND ".join(params))

    def getCount(self, images, department=None, country=None, year=None, dinasty=None,
                 ruler=None, denomination=None, material=None, type_=None):
        query = self._makeQuery(images, department, country, year, dinasty,
                 ruler, denomination, material, type_)
        action = "apis/search?q=" + query + "&format=rss"
        
        raw_data = self._download(action)

        if not raw_data:
            return 0

        tree = lxml.etree.fromstring(raw_data.encode('utf-8'))
        count = tree.xpath("./channel/opensearch:totalResults", namespaces=tree.nsmap)
    
        return int(count[0].text)
    
    def getData(self, item_id):
        action = "id/%s.xml" % item_id
        
        raw_data = self._download(action)

        return raw_data
    
    def getIds(self, images, department=None, country=None, year=None, dinasty=None,
                 ruler=None, denomination=None, material=None, type_=None):
        query = self._makeQuery(images, department, country, year, dinasty,
                 ruler, denomination, material, type_)

        res = []
        start_index = 0

        while True:
            action = "apis/search?q=" + query + "&format=rss"
            if start_index > 0:
                action += "&start=%d" % start_index
            
            raw_data = self._download(action)
    
            if raw_data:
                tree = lxml.etree.fromstring(raw_data.encode('utf-8'))
                rows = tree.xpath("./channel/item/link")
                
                res.extend([row.text.split('/')[-1] for row in rows])
                
                count = tree.xpath("./channel/opensearch:totalResults", namespaces=tree.nsmap)
                count = int(count[0].text)
                items_per_page = tree.xpath("./channel/opensearch:itemsPerPage", namespaces=tree.nsmap)
                items_per_page = int(items_per_page[0].text)

                start_index += items_per_page
                if start_index >= count:
                    break;
            else:
                break
    
        print(res)
        return res
    
    def getItems(self, target, images, department=None, country=None, year=None, dinasty=None,
                 ruler=None, denomination=None, material=None, type_=None):
        query = self._makeQuery(images, department, country, year, dinasty,
                 ruler, denomination, material, type_)
        action = "get_facet_options?q=" + query + "&category=" + target + "&mincount=1&pipeline=results&lang=" + self.lang

        raw_data = self._download(action)

        if not raw_data or "<option disabled>No options available</option>" in raw_data:
            return []

        tree = lxml.html.fromstring(raw_data)
        rows = tree.xpath("/html/body/select/option")

        return [(row.values()[0], row.text) for row in rows]

    def close(self):
        self.cache.close()


@storeDlgSizeDecorator
class NumishareDialog(QDialog):
    HEIGHT = 62

    def __init__(self, model, parent=None):
        super().__init__(parent,
                         Qt.WindowCloseButtonHint | Qt.WindowSystemMenuHint)
        self.setWindowIcon(QIcon(':/numishare.png'))
        self.setWindowTitle("Numishare")

        fields = model.fields

        settings = Settings()
        self.lang = settings['colnect_locale']
        self.autoclose = settings['colnect_autoclose']

        layout = QFormLayout()
        layout.setRowWrapPolicy(QFormLayout.WrapLongRows)

        departments = (('Greek', self.tr("Greek")),
                       ('Roman', self.tr("Roman")),
                       ('Byzantine', self.tr("Byzantine")), 
                       ('Islamic', self.tr("Islamic")), 
                       ('East%%20Asian', self.tr("East Asia")), 
                       ('South%%20Asian', self.tr("South Asia")), 
                       ('Medieval', self.tr("Medieval")), 
                       ('Modern', self.tr("Modern")), 
                       ('North%20American', self.tr("North America")), 
                       ('Latin%20American', self.tr("Latin America")), 
                       ('Medal', self.tr("Medals And Decorations")))

        self.departmentSelector = QComboBox()
        self.departmentSelector.setSizePolicy(QSizePolicy.Fixed,
                                              QSizePolicy.Fixed)
        for department in departments:
            self.departmentSelector.addItem(department[1], department[0])
        layout.addRow(fields.getCustomTitle('region'), self.departmentSelector)
        self.departmentSelector.currentIndexChanged.connect(self.departmentChanged)

        self.countrySelector = QComboBox()
        self.countrySelector.setSizePolicy(QSizePolicy.Fixed,
                                           QSizePolicy.Fixed)
        self.countrySelector.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.countrySelector.currentIndexChanged.connect(self.partChanged)
        layout.addRow(fields.getCustomTitle('country'), self.countrySelector)

        self.dinastySelector = QComboBox()
        self.dinastySelector.setSizePolicy(QSizePolicy.Fixed,
                                           QSizePolicy.Fixed)
        self.dinastySelector.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.dinastySelector.currentIndexChanged.connect(self.partChanged)
        layout.addRow(fields.getCustomTitle('period'), self.dinastySelector)

        self.rulerSelector = QComboBox()
        self.rulerSelector.setSizePolicy(QSizePolicy.Fixed,
                                         QSizePolicy.Fixed)
        self.rulerSelector.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.rulerSelector.currentIndexChanged.connect(self.partChanged)
        layout.addRow(fields.getCustomTitle('ruler'), self.rulerSelector)

        self.yearSelector = QComboBox()
        self.yearSelector.setSizePolicy(QSizePolicy.Fixed,
                                        QSizePolicy.Fixed)
        self.yearSelector.currentIndexChanged.connect(self.partChanged)
        self.yearSelector.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        layout.addRow(fields.getCustomTitle('year'), self.yearSelector)

        self.denominationSelector = QComboBox()
        self.denominationSelector.setSizePolicy(QSizePolicy.Fixed,
                                         QSizePolicy.Fixed)
        self.denominationSelector.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.denominationSelector.currentIndexChanged.connect(self.partChanged)
        layout.addRow(fields.getCustomTitle('unit'), self.denominationSelector)

        self.materialSelector = QComboBox()
        self.materialSelector.setSizePolicy(QSizePolicy.Fixed,
                                            QSizePolicy.Fixed)
        self.materialSelector.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.materialSelector.currentIndexChanged.connect(self.partChanged)
        layout.addRow(fields.getCustomTitle('material'), self.materialSelector)

        self.typeSelector = QComboBox()
        self.typeSelector.setSizePolicy(QSizePolicy.Fixed,
                                            QSizePolicy.Fixed)
        self.typeSelector.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.typeSelector.currentIndexChanged.connect(self.partChanged)
        layout.addRow(fields.getCustomTitle('type'), self.typeSelector)

        self.imagesSelector = QCheckBox(self.tr("Has images"))
        self.imagesSelector.stateChanged.connect(self.partChanged)
        layout.addRow(self.imagesSelector)

        self.parts = (self.countrySelector, self.dinastySelector,
                      self.rulerSelector, self.typeSelector, self.yearSelector,
                      self.denominationSelector, self.materialSelector,
                      self.imagesSelector)

        self.table = QTableWidget(self)
        self.table.doubleClicked.connect(self.tableClicked)
        self.table.setColumnCount(10)
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

        field_names = ('obverseimg', 'reverseimg', 'title', 'unit', 'mint',
                       'country', 'period', 'ruler', 'year', 'material')
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

        self.numishare = NumishareConnector(self)

        default_department = self.settings['numishare_department']
        index = self.departmentSelector.findData(default_department)
        if index >= 0:
            self.departmentSelector.setCurrentIndex(index)
            self.departmentChanged(0)

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
        if index.row() < len(self.items):
            item_id = self.items[index.row()]
            newRecord = self.model.record()
            self.makeItem(item_id, newRecord)
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

    def _getValue(self, tree, key):
        nsmap = {'nuds': 'http://nomisma.org/nuds',
                 'xlink': 'http://www.w3.org/1999/xlink',
                 'mets': 'http://www.loc.gov/METS/'}

        el = tree.xpath(key, namespaces=nsmap)
        if el:
            return el[0].text
        
        return None

    def _getAttrib(self, tree, key, attrib):
        nsmap = {'nuds': 'http://nomisma.org/nuds',
                 'xlink': 'http://www.w3.org/1999/xlink',
                 'mets': 'http://www.loc.gov/METS/'}

        el = tree.xpath(key, namespaces=nsmap)
        if el:
            return el[0].attrib[attrib]
        
        return None

    def _setRecordField(self, tree, key, record, field):
        value = self._getValue(tree, key)
        if value:
            record.setValue(field, value)
            return True
        
        return False

    def makeItem(self, item_id, record):
        data = self.numishare.getData(item_id)
        tree = lxml.etree.fromstring(data.encode('utf-8'))

        self._setRecordField(tree, "./nuds:descMeta/nuds:title", record, 'title')
        self._setRecordField(tree, "./nuds:descMeta/nuds:typeDesc/nuds:geographic/nuds:geogname[@xlink:role='region']", record, 'country')
        self._setRecordField(tree, "./nuds:descMeta/nuds:typeDesc/nuds:geographic/nuds:geogname[@xlink:role='mint']", record, 'mint')
        self._setRecordField(tree, "./nuds:descMeta/nuds:typeDesc/nuds:denomination", record, 'unit')
        self._setRecordField(tree, "./nuds:descMeta/nuds:typeDesc/nuds:material", record, 'material')
        self._setRecordField(tree, "./nuds:descMeta/nuds:physDesc/nuds:measurementsSet/nuds:weight", record, 'weight')
        self._setRecordField(tree, "./nuds:descMeta/nuds:physDesc/nuds:measurementsSet/nuds:diameter", record, 'diameter')
        self._setRecordField(tree, "./nuds:descMeta/nuds:adminDesc/nuds:department", record, 'region')
        self._setRecordField(tree, "./nuds:descMeta/nuds:typeDesc/nuds:authority/nuds:persname[@xlink:role='dynasty']", record, 'period')
        self._setRecordField(tree, "./nuds:descMeta/nuds:typeDesc/nuds:authority/nuds:persname[@xlink:role='authority']", record, 'ruler')
        self._setRecordField(tree, "./nuds:descMeta/nuds:physDesc/nuds:measurementsSet/nuds:shape", record, 'shape')
        if not self._setRecordField(tree, "./nuds:descMeta/nuds:subjectSet/nuds:subject[@localType='subjectEvent']", record, 'subjectshort'):
            self._setRecordField(tree, "./nuds:descMeta/nuds:subjectSet/nuds:subject[@localType='subjectPerson']", record, 'subjectshort')
        self._setRecordField(tree, "./nuds:descMeta/nuds:subjectSet/nuds:subject[@localType='series']", record, 'series')
        self._setRecordField(tree, "./nuds:descMeta/nuds:noteSet/nuds:note", record, 'note')

        el1 = self._getValue(tree, "./nuds:descMeta/nuds:typeDesc/nuds:obverse/nuds:legend")
        el2 = self._getValue(tree, "./nuds:descMeta/nuds:typeDesc/nuds:obverse/nuds:type/nuds:description")
        value = ' - '.join(filter(None, [el1, el2]))
        record.setValue('obversedesign', value)
        el1 = self._getValue(tree, "./nuds:descMeta/nuds:typeDesc/nuds:reverse/nuds:legend")
        el2 = self._getValue(tree, "./nuds:descMeta/nuds:typeDesc/nuds:reverse/nuds:type/nuds:description")
        value = ' - '.join(filter(None, [el1, el2]))
        record.setValue('reversedesign', value)

        if not self._setRecordField(tree, "./nuds:descMeta/nuds:typeDesc/nuds:date", record, 'year'):
            self._setRecordField(tree, "./nuds:descMeta/nuds:typeDesc/nuds:dateOnObject/nuds:date", record, 'year')
        el1 = self._getValue(tree, "./nuds:descMeta/nuds:typeDesc/nuds:dateRange/nuds:fromDate")
        el2 = self._getValue(tree, "./nuds:descMeta/nuds:typeDesc/nuds:dateRange/nuds:toDate")
        value = ' - '.join(filter(None, [el1, el2]))
        record.setValue('dateemis', value)
        
        nsmap = {'nuds': 'http://nomisma.org/nuds',
                 'xlink': 'http://www.w3.org/1999/xlink',
                 'mets': 'http://www.loc.gov/METS/'}

        refs = tree.xpath("./nuds:descMeta/nuds:refDesc/nuds:reference", namespaces=nsmap)
        for i, ref in enumerate(refs[:4], start=1):
            value = " ".join([item.text for item in ref])
            record.setValue('catalognum%d' % i, value)

        id_ = self._getValue(tree, "./nuds:control/nuds:recordId")
        record.setValue('url', "https://numismatics.org/collection/%s" % id_)

        url = self._getAttrib(tree, "./nuds:digRep/mets:fileSec/mets:fileGrp[@USE='obverse']/mets:file[@USE='archive']/mets:FLocat",
                             '{http://www.w3.org/1999/xlink}href')
        if url:
            image = self.numishare.getImage(url, True)
            record.setValue('obverseimg', image)

        url = self._getAttrib(tree, "./nuds:digRep/mets:fileSec/mets:fileGrp[@USE='reverse']/mets:file[@USE='archive']/mets:FLocat",
                             '{http://www.w3.org/1999/xlink}href')
        if url:
            image = self.numishare.getImage(url, True)
            record.setValue('reverseimg', image)

    def departmentChanged(self, _index):
        self._clearTable()
        self._partsEnable(True)

        self.countrySelector.clear()
        self.rulerSelector.clear()
        self.dinastySelector.clear()
        self.yearSelector.clear()
        self.denominationSelector.clear()
        self.materialSelector.clear()
        self.typeSelector.clear()
        
        self.partChanged()
        
        department = self.departmentSelector.currentData()
        self.settings['numishare_department'] = department

    def partChanged(self):
        self._clearTable()

        department = self.departmentSelector.currentData()
        country = self.countrySelector.currentData()
        ruler = self.rulerSelector.currentData()
        dinasty = self.dinastySelector.currentData()
        year = self.yearSelector.currentData()
        denomination = self.denominationSelector.currentData()
        material = self.materialSelector.currentData()
        type_ = self.typeSelector.currentData()
        images = self.imagesSelector.isChecked()

        countries = self.numishare.getItems("region_facet", images, department=department,
                ruler=ruler, dinasty=dinasty, year=year,
                denomination=denomination, material=material, type_=type_)
        self.countrySelector.currentIndexChanged.disconnect(self.partChanged)
        self.countrySelector.clear()
        self.countrySelector.addItem(self.tr("(All)"), None)
        for item in countries:
            self.countrySelector.addItem(item[1], item[0])
        index = self.countrySelector.findData(country)
        if index >= 0:
            self.countrySelector.setCurrentIndex(index)
        self.countrySelector.currentIndexChanged.connect(self.partChanged)

        rulers = self.numishare.getItems("authority_facet", images, department=department,
                country=country, dinasty=dinasty, year=year,
                denomination=denomination, material=material, type_=type_)
        self.rulerSelector.currentIndexChanged.disconnect(self.partChanged)
        self.rulerSelector.clear()
        self.rulerSelector.addItem(self.tr("(All)"), None)
        for item in rulers:
            self.rulerSelector.addItem(item[1], item[0])
        index = self.rulerSelector.findData(ruler)
        if index >= 0:
            self.rulerSelector.setCurrentIndex(index)
        self.rulerSelector.currentIndexChanged.connect(self.partChanged)

        dinasties = self.numishare.getItems("dynasty_facet", images, department=department,
                country=country, ruler=ruler, year=year,
                denomination=denomination, material=material, type_=type_)
        self.dinastySelector.currentIndexChanged.disconnect(self.partChanged)
        self.dinastySelector.clear()
        self.dinastySelector.addItem(self.tr("(All)"), None)
        for item in dinasties:
            self.dinastySelector.addItem(item[1], item[0])
        index = self.dinastySelector.findData(dinasty)
        if index >= 0:
            self.dinastySelector.setCurrentIndex(index)
        self.dinastySelector.currentIndexChanged.connect(self.partChanged)

        years = self.numishare.getItems("year_num", images, department=department,
                country=country, ruler=ruler, dinasty=dinasty,
                denomination=denomination, material=material, type_=type_)
        self.yearSelector.currentIndexChanged.disconnect(self.partChanged)
        self.yearSelector.clear()
        self.yearSelector.addItem(self.tr("(All)"), None)
        for item in years:
            self.yearSelector.addItem(item[0], item[0])
        index = self.yearSelector.findData(year)
        if index >= 0:
            self.yearSelector.setCurrentIndex(index)
        self.yearSelector.currentIndexChanged.connect(self.partChanged)

        denominations = self.numishare.getItems("denomination_facet", images, department=department,
                country=country, ruler=ruler, dinasty=dinasty, year=year,
                material=material, type_=type_)
        self.denominationSelector.currentIndexChanged.disconnect(self.partChanged)
        self.denominationSelector.clear()
        self.denominationSelector.addItem(self.tr("(All)"), None)
        for item in denominations:
            self.denominationSelector.addItem(item[1], item[0])
        index = self.denominationSelector.findData(denomination)
        if index >= 0:
            self.denominationSelector.setCurrentIndex(index)
        self.denominationSelector.currentIndexChanged.connect(self.partChanged)

        materials = self.numishare.getItems("material_facet", images, department=department,
                country=country, ruler=ruler, dinasty=dinasty, year=year,
                denomination=denomination, type_=type_)
        self.materialSelector.currentIndexChanged.disconnect(self.partChanged)
        self.materialSelector.clear()
        self.materialSelector.addItem(self.tr("(All)"), None)
        for item in materials:
            self.materialSelector.addItem(item[1], item[0])
        index = self.materialSelector.findData(material)
        if index >= 0:
            self.materialSelector.setCurrentIndex(index)
        self.materialSelector.currentIndexChanged.connect(self.partChanged)

        types = self.numishare.getItems("objectType_facet", images, department=department,
                country=country, ruler=ruler, dinasty=dinasty, year=year,
                denomination=denomination, material=material)
        self.typeSelector.currentIndexChanged.disconnect(self.partChanged)
        self.typeSelector.clear()
        self.typeSelector.addItem(self.tr("(All)"), None)
        for item in types:
            self.typeSelector.addItem(item[1], item[0])
        index = self.typeSelector.findData(type_)
        if index >= 0:
            self.typeSelector.setCurrentIndex(index)
        self.typeSelector.currentIndexChanged.connect(self.partChanged)

        if country or ruler or dinasty or year or denomination or material or type_:
            count = self.numishare.getCount(images, department=department,
                country=country, ruler=ruler, dinasty=dinasty, year=year,
                denomination=denomination, material=material, type_=type_)
            print('TOTAL_LEN', count)

            if count == 0:
                self.label_empty.show()
                self.label.hide()
            else:
                self.previewButton.setEnabled(True)
                self.label.hide()

    def preview(self):
        self.table.show()

        department = self.departmentSelector.currentData()
        country = self.countrySelector.currentData()
        ruler = self.rulerSelector.currentData()
        dinasty = self.dinastySelector.currentData()
        year = self.yearSelector.currentData()
        denomination = self.denominationSelector.currentData()
        material = self.materialSelector.currentData()
        type_ = self.typeSelector.currentData()
        images = self.imagesSelector.isChecked()

        item_ids = self.numishare.getIds(images, department=department,
                country=country, ruler=ruler, dinasty=dinasty, year=year,
                denomination=denomination, material=material, type_=type_)

        if item_ids:
            progressDlg = ProgressDialog(self.tr("Downloading"), self.tr("Cancel"),
                                         len(item_ids), self)

            self.table.setRowCount(len(item_ids))
            for i, item_id in enumerate(item_ids):
                progressDlg.step()
                if progressDlg.wasCanceled():
                    break

                self.items.append(item_id)
                
                data = self.numishare.getData(item_id)
                tree = lxml.etree.fromstring(data.encode('utf-8'))

                url = self._getAttrib(tree, "./nuds:digRep/mets:fileSec/mets:fileGrp[@USE='obverse']/mets:file[@USE='thumbnail']/mets:FLocat",
                                     '{http://www.w3.org/1999/xlink}href')
                if url:
                    image = self._getImage(url)
                    pixmap = QPixmap.fromImage(image)
                    item = QTableWidgetItem()
                    item.setData(Qt.DecorationRole, pixmap)
                    self.table.setItem(i, 0, item)

                url = self._getAttrib(tree, "./nuds:digRep/mets:fileSec/mets:fileGrp[@USE='reverse']/mets:file[@USE='thumbnail']/mets:FLocat",
                                     '{http://www.w3.org/1999/xlink}href')
                if url:
                    image = self._getImage(url)
                    pixmap = QPixmap.fromImage(image)
                    item = QTableWidgetItem()
                    item.setData(Qt.DecorationRole, pixmap)
                    self.table.setItem(i, 1, item)

                value = self._getValue(tree, "./nuds:descMeta/nuds:title")
                item = QTableWidgetItem(value)
                self.table.setItem(i, 2, item)

                value = self._getValue(tree, "./nuds:descMeta/nuds:typeDesc/nuds:denomination")
                item = QTableWidgetItem(value)
                self.table.setItem(i, 3, item)

                value = self._getValue(tree, "./nuds:descMeta/nuds:typeDesc/nuds:geographic/nuds:geogname[@xlink:role='mint']")
                item = QTableWidgetItem(value)
                self.table.setItem(i, 4, item)

                value = self._getValue(tree, "./nuds:descMeta/nuds:typeDesc/nuds:geographic/nuds:geogname[@xlink:role='region']")
                item = QTableWidgetItem(value)
                self.table.setItem(i, 5, item)

                value = self._getValue(tree, "./nuds:descMeta/nuds:typeDesc/nuds:authority/nuds:persname[@xlink:role='dynasty']")
                item = QTableWidgetItem(value)
                self.table.setItem(i, 6, item)

                value = self._getValue(tree, "./nuds:descMeta/nuds:typeDesc/nuds:authority/nuds:persname[@xlink:role='authority']")
                item = QTableWidgetItem(value)
                self.table.setItem(i, 7, item)

                value = self._getValue(tree, "./nuds:descMeta/nuds:typeDesc/nuds:date")
                if not value:
                    value = self._getValue(tree, "./nuds:descMeta/nuds:typeDesc/nuds:dateOnObject/nuds:date")
                if not value:
                    el1 = self._getValue(tree, "./nuds:descMeta/nuds:typeDesc/nuds:dateRange/nuds:fromDate")
                    el2 = self._getValue(tree, "./nuds:descMeta/nuds:typeDesc/nuds:dateRange/nuds:toDate")
                    value = ' - '.join(filter(None, [el1, el2]))
                item = QTableWidgetItem(value)
                self.table.setItem(i, 8, item)
            
                value = self._getValue(tree, "./nuds:descMeta/nuds:typeDesc/nuds:material")
                item = QTableWidgetItem(value)
                self.table.setItem(i, 9, item)

            progressDlg.reset()

            self.addButton.setEnabled(True)
            self.addCloseButton.setEnabled(True)

    def _getImage(self, url):
        image = QImage()

        if not url:
            return image

        result = image.loadFromData(self.numishare.getImage(url, False))
        if result:
            if image.height() > self.HEIGHT:
                image = image.scaled(self.HEIGHT, self.HEIGHT,
                                     Qt.KeepAspectRatio, Qt.SmoothTransformation)
        return image

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
        self.numishare.close()
        super().accept()
