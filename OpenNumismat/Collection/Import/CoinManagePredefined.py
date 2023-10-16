# -*- coding: utf-8 -*-

from PySide6 import QtCore, QtGui
from PySide6.QtSql import QSqlDatabase, QSqlQuery
from PySide6.QtWidgets import QFileDialog

import OpenNumismat
from OpenNumismat.Collection.Import import _Import, _DatabaseServerError


class ImportCoinManagePredefined(_Import):
    Columns = {
        'title': None,
        'value': None,
        'unit': 'Denomination',
        'country': 'Country',
        'year': 'Year',
        'period': 'Type',
        'mint': 'Mints',
        'mintmark': 'Mint',
        'issuedate': None,
        'type': None,
        'series': None,
        'subjectshort': None,
        'status': None,
        'material': 'Composition',
        'fineness': None,
        'shape': None,
        'diameter': 'Diameter',
        'thickness': 'Thickness',
        'weight': 'Weight',
        'grade': None,
        'edge': 'Edge',
        'edgelabel': None,
        'obvrev': None,
        'quality': None,
        'mintage': 'Mintage',
        'dateemis': 'Type Years',
        'catalognum1': None,
        'catalognum2': None,
        'catalognum3': None,
        'catalognum4': None,
        'rarity': None,
        'price1': None,
        'price2': None,
        'price3': None,
        'price4': None,
        'variety': 'Variety',
        'paydate': None,
        'payprice': None,
        'totalpayprice': None,
        'saller': None,
        'payplace': None,
        'payinfo': None,
        'saledate': None,
        'saleprice': None,
        'totalsaleprice': None,
        'buyer': None,
        'saleplace': None,
        'saleinfo': None,
        'note': None,
        'obverseimg': None,
        'obversedesign': None,
        'obversedesigner': 'Designer',
        'reverseimg': None,
        'reversedesign': None,
        'reversedesigner': 'Designer',
        'edgeimg': None,
        'subject': None,
        'photo1': None,
        'photo2': None,
        'photo3': None,
        'photo4': None,
        'storage': None,
        'features': None
    }

    def __init__(self, parent=None):
        super(ImportCoinManagePredefined, self).__init__(parent)

    def _connect(self, src):
        db = QSqlDatabase.addDatabase('QODBC', 'CoinManage')
        db.setDatabaseName("DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=%s" % src)
        if not db.open():
            db.setDatabaseName("DRIVER={Microsoft Access Driver (*.mdb)};DBQ=%s" % src)
            if not db.open():
                raise _DatabaseServerError(db.lastError().text())

        # Check images folder
        self.imgDir = QtCore.QDir(src)
        if not self.imgDir.cd('../../Images'):
            directory = QFileDialog.getExistingDirectory(self.parent(),
                            self.tr("Select directory with pre-defined images"),
                            OpenNumismat.HOME_PATH)
            if directory:
                self.imgDir = QtCore.QDir(directory)
            else:
                return False

        return db

    def _check(self, db):
        self.priceTable = None
        tables = [row.lower() for row in db.tables()]

        for requiredTables in ('coinattributes', 'cointypes'):
            if requiredTables not in tables:
                return False

        for table in tables:
            if table[:6] == 'cmval~':
                self.priceTable = table

        if not self.priceTable:
            # Prices not found
            return False

        return True

    def _getRows(self, db):
        priceFields = ['F-12', 'F-16', 'VF-20', 'VF-30', 'XF-40', 'XF-45',
                       'AU-50', 'AU-55', 'AU-57', 'AU-58', 'AU-59', 'MS-60',
                       'MS-61', 'MS-62', 'MS-63', 'MS-64', 'MS-65', 'MS-66',
                       'MS-67', 'MS-68', 'MS-69', 'MS-70', 'F', 'VF', 'EF',
                       'AU', 'Unc', 'BU']
        priceSql = []
        for field in priceFields:
            priceSql.append("[%s].[%s]" % (self.priceTable, field))

        sql = "SELECT cointypes.*, \
                coinattributes.*, %s FROM (cointypes \
            LEFT JOIN coinattributes ON cointypes.[type id] = coinattributes.[type id]) \
            LEFT JOIN [%s] ON cointypes.[coin id] = [%s].[coin id]" % (','.join(priceSql), self.priceTable, self.priceTable)

        query = QSqlQuery(sql, db)
        records = []
        while query.next():
            records.append(query.record())

        return records

    def _setRecord(self, record, row):
        for dstColumn, srcColumn in self.Columns.items():
            if srcColumn:
                rawData = row.value(srcColumn)
                if isinstance(rawData, str):
                    if srcColumn == 'Mintage':
                        rawData = rawData.replace(',', '').replace('(', '').replace(')', '')
                    value = rawData.strip()
                else:
                    value = rawData

                record.setValue(dstColumn, value)

        # Process Status field
        record.setValue('status', 'demo')

        # Process prices
        fineFields = ['F-16', 'F-12', 'F']
        self.__processPrices(row, record, fineFields, 'price1')
        vfFields = ['VF-30', 'VF-20', 'VF']
        self.__processPrices(row, record, vfFields, 'price2')
        xfFields = ['XF-45', 'XF-40', 'AU-50', 'AU-55', 'AU-57', 'AU-58', 'AU-59', 'EF', 'AU']
        self.__processPrices(row, record, xfFields, 'price3')
        uncFields = ['MS-64', 'MS-63', 'MS-62', 'MS-61', 'MS-60', 'MS-65',
                     'MS-66', 'MS-67', 'MS-68', 'MS-69', 'MS-70', 'Unc', 'BU']
        self.__processPrices(row, record, uncFields, 'price4')

        value = row.value('UseGraphic')
        country = row.value('Country')
        typeId = row.value('Type ID')
        if value and country:
            dir_ = QtCore.QDir(self.imgDir)
            dir_.cd(country)
            image = QtGui.QImage()
            if image.load(dir_.absoluteFilePath(value)):
                record.setValue('obverseimg', image)
        if typeId and country:
            dir_ = QtCore.QDir(self.imgDir)
            dir_.cd(country)
            image = QtGui.QImage()
            if image.load(dir_.absoluteFilePath(str(typeId))):
                if record.isNull('obverseimg'):
                    record.setValue('obverseimg', image)
                else:
                    record.setValue('photo1', image)

        # Make a coin title (1673 Charles II Farthing - Brittania)
        year = record.value('year')
        period = record.value('period')
        unit = record.value('unit')
        variety = record.value('variety')
        mainTitle = ' '.join(filter(None, [year, period, unit]))
        title = ' - '.join(filter(None, [mainTitle, variety]))
        record.setValue('title', title)

    def _close(self, connection):
        connection.close()
        QSqlDatabase.removeDatabase('CoinManage')

    def __processPrices(self, row, record, srcFields, dstField):
        for field in srcFields:
            value = row.value(field)
            if isinstance(value, float) and value > 0:
                record.setValue(dstField, value)
                break
