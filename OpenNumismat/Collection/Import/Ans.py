import re
import urllib3
from urllib.parse import quote_plus

ansAvailable = True

try:
    import lxml.etree
    import lxml.html
except ImportError:
    print('lxml module missed. Importing from ANS not available')
    ansAvailable = False

from PySide6.QtCore import Qt, QObject
from PySide6.QtGui import QImage, QPixmap, QIcon
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
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
from OpenNumismat.Settings import Settings
from OpenNumismat.Tools.CursorDecorators import waitCursorDecorator
from OpenNumismat.Tools.DialogDecorators import storeDlgSizeDecorator
from OpenNumismat.Tools.Gui import ProgressDialog

CONNECTION_TIMEOUT = 10


class AnsConnector(QObject):

    def __init__(self, parent):
        super().__init__(parent)

        urllib3.disable_warnings()
        timeout = urllib3.Timeout(connect=CONNECTION_TIMEOUT / 2,
                                  read=CONNECTION_TIMEOUT)
        self.http = urllib3.PoolManager(num_pools=5,
                                        headers={'User-Agent': version.AppName},
                                        timeout=timeout,
                                        cert_reqs="CERT_NONE")
        self.cache = Cache()
        if Settings()['ans_locale_en']:
            self.lang = 'en'
        else:
            self.lang = Settings()['locale']

    @waitCursorDecorator
    def getImage(self, url, full):
        data = None

        if not url:
            return data

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

    @waitCursorDecorator
    def download_data(self, url):
        raw_data = self.cache.get(url)
        is_cashed = bool(raw_data)
        if not is_cashed:
            try:
                resp = self.http.request("GET", url)
                raw_data = resp.data.decode()
            except urllib3.exceptions.MaxRetryError:
                QMessageBox.warning(self.parent(), "ANS",
                                    self.tr("American Numismatic Society not response"))
                return ''
            except:
                return ''

        if not is_cashed:
            self.cache.set(url, raw_data)

        return raw_data

    def _baseUrl(self):
        url = "https://numismatics.org/search/"
        return url
    
    def _makeQuery(self, images, department=None, country=None, year=None, dynasty=None,
                 ruler=None, denomination=None, material=None, type_=None):
        params = []
        if images:
            params.append('imagesavailable:true')
        if department:
            params.append(f'department_facet:"{department}"')
        if country:
            params.append(f'region_facet:"{country}"')
        if year:
            params.append(f'year_num:"{year}"')
        if dynasty:
            params.append(f'dynasty_facet:"{dynasty}"')
        if ruler:
            params.append(f'authority_facet:"{ruler}"')
        if denomination:
            params.append(f'denomination_facet:"{denomination}"')
        if material:
            params.append(f'material_facet:"{material}"')
        if type_:
            params.append(f'objectType_facet:"{type_}"')

        return quote_plus(" AND ".join(params))

    def getCount(self, images, department=None, country=None, year=None, dynasty=None,
                 ruler=None, denomination=None, material=None, type_=None):
        query = self._makeQuery(images, department, country, year, dynasty,
                 ruler, denomination, material, type_)
        action = f"apis/search?q={query}&format=rss"
        
        raw_data = self.download_data(self._baseUrl() + action)

        if not raw_data:
            return 0

        tree = lxml.etree.fromstring(raw_data.encode('utf-8'))
        count = tree.xpath("./channel/opensearch:totalResults", namespaces=tree.nsmap)
    
        return int(count[0].text)
    
    def getTranslation(self, src, lang):
        url = f"https://nomisma.org/apis/getLabel?uri={src}&lang={lang}"
        raw_data = self.download_data(url)
        if raw_data:
            tree = lxml.etree.fromstring(raw_data.encode('utf-8'))
            data = tree.xpath("/response")
            if data:
                return data[0].text
        
        return ''
    
    def getData(self, item_id):
        action = f"id/{item_id}.xml"
        
        raw_data = self.download_data(self._baseUrl() + action)

        return raw_data
    
    def getIds(self, images, department=None, country=None, year=None, dynasty=None,
               ruler=None, denomination=None, material=None, type_=None):
        query = self._makeQuery(images, department, country, year, dynasty,
                 ruler, denomination, material, type_)

        res = []
        start_index = 0

        while True:
            action = f"apis/search?q={query}&format=rss"
            if start_index > 0:
                action += f"&start={start_index}"
            
            raw_data = self.download_data(self._baseUrl() + action)
    
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
                    break
            else:
                break
    
        return res
    
    def getItems(self, target, images, department=None, country=None, year=None, dynasty=None,
                 ruler=None, denomination=None, material=None, type_=None):
        query = self._makeQuery(images, department, country, year, dynasty,
                 ruler, denomination, material, type_)
        action = f"get_facet_options?q={query}&category={target}&mincount=1&pipeline=results&lang={self.lang}"

        raw_data = self.download_data(self._baseUrl() + action)

        if not raw_data or "<option disabled>No options available</option>" in raw_data:
            return []

        tree = lxml.html.fromstring(raw_data)
        rows = tree.xpath("/html/body/select/option")

        return [(row.values()[0], row.text) for row in rows]

    def close(self):
        self.cache.close()


@storeDlgSizeDecorator
class AnsDialog(QDialog):
    HEIGHT = 62
    NSMAP = {'nuds': 'http://nomisma.org/nuds',
             'xlink': 'http://www.w3.org/1999/xlink',
             'mets': 'http://www.loc.gov/METS/'}

    def __init__(self, model, parent=None):
        super().__init__(parent,
                         Qt.WindowCloseButtonHint | Qt.WindowSystemMenuHint)
        self.setWindowIcon(QIcon(':/ans.png'))
        self.setWindowTitle("American Numismatic Society")

        fields = model.fields
        self.model = model
        self.items = []

        settings = Settings()
        if settings['ans_locale_en']:
            self.lang = 'en'
        else:
            self.lang = settings['locale']
        self.split_denomination = settings['ans_split_denomination']
        self.trim_title = settings['ans_trim_title']
        self.trim_title = settings['ans_trim_title']
        self.enable_bc = self.model.settings['enable_bc']

        layout = QFormLayout()
        layout.setRowWrapPolicy(QFormLayout.WrapLongRows)

        mainLabel = QLabel(self.tr(
            "Catalog information courtesy of"
            " the <a href=\"https://numismatics.org/search/\">"
            "American Numismatic Society</a> collections database."))
        mainLabel.setTextFormat(Qt.RichText)
        mainLabel.setTextInteractionFlags(Qt.TextBrowserInteraction)
        mainLabel.setOpenExternalLinks(True)
        font = mainLabel.font()
        font.setPointSize(11)
        mainLabel.setFont(font)
        layout.addRow(mainLabel)
        licenseLabel = QLabel(self.tr(
            "All images of objects produced on or before 1925 are in the"
            " <a href=\"https://creativecommons.org/choose/mark/\">"
            "Public Domain</a>. Others are available for Non-Commercial purposes."
            " <a href=\"https://numismatics.org/collections/photography-permissions/\">Policy</a>."))
        licenseLabel.setTextFormat(Qt.RichText)
        licenseLabel.setTextInteractionFlags(Qt.TextBrowserInteraction)
        licenseLabel.setOpenExternalLinks(True)
        layout.addRow(licenseLabel)
        layout.addRow(QWidget())

        departments = (('Greek', self.tr("Greek")),
                       ('Roman', self.tr("Roman")),
                       ('Byzantine', self.tr("Byzantine")), 
                       ('Islamic', self.tr("Islamic")), 
                       ('East Asian', self.tr("East Asia")), 
                       ('South Asian', self.tr("South Asia")), 
                       ('Medieval', self.tr("Medieval")), 
                       ('Modern', self.tr("Modern")), 
                       ('North American', self.tr("North America")), 
                       ('Latin American', self.tr("Latin America")), 
                       ('Medal', self.tr("Medals And Decorations")),
                       ('Decoration', self.tr("Decoration")))

        self.departmentSelector = QComboBox()
        self.departmentSelector.setSizePolicy(QSizePolicy.Fixed,
                                              QSizePolicy.Fixed)
        for department in departments:
            self.departmentSelector.addItem(department[1], department[0])
        ans_department = self.model.settings['ans_department']
        index = self.departmentSelector.findData(ans_department)
        self.departmentSelector.setCurrentIndex(index)
        layout.addRow(fields.getCustomTitle('region'), self.departmentSelector)
        self.departmentSelector.currentIndexChanged.connect(self.departmentChanged)

        self.countrySelector = QComboBox()
        self.countrySelector.setSizePolicy(QSizePolicy.Fixed,
                                           QSizePolicy.Fixed)
        self.countrySelector.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.countrySelector.currentIndexChanged.connect(self.partChanged)
        layout.addRow(fields.getCustomTitle('country'), self.countrySelector)

        self.dynastySelector = QComboBox()
        self.dynastySelector.setSizePolicy(QSizePolicy.Fixed,
                                           QSizePolicy.Fixed)
        self.dynastySelector.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.dynastySelector.currentIndexChanged.connect(self.partChanged)
        layout.addRow(fields.getCustomTitle('period'), self.dynastySelector)

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
        if self.model.settings['ans_has_image']:
            self.imagesSelector.setCheckState(Qt.Checked)
        self.imagesSelector.checkStateChanged.connect(self.partChanged)
        layout.addRow(self.imagesSelector)

        self.parts = (self.countrySelector, self.dynastySelector,
                      self.rulerSelector, self.typeSelector, self.yearSelector,
                      self.denominationSelector, self.materialSelector)

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

        self.connector = AnsConnector(self)

        self.departmentChanged()

    def sectionDoubleClicked(self, index):
        self.table.resizeColumnToContents(index)

    def _partsEnable(self, enabled):
        for part in self.parts:
            part.setEnabled(enabled)
        self.imagesSelector.setEnabled(enabled)
        
    def tableClicked(self, index):
        if index and index.row() < len(self.items):
            record = self.makeCoin(index)
            self.model.addCoin(record, self)

    def makeCoin(self, index):
        item_id = self.items[index.row()]
        record = self.model.record()
        self.makeItem(item_id, record)
        return record

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
        el = tree.xpath(key, namespaces=self.NSMAP)
        if el:
            if el[0].attrib.has_key('{http://www.w3.org/1999/xlink}href'):
                src = el[0].attrib['{http://www.w3.org/1999/xlink}href']
                data = self.connector.getTranslation(src, self.lang)
                if data:
                    return data
                
            return el[0].text
        
        return None

    def _getAttrib(self, tree, key, attrib):
        el = tree.xpath(key, namespaces=self.NSMAP)
        if el and el[0].attrib.has_key(attrib):
            return el[0].attrib[attrib]
        
        return None

    def _setRecordField(self, tree, key, record, field):
        value = self._getValue(tree, key)
        if value:
            record.setValue(field, value)
            return True
        
        return False

    def makeItem(self, item_id, record):
        data = self.connector.getData(item_id)
        data = data.replace('xml:id="', 'xml:id="XXid')
        tree = lxml.etree.fromstring(data.encode('utf-8'))

        id_ = self._getValue(tree, "./nuds:control/nuds:recordId")
        record.setValue('url', f"https://numismatics.org/collection/{id_}")

        title = self._getValue(tree, "./nuds:descMeta/nuds:title")
        if title and id_:
            if self.trim_title:
                title = re.sub(f"{id_}$", '', title)
                title = re.sub(r"\. $", '', title)

            record.setValue('title', title)
            
        self._setRecordField(tree, "./nuds:descMeta/nuds:adminDesc/nuds:department", record, 'region')
        self._setRecordField(tree, "./nuds:descMeta/nuds:physDesc/nuds:measurementsSet/nuds:weight", record, 'weight')
        self._setRecordField(tree, "./nuds:descMeta/nuds:physDesc/nuds:measurementsSet/nuds:diameter", record, 'diameter')
        self._setRecordField(tree, "./nuds:descMeta/nuds:physDesc/nuds:measurementsSet/nuds:shape", record, 'shape')
        self._setRecordField(tree, "./nuds:descMeta/nuds:subjectSet/nuds:subject[@localType='series']", record, 'series')
        self._setRecordField(tree, "./nuds:descMeta/nuds:noteSet/nuds:note", record, 'note')
        if not self._setRecordField(tree, "./nuds:descMeta/nuds:subjectSet/nuds:subject[@localType='subjectEvent']", record, 'subjectshort'):
            self._setRecordField(tree, "./nuds:descMeta/nuds:subjectSet/nuds:subject[@localType='subjectPerson']", record, 'subjectshort')

        refs = tree.xpath("./nuds:descMeta/nuds:refDesc/nuds:reference", namespaces=self.NSMAP)
        for i, ref in enumerate(refs[:4], start=1):
            value = " ".join([item.text for item in ref])
            record.setValue(f'catalognum{i}', value)

        url = self._getAttrib(tree, "./nuds:digRep/mets:fileSec/mets:fileGrp[@USE='obverse']/mets:file[@USE='archive']/mets:FLocat",
                             '{http://www.w3.org/1999/xlink}href')
        if url:
            image = self.connector.getImage(url, True)
            record.setValue('obverseimg', image)

        url = self._getAttrib(tree, "./nuds:digRep/mets:fileSec/mets:fileGrp[@USE='reverse']/mets:file[@USE='archive']/mets:FLocat",
                             '{http://www.w3.org/1999/xlink}href')
        if url:
            image = self.connector.getImage(url, True)
            record.setValue('reverseimg', image)

        url = self._getAttrib(tree, "./nuds:descMeta/nuds:refDesc/nuds:reference",
                             '{http://www.w3.org/1999/xlink}href')
        if url:
            if url.startswith('https://rpc.ashmus.ox.ac.uk'):
                url += '/xml'
            else:
                url += '.xml'
            raw_data = self.connector.download_data(url)
            if raw_data:
                tree = lxml.etree.fromstring(raw_data.encode('utf-8'))

        denomination = self._getValue(tree, "./nuds:descMeta/nuds:typeDesc/nuds:denomination")
        if denomination:
            if self.split_denomination:
                parts = re.match(r'(^[0-9,\.\s\-/]+)(.*)', denomination)
                if parts:
                    value, unit = parts.groups()
                    record.setValue('value', value)
                    record.setValue('unit', unit)
                else:
                    record.setValue('unit', denomination)
            else:
                record.setValue('unit', denomination)

        self._setRecordField(tree, "./nuds:descMeta/nuds:typeDesc/nuds:geographic/nuds:geogname[@xlink:role='region']", record, 'country')
        self._setRecordField(tree, "./nuds:descMeta/nuds:typeDesc/nuds:geographic/nuds:geogname[@xlink:role='mint']", record, 'mint')
        self._setRecordField(tree, "./nuds:descMeta/nuds:typeDesc/nuds:objectType", record, 'type')
        self._setRecordField(tree, "./nuds:descMeta/nuds:typeDesc/nuds:material", record, 'material')
        self._setRecordField(tree, "./nuds:descMeta/nuds:typeDesc/nuds:authority/nuds:persname[@xlink:role='dynasty']", record, 'period')
        self._setRecordField(tree, "./nuds:descMeta/nuds:typeDesc/nuds:authority/nuds:persname[@xlink:role='authority']", record, 'ruler')

        el1 = self._getValue(tree, "./nuds:descMeta/nuds:typeDesc/nuds:obverse/nuds:legend")
        el2 = self._getValue(tree, f"./nuds:descMeta/nuds:typeDesc/nuds:obverse/nuds:type/nuds:description[@xml:lang='{self.lang}']")
        if not el2:
            el2 = self._getValue(tree, "./nuds:descMeta/nuds:typeDesc/nuds:obverse/nuds:type/nuds:description[@xml:lang='en']")
        value = ' - '.join(filter(None, [el1, el2]))
        record.setValue('obversedesign', value)
        el1 = self._getValue(tree, "./nuds:descMeta/nuds:typeDesc/nuds:reverse/nuds:legend")
        el2 = self._getValue(tree, f"./nuds:descMeta/nuds:typeDesc/nuds:reverse/nuds:type/nuds:description[@xml:lang='{self.lang}']")
        if not el2:
            el2 = self._getValue(tree, "./nuds:descMeta/nuds:typeDesc/nuds:reverse/nuds:type/nuds:description[@xml:lang='en']")
        value = ' - '.join(filter(None, [el1, el2]))
        record.setValue('reversedesign', value)

        year = self._getValue(tree, "./nuds:descMeta/nuds:typeDesc/nuds:date")
        if not year:
            year = self._getValue(tree, "./nuds:descMeta/nuds:typeDesc/nuds:dateOnObject/nuds:date")
        if year:
            if self.enable_bc and 'BC' in year:
                year = year.replace('BCE', '').replace('BC', '').strip()
                year = -int(year)
            elif 'CE' in year:
                year = year.replace('CE', '').strip()

            record.setValue('year', year)
        el1 = self._getValue(tree, "./nuds:descMeta/nuds:typeDesc/nuds:dateRange/nuds:fromDate")
        el2 = self._getValue(tree, "./nuds:descMeta/nuds:typeDesc/nuds:dateRange/nuds:toDate")
        value = ' - '.join(filter(None, [el1, el2]))
        record.setValue('dateemis', value)
        
    def departmentChanged(self):
        self._clearTable()

        if self.departmentSelector.currentIndex() >= 0:
            self._partsEnable(True)
    
            for part in self.parts:
                part.currentIndexChanged.disconnect(self.partChanged)
                part.clear()
                part.currentIndexChanged.connect(self.partChanged)
    
            self.partChanged()
        else:
            self._partsEnable(False)

    def partChanged(self):
        self._clearTable()

        department = self.departmentSelector.currentData()
        country = self.countrySelector.currentData()
        ruler = self.rulerSelector.currentData()
        dynasty = self.dynastySelector.currentData()
        year = self.yearSelector.currentData()
        denomination = self.denominationSelector.currentData()
        material = self.materialSelector.currentData()
        type_ = self.typeSelector.currentData()
        images = self.imagesSelector.isChecked()

        countries = self.connector.getItems("region_facet", images, department=department,
                ruler=ruler, dynasty=dynasty, year=year,
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

        rulers = self.connector.getItems("authority_facet", images, department=department,
                country=country, dynasty=dynasty, year=year,
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

        dynasties = self.connector.getItems("dynasty_facet", images, department=department,
                country=country, ruler=ruler, year=year,
                denomination=denomination, material=material, type_=type_)
        self.dynastySelector.currentIndexChanged.disconnect(self.partChanged)
        self.dynastySelector.clear()
        self.dynastySelector.addItem(self.tr("(All)"), None)
        for item in dynasties:
            self.dynastySelector.addItem(item[1], item[0])
        index = self.dynastySelector.findData(dynasty)
        if index >= 0:
            self.dynastySelector.setCurrentIndex(index)
        self.dynastySelector.currentIndexChanged.connect(self.partChanged)

        years = self.connector.getItems("year_num", images, department=department,
                country=country, ruler=ruler, dynasty=dynasty,
                denomination=denomination, material=material, type_=type_)
        self.yearSelector.currentIndexChanged.disconnect(self.partChanged)
        self.yearSelector.clear()
        self.yearSelector.addItem(self.tr("(All)"), None)
        for item in years:
            year_showed = item[0]
            if self.enable_bc and int(year_showed) < 0:
                year_showed = str(-int(year_showed)) + " BC"
            self.yearSelector.addItem(year_showed, item[0])
        index = self.yearSelector.findData(year)
        if index >= 0:
            self.yearSelector.setCurrentIndex(index)
        self.yearSelector.currentIndexChanged.connect(self.partChanged)

        denominations = self.connector.getItems("denomination_facet", images, department=department,
                country=country, ruler=ruler, dynasty=dynasty, year=year,
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

        materials = self.connector.getItems("material_facet", images, department=department,
                country=country, ruler=ruler, dynasty=dynasty, year=year,
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

        types = self.connector.getItems("objectType_facet", images, department=department,
                country=country, ruler=ruler, dynasty=dynasty, year=year,
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

        if country or ruler or dynasty or year or denomination or material or type_:
            count = self.connector.getCount(images, department=department,
                country=country, ruler=ruler, dynasty=dynasty, year=year,
                denomination=denomination, material=material, type_=type_)

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
        dynasty = self.dynastySelector.currentData()
        year = self.yearSelector.currentData()
        denomination = self.denominationSelector.currentData()
        material = self.materialSelector.currentData()
        type_ = self.typeSelector.currentData()
        images = self.imagesSelector.isChecked()

        item_ids = self.connector.getIds(images, department=department,
                country=country, ruler=ruler, dynasty=dynasty, year=year,
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
                
                data = self.connector.getData(item_id)
                data = data.replace('xml:id="', 'xml:id="XXid')
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

                title = self._getValue(tree, "./nuds:descMeta/nuds:title")
                id_ = self._getValue(tree, "./nuds:control/nuds:recordId")
                if title and id_:
                    item = QTableWidgetItem(title)
                    self.table.setItem(i, 2, item)

                url = self._getAttrib(tree, "./nuds:descMeta/nuds:refDesc/nuds:reference",
                                     '{http://www.w3.org/1999/xlink}href')
                if url:
                    if url.startswith('https://rpc.ashmus.ox.ac.uk'):
                        url += '/xml'
                    else:
                        url += '.xml'
                    raw_data = self.connector.download_data(url)
                    if raw_data:
                        tree = lxml.etree.fromstring(raw_data.encode('utf-8'))

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

        result = image.loadFromData(self.connector.getImage(url, False))
        if result:
            if image.height() > self.HEIGHT:
                image = image.scaled(self.HEIGHT, self.HEIGHT,
                                     Qt.KeepAspectRatio, Qt.SmoothTransformation)
        return image

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
                btn = self.model.addCoins(record, len(indexes) - progress, self)
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
        if self.departmentSelector.currentIndex() >= 0:
            self.model.settings['ans_department'] = self.departmentSelector.currentData()
        self.model.settings['ans_has_image'] = self.imagesSelector.isChecked()
        self.model.settings.save()

        self.connector.close()
        super().done(r)
