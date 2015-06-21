# -*- coding: utf-8 -*-

import csv
import sys

from PyQt5 import QtGui

from OpenNumismat.Collection.Import import _Import


class ImportCabinet(_Import):
    Columns = {
        'title': None,
        'value': 'Nominal',
        'unit': 'idCurrency',
        'country': 'idCountry',
        'year': 'Date',
        'period': None,
        'mint': 'MintMark',
        'mintmark': None,
        'issuedate': None,
        'type': 'Type',
        'series': 'idSeries',
        'subjectshort': None,
        'status': None,
        'material': 'idMaterial',
        'fineness': 'idProbe',
        'shape': 'idForm',
        'diameter': 'Diameter',
        'thickness': 'Thickness',
        'weight': 'Weight',
        'grade': 'idSostojanie1',
        'edge': 'RandType',
        'edgelabel': 'Text_Rand',
        'obvrev': None,
        'quality': None,
        'mintage': 'Mintage',
        'dateemis': None,
        'catalognum1': 'Catalog',
        'catalognum2': 'Catalog_s1',
        'catalognum3': 'Catalog_s2',
        'catalognum4': 'Catalog_s3',
        'rarity': None,
        'price1': None,
        'price2': None,
        'price3': None,
        'price4': None,
        'paydate': 'Purchased',
        'payprice': 'Price',
        'totalpayprice': 'Price',
        'seller': 'SellerID',
        'payplace': 'PurchasedIn',
        'payinfo': 'PurchasedInfo',
        'saledate': 'Sold',
        'saleprice': 'PriceSold',
        'totalsaleprice': 'PriceSold',
        'buyer': 'BuyerID',
        'saleplace': None,
        'saleinfo': None,
        'note': None,
        'obverseimg': 'Picture',
        'obversedesign': 'Text_Avers',
        'obversedesigner': None,
        'reverseimg': 'Picture2',
        'reversedesign': 'Text_Revers',
        'reversedesigner': None,
        'edgeimg': None,
        'subject': 'HyperLinkCaption',
        'photo1': 'Picture3',
        'photo2': 'Picture4',
        'photo3': 'Picture5',
        'photo4': 'Picture6',
        'storage': 'CoinLocation',
        'features': 'CoinInfo'
    }

    def __init__(self, parent=None):
        super(ImportCabinet, self).__init__(parent)

    @staticmethod
    def isAvailable():
        return True

    def _connect(self, src):
        csv.field_size_limit(sys.maxsize)

        country = {}
        first_line = True
        with open(src + '/Территории.txt', 'r', encoding='utf-16-le') as f:
            reader = csv.reader(f, delimiter='\t')
            for row in reader:
                if first_line:
                    first_line = False
                else:
                    country[int(row[0])] = row[1]

        currency = {}
        first_line = True
        with open(src + '/Валюты.txt', 'r', encoding='utf-16-le') as f:
            reader = csv.reader(f, delimiter='\t')
            for row in reader:
                if first_line:
                    first_line = False
                else:
                    currency[int(row[0])] = row[1]

        material = {}
        first_line = True
        with open(src + '/Материал.txt', 'r', encoding='utf-16-le') as f:
            reader = csv.reader(f, delimiter='\t')
            for row in reader:
                if first_line:
                    first_line = False
                else:
                    material[int(row[0])] = row[1]

        form = {}
        first_line = True
        with open(src + '/Форма.txt', 'r', encoding='utf-16-le') as f:
            reader = csv.reader(f, delimiter='\t')
            for row in reader:
                if first_line:
                    first_line = False
                else:
                    form[int(row[0])] = row[1]

        sostojanie = {}
        first_line = True
        with open(src + '/Сохранность.txt', 'r', encoding='utf-16-le') as f:
            reader = csv.reader(f, delimiter='\t')
            for row in reader:
                if first_line:
                    first_line = False
                else:
                    sostojanie[int(row[0])] = row[1]

        address = {}
        first_line = True
        with open(src + '/Адресная книга.txt', 'r', encoding='utf-16-le') as f:
            reader = csv.reader(f, delimiter='\t')
            for row in reader:
                if first_line:
                    first_line = False
                else:
                    address[int(row[0])] = row[1]

        series = {}
        first_line = True
        with open(src + '/Серия.txt', 'r', encoding='utf-16-le') as f:
            reader = csv.reader(f, delimiter='\t')
            for row in reader:
                if first_line:
                    first_line = False
                else:
                    series[int(row[0])] = row[1]

        probe = {}
        first_line = True
        with open(src + '/Проба.txt', 'r', encoding='utf-16-le') as f:
            reader = csv.reader(f, delimiter='\t')
            for row in reader:
                if first_line:
                    first_line = False
                else:
                    probe[int(row[0])] = row[1]

        self.tables = {'idCountry': country, 'idCurrency': currency,
                  'idMaterial': material, 'idForm': form,
                  'idSostojanie1': sostojanie, 'idSostojanie2': sostojanie,
                  'idSoldPriceCurrensy': currency, 'idPriceCurrensy': currency,
                  'SellerID': address, 'BuyerID': address, 'idSeries': series,
                  'idProbe': probe}

        return src

    def _check(self, cursor):
        return True

    def _getRows(self, cursor):
        rows = []
        titles = []
        with open(cursor + '/Монеты.txt', 'r', encoding='utf-16-le') as f:
            reader = csv.reader(f, delimiter='\t')
            for row in reader:
                if not titles:
                    titles = row
                else:
                    r = {}
                    for i in range(len(titles)):
                        r[titles[i]] = row[i]

                    rows.append(r)

        return rows

    def _setRecord(self, record, row):
        for dstColumn, srcColumn in self.Columns.items():
            if srcColumn and srcColumn in row:
                rawData = row[srcColumn]
                if srcColumn in self.tables:
                    try:
                        index = int(rawData)
                        value = self.tables[srcColumn][index]
                    except ValueError:
                        value = None
                elif srcColumn in ['Picture', 'Picture1', 'Picture2', 'Picture3', 'Picture4', 'Picture5', 'Picture6']:
                    if rawData:
                        value = QtGui.QImage()
                        value.loadFromData(bytearray.fromhex(rawData))
                    else:
                        value = None
                else:
                    value = rawData

                record.setValue(dstColumn, value)

            if dstColumn == 'status':
                record.setValue(dstColumn, 'demo')
                if 'Sold' in row or 'PriceSold' in row:
                    record.setValue(dstColumn, 'sold')
                elif ('Present' in row and row['Present'] == 1) or 'Purchased' in row or 'Price' in row or 'PurchasedInfo' in row:
                    record.setValue(dstColumn, 'owned')

    def _close(self, connection):
        pass
