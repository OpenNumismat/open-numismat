# -*- coding: utf-8 -*-

import base64

available = True

try:
    import lxml.etree
except ImportError:
    print('lxml module missed. Importing from CollectionStudio not available')
    available = False

from PyQt6 import QtCore, QtGui

from OpenNumismat.Collection.Import import _Import
from OpenNumismat.Tools.Converters import stringToMoney


class ImportCollectionStudio(_Import):
    Columns = {
        'title': None,
        'value': 'Nominal',
        'unit': 'Currency',
        'country': 'Country',
        'year': 'Year',
        'period': 'Region',
        'mint': 'Mint',
        'mintmark': None,
        'issuedate': None,
        'type': 'CoinType',
        'series': None,
        'subjectshort': None,
        'status': None,
        'material': 'Material',
        'fineness': None,
        'shape': None,
        'diameter': 'Diameter',
        'thickness': 'Thickness',
        'weight': 'Weight',
        'grade': 'Quality',
        'edge': 'HerdType',
        'edgelabel': None,
        'obvrev': 'ReversRotation',
        'quality': None,
        'mintage': None,
        'dateemis': None,
        'catalognum1': 'ExternalIndex',
        'catalognum2': 'Krause',
        'catalognum3': None,
        'catalognum4': None,
        'rarity': None,
        'price1': None,
        'price2': None,
        'price3': None,
        'price4': 'CatalogPrice',
        'variety': None,
        'paydate': 'Income',
        'payprice': 'Price',
        'totalpayprice': 'Price',
        'saller': 'Donator',
        'payplace': None,
        'payinfo': 'BuyComments',
        'saledate': None,
        'saleprice': None,
        'totalsaleprice': None,
        'buyer': None,
        'saleplace': None,
        'saleinfo': None,
        'note': None,
        'obverseimg': None,
        'obversedesign': None,
        'obversedesigner': None,
        'reverseimg': None,
        'reversedesign': None,
        'reversedesigner': None,
        'edgeimg': None,
        'subject': None,
        'photo1': None,
        'photo2': None,
        'photo3': None,
        'photo4': None,
        'storage': 'Storage',
        'features': 'Comments',
        'quantity': 'Duplicates',
        'url': None,
        'barcode': 'Barcode',
    }

    def __init__(self, parent=None):
        super(ImportCollectionStudio, self).__init__(parent)

    @staticmethod
    def isAvailable():
        return available

    def _connect(self, src):
        return src

    def _getRows(self, srcFile):
        tree = lxml.etree.parse(srcFile)
        rows = tree.xpath("/Collection/ITEM")
        return rows

    def _setRecord(self, record, row):
        for dstColumn, srcColumn in self.Columns.items():
            if srcColumn and row.find(srcColumn) is not None:
                rawData = row.find(srcColumn).text
                if rawData:
                    if srcColumn == 'Income':
                        value = QtCore.QDate.fromString(rawData, 'ddMMyyyy')
                    elif srcColumn == 'Year' and rawData == 'N/A':
                        value = None
                    elif srcColumn in ['Nominal', 'Diameter', 'Thickness',
                                       'ReversRotation', 'Weight']:
                        if rawData == '0':
                            value = None
                        else:
                            value = rawData
                    elif srcColumn == 'Duplicates':
                        if rawData == '0':
                            value = None
                        else:
                            value = int(rawData) + 1
                    elif srcColumn in ['Price', 'CatalogPrice']:
                        if rawData == '0':
                            value = None
                        else:
                            try:
                                value = stringToMoney(rawData)
                            except ValueError:
                                value = None
                    else:
                        value = rawData

                    record.setValue(dstColumn, value)

            if dstColumn == 'status':
                value = 'owned'
                # Process Status fields that contain translated text
                element = row.find('ItemStatus').find('Status')
                if element.text in ['Private', 'Частный', 'Прыватны']:
                    value = 'demo'
                elif element.text in ['Lost', 'Утерян', 'Згублен']:
                    value = 'wish'
                elif element.text in ['Sold', 'Продан', 'Прададзен']:
                    value = 'sold'

                record.setValue(dstColumn, value)

        imgFields = ['obverseimg', 'reverseimg', 'photo1',
                     'photo2', 'photo3', 'photo4']
        imageNo = 0
        imageElements = row.find('Images')
        if imageElements is not None:
            for element in imageElements.iter('Data'):
                if element.text:
                    value = base64.b64decode(bytes(element.text, 'latin-1'))
                    image = QtGui.QImage()
                    image.loadFromData(value)
                    record.setValue(imgFields[imageNo], image)
                    imageNo = imageNo + 1

        record.setValue('title', self.__generateTitle(record))

    def __generateTitle(self, record):
        title = ""
        if record.value('value'):
            title = title + record.value('value')
        if record.value('unit'):
            if title:
                title = title + ' '
            title = title + record.value('unit')
        if record.value('country'):
            if title:
                title = title + ', '
            title = title + record.value('country')
        if record.value('year'):
            if title:
                title = title + ' '
            title = title + '(' + record.value('year') + ')'

        return title
